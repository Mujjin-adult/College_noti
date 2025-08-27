from playwright.sync_api import sync_playwright


def crawl_with_headless(url: str, actions=None):
    """
    Playwright 기반 동적 렌더링 크롤러 예시
    actions: {'scroll': True, 'click': ['#btn']}
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        if actions:
            if actions.get("scroll"):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            for selector in actions.get("click", []):
                page.click(selector)
        html = page.content()
        browser.close()
        return html
