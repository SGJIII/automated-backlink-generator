from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models import Website, EmailLog, User, db
from content_generator import generate_outreach_email_content  # Change this line
from email_sender import send_email

scheduler = BackgroundScheduler()
scheduler.start()

def schedule_followup(website_id, user_id):
    website = Website.query.get(website_id)
    if website:
        # Generate follow-up content
        followup_content = generate_outreach_email_content(website, user_id, is_followup=True)  # Update this line
        # Send follow-up email
        success = send_email(user_id, website.author_email, "Follow-up: Backlink Request", followup_content)
        if success:
            # Log the follow-up email
            email_log = EmailLog(website_id=website_id, email_type='followup', content=followup_content)
            db.session.add(email_log)
            db.session.commit()

def send_followup(website_id, user_id):
    website = Website.query.get(website_id)
    user = User.query.get(user_id)
    if website and website.status == 'outreach_started' and user:
        followup_attempt = EmailLog.query.filter_by(website_id=website_id, email_type='followup').count() + 1
        followup_content = generate_followup_email(website, followup_attempt)
        send_email(user.id, website.author_email, "Follow-up: Backlink Request", followup_content)
        
        log_entry = EmailLog(website_id=website_id, sent_date=datetime.now(), email_type='followup', content=followup_content)
        db.session.add(log_entry)
        db.session.commit()
        
        # Schedule the next followup
        schedule_followup(website_id, user_id)
