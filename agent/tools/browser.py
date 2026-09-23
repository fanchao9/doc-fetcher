import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

DOWNLOAD_DIR = Path("./temp_downloads")


def fetch_documents_from_portal(matter: str, document_type: str, max_docs: int = 10) -> dict:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_files: list[str] = []
    limit = min(max(1, max_docs), 10)

    clean_type = document_type.replace("_", " ").strip()
    tab_pattern = re.compile(rf"^{re.escape(clean_type)}", re.IGNORECASE)

    metadata = {
        "matter": matter,
        "details_text": "",
        "tab_counts": {},
        "files_downloaded": []
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto("https://uarb.novascotia.ca/fmi/webd/UARB15?redirected=true", wait_until="load", timeout=45000)
            page.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="load", timeout=45000)
            page.wait_for_timeout(2000)

            search_input = page.locator(".inner_border > .text, textarea.fm-widget, input.fm-widget").nth(7)
            search_input.wait_for(state="visible", timeout=20000)
            search_input.click()
            page.wait_for_timeout(500)
            page.keyboard.type(matter, delay=100)
            page.keyboard.press("Enter")

            search_btn = page.get_by_role("button", name="Search").nth(4)
            search_btn.wait_for(state="visible", timeout=10000)
            search_btn.click()
            page.wait_for_timeout(3000)

            try:
                header_text = page.locator(".fm_object_19, .fm-text-paragraph, .inner_border").all_inner_texts()
                metadata["details_text"] = " ".join([t.strip() for t in header_text if t.strip()])[:1500]
            except Exception:
                pass

            buttons = page.get_by_role("button").all()
            for b in buttons:
                txt = b.inner_text().strip().replace("\n", " ")
                if any(k in txt for k in ["Exhibits", "Key Documents", "Other Documents", "Transcripts", "Recordings"]):
                    metadata["tab_counts"][txt] = txt
            category_tab = page.get_by_role("button", name=tab_pattern).first
            category_tab.wait_for(state="visible", timeout=10000)
            category_tab.click()
            page.wait_for_timeout(2500)
            go_buttons = page.get_by_role("button", name="GO GET IT").all()

            for i, _ in enumerate(go_buttons[:limit]):
                current_go_btn = page.get_by_role("button", name="GO GET IT").nth(i)
                current_go_btn.click()
                page.wait_for_timeout(2000)

                doc_file_btn = page.get_by_role("button", name=re.compile(r"\.(pdf|docx?|xlsx?)$", re.I)).first

                try:
                    if doc_file_btn.is_visible(timeout=5000):
                        with page.expect_download(timeout=15000) as download_info:
                            doc_file_btn.click()
                        download = download_info.value

                        target_path = DOWNLOAD_DIR / download.suggested_filename
                        download.save_as(str(target_path))
                        saved_files.append(str(target_path))
                except PlaywrightTimeoutError:
                    pass

                close_btn = page.get_by_role("button", name="Close")
                if close_btn.is_visible(timeout=3000):
                    close_btn.click()
                    page.wait_for_timeout(1000)

        finally:
            context.close()
            browser.close()

    metadata["files_downloaded"] = saved_files
    return metadata