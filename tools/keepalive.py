#!/usr/bin/env python3
"""Visit the app with a real browser so Streamlit Community Cloud never puts it to sleep.

A plain HTTP request is not enough: the app only starts when a browser runs its
JavaScript and opens the websocket. This script opens the page, presses the
"get this app back up" button if the app had already dozed off, and waits until
the hub has rendered.

usage: python tools/keepalive.py https://fos-tag.streamlit.app/
"""
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "https://fos-tag.streamlit.app/"
MARK = "Tools and Games"            # text that only the rendered hub shows

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(url, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(6000)
    woke = False
    btn = page.get_by_role("button", name="Yes, get this app back up!")
    if btn.count():
        btn.first.click()
        woke = True
        print("app was asleep; pressed the wake-up button")
    def rendered() -> bool:
        # On Community Cloud the app itself lives in an iframe, so look through every frame.
        for frame in page.frames:
            try:
                if MARK in frame.inner_text("body", timeout=2000):
                    return True
            except Exception:
                pass
        return False

    deadline = time.time() + 240
    ok = False
    while time.time() < deadline:
        if rendered():
            ok = True
            break
        btn = page.get_by_role("button", name="Yes, get this app back up!")
        if btn.count():
            btn.first.click()
            woke = True
            print("app was asleep; pressed the wake-up button")
        page.wait_for_timeout(3000)
    page.screenshot(path="keepalive.png")
    browser.close()
    print("app is up" if ok else "app did not render in time", "(woke it)" if woke else "")
    sys.exit(0 if ok else 1)
