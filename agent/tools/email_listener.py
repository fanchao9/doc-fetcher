import imaplib
import email
from email.header import decode_header
import os

def check_for_new_emails() -> list[dict]:
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")

    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(user, password)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")
    if status != "OK" or not messages[0]:
        mail.close()
        mail.logout()
        return []

    incoming_requests = []

    for num in messages[0].split():
        status, data = mail.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        sender = email.utils.parseaddr(msg.get("From"))[1]
        subject_header = decode_header(msg.get("Subject", ""))[0]
        subject = subject_header[0]
        if isinstance(subject, bytes):
            subject = subject.decode(subject_header[1] or "utf-8")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        incoming_requests.append({
            "sender": sender,
            "subject": subject,
            "body": body
        })

    mail.close()
    mail.logout()
    return incoming_requests