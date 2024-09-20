import os
from flask import Flask, render_template, session, redirect, url_for, jsonify
from flask_migrate import Migrate
from db import db  # Import db from db.py

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

# Import models after initializing db and migrate
from models import Website, EmailLog, Content

# Import the authentication blueprint from auth.py
from auth import auth_bp
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
    
    from scraper import scrape_websites_for_backlinks
    with app.app_context():
        scrape_websites_for_backlinks('crypto currency IRA')
    return jsonify({"message": "Scraping started!"})

@app.route('/websites')
def show_websites():
    if 'email' not in session:
        return redirect(url_for('auth.login'))
    websites = Website.query.all()
    return render_template('websites.html', websites=websites)

if __name__ == '__main__':
    app.run(debug=True)
