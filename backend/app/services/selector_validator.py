"""选择器验证：生成脚本后预跑检查选择器是否真实存在，不执行任何操作。"""
import re
import asyncio
from playwright.async_api import async_playwright


def extract_selectors(script_content: str) -> list[str]:
    """从脚本代码中提取所有CSS选择器。
    
    支持的模式:
    - page.query_selector("selector")
    - page.locator("selector")
    - page.querySelector("selector")
    - page.wait_for_selector("selector")
    - locator('.product-card') 等嵌套调用
    """
    selectors = set()
    
    patterns = [
        r'''(?:query_selector|locator|querySelector|wait_for_selector)\s*\(\s*["']([^"']+)["']''',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, script_content):
            sel = match.group(1).strip()
            # 跳过变量占位符 (f-string 里的 {variable})
            if '{' in sel and '}' in sel:
                continue
            # 跳过明显不是CSS选择器的
            if sel.startswith('screenshot_') or sel.startswith('['):
                continue
            selectors.add(sel)
    
    return list(selectors)


async def validate_selectors(url: str, selectors: list[str], timeout: float = 10.0) -> dict:
    """用Playwright加载页面，逐个检查选择器是否存在。
    
    只做 goto + query_selector，不点击、不填表、不提交。
    
    返回: {
        "valid": bool,          # 是否全部通过
        "found": [str],         # 找到的选择器
        "missing": [str],       # 找不到的选择器
    }
    """
    if not selectors:
        return {"valid": True, "found": [], "missing": []}
    
    found = []
    missing = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=int(timeout * 1000), wait_until="domcontentloaded")
            try:
                await page.wait_for_load_state("networkidle", timeout=int(timeout * 1000))
            except Exception:
                pass  # networkidle 超时不致命，页面可能已经加载完了
            
            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        found.append(sel)
                    else:
                        missing.append(sel)
                except Exception:
                    missing.append(sel)
            
            await browser.close()
    except Exception as e:
        return {
            "valid": False,
            "found": [],
            "missing": selectors,
            "error": str(e),
        }
    
    return {
        "valid": len(missing) == 0,
        "found": found,
        "missing": missing,
    }


def build_validation_feedback(missing_selectors: list[str]) -> str:
    """把验证失败的选择器转成给LLM的反馈提示。"""
    lines = [
        "",
        "=== 上一次生成的脚本中以下选择器在页面上找不到，请修正 ===",
    ]
    for sel in missing_selectors:
        lines.append(f"  找不到: {sel}")
    lines.append("")
    lines.append("请根据上面提供的实际HTML结构，使用页面上真实存在的class和id。")
    lines.append("")
    return "\n".join(lines)
