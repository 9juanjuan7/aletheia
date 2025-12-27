from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
import os
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# Load data
with open('data/publications.json', 'r') as f:
    PUBLICATIONS = json.load(f)

with open('data/myths.json', 'r') as f:
    MYTHS = json.load(f)

NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')  # Get from newsapi.org

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '')
    
    # Extract domain
    domain = urlparse(url).netloc.replace('www.', '')
    
    # Look up publication
    publication = None
    for pub in PUBLICATIONS:
        if pub['domain'] == domain:
            publication = pub
            break
    
    # Detect myths
    detected_myths = []
    title_lower = title.lower()
    for myth in MYTHS:
        for keyword in myth['keywords']:
            if keyword.lower() in title_lower:
                detected_myths.append(myth)
                break
    
    # Get related articles (if NEWS_API_KEY is set)
    related_articles = []
    if NEWS_API_KEY:
        related_articles = get_related_articles(title)
    
    # Missing context (placeholder for now)
    missing_context = [
        "Study funding sources",
        "Conflicting research",
        "Sample size limitations"
    ]
    
    return jsonify({
        'publication': publication,
        'myths': detected_myths,
        'related_articles': related_articles,
        'missing_context': missing_context
    })

def get_related_articles(title):
    if not NEWS_API_KEY:
        return []
    
    try:
        # Extract key terms from title (simple approach)
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
    except:
        pass
    
    return []

if __name__ == '__main__':
    app.run(debug=True, port=5000)
