import requests
import os
import re
from pyhunter import PyHunter

hunter = PyHunter(os.getenv("HUNTER_API_KEY"))

def find_email(author_names, domain):
    if not author_names:
        return None
    
    authors = [name.strip() for name in author_names.split(',')]
    emails = []
    
    for author in authors:
        try:
            result = hunter.domain_search(domain, full_name=author)
            if result and 'emails' in result and result['emails']:
                emails.append(result['emails'][0]['value'])
            else:
                # If no specific email found, use pattern
                emails.append(f"{author.lower().replace(' ', '.')}@{domain}")
        except Exception as e:
            print(f"Error finding email for {author} at {domain}: {str(e)}")
            emails.append(f"{author.lower().replace(' ', '.')}@{domain}")
    
    return ', '.join(emails)

def process_email_finding():
    websites = Website.query.filter_by(status='author_found').all()
    for website in websites:
        domain = website.url.split('//')[1].split('/')[0]
        email = find_email(website.author_name, domain)
        website.author_email = email
        website.status = 'email_found'
    db.session.commit()
