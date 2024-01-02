# email_utils.py

from email.mime.text import MIMEText
import smtplib
from custom_logger import setup_logger
from libs.config import read_config

config = read_config()

logger = setup_logger(__name__)

def send_email(to, message, subject):
    smtp_server = config.get("email_server", "smtp.gmail.com")
    smtp_port = config.get("email_port", "587")
    smtp_username = config.get("email_username", "test@gmail.com")
    smtp_password = config.get("email_password", "test")

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = config.get("email_sender", "test@gmail.com")
    msg['To'] = to

    server.sendmail(config.get("email_sender", "test@gmail.com"), [to], msg.as_string())

    server.quit()
    logger.info(f"Email sent for email id : {to} - with message : {message}")