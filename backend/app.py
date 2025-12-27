from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
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

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '')
    
    domain = urlparse(url).netloc.replace('www.', '')
    
    # Check cache first
    publication = None
    for pub in PUBLICATIONS:
        if pub['domain'] == domain:
            publication = pub
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
    
    # Detect myths
    detected_myths = []
    title_lower = title.lower()
    for myth in MYTHS:
        for keyword in myth['keywords']:
            if keyword.lower() in title_lower:
                detected_myths.append(myth)
                break
    
    return jsonify({
        'publication': publication,
        'myths': detected_myths,
        'related_articles': [],
        'missing_context': [
            "Study funding sources",
            "Conflicting research",
            "Sample size limitations"
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
