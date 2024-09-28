import os
from flask import Flask, render_template, session, redirect, url_for, jsonify
from flask_migrate import Migrate
from db import db  # Import db from db.py
from models import Website, EmailLog, Content
from auth import auth_bp
from analyzer import get_domain_authority
from scraper import scrape_websites_for_backlinks, scrape_author
import traceback  # Add this import

# Initialize Flask app
app = Flask(__name__)

# Configure database URI and disable track modifications
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), "backlink_generator.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set the secret key for sessions
# You can generate a secure key using the os module: os.urandom(24)
app.secret_key = os.urandom(24)

# Initialize the database and migration
db.init_app(app)
migrate = Migrate(app, db)

# Import scraper after initializing app
from scraper import scrape_websites_for_backlinks

# Register the authentication blueprint
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Check if the user is logged in by looking for email in session
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html', email=session['email'])

# Function to inject Google Client ID into templates
@app.context_processor
def inject_google_client_id():
    return {'google_client_id': os.getenv('GOOGLE_CLIENT_ID')}

@app.route('/scrape')
def start_scraper():
    if 'email' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    with app.app_context():
        scrape_websites_for_backlinks('crypto currency IRA')
    return jsonify({"message": "Scraping started!"})

@app.route('/websites')
def show_websites():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    websites = Website.query.all()
    
    for website in websites:
        if website.status == 'pending' or website.author_name is None:
            website.author_name = scrape_author(website.url)
            website.status = 'author_found' if website.author_name else 'pending'
        
        if website.status == 'author_found' and website.author_email is None:
            try:
                domain = website.url.split('//')[1].split('/')[0]
                website.author_email = find_email(website.author_name, domain)
                website.status = 'email_found' if website.author_email else 'author_found'
            except Exception as e:
                print(f"Error finding email for {website.url}: {str(e)}")
        
        if website.domain_authority is None:
            da, _ = get_domain_authority(website.url)
            website.domain_authority = da
    
    db.session.commit()
    
    return render_template('websites.html', websites=websites)

if __name__ == '__main__':
    app.run(debug=True)
