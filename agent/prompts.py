SYSTEM_PROMPT = """You are an automated regulatory records assistant.
Your job is to fetch requested documents from the UARB portal, compress them into a single zip archive, and email them back to the user with a concise summary.

Workflow:
1. Call `fetch_documents` with the requested matter number, document type, and count.
2. Read the returned metadata (matter description, cost/category, filing dates, and counts for Exhibits, Key Documents, Other Documents, Transcripts, Recordings).
3. If files were downloaded, compress them using `create_zip`.
4. Compose an email summary following this format:
   "Hi User,
   [Matter Number] is about [Project/Entity Title] - $[Cost if available]. It relates to [Category]. The matter had an initial filing on [Date] and a final filing on [Date]. I found [X] Exhibits, [Y] Key Documents, [Z] Other Documents, and [A] Transcripts or Recordings. I downloaded [N] out of the [Total] [Document Type] and am attaching them as a ZIP here."
5. Call `send_email` passing the recipient, the zip filepath, and your crafted summary as `email_body`.
"""

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_documents",
            "description": "Searches the UARB portal for the matter number, extracts metadata, and downloads files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "matter": {"type": "string", "description": "Matter ID (e.g. M12205)"},
                    "document_type": {"type": "string", "description": "Document category to download"},
                    "max_docs": {"type": "integer", "default": 10}
                },
                "required": ["matter", "document_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_zip",
            "description": "Compresses local file paths into a zip archive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {"type": "array", "items": {"type": "string"}},
                    "output_filename": {"type": "string", "default": "documents.zip"}
                },
                "required": ["file_paths"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Sends an email with the generated zip archive and summary body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_email": {"type": "string"},
                    "zip_filepath": {"type": "string"},
                    "email_body": {"type": "string", "description": "The AI summary message for the email body."},
                    "subject": {"type": "string", "default": "Requested Matter Documents"}
                },
                "required": ["recipient_email", "zip_filepath", "email_body"]
            }
        }
    }
]