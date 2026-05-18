from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import TestSuite, TestScript, TestExecution
from app.utils import format_datetime
from app.services.llm_service import generate_script, build_script_prompt
from app.services.executor import execute_suite
from app.services.selector_validator import extract_selectors, validate_selectors, build_validation_feedback
import httpx


router = APIRouter(prefix="/api", tags=["generation"])


def fetch_page_html(url: str) -> tuple:
    """获取页面HTML结构，用于生成准确的选择器
    
    返回: (html_text, feature_summary)
    """
    try:
        import re
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url)
            html = resp.text
            # 移除script和style标签内容，只保留结构
            html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL)
            # 移除注释
            html_clean = re.sub(r'<!--.*?-->', '', html_clean, flags=re.DOTALL)
            
            # 分析页面实际存在的功能（只检查HTML标签，不检查文本内容）
            features = []
            # 检查是否有真正的input标签（排除type=hidden）
            if re.search(r'<input(?![^>]*type=["\']hidden["\'])', html_clean, re.IGNORECASE):
                features.append("包含输入框")
            if re.search(r'<button', html_clean, re.IGNORECASE):
                features.append("包含按钮")
            if re.search(r'<select', html_clean, re.IGNORECASE):
                features.append("包含下拉选择框")
            # 分页：检查是否有分页相关的class或组件
            if re.search(r'class="[^"]*(?:pagination|pager|page-nav)[^"]*"', html_clean, re.IGNORECASE):
                features.append("有分页组件")
            # 搜索：检查是否有搜索框
            if re.search(r'<input[^>]*(?:search|placeholder)', html_clean, re.IGNORECASE):
                features.append("有搜索框")
            # 排序：检查是否有排序相关的select或按钮
            if re.search(r'<select[^>]*(?:sort|order)', html_clean, re.IGNORECASE):
                features.append("有排序选择框")
            
            # 提取主要class和id
            classes = re.findall(r'class="([^"]*)"', html_clean)
            ids = re.findall(r'id="([^"]*)"', html_clean)
            
            feature_summary = f"页面包含的class: {', '.join(set(classes[:10]))}\n"
            feature_summary += f"页面包含的id: {', '.join(set(ids[:10]))}\n"
            feature_summary += f"页面特征: {', '.join(features) if features else '无特殊功能特征'}"
            
            # 简化：只保留前2000字符的关键结构
            return html_clean[:2000], feature_summary
    except Exception as e:
        return f"<!-- 获取页面失败: {str(e)} -->", "无法分析页面功能"


@router.post("/suites/{suite_id}/generate")
async def generate_suite_script(suite_id: int, db: Session = Depends(get_db)):
    """Generate a Playwright test script from suite cases using LLM."""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")

    if not suite.functions:
        raise HTTPException(status_code=400, detail="套件下没有功能，请先添加功能")

    # Build cases list for prompt from all functions in suite
    cases_list = []
    function_urls = []
    for func in suite.functions:
        if func.url:
            function_urls.append(func.url)
        for c in func.cases:
            cases_list.append({
                "id": c.id,
                "name": c.name,
                "case_type": c.case_type,
                "description": c.description,
                "expected_result": c.expected_result,
                "function_name": func.name,
                "function_url": func.url,
            })

    if not cases_list:
        raise HTTPException(status_code=400, detail="套件下没有测试用例，请先添加用例")

    # Use function URLs for script generation
    urls_text = "\n".join([f"- {u}" for u in function_urls]) if function_urls else "未指定"
    
    # 获取第一个URL的页面HTML结构和功能分析
    page_html = ""
    feature_summary = ""
    if function_urls:
        page_html, feature_summary = fetch_page_html(function_urls[0])
    
    prompt = build_script_prompt(suite.name, urls_text, cases_list, page_html, feature_summary)
    
    # 生成脚本（单次，不重试）
    script_content = await generate_script(db, prompt)
    
    # 验证选择器（只检查，不重试，避免耗时过长）
    validation_result = None
    selectors = extract_selectors(script_content)
    if selectors and function_urls:
        test_url = list(set(function_urls))[0]
        validation_result = await validate_selectors(test_url, selectors)
    
    # Mark old scripts as not current
    db.query(TestScript).filter(
        TestScript.suite_id == suite_id, TestScript.is_current == True
    ).update({"is_current": False})

    # Determine version
    last = (
        db.query(TestScript)
        .filter(TestScript.suite_id == suite_id)
        .order_by(TestScript.version.desc())
        .first()
    )
    version = (last.version + 1) if last else 1

    script = TestScript(
        suite_id=suite_id,
        version=version,
        script_content=script_content,
        is_current=True,
    )
    db.add(script)
    db.commit()
    db.refresh(script)

    result = {
        "id": script.id,
        "suite_id": script.suite_id,
        "version": script.version,
        "script_content": script.script_content,
        "is_current": script.is_current,
        "created_at": format_datetime(script.created_at),
    }
    if validation_result:
        result["selector_validation"] = validation_result
    return result


@router.post("/suites/{suite_id}/execute")
def execute_suite_endpoint(suite_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Execute the current script for a suite."""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")

    script = (
        db.query(TestScript)
        .filter(TestScript.suite_id == suite_id, TestScript.is_current == True)
        .first()
    )
    if not script:
        raise HTTPException(status_code=400, detail="未生成测试脚本，请先生成")

    execution = TestExecution(
        suite_id=suite_id,
        script_id=script.id,
        status="pending",
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Run in background with its own db session
    import threading
    def _run():
        from app.models.database import SessionLocal
        db2 = SessionLocal()
        try:
            execute_suite(db2, execution.id)
        finally:
            db2.close()
    threading.Thread(target=_run, daemon=True).start()

    return {
        "id": execution.id,
        "suite_id": execution.suite_id,
        "status": execution.status,
        "created_at": format_datetime(execution.created_at),
    }


@router.get("/suites/{suite_id}/executions")
def list_suite_executions(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")

    execs = (
        db.query(TestExecution)
        .filter(TestExecution.suite_id == suite_id)
        .order_by(TestExecution.created_at.desc())
        .all()
    )

    return [
        {
            "id": e.id,
            "suite_id": e.suite_id,
            "script_id": e.script_id,
            "status": e.status,
            "start_time": format_datetime(e.start_time),
            "end_time": format_datetime(e.end_time),
            "duration": e.duration,
            "total_cases": e.total_cases or 0,
            "passed_cases": e.passed_cases or 0,
            "failed_cases": e.failed_cases or 0,
            "error_message": e.error_message,
            "created_at": format_datetime(e.created_at),
        }
        for e in execs
    ]


@router.get("/suites/{suite_id}/scripts")
def list_suite_scripts(suite_id: int, db: Session = Depends(get_db)):
    scripts = (
        db.query(TestScript)
        .filter(TestScript.suite_id == suite_id)
        .order_by(TestScript.version.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "suite_id": s.suite_id,
            "version": s.version,
            "script_content": s.script_content,
            "is_current": s.is_current,
            "created_at": format_datetime(s.created_at),
        }
        for s in scripts
    ]


@router.get("/scripts/{script_id}")
def get_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(TestScript).filter(TestScript.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return {
        "id": script.id,
        "suite_id": script.suite_id,
        "version": script.version,
        "script_content": script.script_content,
        "is_current": script.is_current,
        "created_at": format_datetime(script.created_at),
    }
