from db import db

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), unique=True, nullable=False)
    domain_authority = db.Column(db.Float)
    author_name = db.Column(db.String(200))
    author_email = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')
    automated_reply_enabled = db.Column(db.Boolean, default=False)

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
    name = db.Column(db.String(120), nullable=True)  # Allow null for now
    email_provider = db.Column(db.String(50), nullable=True)
    email_settings = db.Column(db.JSON, nullable=True)
