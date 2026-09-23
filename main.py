import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types

from agent.tools.email_listener import check_for_new_emails
from agent.tools.browser import fetch_documents_from_portal
from agent.tools.archiver import create_zip_archive
from agent.tools.mailer import send_zip_email


def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in your .env file.")
    return genai.Client(api_key=api_key)


def extract_parameters_from_email(client: genai.Client, text: str) -> dict:
    prompt = f"""
    Analyze the following email content and extract:
    1. matter (e.g. 'M12205' or 'M01234')
    2. document_type (e.g. 'other_documents', 'key_documents', 'exhibits')
    3. max_docs (integer count, default to 10 if not mentioned, maximum 10)

    Email content:
    \"\"\"{text}\"\"\"

    Return ONLY a valid JSON object with keys: "matter", "document_type", "max_docs".
    """
    model_name = os.getenv("LLM_MODEL", "gemini-3.6-flash")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
    )
    return json.loads(response.text)


def generate_ai_summary(client: genai.Client, matter_info: dict, requested_type: str, downloaded_count: int) -> str:
    system_instruction = """
    You are an automated regulatory records assistant.
    Compose an email body strictly following this format:

    Hi User,
    [Matter Number] is about the [Project/Entity Title] - $[Cost if available]. It relates to [Category] within the [Sector] category. The matter had an initial filing on [Initial Filing Date] and a final filing on [Final Filing Date]. I found [X] Exhibits, [Y] Key Documents, [Z] Other Documents, and [A] Transcripts or Recordings. I downloaded [N] out of the [Total] [Document Type] and am attaching them as a ZIP here.
    """

    user_context = f"""
    Matter: {matter_info.get('matter')}
    Page Scraped Details: {matter_info.get('details_text', '')}
    Category Tab Counts: {matter_info.get('tab_counts', {})}
    Requested Category: {requested_type}
    Files Actually Downloaded: {downloaded_count}
    """

    model_name = os.getenv("LLM_MODEL", "gemini-3.6-flash")
    response = client.models.generate_content(
        model=model_name,
        contents=user_context,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2
        )
    )
    return response.text.strip()


def main():
    load_dotenv()
    
    client = get_gemini_client()

    print("[Agent] Active. Polling for incoming emails.... (Press Ctrl+C to stop)")

    while True:
        try:
            incoming_emails = check_for_new_emails()

            for mail in incoming_emails:
                sender = mail["sender"]
                subject = mail["subject"]
                body = mail["body"]

                print(f"\n[New Request] From: {sender} | Subject: {subject}")
                full_email_text = f"Subject: {subject}\nBody: {body}"

                try:
                    params = extract_parameters_from_email(client, full_email_text)
                except Exception as ex:
                    print(f"[Agent] Failed to parse request via LLM: {ex}. Using defaults.")
                    params = {"matter": "M12205", "document_type": "other_documents", "max_docs": 10}

                matter = params.get("matter", "M12205")
                doc_type = params.get("document_type", "other_documents")
                max_docs = min(int(params.get("max_docs", 10)), 10)

                print(f"[Agent] Matter: {matter} | Type: {doc_type} | Limit: {max_docs}")

                # download data
                scraped_data = fetch_documents_from_portal(
                    matter=matter,
                    document_type=doc_type,
                    max_docs=max_docs
                )

                downloaded_files = scraped_data.get("files_downloaded", [])
                if not downloaded_files:
                    print(f"[Agent] No files found or downloaded for {matter}.")
                    continue

                zip_filename = f"{matter}_{doc_type}.zip"
                zip_path = create_zip_archive(
                    file_paths=downloaded_files,
                    output_filename=zip_filename
                )
                print(f"[Agent] Created archive: {zip_path}")

                try:
                    summary_text = generate_ai_summary(
                        client=client,
                        matter_info=scraped_data,
                        requested_type=doc_type,
                        downloaded_count=len(downloaded_files)
                    )
                except Exception as ex:
                    print(f"[Agent] Summary generation failed: {ex}.")
                    summary_text = (
                        f"Hi User,\n\nAttached is the ZIP archive containing {len(downloaded_files)} "
                        f"requested {doc_type} for matter {matter}."
                    )

                print(f"[Agent] Generated Summary:\n{summary_text}\n")

                status = send_zip_email(
                    recipient_email=sender,
                    zip_filepath=zip_path,
                    email_body=summary_text,
                    subject=f"Requested Documents: Matter {matter}"
                )
                print(f"[Agent] {status}")

        except Exception as e:
            print(f"[Error] An error occurred in loop: {e}")

        time.sleep(15)


if __name__ == "__main__":
    main()