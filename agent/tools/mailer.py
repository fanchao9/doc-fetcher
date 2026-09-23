import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_zip_email(recipient_email: str, zip_filepath: str, email_body: str, subject: str = "Requested Documents") -> str:
    zip_path = Path(zip_filepath)
    if not zip_path.exists():
        raise FileNotFoundError(f"Archive {zip_filepath} does not exist.")

    sender_email = os.getenv("EMAIL_USER")
    sender_pass = os.getenv("EMAIL_PASS")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(email_body)

    with open(zip_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="zip",
            filename=zip_path.name
        )

    # Use SMTP_SSL for port 465
    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
        server.login(sender_email, sender_pass)
        server.send_message(msg)

    return f"Email successfully dispatched to {recipient_email} with {zip_path.name}."