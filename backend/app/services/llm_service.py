import httpx
import json
from sqlalchemy.orm import Session
from app.models.models import ModelConfig


async def get_default_config(db: Session) -> ModelConfig:
    cfg = db.query(ModelConfig).filter(ModelConfig.is_default == True).first()
    if not cfg:
        cfg = db.query(ModelConfig).first()
    if not cfg:
        raise ValueError("未配置模型，请先在设置中添加模型配置")
    return cfg


async def call_llm(db: Session, system_prompt: str, user_prompt: str, temperature: float = 0.1, max_tokens: int = 8000) -> str:
    """通用LLM调用"""
    cfg = await get_default_config(db)

    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"

    base_url = (cfg.base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": cfg.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"] or ""
    return content.strip()


async def generate_script(db: Session, prompt: str) -> str:
    """生成测试脚本"""
    cfg = await get_default_config(db)

    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"

    base_url = (cfg.base_url or "https://api.openai.com/v1").rstrip("/")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": cfg.model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个专业的自动化测试脚本生成器。"
                    "请只输出可执行的Python Playwright脚本代码，不要包含任何解释或markdown标记。"
                    "脚本必须使用 sync_playwright，chromium 无头模式。"
                    "对每个用例打印结果，格式: [PASS] #用例ID 用例名称 或 [FAIL] #用例ID 用例名称 | 失败原因。"
                    "用例ID和名称必须与用户提供的列表完全一致。"
                    "每个用例执行过程中必须调用 take_screenshot(step_number, description) 截图。"
                    "take_screenshot 由执行环境提供，不要自己实现。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 8000,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"] or ""
    # MiMo等推理模型的回复在reasoning_content中
    if not content.strip() and data["choices"][0]["message"].get("reasoning_content"):
        content = data["choices"][0]["message"]["reasoning_content"]

    # Strip markdown fences
    if content.startswith("```"):
        lines = content.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == "```":
                end = i
                break
        content = "\n".join(lines[start:end])

    return content.strip()


async def generate_test_cases_from_url(db: Session, url: str, description: str = "") -> list:
    """从URL生成测试用例"""
    
    # 获取页面实际HTML结构
    page_html = ""
    feature_info = ""
    try:
        import re as _re
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url)
            html = resp.text
            # 清理HTML，只保留结构
            html_clean = _re.sub(r'<script[^>]*>.*?</script>', '', html, flags=_re.DOTALL)
            html_clean = _re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=_re.DOTALL)
            html_clean = _re.sub(r'<!--.*?-->', '', html_clean, flags=_re.DOTALL)
            
            # 分析页面实际存在的功能和元素
            features = []
            html_lower = html_clean.lower()
            
            # 检测实际存在的UI元素
            if '<input' in html_lower or '<textarea' in html_lower:
                input_types = _re.findall(r'<input[^>]*type=["\'](\w+)["\']', html_lower)
                features.append(f"包含输入框 (类型: {', '.join(set(input_types))})" if input_types else "包含输入框")
            if '<button' in html_lower or 'btn' in html_lower:
                features.append("包含按钮")
            if '<select' in html_lower or '<option' in html_lower:
                features.append("包含下拉选择框")
            if '<form' in html_lower:
                features.append("包含表单")
            if '<table' in html_lower or '<th' in html_lower or '<td' in html_lower:
                features.append("包含表格")
            if 'pagination' in html_lower or 'page-link' in html_lower or 'pager' in html_lower:
                features.append("包含分页")
            if '<input[^>]*type=["\']search["\']' in html_lower or 'search' in html_lower.split('<input')[0] if '<input' in html_lower else False:
                features.append("包含搜索")
            if '<a ' in html_lower:
                links = _re.findall(r'<a[^>]*href=["\']([^"\']+)["\']', html_lower)
                if links:
                    features.append(f"包含链接 (如: {', '.join(links[:3])})")
            
            # 提取主要的class和id，帮助LLM生成准确选择器
            classes = _re.findall(r'class="([^"]*)"', html_clean)
            ids = _re.findall(r'id="([^"]*)"', html_clean)
            
            # 构建功能描述
            feature_info = "=== 页面实际存在的功能和元素 ===\n"
            feature_info += "\n".join([f"- {f}" for f in features]) if features else "- 页面结构简单，无复杂交互元素"
            feature_info += f"\n\n页面包含的CSS类: {', '.join(set(classes[:15]))}"
            feature_info += f"\n页面包含的ID: {', '.join(set(ids[:10]))}"
            feature_info += "\n\n⚠️ 重要：只能为上面列出的实际存在的功能生成测试用例！不要凭想象添加页面没有的功能！"
            
            page_html = html_clean[:2000]
    except Exception as e:
        feature_info = f"无法获取页面: {str(e)}"

    system_prompt = """你是一个专业的测试工程师。请根据给定的URL和页面实际结构，生成测试用例列表。

输出格式必须是JSON数组，每个用例包含：
- name: 用例名称
- case_type: "positive" 或 "negative"
- description: 用例描述（这个用例测试什么）
- focus_point: 关注点（重点关注什么）
- preconditions: 前提条件（执行前需要什么条件）
- expected_result: 预期结果描述

只输出JSON数组，不要有其他内容。"""

    user_prompt = f"""URL: {url}
{f'页面描述: {description}' if description else ''}

{feature_info}

{f'页面HTML结构: {page_html[:1500]}' if page_html else ''}

请基于页面实际存在的功能生成5-10个测试用例，包括：
- 正例：正常场景的测试（只测试页面实际存在的功能）
- 反例：边界条件、错误输入等异常场景

⚠️ 再次强调：不要生成页面不存在功能的用例（如页面没有搜索框就不要生成搜索测试）"""

    content = await call_llm(db, system_prompt, user_prompt)

    # 尝试解析JSON
    try:
        # 去掉可能的markdown标记
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取JSON部分
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        print(f"[ERROR] LLM返回内容无法解析: {content[:500]}")
        raise ValueError(f"无法解析LLM返回的JSON: {content[:200]}")


async def generate_test_cases_from_swagger(db: Session, swagger_content: str) -> list:
    """从Swagger文档生成测试用例"""
    system_prompt = """你是一个专业的测试工程师。请根据Swagger/OpenAPI文档，为每个API接口生成测试用例。

输出格式必须是JSON数组，每个用例包含：
- name: 用例名称（接口名 + 场景描述）
- case_type: "positive" 或 "negative"
- url: 测试URL
- input_data: 请求参数（JSON格式）
- expected_result: 预期结果描述

只输出JSON数组，不要有其他内容。"""

    user_prompt = f"""Swagger文档内容：
{swagger_content[:5000]}

请为每个接口生成正例和反例测试用例。"""

    content = await call_llm(db, system_prompt, user_prompt)

    try:
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"无法解析LLM返回的JSON: {content[:200]}")


async def generate_test_cases_from_prd(db: Session, prd_content: str) -> list:
    """从需求文档生成测试用例"""
    system_prompt = """你是一个专业的测试工程师。请根据产品需求文档(PRD)，生成功能测试用例。

输出格式必须是JSON数组，每个用例包含：
- name: 用例名称
- case_type: "positive" 或 "negative"
- description: 用例描述（这个用例测试什么）
- focus_point: 关注点（重点关注什么）
- preconditions: 前提条件（执行前需要什么条件）
- expected_result: 预期结果描述

只输出JSON数组，不要有其他内容。"""

    user_prompt = f"""产品需求文档：
{prd_content[:8000]}

请根据需求生成全面的测试用例，覆盖正常流程和异常场景。"""

    content = await call_llm(db, system_prompt, user_prompt)

    try:
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"无法解析LLM返回的JSON: {content[:200]}")


def build_script_prompt(suite_name: str, suite_url: str, cases: list, page_html: str = "", feature_summary: str = "") -> str:
    positive_cases = [c for c in cases if c["case_type"] == "positive"]
    negative_cases = [c for c in cases if c["case_type"] == "negative"]
    
    # 获取所有功能的URL
    function_urls = list(set([c.get("function_url") for c in cases if c.get("function_url")]))
    urls_text = ", ".join(function_urls) if function_urls else "未指定"
    
    parts = [
        f"请为以下测试套件生成 Playwright (Python) 自动化测试脚本。",
        f"测试目标网址: {urls_text}",
        f"套件名称: {suite_name}",
        "",
        "重要：必须使用上面提供的测试目标网址，不要使用其他网址！",
        "",
    ]
    
    # 添加实际页面HTML结构
    if page_html:
        parts.extend([
            "=== 实际页面HTML结构（请基于此生成选择器）===",
            "注意：请使用实际存在的class和id，不要猜测！",
            "",
            page_html[:2000],  # 限制长度避免token超限
            "",
            "=== 页面HTML结束 ===",
            "",
        ])
    
    # 添加页面功能分析
    if feature_summary:
        parts.extend([
            "=== 页面功能分析（重要！请基于实际功能生成用例）===",
            feature_summary,
            "",
            "注意：以上是页面实际存在的功能。如果用例要求测试页面不存在的功能（如搜索、分页等），"
            "必须仍然生成测试代码，但应在代码中检测该功能是否存在，不存在则打印 [FAIL] 并说明原因。",
            "",
        ])
    
    parts.extend([
        "要求：",
        "1. 使用 sync_playwright，headless=True",
        "2. 必须基于上面的实际HTML结构选择元素，不要使用猜测的选择器",
        "3. 直接调用 take_screenshot(step_number, description) 来截图（函数由执行环境提供，不要自己实现）。",
        "4. 测试完成后，对每个用例打印一行结果，格式：",
        "   [PASS] #用例ID 用例名称  或  [FAIL] #用例ID 用例名称 | 失败原因",
        "   例如: [PASS] #61 商品列表页面正常加载",
        "   ⚠️ 用例ID和名称必须与上面列出的完全一致，一字不差！",
        "5. 最后打印汇总行，格式：[SUMMARY] passed=N failed=N total=N",
        "6. ⚠️ 必须覆盖上面列出的所有用例，不能跳过任何一个！如果页面没有对应功能，也要写测试代码并在断言失败时打印 [FAIL]",
        "7. ⚠️ 每个用例执行过程中必须至少调用一次 take_screenshot！不管是通过还是失败，都要截图记录。step_number 从1开始递增，不能重复。",
        "",
    ])

    if positive_cases:
        parts.append("=== 正例（应该成功） ===")
        for i, c in enumerate(positive_cases, 1):
            parts.append(f"{i}. #{c['id']} {c['name']}")
            if c.get("input_data"):
                parts.append(f"   输入: {json.dumps(c['input_data'], ensure_ascii=False)}")
            if c.get("expected_result"):
                parts.append(f"   预期: {c['expected_result']}")
        parts.append("")

    if negative_cases:
        parts.append("=== 反例（应该失败或报错） ===")
        for i, c in enumerate(negative_cases, 1):
            parts.append(f"{i}. #{c['id']} {c['name']}")
            if c.get("input_data"):
                parts.append(f"   输入: {json.dumps(c['input_data'], ensure_ascii=False)}")
            if c.get("expected_result"):
                parts.append(f"   预期: {c['expected_result']}")
        parts.append("")

    return "\n".join(parts)


async def generate_cases_from_text(db: Session, description: str, function_name: str) -> list:
    """从自然语言描述生成测试用例"""
    system_prompt = "你是一个测试专家，根据用户描述生成测试用例。只返回JSON数组，不要其他文字。"
    
    user_prompt = f"""根据以下描述，生成测试用例列表。

功能名称：{function_name}
用户描述：{description}

要求：
1. 分析功能点和场景
2. 生成正例（正常流程）和反例（异常/边界情况）
3. 每个用例要有明确的关注点和预期结果

返回JSON数组：
[
    {{
        "name": "用例名称",
        "type": "正例或反例",
        "description": "用例描述",
        "focus_point": "关注点",
        "preconditions": "前置条件",
        "expected_result": "预期结果"
    }}
]"""

    response = await call_llm(db, system_prompt, user_prompt)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise Exception("无法解析生成结果")
