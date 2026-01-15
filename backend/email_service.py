import smtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

GMAIL_USER = "rajitkumaran27@gmail.com"
GMAIL_APP_PASSWORD = "kugj lxnd rtza tapk"


def send_email(to_emails: list[str], subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)
