import re
import smtplib
from email.message import EmailMessage

def clean_text(text):
    # Remove HTML tags
    text = re.sub(r'<[^>]*?>', '', text)
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s{2,}', ' ', text)
    # Trim leading and trailing whitespace
    text = text.strip()
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text


def send_email(subject, body, to_email, smtp_host, smtp_port, smtp_user, smtp_password, from_email=None, use_tls=True):
    """Send a plain-text email using SMTP."""
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_email or smtp_user
        msg["To"] = to_email
        msg.set_content(body)

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        
        if use_tls:
            server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
    except smtplib.SMTPAuthenticationError as e:
        raise Exception(f"SMTP Authentication failed. Check your username and password. Error: {str(e)}")
    except smtplib.SMTPConnectError as e:
        raise Exception(f"Could not connect to SMTP server {smtp_host}:{smtp_port}. Check your SMTP settings. Error: {str(e)}")
    except smtplib.SMTPException as e:
        raise Exception(f"SMTP error occurred: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error while sending email: {str(e)}")