from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from models import Website, EmailLog, User, db
from content_generator import generate_followup_email
from email_sender import send_email

scheduler = BackgroundScheduler()
scheduler.start()

def schedule_followup(website_id, user_id):
    website = Website.query.get(website_id)
    if website and website.status == 'outreach_started':
        next_followup = datetime.now() + timedelta(days=3.5)
        scheduler.add_job(send_followup, 'date', run_date=next_followup, args=[website_id, user_id])

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
