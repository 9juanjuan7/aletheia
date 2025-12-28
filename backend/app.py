from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from services.publication_researcher import PublicationResearcher
from tavily import TavilyClient

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load existing data
with open('data/publications.json', 'r') as f:
    PUBLICATIONS = json.load(f)

with open('data/myths.json', 'r') as f:
    MYTHS = json.load(f)

# Initialize services
researcher = PublicationResearcher()
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

def is_publication_complete(publication):
    """Check if publication data is complete enough to use"""
    if not publication:
        return False
    
    required_fields = ['name', 'domain', 'credibility_score']
    
    for field in required_fields:
        if field not in publication or not publication[field]:
            return False
    
    if publication.get('credibility_score', 0) <= 0 or publication.get('credibility_score', 0) > 10:
        return False
    
    if not publication.get('funding_sources') and publication.get('ownership') == 'Unknown':
        return False
    
    return True

def extract_domain(url):
    """Extract clean domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain if domain else None
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

def calculate_promise_score(domain, result):
    """Minimal filtering - just skip obvious junk"""
    score = 5.0
    
    # Check cache FIRST (most reliable indicator)
    for pub in PUBLICATIONS:
        if pub.get('domain') == domain:
            cached_score = pub.get('credibility_score', 0)
            if cached_score > 0:
                print(f"    ✅ Cached credibility: {cached_score}/10")
                return cached_score
    
    # Filter obvious junk
    domain_lower = domain.lower()
    title_lower = result.get('title', '').lower()
    
    # Skip obvious commercial sites
    if any(x in domain_lower for x in ['shop', 'store', 'buy', 'order', 'supplement', 'pills']):
        score = 1
        print(f"    🚫 Commercial/sales site")
        return score
    
    # Skip free blog platforms (lower quality)
    if any(x in domain_lower for x in ['wordpress.com', 'blogspot', 'wix.com', 'weebly']):
        score = 3
        print(f"    ⚠️ Free blog platform")
        return score
    
    # Skip clickbait patterns
    if any(x in title_lower for x in ['doctors hate', 'secret cure', 'they dont want', 'big pharma hiding']):
        score = 2
        print(f"    🚫 Clickbait title pattern")
        return score
    
    # Everything else: neutral - let funding analysis decide
    print(f"    → Will analyze funding to determine credibility")
    return score

def find_counter_perspective(title, main_domain):
    """Find ONE counter-perspective using Tavily with minimal filtering"""
    try:
        # Extract topic from title
        topic = ' '.join(title.split()[:8])
        
        # Search for counter-perspectives
        query = f"{topic} debunked myth fact check evidence research"
        
        print(f"🔍 Searching for counter-perspective: {query[:60]}...")
        
        response = tavily_client.search(
            query=query,
            max_results=5,
            search_depth="basic"
        )
        
        candidates = []
        
        # Evaluate candidates
        print(f"\n  📋 Evaluating {len(response.get('results', []))} candidates...")
        for i, result in enumerate(response.get('results', []), 1):
            result_domain = extract_domain(result.get('url', ''))
            
            # Skip same domain
            if not result_domain or result_domain == main_domain:
                print(f"  [{i}] Skipped: {result_domain or 'invalid'} (same as main or invalid)")
                continue
            
            print(f"\n  [{i}] Evaluating: {result_domain}")
            
            # Calculate promise score
            promise_score = calculate_promise_score(result_domain, result)
            
            candidates.append({
                'domain': result_domain,
                'promise_score': promise_score,
                'result': result
            })
            
            print(f"      Promise score: {promise_score}/10")
        
        if not candidates:
            print("\n⚠️  No valid counter-perspective candidates found")
            return None
        
        # Sort by promise score and pick best
        candidates.sort(key=lambda x: x['promise_score'], reverse=True)
        best = candidates[0]
        
        print(f"\n🎯 Best candidate: {best['domain']} (score: {best['promise_score']}/10)")
        
        # Analyze the best candidate
        counter_pub = get_or_research_publication(best['domain'])
        
        if counter_pub:
            return {
                'article': {
                    'title': best['result'].get('title', 'Unknown'),
                    'url': best['result'].get('url', ''),
                    'snippet': best['result'].get('content', '')[:200]
                },
                'publication': counter_pub
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Counter-perspective search failed: {e}")
        import traceback
        traceback.print_exc()
        return None

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
    
    # 3. Find counter-perspective
    print("\n🔄 Step 3: Searching for counter-perspective...")
    counter_perspective = find_counter_perspective(title, domain)
    
    # 4. Generate analysis
    print("\n📊 Step 4: Generating comparative analysis...")
    analysis = generate_analysis(main_publication, counter_perspective)
    
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE")
    print(f"   Main credibility: {main_publication.get('credibility_score', 'N/A')}/10")
    if counter_perspective:
        counter_name = counter_perspective['publication'].get('name', 'Unknown')
        counter_score = counter_perspective['publication'].get('credibility_score', 'N/A')
        print(f"   Counter source: {counter_name}")
        print(f"   Counter credibility: {counter_score}/10")
        if isinstance(counter_score, (int, float)) and isinstance(main_publication.get('credibility_score', 0), (int, float)):
            diff = abs(counter_score - main_publication.get('credibility_score', 0))
            print(f"   Credibility gap: {diff:.1f} points")
    else:
        print(f"   Counter source: Not found")
    print(f"{'='*60}\n")
    
    return jsonify({
        'main_publication': main_publication,
        'myths': detected_myths,
        'counter_perspective': counter_perspective,
        'analysis': analysis,
        'missing_context': generate_missing_context(main_publication, counter_perspective)
    })

def generate_analysis(main_pub, counter):
    """Generate comparative analysis"""
    analysis = {
        'main_credibility': main_pub.get('credibility_score', 0),
        'main_red_flags': main_pub.get('red_flags', []),
        'main_green_flags': main_pub.get('green_flags', []),
        'main_funding': main_pub.get('funding_sources', []),
        'main_conflicts': main_pub.get('conflicts_of_interest', [])
    }
    
    if counter:
        counter_pub = counter.get('publication', {})
        main_score = main_pub.get('credibility_score', 0)
        counter_score = counter_pub.get('credibility_score', 0)
        
        analysis['counter_credibility'] = counter_score
        analysis['counter_red_flags'] = counter_pub.get('red_flags', [])
        analysis['counter_green_flags'] = counter_pub.get('green_flags', [])
        analysis['counter_funding'] = counter_pub.get('funding_sources', [])
        analysis['counter_conflicts'] = counter_pub.get('conflicts_of_interest', [])
        analysis['credibility_difference'] = abs(main_score - counter_score)
        
        # Generate warning based on credibility gap
        if analysis['credibility_difference'] >= 3:
            if counter_score > main_score:
                analysis['warning'] = "Higher credibility source presents different perspective"
                analysis['recommendation'] = "Consider the counter-perspective from more credible source"
            else:
                analysis['warning'] = "Lower credibility counter-source found"
                analysis['recommendation'] = "Main source appears more reliable"
        elif analysis['credibility_difference'] >= 1.5:
            analysis['warning'] = "Moderate credibility difference"
            analysis['recommendation'] = "Compare funding sources and conflicts of interest"
        else:
            analysis['warning'] = None
            analysis['recommendation'] = "Similar credibility - check funding transparency"
    else:
        analysis['counter_credibility'] = None
        analysis['counter_red_flags'] = []
        analysis['counter_green_flags'] = []
        analysis['counter_funding'] = []
        analysis['counter_conflicts'] = []
        analysis['credibility_difference'] = 0
        analysis['warning'] = "No counter-perspective found"
        analysis['recommendation'] = "Search for alternative sources independently"
    
    return analysis

def generate_missing_context(main_pub, counter):
    """Generate list of missing context"""
    context = []
    
    # Main source issues
    if main_pub.get('funding_transparency') in ['low', 'none', 'unknown']:
        context.append("Funding sources unclear or undisclosed")
    
    if main_pub.get('conflicts_of_interest'):
        conflicts = main_pub.get('conflicts_of_interest', [])
        if conflicts:
            context.append(f"Conflicts: {conflicts[0]}")
    
    if not main_pub.get('primary_source_links'):
        context.append("Article may not link to original research")
    
    # Counter-perspective insights
    if counter:
        counter_pub = counter.get('publication', {})
        counter_cred = counter_pub.get('credibility_score', 0)
        main_cred = main_pub.get('credibility_score', 0)
        
        if counter_cred > main_cred + 2:
            context.append("Alternative source has significantly higher credibility")
        
        # Compare funding
        main_funding = set(main_pub.get('funding_sources', []))
        counter_funding = set(counter_pub.get('funding_sources', []))
        
        if 'Independent' in counter_funding and 'Independent' not in main_funding:
            context.append("Counter-source is independently funded")
    else:
        context.append("No alternative perspectives found - single narrative")
    
    # Defaults
    if not context:
        context = [
            "Consider checking original study",
            "Look for independent verification"
        ]
    
    return context[:5]  # Limit to 5 items

if __name__ == '__main__':
    app.run(debug=True, port=5000)
