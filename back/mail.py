import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=_env_path)

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_PASS = os.getenv("GMAIL_PASS", "")


def enviar_mail(mail, archivo):
    msg = MIMEMultipart()
    msg["Subject"] = "taller.ai — Tu documento"
    msg["From"] = GMAIL_USER
    msg["To"] = mail
    msg.attach(MIMEText("Te enviamos el documento generado con taller.ai", "plain"))

    with open(archivo, "rb") as f:
        parte = MIMEBase("application", "octet-stream")
        parte.set_payload(f.read())

    encoders.encode_base64(parte)
    parte.add_header(
        "Content-Disposition",
        f"attachment; filename={os.path.basename(archivo)}"
    )

    msg.attach(parte)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
