from db import db

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    domain_authority = db.Column(db.Float)
    author_name = db.Column(db.String(200))
    author_email = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')
    automated_reply_enabled = db.Column(db.Boolean, default=False)
    outreach_attempts = db.relationship('OutreachAttempt', backref='website', lazy=True)
    campaigns = db.relationship('Campaign', secondary='campaign_website', backref='websites')

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
    name = db.Column(db.String(120), nullable=True)  # Changed to nullable=True
    company = db.Column(db.String(120), nullable=True)  # Changed to nullable=True
    company_profile = db.Column(db.Text, nullable=True)  # Changed to nullable=True
    email_provider = db.Column(db.String(50), nullable=True)
    email_settings = db.Column(db.JSON, nullable=True)
    campaigns = db.relationship('Campaign', backref='user', lazy=True)

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='active')
    created_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    websites = db.relationship('Website', secondary='campaign_website', backref='campaigns')
    outreach_attempts = db.relationship('OutreachAttempt', backref='campaign', lazy=True)

class OutreachAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    last_contact_date = db.Column(db.DateTime)

# Association table for many-to-many relationship between Campaign and Website
campaign_website = db.Table('campaign_website',
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True),
    db.Column('website_id', db.Integer, db.ForeignKey('website.id'), primary_key=True)
)
