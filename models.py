from db import db

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2083), unique=True, nullable=False)
    domain_authority = db.Column(db.Integer)
    author_name = db.Column(db.String(100))  # New field
    author_email = db.Column(db.String(320))  # Renamed from contact_email
    status = db.Column(db.String(50))  # 'pending', 'author_found', 'email_found', 'emailed', 'linked'

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    sent_date = db.Column(db.DateTime)
    response = db.Column(db.Text)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('website.id'))
    content_text = db.Column(db.Text)
    created_date = db.Column(db.DateTime)
