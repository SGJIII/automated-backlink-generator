# scraper.py

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from models import Website, db  # Import your models
import json
import re

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

def scrape_author(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        authors = []

        # Check for meta tag
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author:
            authors.append(meta_author['content'])

        # Check for common author classes
        author_classes = [
            '.author-name', '.byline-author', '.article-author', 
            '[itemprop="author"]', '.post-author', '.entry-author',
            '[data-cy="author-name"]'  # Fortune.com specific
        ]
        for class_ in author_classes:
            author_elements = soup.select(class_)
            for element in author_elements:
                authors.append(element.text.strip())

        # Check for author in structured data
        script = soup.find('script', type='application/ld+json')
        if script:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if 'author' in data:
                    if isinstance(data['author'], list):
                        authors.extend([author.get('name', '') for author in data['author'] if isinstance(author, dict)])
                    elif isinstance(data['author'], dict):
                        authors.append(data['author'].get('name', ''))
                    elif isinstance(data['author'], str):
                        authors.append(data['author'])

        # Clean up author names
        cleaned_authors = []
        for author in authors:
            # Remove common prefixes and suffixes
            author = re.sub(r'^(by|written by|reviewed by|edited by)\s+', '', author, flags=re.IGNORECASE)
            author = re.sub(r'\s+(contributor|staff writer|editor|reviewer)$', '', author, flags=re.IGNORECASE)
            
            # Split multiple authors
            split_authors = re.split(r'\s*(?:,|and)\s*', author)
            cleaned_authors.extend([name.strip() for name in split_authors if name.strip()])

        # Remove duplicates while preserving order
        unique_authors = []
        for author in cleaned_authors:
            if author not in unique_authors:
                unique_authors.append(author)

        return ', '.join(unique_authors) if unique_authors else None

    except Exception as e:
        print(f"Error scraping author for {url}: {str(e)}")
        return None

def scrape_websites_for_backlinks(keyword):
    results = search_google(keyword)
    for result in results:
        website_url = result['link']
        website = Website.query.filter_by(url=website_url).first()
        if not website:
            author_name = scrape_author(website_url)
            new_website = Website(
                url=website_url,
                domain_authority=None,
                author_name=author_name,
                author_email=None,
                status='author_found' if author_name else 'pending'
            )
            db.session.add(new_website)
    db.session.commit()
    print("Scraping completed and websites added to database.")
