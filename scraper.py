# scraper.py

import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from models import Website, db  # Import your models
import json
import re
import traceback
from openai import OpenAI
import PyPDF2
import io
from email_finder import find_email  # Add this import at the top of the file


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

client = OpenAI(api_key=api_key)

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
        email_link = soup.find('a', href=re.compile(r'^mailto:'))
        if email_link:
            email = email_link.get('href').replace('mailto:', '').strip()
            return email
        return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def scrape_author(url):
    print(f"Scraping author for URL: {url}")
    author_text = scrape_author_text(url)
    print(f"Author text: {author_text[:500]}...")  # Print first 500 characters of author text
    authors = extract_authors_with_gpt(author_text)
    print(f"Extracted authors: {authors}")
    if authors and authors != "None found":
        # Clean and validate the extracted names
        cleaned_authors = clean_author_names(authors.split(','))
        print(f"Cleaned authors: {cleaned_authors}")
        return ', '.join(cleaned_authors) if cleaned_authors else None
    return None

def extract_authors_from_json(data):
    authors = []
    if isinstance(data, dict):
        if 'author' in data:
            author = data['author']
            if isinstance(author, list):
                for item in author:
                    name = extract_name_from_author(item)
                    if name:
                        authors.append(name)
            else:
                name = extract_name_from_author(author)
                if name:
                    authors.append(name)
        # Recursively search for 'author' keys in nested structures
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                authors.extend(extract_authors_from_json(value))
    elif isinstance(data, list):
        for item in data:
            authors.extend(extract_authors_from_json(item))
    return authors

def extract_name_from_author(author):
    if isinstance(author, dict):
        return author.get('name')
    elif isinstance(author, str):
        return author.strip()
    return None

def clean_author_names(names):
    cleaned_names = []
    for name in names:
        # Split concatenated names
        split_names = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', name)
        cleaned_names.extend(split_names)
    
    # Remove duplicates while preserving order
    seen = set()
    return [name for name in cleaned_names if not (name in seen or seen.add(name))]

def is_valid_name(name):
    # Check if the name contains at least two words
    if len(name.split()) < 2:
        return False
    
    # Check if the name only contains letters, spaces, hyphens, and apostrophes
    if not re.match(r'^[A-Za-z\s\'-]+$', name):
        return False
    
    # Check if each word in the name starts with a capital letter
    if not all(word[0].isupper() for word in name.split()):
        return False
    
    # Check if the name is not too short or too long
    if len(name) < 4 or len(name) > 40:
        return False
    
    # Check against a list of common non-name words
    non_name_words = ['inc', 'llc', 'company', 'corporation', 'bitcoin', 'crypto', 'ira', 'investment']
    if any(word.lower() in non_name_words for word in name.split()):
        return False
    
    return True

def scrape_websites_for_backlinks(keyword, fetch_more=False):
    base_url = "https://serpapi.com/search.json"
    params = {
        "q": keyword,
        "api_key": SERPAPI_API_KEY,
        "num": 10
    }
    
    if fetch_more:
        params["start"] = 11  # Start from the 11th result for fetching more

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        organic_results = data.get('organic_results', [])
        return [result['link'] for result in organic_results]
    except Exception as e:
        print(f"Error fetching search results: {str(e)}")
        return []

def scrape_author_text(url):
    try:
        print(f"Scraping author text for URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        if url.lower().endswith('.pdf'):
            return extract_text_from_pdf(response.content)[:10000]
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Start scraping from the beginning of the body tag
        body = soup.find('body')
        if body:
            full_content = body.get_text(separator=' ', strip=True)
        else:
            full_content = soup.get_text(separator=' ', strip=True)
        
        # Combine with existing targeted scraping
        author_text = full_content[:10000] + "\n"  # First 10000 characters from body
        
        # Check meta tags
        meta_authors = soup.find_all('meta', {'name': ['author', 'article:author']})
        for meta in meta_authors:
            author_text += meta.get('content', '') + "\n"
        
        # Check common author-related classes
        author_classes = ['author', 'byline', 'writer', 'contributor', 'editor', 'reviewer']
        for cls in author_classes:
            elements = soup.find_all(class_=lambda x: x and cls in x.lower())
            for el in elements:
                author_text += el.get_text(strip=True) + "\n"
        
        # Check structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if 'author' in data:
                    author_text += json.dumps(data['author']) + "\n"
            except json.JSONDecodeError:
                pass
        
        print(f"Scraped author text: {author_text[:200]}...")  # Print first 200 characters
        return author_text.strip()[:20000]  # Limit to 20000 characters
    
    except Exception as e:
        print(f"Error scraping author text for {url}: {str(e)}")
        return ""

def extract_text_from_pdf(content):
    try:
        with io.BytesIO(content) as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_authors_with_gpt(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts author names from text. Your task is to identify and list all potential author names from the given text, including writers, contributors, editors, and reviewers."},
                {"role": "user", "content": f"Extract all full names of individuals who are likely to be authors, contributors, editors, or reviewers of the content. Return the names as a comma-separated list, or 'None found' if no names are present. Include both main authors and any mentioned reviewers or contributors.Do not include titles, dates, or any other text. Limit the response to a maximum of 10 names"},
                {"role": "user", "content": text}
            ]
        )
        names = response.choices[0].message.content.strip()
        print(f"Extracted names: {names}")
        
        if names and names != "None found":
            name_list = [name.strip() for name in names.split(',')]
            filtered_names = [name for name in name_list if is_valid_name(name)]
            
            if filtered_names:
                return ', '.join(filtered_names)
        
        return None
    except Exception as e:
        print(f"Error extracting authors with GPT: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        return None