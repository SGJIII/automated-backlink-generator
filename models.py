from db import db
from datetime import datetime

# Association table for many-to-many relationship between Campaign and Website
campaign_website = db.Table('campaign_website',
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True),
    db.Column('website_id', db.Integer, db.ForeignKey('website.id'), primary_key=True)
)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    domain_authority = db.Column(db.Float)
    page_authority = db.Column(db.Float)
    author_name = db.Column(db.Text)  # Changed from String(200) to Text
    author_email = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')
    automated_reply_enabled = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(500))  # Add this line
    snippet = db.Column(db.Text)  # Add this line
    outreach_attempts = db.relationship('OutreachAttempt', backref='website', lazy=True)
    source = db.Column(db.String(200))  # Add this line

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    sent_date = db.Column(db.DateTime)
    email_type = db.Column(db.String(50))  # 'initial', 'followup', 'reply'
    content = db.Column(db.Text)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    content_text = db.Column(db.Text)
    created_date = db.Column(db.DateTime)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)
    company = db.Column(db.String(120), nullable=True)
    company_profile = db.Column(db.Text, nullable=True)
    email_provider = db.Column(db.String(50), nullable=True)
    email_settings = db.Column(db.JSON, nullable=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    campaign_type = db.Column(db.String(20), nullable=False)
    target_url = db.Column(db.String(200))
    keyword = db.Column(db.String(100))
    press_release = db.Column(db.Text)
    topic = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('campaigns', lazy=True))
    websites = db.relationship('Website', secondary=campaign_website, lazy='subquery',
        backref=db.backref('campaigns', lazy=True))

class OutreachAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    last_contact_date = db.Column(db.DateTime, default=datetime.utcnow)
    automated_followup = db.Column(db.Boolean, default=False)
    automated_reply = db.Column(db.Boolean, default=False)
    cached_email_content = db.Column(db.Text)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    outreach_attempts = db.relationship('OutreachAttempt', backref='author', lazy=True)
