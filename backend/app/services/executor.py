import os
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import TestExecution, TestScript, TestScreenshot, TestCase, TestCaseResult

from app.utils import CHINA_TZ

SCREENSHOTS_DIR = "/home/tang/ai-test-platform/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def _inject_screenshot_code(script: str, execution_id: int) -> str:
    """Replace take_screenshot calls with real Playwright screenshot code."""
    # Fix common import errors from LLM
    script = script.replace("from sync_playwright import sync_playwright", "from playwright.sync_api import sync_playwright")
    script = script.replace("from sync_playwright import *", "from playwright.sync_api import *")
    
    # Remove existing take_screenshot definition from script
    # Use a more careful regex that only matches the function definition and its body
    lines = script.split('\n')
    new_lines = []
    skip_until_next_def = False
    
    for i, line in enumerate(lines):
        # Check if this line starts a take_screenshot function definition
        if re.match(r'^def take_screenshot\s*\(', line):
            skip_until_next_def = True
            continue
        
        # If we're skipping, check if we've reached the next function/class/top-level code
        if skip_until_next_def:
            # If we hit a line that's not indented (or is a new def/class), stop skipping
            if line and not line[0].isspace() and not line.startswith('#'):
                skip_until_next_def = False
            else:
                continue
        
        new_lines.append(line)
    
    script = '\n'.join(new_lines)
    
    header = f'''
import os, sys, traceback
_SCREENSHOT_DIR = "{SCREENSHOTS_DIR}/{execution_id}"
os.makedirs(_SCREENSHOT_DIR, exist_ok=True)
_step_counter = [0]
_progress_counter = [0]
_total_cases = [0]

def set_total_cases(total):
    _total_cases[0] = total
    print(f"[PROGRESS] current=0 total={{total}}")

def report_progress():
    _progress_counter[0] += 1
    print(f"[PROGRESS] current={{_progress_counter[0]}} total={{_total_cases[0]}}")

def take_screenshot(page_or_step=None, step_or_desc=None, description=None):
    try:
        _step_counter[0] += 1
        # 兼容两种调用方式: take_screenshot(page, step, desc) 或 take_screenshot(step, desc)
        if page_or_step is not None and hasattr(page_or_step, 'screenshot'):
            # 第一个参数是page对象
            page = page_or_step
            num = step_or_desc if step_or_desc is not None else _step_counter[0]
            desc = description or ""
        else:
            # 没有传page，从调用栈获取
            page = None
            num = page_or_step if page_or_step is not None else _step_counter[0]
            desc = step_or_desc or ""
            caller_frame = sys._getframe(1)
            page = caller_frame.f_globals.get("page") or caller_frame.f_locals.get("page")
        if page is None:
            print("[SCREENSHOT_ERROR] page not found")
            return None
        path = os.path.join(_SCREENSHOT_DIR, "step_{{}}.png".format(num))
        page.screenshot(path=path)
        # Write meta for post-processing
        print("[SCREENSHOT_META] step={{}} desc={{}} path={{}}".format(num, desc, path))
        return path
    except Exception as e:
        print("[SCREENSHOT_ERROR] {{}}".format(e))
        return None
'''
    return header + "\n" + script


def _parse_output(output: str):
    """Parse test output for results and screenshots."""
    results = []
    screenshots = []
    summary = None

    for line in output.split("\n"):
        line = line.strip()

        # Parse [PASS] or [FAIL] lines - 支持 [FAIL] #ID 用例名 | 失败原因 格式
        match = re.match(r"\[(PASS|FAIL)\]\s*(.*?)$", line)
        if match:
            status = match.group(1).lower()
            content = match.group(2).strip()
            
            # 提取 case_id: #123 开头
            case_id = None
            id_match = re.match(r"#(\d+)\s*(.*)", content)
            if id_match:
                case_id = int(id_match.group(1))
                content = id_match.group(2).strip()
            
            # 检查是否有失败原因（用 | 分隔）
            if "|" in content:
                parts = content.split("|", 1)
                name = parts[0].strip()
                error_message = parts[1].strip()
            else:
                name = content
                error_message = None
            
            results.append({
                "status": status,
                "name": name,
                "case_id": case_id,
                "error_message": error_message
            })

        # Parse screenshot metadata
        match = re.search(r"\[SCREENSHOT_META\] step=(\d+(?:\.\d+)?) desc=(.*?) path=(.*)", line)
        if match:
            screenshots.append({
                "step_number": float(match.group(1)),
                "description": match.group(2).strip(),
                "path": match.group(3).strip(),
            })

        # Parse summary
        match = re.search(r"\[SUMMARY\] passed=(\d+) failed=(\d+) total=(\d+)", line)
        if match:
            summary = {"passed": int(match.group(1)), "failed": int(match.group(2)), "total": int(match.group(3))}

    return results, screenshots, summary


def execute_suite(db: Session, execution_id: int):
    """Execute a test suite's current script."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        return

    script = (
        db.query(TestScript)
        .filter(TestScript.suite_id == execution.suite_id, TestScript.is_current == True)
        .first()
    )
    if not script:
        execution.status = "error"
        execution.error_message = "未找到测试脚本"
        db.commit()
        return

    # 计算用例数量，动态调整超时时间
    from app.models.models import TestSuiteFunction, TestFunctionCase, TestCase
    suite_functions = db.query(TestSuiteFunction).filter(TestSuiteFunction.suite_id == execution.suite_id).all()
    function_ids = [sf.function_id for sf in suite_functions]
    function_cases = db.query(TestFunctionCase).filter(TestFunctionCase.function_id.in_(function_ids)).all()
    case_ids = [fc.test_case_id for fc in function_cases]
    cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
    total_cases = len(cases)
    
    # 动态超时：每个用例60秒，最少120秒，最多600秒
    timeout = max(120, min(600, total_cases * 60))
    
    execution.status = "running"
    execution.start_time = datetime.now(timezone.utc)
    execution.total_cases = total_cases
    execution.completed_cases = 0
    db.commit()

    # Prepare script file
    full_script = _inject_screenshot_code(script.script_content, execution_id)

    tmp_file = None
    try:
        tmp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
        tmp_file.write(full_script)
        tmp_file.close()

        PYTHON = "/home/tang/.hermes/hermes-agent/venv/bin/python3"
        
        # 使用Popen实现实时输出读取
        process = subprocess.Popen(
            [PYTHON, tmp_file.name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=SCREENSHOTS_DIR,
        )
        
        output_lines = []
        import select
        start_time = time.time()
        
        # 实时读取输出
        while True:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > timeout:
                process.kill()
                raise subprocess.TimeoutExpired(cmd=tmp_file.name, timeout=timeout)
            
            # 检查是否有输出可读
            ready, _, _ = select.select([process.stdout], [], [], 0.1)
            if ready:
                line = process.stdout.readline()
                if line:
                    output_lines.append(line)
                    line = line.strip()
                    
                    # 解析进度信息
                    progress_match = re.search(r"\[PROGRESS\] current=(\d+) total=(\d+)", line)
                    if progress_match:
                        current = int(progress_match.group(1))
                        total = int(progress_match.group(2))
                        execution.completed_cases = current
                        db.commit()
            
            # 检查进程是否结束
            if process.poll() is not None:
                # 读取剩余输出
                remaining = process.stdout.read()
                if remaining:
                    output_lines.append(remaining)
                break
        
        output = ''.join(output_lines)
        print(f"[DEBUG] Script output: {output[:500]}")  # Debug logging
        
        results, screenshots, summary = _parse_output(output)

        # Save screenshots to DB - 根据步骤号推断属于哪个用例
        for s in screenshots:
            if os.path.exists(s["path"]):
                # 步骤号整数部分对应用例序号（从1开始）
                case_id = None
                step_num = s["step_number"]
                case_index = int(step_num) - 1
                if 0 <= case_index < len(results):
                    # 优先用 case_id 匹配，其次用名字
                    r = results[case_index]
                    if r.get("case_id"):
                        case_id = r["case_id"]
                    else:
                        case_name = r["name"]
                        matching = next((c for c in cases if c.name == case_name), None)
                        if matching:
                            case_id = matching.id
                
                db.add(TestScreenshot(
                    execution_id=execution_id,
                    case_id=case_id,
                    step_number=s["step_number"],
                    step_description=s["description"],
                    screenshot_path=s["path"],
                ))

        # Save test case results to DB - 优先用case_id匹配
        for r in results:
            if r.get("case_id"):
                case_id = r["case_id"]
            else:
                matching = next((c for c in cases if c.name == r["name"]), None)
                case_id = matching.id if matching else None
            db.add(TestCaseResult(
                execution_id=execution_id,
                case_id=case_id,
                status="passed" if r["status"] == "pass" else "failed",
                error_message=r.get("error_message"),
            ))

        # Determine overall status - 只要脚本执行完成就标记为passed
        if summary:
            execution.passed_cases = summary["passed"]
            execution.failed_cases = summary["failed"]
            execution.status = "passed"
        elif results:
            execution.passed_cases = sum(1 for r in results if r["status"] == "pass")
            execution.failed_cases = sum(1 for r in results if r["status"] == "fail")
            execution.status = "passed"
        else:
            execution.status = "error"
            execution.error_message = f"脚本执行无输出。返回码: {process.returncode}\n完整输出:\n{output}"

    except subprocess.TimeoutExpired:
        execution.status = "error"
        execution.error_message = f"执行超时（{timeout}秒）"
    except Exception as e:
        execution.status = "error"
        execution.error_message = str(e)
    finally:
        if tmp_file and os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

        execution.end_time = datetime.now(timezone.utc)
        if execution.start_time:
            # 确保两个datetime都是aware或都是naive
            start = execution.start_time
            end = execution.end_time
            if start.tzinfo is None and end.tzinfo is not None:
                start = start.replace(tzinfo=timezone.utc)
            elif start.tzinfo is not None and end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            delta = end - start
            execution.duration = int(delta.total_seconds())
        db.commit()
