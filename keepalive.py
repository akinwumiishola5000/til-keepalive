"""
Keep The Insilico Lab Streamlit apps awake.
Opens each app in a headless browser, clicks the wake-up button if the app
is asleep, and waits until the app has actually rendered.
Exits with an error if any app fails, so GitHub emails you.
"""
import re
import sys
import time

from playwright.sync_api import sync_playwright

APPS = [
    "https://theinsilicolab-workspace.streamlit.app/",
    "https://theinsilicolab-molcov.streamlit.app/",
    "https://theinsilicolab-holosift.streamlit.app/",
]

WAKE_TEXT = re.compile(r"get this app back up", re.I)
BOOT_TIMEOUT_S = 240  # how long to wait for a sleeping app to boot


def app_rendered(page) -> bool:
    """True if the Streamlit app container exists in the page or any iframe."""
    for frame in page.frames:
        try:
            if frame.locator('[data-testid="stApp"]').count() > 0:
                return True
        except Exception:
            pass
    return False


def click_wake_button(page) -> bool:
    """Click the 'Yes, get this app back up!' button if present."""
    for frame in page.frames:
        try:
            btn = frame.get_by_role("button", name=WAKE_TEXT)
            if btn.count() > 0:
                btn.first.click()
                return True
        except Exception:
            pass
    return False


def visit(browser, url: str) -> bool:
    page = browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(10_000)  # let the sleep page or app load

        woke = click_wake_button(page)
        print(f"{url}: {'was ASLEEP, clicked wake button' if woke else 'no wake button'}")

        deadline = time.time() + BOOT_TIMEOUT_S
        while time.time() < deadline:
            if app_rendered(page):
                print(f"{url}: app is UP")
                return True
            page.wait_for_timeout(5_000)

        print(f"{url}: app did not render within {BOOT_TIMEOUT_S}s")
        return False
    except Exception as exc:
        print(f"{url}: ERROR {exc}")
        return False
    finally:
        page.close()


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        results = [visit(browser, url) for url in APPS]
        browser.close()
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
