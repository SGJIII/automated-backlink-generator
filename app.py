from dotenv import load_dotenv
import os
from flask import Flask, render_template, session, redirect, url_for, jsonify, request, flash  # Add this import
from flask_migrate import Migrate
from db import db  # Import db from db.py
from models import Website, EmailLog, Content, User, Campaign, OutreachAttempt
from auth import auth_bp
from analyzer import get_domain_authority, analyze_websites_for_campaign
from scraper import scrape_websites_for_backlinks, scrape_author, scrape_author_text
import traceback  # Add this import
from email_finder import find_email, process_email_finding  # Add this import
from content_generator import generate_outreach_email_content
from email_sender import send_email
from automated_followup import schedule_followup
from automated_reply import process_reply
from flask_session import Session
from sqlalchemy import func

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
    
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('auth.login'))
    
    # Check if user has completed their profile
    if not user.name or not user.company or not user.company_profile:
        flash('Please complete your profile before accessing the dashboard.', 'warning')
        return redirect(url_for('user_settings'))
    
    return render_template('dashboard.html', user=user)

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

@app.route('/campaign/<int:campaign_id>/websites')
def show_websites(campaign_id):
    if 'email' not in session:
        return redirect(url_for('login'))
    
    campaign = Campaign.query.get_or_404(campaign_id)
    websites = Website.query.filter(Website.campaigns.any(id=campaign_id)).all()
    
    return render_template('campaign_websites.html', campaign=campaign, websites=websites)

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

@app.route('/start_outreach/<int:website_id>/<int:campaign_id>')
def start_outreach(website_id, campaign_id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=session['email']).first()
    website = Website.query.get_or_404(website_id)
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if website.status == 'email_found':
        outreach_attempt = OutreachAttempt(campaign_id=campaign.id, website_id=website.id)
        db.session.add(outreach_attempt)
        db.session.commit()
        
        email_content = generate_outreach_email_content(website, user, campaign.target_url)
        return render_template('outreach_email.html', website=website, email_content=email_content, campaign_id=campaign.id)
    
    return redirect(url_for('campaign_details', campaign_id=campaign.id))

@app.route('/approve_general_outreach/<int:website_id>', methods=['POST'])
def approve_general_outreach(website_id):
    website = Website.query.get(website_id)
    if website:
        email_content = request.form['email_content']
        automated_followup = 'automated_followup' in request.form
        automated_reply = 'automated_reply' in request.form
        
        # Get the current user
        user = User.query.filter_by(email=session['email']).first()
        
        # Send the email
        success = send_email(user.id, website.author_email, "Backlink Request", email_content)
        
        if success:
            # Update website status
            website.status = 'outreach_sent'
            db.session.commit()
            
            if automated_followup:
                schedule_followup(website_id, user.id)
            
            if automated_reply:
                # Set a flag in the database to enable automated replies
                website.automated_reply_enabled = True
                db.session.commit()
            
            flash('Email sent successfully!', 'success')
        else:
            flash('Failed to send email. Please check your email settings.', 'error')
        
        return redirect(url_for('dashboard'))
    flash('Website not found.', 'error')
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
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Handle form submission (update email settings)
        # ... (implement the logic to save email settings)
        flash('Email settings updated successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('email_settings.html', user=user)

@app.route('/user_settings', methods=['GET', 'POST'])
def user_settings():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        # Create a new user if they don't exist
        user = User(email=session['email'])
        db.session.add(user)
        db.session.commit()
    
    if request.method == 'POST':
        user.name = request.form['name']
        user.company = request.form['company']
        user.company_profile = request.form['company_profile']
        db.session.commit()
        flash('User settings updated successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('user_settings.html', user=user)

@app.route('/new_campaign', methods=['GET', 'POST'])
def new_campaign():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        target_url = request.form['target_url']
        keyword = request.form['keyword']
        name = request.form['name']
        campaign = Campaign(user_id=user.id, target_url=target_url, keyword=keyword, name=name)
        db.session.add(campaign)
        db.session.commit()
        
        return redirect(url_for('campaign_websites', campaign_id=campaign.id))
    
    return render_template('new_campaign.html')

@app.route('/campaign/<int:campaign_id>/websites')
def view_campaign_websites(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('campaign_websites.html', campaign=campaign)

@app.route('/campaign/<int:campaign_id>/analyze', methods=['POST'])
def analyze_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    try:
        analyze_websites_for_campaign(campaign.id)
        return jsonify({'success': True, 'message': 'Analysis started successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/campaign/<int:campaign_id>/fetch_more', methods=['POST'])
def fetch_more_websites(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    try:
        new_websites = analyze_websites_for_campaign(campaign.id, fetch_more=True)
        return jsonify({'success': True, 'websites': new_websites})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/campaign/<int:campaign_id>/begin_outreach/<int:website_id>', methods=['GET', 'POST'])
def begin_outreach(campaign_id, website_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    website = Website.query.get_or_404(website_id)
    email_content = generate_outreach_email_content(website, campaign.user_id, campaign.user.name, campaign.user.company, campaign.user.company_profile, campaign.target_url)
    return render_template('outreach_email.html', campaign=campaign, website=website, email_content=email_content)

@app.route('/campaign/<int:campaign_id>/approve_outreach/<int:website_id>', methods=['POST'])
def approve_campaign_outreach(campaign_id, website_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    website = Website.query.get_or_404(website_id)
    email_content = request.form['email_content']
    automated_followup = 'automated_followup' in request.form
    automated_reply = 'automated_reply' in request.form
    
    # Send email
    success = send_email(campaign.user_id, website.author_email, "Outreach Email", email_content)
    
    if success:
        outreach_attempt = OutreachAttempt(
            campaign_id=campaign.id, 
            website_id=website.id, 
            status='sent',
            automated_followup=automated_followup,
            automated_reply=automated_reply
        )
        db.session.add(outreach_attempt)
        website.status = 'outreach_sent'
        if automated_followup:
            schedule_followup(website.id, campaign.user_id)
        db.session.commit()
        flash('Outreach email sent successfully', 'success')
    else:
        flash('Failed to send outreach email', 'error')
    
    return redirect(url_for('campaign_details', campaign_id=campaign.id))

@app.route('/campaign/<int:campaign_id>')
def view_campaign_details(campaign_id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Count active sequences
    active_sequences_count = OutreachAttempt.query.filter_by(campaign_id=campaign_id, status='active').count()
    
    # Count total websites
    total_websites_count = Website.query.filter(Website.campaigns.any(id=campaign_id)).count()
    
    # Count websites with successful outreach
    successful_outreach_count = Website.query.filter(Website.campaigns.any(id=campaign_id), Website.status == 'outreach_sent').count()
    
    return render_template('campaign_details.html', 
                           campaign=campaign,
                           active_sequences_count=active_sequences_count,
                           total_websites_count=total_websites_count,
                           successful_outreach_count=successful_outreach_count)

@app.route('/campaign/<int:campaign_id>/delete', methods=['POST'])
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/campaign/<int:campaign_id>/pause', methods=['POST'])
def pause_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.status = 'paused'
    db.session.commit()
    flash('Campaign paused successfully', 'success')
    return redirect(url_for('campaign_details', campaign_id=campaign.id))

@app.route('/campaign/<int:campaign_id>/resume', methods=['POST'])
def resume_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.status = 'active'
    db.session.commit()
    flash('Campaign resumed successfully', 'success')
    return redirect(url_for('campaign_details', campaign_id=campaign.id))

@app.route('/campaigns')
def show_campaigns():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    campaigns = Campaign.query.all()
    return render_template('campaigns.html', campaigns=campaigns)

@app.route('/campaign/<int:campaign_id>')
def campaign_details(campaign_id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('campaign_details.html', campaign=campaign)

@app.route('/campaign/<int:campaign_id>/websites')
def campaign_websites(campaign_id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    campaign = Campaign.query.get_or_404(campaign_id)
    websites = Website.query.filter(Website.campaigns.any(id=campaign_id)).all()
    return render_template('campaign_websites.html', campaign=campaign, websites=websites)

@app.route('/campaign/<int:campaign_id>/outreach')
def campaign_outreach(campaign_id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    
    campaign = Campaign.query.get_or_404(campaign_id)
    outreach_attempts = OutreachAttempt.query.join(Website).filter(Website.campaigns.any(id=campaign_id)).all()
    return render_template('campaign_outreach.html', campaign=campaign, outreach_attempts=outreach_attempts)

@app.route('/campaign/<int:campaign_id>/sequences')
def campaign_sequences(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    outreach_attempts = OutreachAttempt.query.filter_by(campaign_id=campaign_id).all()
    return render_template('campaign_sequences.html', campaign=campaign, sequences=outreach_attempts)

@app.route('/sequence/<int:sequence_id>/<action>', methods=['POST'])
def update_sequence_status(sequence_id, action):
    sequence = OutreachAttempt.query.get_or_404(sequence_id)
    if action == 'pause':
        sequence.status = 'paused'
    elif action == 'resume':
        sequence.status = 'active'
    db.session.commit()
    return jsonify({'success': True})

@app.route('/sequence/<int:sequence_id>/edit')
def edit_sequence(sequence_id):
    sequence = OutreachAttempt.query.get_or_404(sequence_id)
    return render_template('edit_sequence.html', sequence=sequence)

@app.route('/sequence/<int:sequence_id>/update', methods=['POST'])
def update_sequence(sequence_id):
    sequence = OutreachAttempt.query.get_or_404(sequence_id)
    sequence.automated_followup = 'automated_followup' in request.form
    sequence.automated_reply = 'automated_reply' in request.form
    db.session.commit()
    return redirect(url_for('campaign_sequences', campaign_id=sequence.campaign_id))

@app.before_request
def before_request():
    print("Before request - Session:", session)

if __name__ == '__main__':
    app.run(debug=True)