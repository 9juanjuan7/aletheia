from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import feedparser
from dotenv import load_dotenv
from urllib.parse import urlparse, quote
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

def is_publication_complete(publication):
    """Check if publication data is complete enough to use"""
    if not publication:
        return False
    
    # Required fields that should not be empty
    required_fields = ['name', 'domain', 'credibility_score']
    
    # Check if all required fields exist and are not empty/None
    for field in required_fields:
        if field not in publication or not publication[field]:
            return False
    
    # Check if credibility score is reasonable (not default/placeholder)
    if publication.get('credibility_score', 0) <= 0 or publication.get('credibility_score', 0) > 10:
        return False
    
    # Check if we have funding info (critical for credibility)
    if not publication.get('funding_sources') and publication.get('ownership') == 'Unknown':
        return False
    
    return True

def get_related_articles(title):
    """Find related articles using Google News RSS (free & unlimited)"""
    try:
        # Extract key terms from title (first 5-6 meaningful words)
        keywords = ' '.join(title.split()[:6])
        
        # Google News RSS search URL
        search_query = quote(keywords)
        rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
        
        print(f"📰 Searching Google News for: {keywords}")
        
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        articles = []
        for entry in feed.entries[:5]:  # Get top 5 results
            # Extract actual source from Google News
            source_name = entry.source.title if hasattr(entry, 'source') else 'Unknown'
            
            articles.append({
                'title': entry.title,
                'url': entry.link,
                'source': source_name,
                'published': entry.published if hasattr(entry, 'published') else None
            })
        
        print(f"📰 Found {len(articles)} related articles")
        return articles
        
    except Exception as e:
        print(f"❌ Google News RSS error: {e}")
        return []

def extract_domain(url):
    """Extract clean domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        # Remove Google News redirect
        if 'news.google.com' in domain:
            return None
        return domain
    except:
        return None

def get_or_research_publication(domain):
    """Get publication from cache or research it"""
    if not domain:
        return None
    
    # Check cache
    for pub in PUBLICATIONS:
        if pub.get('domain') == domain:
            if is_publication_complete(pub):
                print(f"✅ Using cached data for {domain}")
                return pub
            else:
                print(f"🔄 Cached data incomplete for {domain}, re-researching...")
                break
    
    # Research needed
    print(f"🔍 Researching new source: {domain}...")
    new_pub = researcher.research(domain)
    
    # Update cache
    updated = False
    for i, pub in enumerate(PUBLICATIONS):
        if pub.get('domain') == domain:
            PUBLICATIONS[i] = new_pub
            updated = True
            break
    
    if not updated:
        PUBLICATIONS.append(new_pub)
    
    # Save to file
    with open('data/publications.json', 'w') as f:
        json.dump(PUBLICATIONS, f, indent=2)
    
    return new_pub

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '')
    
    domain = extract_domain(url)
    
    if not domain:
        return jsonify({'error': 'Invalid URL'}), 400
    
    print(f"\n{'='*60}")
    print(f"🔍 ANALYZING: {title[:50]}...")
    print(f"📍 Domain: {domain}")
    print(f"{'='*60}\n")
    
    # 1. Analyze main publication
    print("📊 Step 1: Analyzing main publication...")
    main_publication = get_or_research_publication(domain)
    
    # 2. Detect myths in title
    print("\n🔍 Step 2: Checking for common health myths...")
    detected_myths = []
    title_lower = title.lower()
    for myth in MYTHS:
        for keyword in myth['keywords']:
            if keyword.lower() in title_lower:
                detected_myths.append(myth)
                break
    
    if detected_myths:
        print(f"⚠️  Found {len(detected_myths)} potential myth(s)")
    else:
        print("✅ No common myths detected")
    
    # 3. Get related articles from Google News
    print("\n📰 Step 3: Finding related coverage...")
    related_articles = get_related_articles(title)
    
    # 4. BRANCH: Analyze each related source
    print(f"\n🌳 Step 4: Branching analysis of {len(related_articles)} related sources...")
    analyzed_sources = []
    
    for i, article in enumerate(related_articles, 1):
        related_domain = extract_domain(article['url'])
        
        if not related_domain or related_domain == domain:
            # Skip same domain or invalid URLs
            continue
        
        print(f"  [{i}/{len(related_articles)}] Analyzing {related_domain}...")
        related_pub = get_or_research_publication(related_domain)
        
        if related_pub:
            analyzed_sources.append({
                'article': article,
                'publication': related_pub
            })
    
    # 5. Calculate consensus across sources
    print("\n📊 Step 5: Calculating consensus...")
    consensus = calculate_consensus(main_publication, analyzed_sources)
    
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE")
    print(f"   Main credibility: {main_publication.get('credibility_score', 'N/A')}/10")
    print(f"   Related sources analyzed: {len(analyzed_sources)}")
    print(f"   Consensus: {consensus.get('agreement_level', 'N/A')}")
    print(f"{'='*60}\n")
    
    return jsonify({
        'main_publication': main_publication,
        'myths': detected_myths,
        'related_sources': analyzed_sources,
        'consensus': consensus,
        'missing_context': generate_missing_context(main_publication, analyzed_sources)
    })

def calculate_consensus(main_pub, related_sources):
    """Calculate consensus and credibility across all sources"""
    if not related_sources:
        return {
            'agreement_level': 'No related sources found',
            'average_credibility': main_pub.get('credibility_score', 0),
            'high_credibility_sources': 0,
            'low_credibility_sources': 0,
            'consensus_strength': 'Unknown'
        }
    
    # Collect all credibility scores
    all_scores = [main_pub.get('credibility_score', 0)]
    for source in related_sources:
        score = source.get('publication', {}).get('credibility_score', 0)
        if score > 0:  # Only count valid scores
            all_scores.append(score)
    
    if len(all_scores) == 0:
        avg_credibility = 0
    else:
        avg_credibility = sum(all_scores) / len(all_scores)
    
    # Count high vs low credibility
    high_cred = len([s for s in all_scores if s >= 7])
    low_cred = len([s for s in all_scores if s < 5])
    
    # Determine consensus strength
    if len(all_scores) > 1:
        score_range = max(all_scores) - min(all_scores)
        if score_range < 2:
            consensus = 'Strong agreement'
            agreement = 'high'
        elif score_range < 4:
            consensus = 'Moderate agreement'
            agreement = 'moderate'
        else:
            consensus = 'Conflicting assessments'
            agreement = 'low'
    else:
        consensus = 'Insufficient sources'
        agreement = 'unknown'
    
    return {
        'agreement_level': agreement,
        'average_credibility': round(avg_credibility, 1),
        'high_credibility_sources': high_cred,
        'low_credibility_sources': low_cred,
        'consensus_strength': consensus,
        'total_sources_analyzed': len(all_scores)
    }

def generate_missing_context(main_pub, related_sources):
    """Generate list of missing context based on analysis"""
    context = []
    
    # Check for funding transparency
    if main_pub.get('funding_transparency') == 'low' or main_pub.get('funding_transparency') == 'none':
        context.append("Funding sources unclear or undisclosed")
    
    # Check for conflicts
    if main_pub.get('conflicts_of_interest'):
        context.append("Financial conflicts of interest present")
    
    # Check for source links
    if not main_pub.get('primary_source_links'):
        context.append("Article may not link to original research")
    
    # Check consensus
    if len(related_sources) < 3:
        context.append("Limited coverage from other sources")
    
    # Default contexts
    if not context:
        context = [
            "Consider checking original study details",
            "Look for potential funding sources",
            "Check if other reputable sources confirm"
        ]
    
    return context

if __name__ == '__main__':
    app.run(debug=True, port=5000)
