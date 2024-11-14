from app import app
from models import db, OutreachAttempt
import json

with app.app_context():
    attempts = OutreachAttempt.query.all()
    for attempt in attempts:
        content = attempt.cached_email_content
        if not content:
            # If content is None or empty, set it to an empty dict
            attempt.cached_email_content = {}
        elif isinstance(content, str):
            try:
                # Try to load the JSON
                json.loads(content)
            except json.JSONDecodeError:
                # If it's invalid JSON, set it to an empty dict
                attempt.cached_email_content = {}
    db.session.commit()
    print("Database records updated.")
