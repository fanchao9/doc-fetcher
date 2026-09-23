from dotenv import load_dotenv
load_dotenv()

from agent.tools.browser import fetch_documents_from_portal
from agent.tools.archiver import create_zip_archive
from agent.tools.mailer import send_zip_email

files = fetch_documents_from_portal(matter="M01234", document_type="other_documents", max_docs=2)
print("Downloaded files:", files)

if files:
    print("Archiver:")
    zip_path = create_zip_archive(files, "test_output.zip")
    print("Created archive at:", zip_path)

    print("Mailer:")
    status = send_zip_email(
        recipient_email="fanchaolin2005@gmail.com",
        zip_filepath=zip_path,
        subject="Agent Manual Tool Test"
    )
    print("Mailer status:", status)