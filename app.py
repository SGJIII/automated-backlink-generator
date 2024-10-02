from dotenv import load_dotenv
import os
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
from flask_migrate import Migrate
from db import db  # Import db from db.py
from models import Website, EmailLog, Content, User
from auth import auth_bp
from analyzer import get_domain_authority
from scraper import scrape_websites_for_backlinks, scrape_author, scrape_author_text
import traceback  # Add this import
from email_finder import find_email, process_email_finding  # Add this import
from content_generator import generate_outreach_email
from email_sender import send_email
from automated_followup import schedule_followup
from automated_reply import process_reply
from flask_session import Session

load_dotenv()
# Initialize Flask app
app = Flask(__name__)

# Configure database URI and disable track modifications
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.getcwd(), "backlink_generator.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Set the secret key for sessions
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)

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
    
    # Fetch all websites from the database
    websites = Website.query.all()
    
    return render_template('websites.html', websites=websites)

# Add a new route for manually triggering the scraper
@app.route('/scrape_websites')
def scrape_websites():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    # Run the scraper
    scrape_websites_for_backlinks('crypto currency IRA')
    
    return redirect(url_for('show_websites'))

@app.route('/reprocess_authors')
def reprocess_authors():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    websites = Website.query.all()
    
    for website in websites:
        try:
            author_text = scrape_author_text(website.url)
            website.author_name = scrape_author(website.url)
            website.status = 'author_found' if website.author_name else 'pending'
        except Exception as e:
            print(f"Error reprocessing website {website.url}: {str(e)}")
            traceback.print_exc()
    
    db.session.commit()
    
    # Process email finding after scraping authors
    process_email_finding(user.id)
    
    return redirect(url_for('show_websites'))

@app.route('/start_outreach/<int:website_id>')
def start_outreach(website_id):
    print("Session contents:", session)  # Debug print
    if 'email' not in session:
        print("Email not in session, redirecting to login")  # Debug print
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        print(f"User not found for email: {session['email']}, creating new user")  # Debug print
        # Create a new user if one doesn't exist
        user = User(email=session['email'], name=session['email'].split('@')[0])  # Using email as name temporarily
        db.session.add(user)
        db.session.commit()
    
    website = Website.query.get(website_id)
    if website and website.status == 'email_found':
        # Generate initial content
        email_content = generate_outreach_email(website, user.id)
        return render_template('outreach_email.html', website=website, email_content=email_content)
    
    # If the website doesn't exist or its status is not 'email_found', redirect to the websites page
    print("Website not found or status not 'email_found', redirecting to show_websites")  # Debug print
    return redirect(url_for('show_websites'))

@app.route('/approve_outreach/<int:website_id>', methods=['POST'])
def approve_outreach(website_id):
    website = Website.query.get(website_id)
    if website:
        email_content = request.form['email_content']
        automated_followup = 'automated_followup' in request.form
        automated_reply = 'automated_reply' in request.form
        
        # Get the current user
        user = User.query.filter_by(email=session['email']).first()
        
        # Send the email
        send_email(user.id, website.author_email, "Backlink Request", email_content)
        
        # Update website status
        website.status = 'outreach_sent'
        db.session.commit()
        
        if automated_followup:
            schedule_followup(website_id, user.id)
        
        if automated_reply:
            # Set a flag in the database to enable automated replies
            website.automated_reply_enabled = True
            db.session.commit()
        
        return redirect(url_for('dashboard'))
    return redirect(url_for('show_websites'))

@app.route('/process_reply/<int:website_id>', methods=['POST'])
def process_incoming_reply(website_id):
    website = Website.query.get(website_id)
    if website and website.automated_reply_enabled:
        reply_content = request.form['reply_content']
        # Get the current user
        user = User.query.filter_by(email=session['email']).first()
        response = process_reply(website, reply_content, user.id)
    return jsonify({"status": "success"})

@app.route('/pause_outreach/<int:website_id>')
def pause_outreach(website_id):
    website = Website.query.get(website_id)
    if website and website.status == 'outreach_started':
        website.status = 'outreach_paused'
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/resume_outreach/<int:website_id>')
def resume_outreach(website_id):
    website = Website.query.get(website_id)
    if website and website.status == 'outreach_paused':
        website.status = 'outreach_started'
        db.session.commit()
        # Get the current user
        user = User.query.filter_by(email=session['email']).first()
        schedule_followup(website_id, user.id)  # Pass user_id to schedule_followup
    return redirect(url_for('dashboard'))

@app.route('/email_settings', methods=['GET', 'POST'])
def email_settings():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=session['email']).first()
    
    if request.method == 'POST':
        user.email_provider = request.form['email_provider']
        if user.email_provider == 'mailgun':
            user.email_settings = {
                'api_key': request.form['mailgun_api_key'],
                'domain': request.form['mailgun_domain']
            }
        elif user.email_provider in ['smtp', 'gmail']:
            user.email_settings = {
                'smtp_server': request.form['smtp_server'],
                'smtp_port': int(request.form['smtp_port']),
                'smtp_username': request.form['smtp_username'],
                'smtp_password': request.form['smtp_password']
            }
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('email_settings.html', user=user)

@app.before_request
def before_request():
    print("Before request - Session:", session)

if __name__ == '__main__':
    app.run(debug=True)
