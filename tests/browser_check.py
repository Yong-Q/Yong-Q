"""Browser integration validation; install Playwright locally to run."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765"
repos = json.loads((ROOT / "data/repositories.json").read_text())
config = json.loads((ROOT / "profile.json").read_text())
results = []

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1280, "height": 1000}, color_scheme="light")
    page_errors = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.route("https://api.github.com/**", lambda route: route.fulfill(json=repos))
    page.goto(BASE)
    page.wait_for_function("document.querySelector('#status').textContent.startsWith('Live')")
    assert page.locator(".project").count() == 3
    assert "classical density functional theory (cDFT)" in page.locator(".intro").inner_text()
    assert "Alex" not in page.locator("body").inner_text()
    assert "@163.com" not in page.locator("body").inner_text()
    page.screenshot(path=str(ROOT / "preview-desktop.png"), full_page=True)
    page.locator("#theme").click()
    assert page.evaluate("document.documentElement.dataset.theme") == "dark"
    page.screenshot(path=str(ROOT / "preview-dark.png"), full_page=True)
    page.locator("#theme").click()
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(ROOT / "preview-mobile.png"), full_page=True)
    results.extend(["desktop: 3 cards and cDFT", "dark theme toggle", "mobile 390px: no horizontal overflow"])

    # Real browser refresh with a newly published repository and untrusted text.
    new = {"name": "New-research", "description": "<img src=x onerror=alert(1)> | new project", "language": "Python", "size": 10,
           "fork": False, "private": False, "archived": False, "pushed_at": "2099-01-01T00:00:00Z"}
    page.unroute("https://api.github.com/**")
    page.route("https://api.github.com/**", lambda route: route.fulfill(json=repos + [new]))
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#recent-projects').textContent.includes('New-research')")
    assert page.locator("#recent-projects img").count() == 0
    results.append("new repository appears on refresh; API text cannot inject HTML")
    before = page.locator("#recent-projects").inner_text()
    page.unroute("https://api.github.com/**")
    page.route("https://api.github.com/**", lambda route: route.fulfill(status=503, body="Unavailable"))
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#status').textContent.includes('unavailable')")
    assert page.locator("#recent-projects").inner_text() == before
    results.append("API failure retains last good display")

    # Direct-file fallback must retain raw curated config, not filtered snapshot config.
    initial = json.loads((ROOT / "data/profile.json").read_text())
    initial["featured"] = [item for item in initial["featured"] if item["name"] != "Sep-Pilot"]
    changed = [dict(item) for item in repos]
    for item in changed:
        if item["name"] == "Reverse-design-of-porous-materials": item["description"] = None
    page.unroute("https://api.github.com/**")
    page.route("https://api.github.com/**", lambda route: route.fulfill(json=changed))
    init_js = "window.PROFILE_INITIAL=" + json.dumps(initial) + ";window.PROFILE_CONFIG=" + json.dumps(config) + ";"
    page.route("**/assets/initial.js", lambda route: route.fulfill(body=init_js, content_type="text/javascript"))
    page.route("**/profile.json", lambda route: route.fulfill(status=403, body="File access unavailable"))
    page.goto(BASE)
    page.wait_for_function("document.querySelector('#status').textContent.startsWith('Live')")
    assert page.locator(".project").count() == 3, "Missing snapshot project must reappear from raw curated config"
    assert config["featured"][0]["summary"] in page.locator(".project").first.inner_text(), "Cleared API description must restore curated summary"
    results.append("direct-file fallback restores missing featured projects and curated summaries")

    # Inspect actual SVG layout and generate a panel image for review.
    page.unroute("**/profile.json")
    page.unroute("**/assets/initial.js")
    page.set_viewport_size({"width": 960, "height": 850})
    page.goto(BASE + "/assets/panel-light.svg")
    overflow = page.evaluate("""[...document.querySelectorAll('text')].filter(t=>{const b=t.getBBox();return b.x<0||b.y<0||b.x+b.width>960||b.y+b.height>850}).map(t=>t.textContent)""")
    assert not overflow, overflow
    page.screenshot(path=str(ROOT / "preview-panel.png"))
    results.append("SVG panel: all text stays inside bounds")
    assert not page_errors, page_errors
    browser.close()

(ROOT / "docs/browser-validation.json").write_text(json.dumps({"checks": results, "passed": len(results)}, indent=2) + "\n")
print(json.dumps({"passed": len(results), "checks": results}, indent=2))
