import traceback
from models import User
from email_providers import send_via_mailgun, send_via_smtp

def send_email(user_id, to_email, subject, body):
    try:
        user = User.query.get(user_id)
        if not user:
            print(f"User with id {user_id} not found")
            return False

        print(f"User email settings: {user.email_settings}")  # Add this line
        print(f"User email provider: {user.email_provider}")  # Add this line

        if not user.email_provider:
            print(f"Email provider not set for user {user_id}")
            return False

        print(f"Attempting to send email to {to_email} using {user.email_provider}")

        if user.email_provider == 'mailgun':
            success = send_via_mailgun(
                from_email=user.email,
                to_email=to_email,
                subject=subject,
                body=body,
                api_key=user.email_settings.get('api_key'),
                domain=user.email_settings.get('domain')
            )
        elif user.email_provider == 'smtp':
            success = send_via_smtp(
                from_email=user.email,
                to_email=to_email,
                subject=subject,
                body=body,
                smtp_server=user.email_settings.get('smtp_server'),
                smtp_port=user.email_settings.get('smtp_port'),
                smtp_username=user.email_settings.get('smtp_username'),
                smtp_password=user.email_settings.get('smtp_password')
            )
        else:
            print(f"Unsupported email provider: {user.email_provider}")
            return False

        if success:
            print(f"Email sent successfully to {to_email}")
        else:
            print(f"Failed to send email to {to_email}")

        return success

    except Exception as e:
        print(f"An error occurred while sending email: {str(e)}")
        traceback.print_exc()  # This will print the full stack trace
        return False
