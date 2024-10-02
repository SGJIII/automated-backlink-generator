from models import User
from email_providers import send_via_mailgun, send_via_smtp

def send_email(user_id, to_email, subject, body):
    user = User.query.get(user_id)
    if not user:
        print(f"User with id {user_id} not found")
        return False

    if user.email_provider == 'mailgun':
        return send_via_mailgun(
            from_email=user.email,
            to_email=to_email,
            subject=subject,
            body=body,
            api_key=user.email_settings.get('api_key'),
            domain=user.email_settings.get('domain')
        )
    elif user.email_provider == 'smtp':
        return send_via_smtp(
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
