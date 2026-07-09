"""
driver.py -- Playwright screenshot driver for the veritrade-imports
Streamlit dashboard.

Launches `uv run streamlit run app.py --server.headless true`, drives it
with a real headless Chromium (via the `playwright` Python package -- no
`chromium-cli`/Node available in this environment, so this talks to
Playwright directly), and saves screenshots to
`.claude/skills/run-veritrade-imports/screenshots/`.

Usage:
  uv run python .claude/skills/run-veritrade-imports/driver.py
  uv run python .claude/skills/run-veritrade-imports/driver.py --port 8502
  uv run python .claude/skills/run-veritrade-imports/driver.py --no-server   # app already running, just drive it

Must be run with PYTHONIOENCODING=utf-8 (Streamlit's emoji-laden log lines
crash the Windows console otherwise -- see SKILL.md Gotchas):
  PYTHONIOENCODING=utf-8 uv run python .claude/skills/run-veritrade-imports/driver.py
"""
from __future__ import annotations

import argparse
import os
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"


def wait_for_server(url: str, timeout: float = 40.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument("--no-server", action="store_true",
                     help="Don't launch streamlit -- assume it's already running on --port")
    args = ap.parse_args()

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    base_url = f"http://localhost:{args.port}"

    proc = None
    if not args.no_server:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        proc = subprocess.Popen(
            ["uv", "run", "streamlit", "run", "app.py",
             "--server.headless", "true", "--server.port", str(args.port)],
            cwd=str(ROOT), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        print(f"Streamlit launching (pid {proc.pid})...")
        if not wait_for_server(base_url):
            print("Streamlit no respondió a tiempo.")
            proc.kill()
            return 1
        print("Streamlit listo.")

    exit_code = 0
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1400, "height": 1000})
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            js_errors = []
            page.on("pageerror", lambda exc: js_errors.append(str(exc)))

            page.goto(base_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1500)
            shot = SCREENSHOT_DIR / "01_home.png"
            page.screenshot(path=str(shot))
            print(f"Screenshot: {shot}")

            page.goto(f"{base_url}/Camiones", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            shot = SCREENSHOT_DIR / "02_camiones_global.png"
            page.screenshot(path=str(shot))
            print(f"Screenshot: {shot}")

            sinotruk_radio = page.get_by_text("🟡 Sinotruk", exact=True)
            sinotruk_radio.click()
            page.wait_for_timeout(2500)
            shot = SCREENSHOT_DIR / "03_camiones_sinotruk_tab.png"
            page.screenshot(path=str(shot))
            print(f"Screenshot: {shot}")

            submarca_heading = page.get_by_text("Sub-marca declarada en aduana").first
            submarca_heading.scroll_into_view_if_needed()
            page.wait_for_timeout(1500)
            shot = SCREENSHOT_DIR / "04_submarca_chart.png"
            page.screenshot(path=str(shot))
            print(f"Screenshot: {shot}")

            print(f"\nConsole errors (informational -- Streamlit itself logs some "
                  f"'Failed to load resource' 404s on tab-switch that don't affect "
                  f"rendering, see SKILL.md Gotchas): {len(console_errors)}")
            for e in console_errors:
                print(f"  {e}")

            print(f"Uncaught JS exceptions (fatal): {len(js_errors)}")
            for e in js_errors:
                print(f"  {e}")
            if js_errors:
                exit_code = 1

            browser.close()
    finally:
        if proc is not None:
            proc.kill()
            proc.wait(timeout=10)
            print("Streamlit detenido.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
