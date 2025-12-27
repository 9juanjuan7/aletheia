from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
from services.publication_researcher import PublicationResearcher

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load existing data
with open('data/publications.json', 'r') as f:
    PUBLICATIONS = json.load(f)

with open('data/myths.json', 'r') as f:
    MYTHS = json.load(f)

# Initialize AI researcher
researcher = PublicationResearcher()

# API keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

def get_related_articles(title):
    """Find related articles using NewsAPI"""
    if not NEWS_API_KEY:
        return []
    
    try:
        # Extract key terms from title
        keywords = ' '.join(title.split()[:5])
        
        response = requests.get(
            'https://newsapi.org/v2/everything',
            params={
                'q': keywords,
                'sortBy': 'relevancy',
                'pageSize': 5,
                'apiKey': NEWS_API_KEY
            },
            timeout=5
        )
        
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            return [{
                'title': art['title'],
                'url': art['url'],
                'source': art['source']['name']
            } for art in articles[:5]]
    except Exception as e:
        print(f"NewsAPI error: {e}")
    
    return []

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '')
    
    domain = urlparse(url).netloc.replace('www.', '')
    
    # Check cache first
    publication = None
    pub_index = None
    for i, pub in enumerate(PUBLICATIONS):
        if pub['domain'] == domain:
            publication = pub
            pub_index = i
            break
    
    # If not in cache, research with AI!
    if not publication:
        print(f"🔍 Researching {domain} with AI...")
        publication = researcher.research(domain)
        
        # Save to cache for next time
        PUBLICATIONS.append(publication)
        with open('data/publications.json', 'w') as f:
            json.dump(PUBLICATIONS, f, indent=2)
        print(f"✅ Saved {domain} to database")
    else:
        # Already in database
        print(f"ℹ️ Found {domain} in cache")
        # Future: Add re-research logic here if needed
    
    # Detect myths
    detected_myths = []
    title_lower = title.lower()
    for myth in MYTHS:
        for keyword in myth['keywords']:
            if keyword.lower() in title_lower:
                detected_myths.append(myth)
                break
    
    # Get related articles
    related_articles = get_related_articles(title)
    
    return jsonify({
        'publication': publication,
        'myths': detected_myths,
        'related_articles': related_articles,
        'missing_context': [
            "Study funding sources",
            "Conflicting research",
            "Sample size limitations"
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
