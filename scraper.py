# scraper.py

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from models import Website  # Import your models
from app import app, db  # Import your Flask app and the db instance

SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')

def search_google(query):
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google",
    }
    response = requests.get('https://serpapi.com/search', params=params)
    results = response.json()
    return results.get('organic_results', [])

def extract_contact_info(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        email = soup.find('a', href=True, text='email')
        return email['href'].replace('mailto:', '') if email else None
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def scrape_websites_for_backlinks(keyword):
    results = search_google(keyword)
    for result in results:
        website_url = result['link']
        domain = urlparse(website_url).netloc
        website = Website.query.filter_by(url=website_url).first()
        if not website:
            contact_email = extract_contact_info(website_url)
            new_website = Website(
                url=website_url,
                domain_authority=0,
                contact_email=contact_email,
                status='pending'
            )
            db.session.add(new_website)
    db.session.commit()
    print("Scraping completed and websites added to database.")

if __name__ == '__main__':
    with app.app_context():  # Create an application context for database operations
        scrape_websites_for_backlinks("crypto currency IRA")
