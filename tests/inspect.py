from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://uarb.novascotia.ca/fmi/webd/UARB15?redirected=true", wait_until="load", timeout=45000)
    page.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="load", timeout=45000)
    page.wait_for_timeout(2000)

    search_box = page.locator(".inner_border > .text, textarea.fm-widget, input.fm-widget").first
    search_box.click()
    search_box.fill("M01234\n")

    page.get_by_role("button", name="Search").nth(4).click()
    page.wait_for_timeout(3000)

    print("\n--- ALL BUTTONS ON PAGE AFTER SEARCH ---")
    buttons = page.get_by_role("button").all()
    for idx, b in enumerate(buttons):
        txt = b.inner_text().strip().replace("\n", " ")
        if txt:
            print(f"[{idx}] '{txt}'")

    print("\nKeeping browser open for 30s. Click the tab manually if you want...")
    page.wait_for_timeout(30000)
    browser.close()