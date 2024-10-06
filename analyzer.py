from dotenv import load_dotenv
import os
import requests
import json
import traceback
from models import Campaign, Website, db
from scraper import scrape_websites_for_backlinks, scrape_author
from email_finder import find_email

load_dotenv()

MOZ_ACCESS_ID = os.getenv('MOZ_ACCESS_ID')
MOZ_SECRET_KEY = os.getenv('MOZ_SECRET_KEY')

def get_domain_authority(url):
    print(f"Entering get_domain_authority for URL: {url}")
    auth = (MOZ_ACCESS_ID, MOZ_SECRET_KEY)
    api_url = "https://lsapi.seomoz.com/v2/url_metrics"
    data = json.dumps({
        "targets": [url]
    })
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        print(f"Sending request to Moz API for URL: {url}")
        response = requests.post(api_url, data=data, auth=auth, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        print(f"Raw response for {url}: {result}")
        
        if result and 'results' in result and len(result['results']) > 0:
            domain_authority = result['results'][0].get('domain_authority', 0)
            page_authority = result['results'][0].get('page_authority', 0)
            print(f"Extracted domain authority for {url}: {domain_authority}")
            return domain_authority, page_authority
        else:
            print(f"Unexpected response format for URL {url}: {result}")
            return 0, 0

    except Exception as e:
        print(f"Error fetching domain authority for {url}: {str(e)}")
        print(traceback.format_exc())
        return 0, 0

def analyze_websites_for_campaign(campaign_id, fetch_more=False):
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        print(f"Campaign with id {campaign_id} not found")
        return

    keyword = campaign.keyword
    scraped_websites = scrape_websites_for_backlinks(keyword, fetch_more)
    
    if not scraped_websites:
        print(f"No websites found for keyword: {keyword}")
        return

    new_websites = []
    for website_url in scraped_websites:
        website = Website.query.filter_by(url=website_url).first()
        if not website:
            author_name = scrape_author(website_url)
            author_email = find_email(author_name, website_url) if author_name else None
            domain_authority, page_authority = get_domain_authority(website_url)
            website = Website(
                url=website_url,
                domain_authority=domain_authority,
                page_authority=page_authority,
                author_name=author_name,
                author_email=author_email,
                status='email_found' if author_email else ('author_found' if author_name else 'pending')
            )
            db.session.add(website)
            new_websites.append(website)
        
        if website not in campaign.websites:
            campaign.websites.append(website)
    
    db.session.commit()
    print(f"Website analysis completed for campaign {campaign_id}")
    return new_websites

def analyze_websites(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        print(f"Campaign with id {campaign_id} not found")
        return

    keyword = campaign.keyword
    scraped_websites = scrape_websites_for_backlinks(keyword)
    
    if not scraped_websites:
        print(f"No websites found for keyword: {keyword}")
        return

    new_websites = []
    for website_url in scraped_websites:
        website = Website.query.filter_by(url=website_url).first()
        if not website:
            author_name = scrape_author(website_url)
            author_email = find_email(author_name, website_url) if author_name else None
            domain_authority, page_authority = get_domain_authority(website_url)
            website = Website(
                url=website_url,
                domain_authority=domain_authority,
                page_authority=page_authority,
                author_name=author_name,
                author_email=author_email,
                status='email_found' if author_email else ('author_found' if author_name else 'pending')
            )
            db.session.add(website)
            new_websites.append(website)
        
        if website not in campaign.websites:
            campaign.websites.append(website)
    
    db.session.commit()
    print(f"Website analysis completed for campaign {campaign_id}")
    return new_websites

# Example usage
if __name__ == "__main__":
    test_url = "https://example.com"
    da, pa = get_domain_authority(test_url)
    print(f"Domain Authority for {test_url}: {da}")
    print(f"Page Authority for {test_url}: {pa}")
