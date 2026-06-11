"""End-to-end UI smoke test for the static web app.

Starts a throwaway static server over public/ and drives both areas with a
headless browser:
- storefront (index.html): renders the catalog (providers + services), and the
  "Instant Estimate" cross-link navigates to the pricing page;
- pricing (pricing.html): the estimate -> provider options -> checkout flow
  produces a persisted booking, and the back-link returns to the storefront.

Exits 0 on pass, 1 on failure, 0 with a SKIP notice if Playwright is unavailable
(so it never breaks a pipeline that hasn't installed browsers).

Usage: python eval/e2e_smoke.py
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("SKIP: Playwright not installed "
          "(pip install playwright && python -m playwright install chromium)")
    raise SystemExit(0)


def _wait_until_up(timeout_s: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(BASE, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def _run_checks() -> list[str]:
    """Return a list of failure messages (empty == pass)."""
    failures: list[str] = []
    js_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.on("console", lambda m: js_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: js_errors.append(str(e)))

        # --- storefront ---
        page.goto(BASE + "/", wait_until="networkidle")
        page.wait_for_timeout(2500)  # in-browser Babel compile
        services = page.locator(".grid > *").count()
        if services < 20:
            failures.append(f"storefront: expected 20+ service cards, got {services}")
        if page.locator("a.estimate").count() != 1:
            failures.append("storefront: missing 'Instant Estimate' cross-link")

        # --- cross-link -> pricing ---
        page.click("a.estimate")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        if not page.url.endswith("pricing.html"):
            failures.append(f"cross-link did not reach pricing.html (url={page.url})")
        if "$" not in page.inner_text("#mid"):
            failures.append("pricing: estimate did not render a price")

        # --- pricing booking flow ---
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(700)
        page.click("#toproviders")
        page.wait_for_timeout(400)
        if page.locator("#opts .opt").count() < 2:
            failures.append("pricing: provider options did not render")
        page.locator("#opts .opt button").first.click()
        page.wait_for_timeout(300)
        page.click("#checkout")
        page.wait_for_timeout(400)
        if page.locator("#bookings-list .bk").count() != 1:
            failures.append("pricing: checkout did not create a booking")

        # --- persistence + back-link ---
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(500)
        if page.locator("#bookings-list .bk").count() != 1:
            failures.append("pricing: booking did not persist across reload")
        page.click(".site-header .logo")   # logo links back to the storefront home
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        if page.evaluate("document.getElementById('root')?.children.length || 0") < 1:
            failures.append("back-link did not return to the storefront")

        browser.close()

    if js_errors:
        failures.append(f"console errors: {js_errors}")
    return failures


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--directory", str(PUBLIC)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        if not _wait_until_up():
            print("FAIL: static server did not come up")
            return 1
        failures = _run_checks()
    finally:
        server.terminate()

    if failures:
        print("E2E SMOKE: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("E2E SMOKE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
