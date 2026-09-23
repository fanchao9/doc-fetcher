from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://uarb.novascotia.ca/fmi/webd/UARB15?redirected=true", wait_until="load", timeout=45000)
    page.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="load", timeout=45000)
    page.wait_for_timeout(3000)

    print("\n--- ALL EDITABLE INPUTS ON INITIAL PAGE ---")
    inputs = page.locator(".inner_border > .text, textarea.fm-widget, input.fm-widget").all()
    for idx, inp in enumerate(inputs):
        box = inp.bounding_box()
        val = inp.input_value() if inp.get_attribute("type") else inp.inner_text()
        print(f"Input [{idx}]: Pos(x={box['x'] if box else '?'}, y={box['y'] if box else '?'}) | Current Val: '{val}'")

    print("\n--- ALL SEARCH BUTTONS ---")
    search_btns = page.get_by_role("button", name="Search").all()
    for idx, b in enumerate(search_btns):
        box = b.bounding_box()
        print(f"Search Button [{idx}]: Pos(x={box['x'] if box else '?'}, y={box['y'] if box else '?'})")

    page.wait_for_timeout(15000)
    browser.close()