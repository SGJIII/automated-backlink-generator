from dotenv import load_dotenv
import os
import requests
import json
import traceback
import random  # Add this import

load_dotenv()

# Load Moz API credentials from .env
MOZ_ACCESS_ID = os.getenv('MOZ_ACCESS_ID')
MOZ_SECRET_KEY = os.getenv('MOZ_SECRET_KEY')
USE_MOZ_API = os.getenv('USE_MOZ_API', 'False').lower() == 'true'

def get_domain_authority(url):
    if not USE_MOZ_API:
        # Return a random value between 0 and 100 when not using the API
        return random.randint(0, 100), random.randint(0, 100)

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

# Example usage
if __name__ == "__main__":
    test_url = "https://example.com"
    da, pa = get_domain_authority(test_url)
    print(f"Domain Authority for {test_url}: {da}")
    print(f"Page Authority for {test_url}: {pa}")
