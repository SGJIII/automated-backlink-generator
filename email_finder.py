import os
import requests
from dotenv import load_dotenv
from models import Website, db
import tldextract

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
HUNTER_EMAIL_FINDER_URL = "https://api.hunter.io/v2/email-finder"
HUNTER_EMAIL_VERIFIER_URL = "https://api.hunter.io/v2/email-verifier"

def find_and_validate_email(author_name, domain):
    if not author_name:
        return None

    names = author_name.split()
    if len(names) < 2:
        return None

    first_name = names[0]
    last_name = names[-1]

    # Extract the root domain without subdomains or "www"
    extracted = tldextract.extract(domain)
    root_domain = f"{extracted.domain}.{extracted.suffix}"

    try:
        # Use Hunter Email Finder API
        finder_params = {
            "domain": root_domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": HUNTER_API_KEY
        }
        finder_response = requests.get(HUNTER_EMAIL_FINDER_URL, params=finder_params)
        finder_result = finder_response.json()

        print(f"Hunter Email Finder API response: {finder_result}")

        if finder_result.get('data', {}).get('email'):
            email = finder_result['data']['email']
            
            # Verify the found email
            verifier_result = verify_email(email)
            if verifier_result['status'] in ['valid', 'accept_all']:
                print(f"Found and verified email for {author_name}: {email}")
                return email

    except Exception as e:
        print(f"Error finding/validating email for {author_name} at {root_domain}: {str(e)}")

    print(f"Could not find or validate email for {author_name} at {root_domain}")
    return None

def verify_email(email):
    try:
        verifier_params = {
            "email": email,
            "api_key": HUNTER_API_KEY
        }
        verifier_response = requests.get(HUNTER_EMAIL_VERIFIER_URL, params=verifier_params)
        verifier_result = verifier_response.json()

        print(f"Hunter Email Verifier API response: {verifier_result}")

        return verifier_result.get('data', {})

    except Exception as e:
        print(f"Error verifying email {email}: {str(e)}")
        return {}

def process_email_finding():
    websites = Website.query.filter_by(status='author_found').all()
    for website in websites:
        try:
            domain = website.url.split('//')[1].split('/')[0]
            authors = [name.strip() for name in website.author_name.split(',')]
            valid_emails = []

            for author in authors:
                email = find_and_validate_email(author, domain)
                if email:
                    valid_emails.append(email)

            if valid_emails:
                website.author_email = ', '.join(valid_emails)
                website.status = 'email_found'
            else:
                website.status = 'email_not_found'

        except Exception as e:
            print(f"Error processing website {website.url}: {str(e)}")
            website.status = 'error'

    db.session.commit()

def find_email(author_names, url):
    if not author_names:
        return None
    
    # Extract the root domain from the URL
    extracted = tldextract.extract(url)
    root_domain = f"{extracted.domain}.{extracted.suffix}"
    
    authors = [name.strip() for name in author_names.split(',')]
    emails = []
    
    for author in authors:
        email = find_and_validate_email(author, root_domain)
        if email:
            emails.append(email)
    
    return ', '.join(emails) if emails else None
