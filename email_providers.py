import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_via_mailgun(from_email, to_email, subject, body, api_key, domain):
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "text": body
            }
        )
        response.raise_for_status()
        print(f"Email sent successfully via Mailgun: {response.text}")
        return True
    except requests.RequestException as e:
        print(f"Error sending email via Mailgun: {str(e)}")
        return False

def send_via_smtp(from_email, to_email, subject, body, smtp_server, smtp_port, smtp_username, smtp_password):
    try:
        print(f"SMTP settings: server={smtp_server}, port={smtp_port}, username={smtp_username}")
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Enable debug output
        server.starttls()
        print("Attempting to log in...")
        server.login(smtp_username, smtp_password)
        print("Login successful")
        server.send_message(msg)
        server.quit()

        print(f"Email sent successfully via SMTP")
        return True
    except Exception as e:
        print(f"Error sending email via SMTP: {str(e)}")
        return False
