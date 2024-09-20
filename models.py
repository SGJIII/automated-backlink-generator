from app import db  # Import the db instance from app.py

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2083), unique=True, nullable=False)
    domain_authority = db.Column(db.Integer)
    contact_email = db.Column(db.String(320))
    status = db.Column(db.String(50))  # 'pending', 'emailed', 'linked'

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
