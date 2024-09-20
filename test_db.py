from app import app, db
from models import Website, EmailLog, Content

# Ensure the app context is set
with app.app_context():
    # Drop all tables (optional, for testing purposes)
    db.drop_all()
    
    # Create all tables
    db.create_all()
    
    # Create a test record
    test_website = Website(
        url="https://example.com",
        domain_authority=50,
        contact_email="contact@example.com",
        status="pending"
    )
    
    # Add the record to the session
    db.session.add(test_website)
    db.session.commit()
    
    # Query the database to verify the record
    websites = Website.query.all()
    print(f"Total websites: {len(websites)}")
    for website in websites:
        print(f"Website: {website.url}, DA: {website.domain_authority}, Email: {website.contact_email}")
