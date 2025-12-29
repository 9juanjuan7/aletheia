from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from services.publication_researcher import PublicationResearcher
from services.claim_analyzer import ClaimAnalyzer
from tavily import TavilyClient
import re

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
claim_analyzer = ClaimAnalyzer()
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

# Domains that need automatic re-research (outdated scoring)
NEEDS_RERESEARCH = [
    'pmc.ncbi.nlm.nih.gov',
    'ncbi.nlm.nih.gov',
    'pubmed.ncbi.nlm.nih.gov',
    'who.int',
    'fda.gov',
    'cdc.gov',
    'usda.gov',
    'nih.gov',
    'cancer.gov'
]

def should_reresearch(domain, publication):
    """
    Determine if a cached publication should be re-researched
    Reasons:
    1. Domain is in NEEDS_RERESEARCH list and score seems outdated
    2. Government/academic domain with suspiciously low score
    3. Cache is very old (future enhancement)
    """
    
    if not publication:
        return True
    
    # Check if domain is flagged for re-research
    if domain in NEEDS_RERESEARCH:
        score = publication.get('credibility_score', 0)
        
        # Government domains should score 4.0+ minimum
        if '.gov' in domain and score < 4.0:
            print(f"  🔄 Government domain with score {score}/10 - re-researching")
            return True
        
        # PMC/NCBI/PubMed should score 7.0+ (academic paper archives)
        if any(x in domain for x in ['pmc.ncbi', 'pubmed', 'ncbi.nlm']) and score < 7.0:
            print(f"  🔄 PMC/NCBI with score {score}/10 should be 7.0+ - re-researching")
            return True
        
        # WHO should score 6.5+ minimum
        if 'who.int' in domain and score < 6.5:
            print(f"  🔄 WHO with score {score}/10 should be 6.5+ - re-researching")
            return True
        
        # FDA/CDC should be 4.5-6.0 range
        if any(x in domain for x in ['fda.gov', 'cdc.gov']) and (score < 4.5 or score > 7.0):
            print(f"  🔄 FDA/CDC with score {score}/10 out of expected range - re-researching")
            return True
        
        # USDA should be 4.0-5.0 range (captured)
        if 'usda.gov' in domain and (score < 3.5 or score > 5.5):
            print(f"  🔄 USDA with score {score}/10 out of expected range - re-researching")
            return True
    
    # Academic domains with very low scores
    if '.edu' in domain:
        score = publication.get('credibility_score', 0)
        if score < 4.0:
            print(f"  🔄 Academic domain with unusually low score {score}/10 - re-researching")
            return True
    
    return False

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
    """Get publication from cache or research it - with automatic re-research for outdated data"""
    if not domain:
        return None
    
    # Check cache
    cached_pub = None
    for pub in PUBLICATIONS:
        if pub.get('domain') == domain:
            cached_pub = pub
            break
    
    # Determine if we should use cache or re-research
    if cached_pub:
        # Check if data is complete
        if not is_publication_complete(cached_pub):
            print(f"🔄 Cached data incomplete for {domain}, re-researching...")
        # Check if needs re-research due to outdated scoring
        elif should_reresearch(domain, cached_pub):
            print(f"🔄 Cached data outdated for {domain}, re-researching with updated criteria...")
        else:
            print(f"✅ Using cached data for {domain}")
            return cached_pub
    
    # Research needed
    print(f"🔍 Researching new source: {domain}...")
    new_pub = researcher.research(domain)
    
    # Update cache
    updated = False
    for i, pub in enumerate(PUBLICATIONS):
        if pub.get('domain') == domain:
            PUBLICATIONS[i] = new_pub
            updated = True
            print(f"  ✅ Updated cache for {domain}")
            break
    
    if not updated:
        PUBLICATIONS.append(new_pub)
        print(f"  ✅ Added {domain} to cache")
    
    # Save to file
    with open('data/publications.json', 'w') as f:
        json.dump(PUBLICATIONS, f, indent=2)
    
    return new_pub

def calculate_promise_score(domain, result):
    """Improved promise score with better heuristics"""
    score = 5.0
    
    # Check cache FIRST
    for pub in PUBLICATIONS:
        if pub.get('domain') == domain:
            cached_score = pub.get('credibility_score', 0)
            if cached_score > 0:
                # But check if it needs re-research
                if should_reresearch(domain, pub):
                    print(f"  🔄 Cached score outdated for {domain}, will re-research")
                    break
                print(f"  ✅ Cached: {domain} = {cached_score}/10")
                return cached_score
    
    domain_lower = domain.lower()
    title_lower = result.get('title', '').lower()
    content_lower = result.get('content', '').lower()
    
    # HIGH TRUST domains
    if any(x in domain_lower for x in ['nih.gov', 'cdc.gov', 'cancer.gov', 'who.int']):
        score += 2
        print(f"  +2 Government health: {domain}")
    
    # PMC/NCBI/PubMed (academic paper archives)
    if any(x in domain_lower for x in ['pmc.ncbi', 'pubmed.ncbi.nlm', 'ncbi.nlm.nih']):
        score += 2.5
        print(f"  +2.5 Academic paper archive: {domain}")
    
    if any(x in domain_lower for x in ['nejm.org', 'thelancet.com', 'jamanetwork.com', 'nature.com', 'science.org', 'cell.com', 'bmj.com']):
        score += 3
        print(f"  +3 Top journal: {domain}")
    
    if any(x in domain_lower for x in ['mayoclinic.org', 'clevelandclinic.org', 'hopkinsmedicine.org', 'mdanderson.org']):
        score += 2
        print(f"  +2 Medical center: {domain}")
    
    if any(x in domain_lower for x in ['snopes.com', 'factcheck.org', 'sciencebasedmedicine.org', 'healthfeedback.org']):
        score += 2
        print(f"  +2 Fact-checker: {domain}")
    
    if '.edu' in domain_lower:
        score += 0.5
        print(f"  +0.5 Academic (.edu): {domain}")
    
    # RED FLAGS
    if any(x in domain_lower for x in ['shop', 'store', 'buy', 'order', 'supplement', 'pills', 'diet', 'cbd', 'vitamin']):
        score = 1
        print(f"  🚫 Commercial site: {domain}")
        return score
    
    # Social media = not credible for evidence
    if any(x in domain_lower for x in ['facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com', 'youtube.com']):
        score = 1
        print(f"  🚫 Social media: {domain}")
        return score
    
    if any(x in domain_lower for x in ['wordpress.com', 'blogspot', 'wix.com', 'weebly', 'medium.com']):
        score -= 2
        print(f"  -2 Blog platform: {domain}")
    
    if any(x in domain_lower for x in ['naturalnews', 'infowars', 'beforeitsnews']):
        score = 0
        print(f"  🚫 Known misinformation: {domain}")
        return score
    
    # Content quality signals
    if any(x in content_lower for x in ['peer-reviewed', 'peer reviewed', 'clinical trial', 'randomized controlled']):
        score += 1.5
        print(f"  +1.5 Scientific content")
    
    if any(x in content_lower for x in ['independent', 'nonprofit', 'non-profit']):
        score += 1
        print(f"  +1 Independent/nonprofit mentioned")
    
    if any(x in title_lower for x in ['study shows', 'research finds', 'according to', 'evidence']):
        score += 0.5
        print(f"  +0.5 Evidence-based title")
    
    # Negative content signals
    if any(x in title_lower for x in ['secret', 'doctors hate', 'they dont want', 'shocking', 'miracle']):
        score -= 2
        print(f"  -2 Clickbait title")
    
    if any(x in content_lower for x in ['sponsored', 'partner content', 'affiliate']):
        score -= 1
        print(f"  -1 Sponsored content")
    
    return min(10, max(0, score))

def extract_key_topics(title):
    """Extract key health topics from title for better evidence search - ENHANCED"""
    
    # Remove common filler words
    stop_words = ['the', 'and', 'or', 'what', 'you', 'need', 'to', 'know', 
                  'a', 'an', 'is', 'are', 'how', 'why', 'when', 'where',
                  'for', 'with', 'about', 'from', 'your', 'that', 'this',
                  'can', 'may', 'should', 'will', 'does']
    
    # Remove special characters and split
    title_clean = re.sub(r'[•\[\]\(\)•]', ' ', title.lower())
    title_clean = re.sub(r'[^\w\s-]', ' ', title_clean)
    words = title_clean.split()
    
    # Filter stop words and short words
    key_words = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_words = []
    for w in key_words:
        if w not in seen:
            seen.add(w)
            unique_words.append(w)
    
    # Take 3-4 most relevant words (fewer is better for focused search)
    topic_phrase = ' '.join(unique_words[:4])
    
    print(f"  🔎 Extracted topics: '{topic_phrase}'")
    
    return topic_phrase

def find_adaptive_evidence(title, main_domain, main_pub, claim_classification, article_content=""):
    """
    ADAPTIVE EVIDENCE SEARCH
    Strategy depends on claim classification (funding-aware)
    """
    
    strategy = claim_classification.get('search_strategy', 'search_independently_funded_analysis')
    classification = claim_classification.get('classification')
    
    print(f"\n🎯 ADAPTIVE EVIDENCE SEARCH")
    print(f"  Classification: {classification}")
    print(f"  Strategy: {strategy}")
    
    # Build search queries based on strategy
    if strategy == 'search_authoritative_confirmation':
        queries = build_confirmation_queries(title, main_pub)
        label = claim_classification.get('result_label', 'Authoritative Confirmation')
    
    elif strategy == 'search_independently_funded_analysis':
        queries = build_independent_funding_queries(title, main_pub)
        label = claim_classification.get('result_label', 'Independent Analysis')
    
    elif strategy == 'search_debunking':
        queries = build_debunking_queries(title)
        label = claim_classification.get('result_label', 'Evidence-Based Analysis')
    
    elif strategy == 'search_recent_peer_reviewed':
        queries = build_research_summary_queries(title)
        label = claim_classification.get('result_label', 'Current Research Summary')
    
    elif strategy == 'search_independently_funded_research':
        queries = build_independent_research_queries(title, main_pub)
        label = claim_classification.get('result_label', 'Independent Research')
    
    else:
        queries = build_default_queries(title)
        label = claim_classification.get('result_label', 'Additional Context')
    
    print(f"  Search queries: {len(queries)}")
    for q in queries:
        print(f"    - {q[:70]}...")
    
    # Execute search
    evidence = execute_evidence_search(queries, main_domain, main_pub, strategy, classification)
    
    if evidence:
        evidence['label'] = label
        evidence['classification'] = classification
    
    return evidence

def build_confirmation_queries(title, main_pub):
    """Build queries to find authoritative confirmation"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} site:nih.gov OR site:cdc.gov OR site:who.int",
        f"{topic_phrase} peer-reviewed consensus",
        f"{topic_phrase} medical research evidence"
    ]

def build_independent_funding_queries(title, main_pub):
    """Build queries specifically seeking sources with different funding - ENHANCED"""
    
    topic_phrase = extract_key_topics(title)
    
    funding = main_pub.get('funding_sources', [])
    industry_ties = main_pub.get('industry_ties', [])
    
    queries = [
        f"{topic_phrase} independent research nonprofit",
        f"{topic_phrase} academic study university research",
        f"{topic_phrase} government health agency analysis"
    ]
    
    return queries

def build_debunking_queries(title):
    """Build queries to find evidence-based debunking"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} scientific evidence fact check",
        f"{topic_phrase} medical research consensus",
        f"{topic_phrase} peer-reviewed study analysis"
    ]

def build_research_summary_queries(title):
    """Build queries for recent research summaries"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} systematic review meta-analysis",
        f"{topic_phrase} recent research peer-reviewed",
        f"{topic_phrase} clinical evidence summary"
    ]

def build_independent_research_queries(title, main_pub):
    """Build queries for independent research on contested topics"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} independent research study",
        f"{topic_phrase} peer-reviewed meta-analysis",
        f"{topic_phrase} university research findings"
    ]

def build_default_queries(title):
    """Default query building"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} scientific evidence research",
        f"{topic_phrase} expert analysis",
        f"{topic_phrase} medical perspective"
    ]

def execute_evidence_search(queries, main_domain, main_pub, strategy, classification):
    """Execute the evidence search with appropriate filtering - ENHANCED"""
    
    try:
        all_candidates = []
        
        for query in queries:
            try:
                print(f"\n  📡 Query: {query[:60]}...")
                response = tavily_client.search(
                    query=query,
                    max_results=3,
                    search_depth="basic"
                )
                
                for result in response.get('results', []):
                    result_domain = extract_domain(result.get('url', ''))
                    if not result_domain or result_domain == main_domain:
                        continue
                    
                    if any(c['domain'] == result_domain for c in all_candidates):
                        continue
                    
                    promise_score = calculate_promise_score(result_domain, result)
                    
                    all_candidates.append({
                        'domain': result_domain,
                        'promise_score': promise_score,
                        'result': result,
                        'query': query
                    })
                
                if any(c['promise_score'] >= 7 for c in all_candidates):
                    print(f"  ✅ Found high-quality candidate, stopping search")
                    break
                    
            except Exception as e:
                print(f"  ⚠️ Search query failed: {e}")
                continue
        
        if not all_candidates:
            print("\n⚠️ No valid evidence candidates found")
            return None
        
        all_candidates.sort(key=lambda x: x['promise_score'], reverse=True)
        
        print(f"\n  📊 Evaluated {len(all_candidates)} total candidates")
        print(f"  🏆 Top 3 scores: {[c['promise_score'] for c in all_candidates[:3]]}")
        
        best = all_candidates[0]
        
        if best['promise_score'] < 4:
            print(f"\n⚠️ Best candidate score too low ({best['promise_score']}/10), skipping")
            return None
        
        print(f"\n🎯 Best candidate: {best['domain']} (score: {best['promise_score']}/10)")
        
        evidence_pub = get_or_research_publication(best['domain'])
        
        if evidence_pub:
            evidence_score = evidence_pub.get('credibility_score', 0)
            main_score = main_pub.get('credibility_score', 0)
            
            # ENHANCED: Different thresholds based on context
            is_basic_fact = classification in ['LIKELY_ESTABLISHED', 'ESTABLISHED_FACT_VERIFIED']
            
            if is_basic_fact:
                # For basic facts, accept evidence at same level as main source
                min_threshold = main_score
                print(f"  ℹ️ Basic fact search - threshold = main source score ({min_threshold}/10)")
            elif 'independent' in strategy or 'debunk' in strategy:
                min_threshold = max(5.0, main_score)
                print(f"  ℹ️ Independent/debunk search - threshold = max(5.0, {main_score}) = {min_threshold}/10")
            else:
                min_threshold = max(6.0, main_score)
                print(f"  ℹ️ Confirmation search - threshold = max(6.0, {main_score}) = {min_threshold}/10")
            
            if evidence_score < min_threshold:
                print(f"⚠️ Evidence source credibility too low ({evidence_score}/10), need >= {min_threshold}/10")
                return None
            
            return {
                'article': {
                    'title': best['result'].get('title', 'Unknown'),
                    'url': best['result'].get('url', ''),
                    'snippet': best['result'].get('content', '')[:200]
                },
                'publication': evidence_pub
            }
        
        return None
        
    except Exception as e:
        print(f"❌ Evidence search failed: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '')
    article_content = data.get('content', '')
    
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
    
    # 2. FUNDING-AWARE CLAIM CLASSIFICATION
    print("\n🔬 Step 2: Funding-aware claim classification...")
    claim_classification = claim_analyzer.analyze_claim(title, article_content, main_publication)
    
    # 3. Detect myths in title
    print("\n🔍 Step 3: Checking for common health myths...")
    detected_myths = []
    title_lower = title.lower()
    for myth in MYTHS:
        for keyword in myth['keywords']:
            if keyword.lower() in title_lower:
                detected_myths.append(myth)
                break
    
    if detected_myths:
        print(f"⚠️ Found {len(detected_myths)} potential myth(s)")
    else:
        print("✅ No common myths detected")
    
    # 4. ADAPTIVE EVIDENCE SEARCH
    print("\n🔄 Step 4: Adaptive evidence search...")
    evidence = find_adaptive_evidence(
        title, 
        domain, 
        main_publication, 
        claim_classification,
        article_content
    )
    
    # 5. Generate analysis
    print("\n📊 Step 5: Generating comparative analysis...")
    analysis = generate_analysis(main_publication, evidence, claim_classification)
    
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE")
    print(f"  Classification: {claim_classification['classification']}")
    print(f"  Main credibility: {main_publication.get('credibility_score', 'N/A')}/10")
    if evidence:
        evidence_name = evidence['publication'].get('name', 'Unknown')
        evidence_score = evidence['publication'].get('credibility_score', 'N/A')
        print(f"  Evidence source: {evidence_name}")
        print(f"  Evidence credibility: {evidence_score}/10")
    else:
        print(f"  Evidence source: Not found")
    print(f"{'='*60}\n")
    
    return jsonify({
        'main_publication': main_publication,
        'claim_classification': claim_classification,
        'myths': detected_myths,
        'evidence': evidence,
        'analysis': analysis,
        'missing_context': generate_missing_context(main_publication, evidence, claim_classification)
    })

def generate_analysis(main_pub, evidence, claim_classification):
    """Generate comparative analysis with funding-aware context"""
    
    analysis = {
        'main_credibility': main_pub.get('credibility_score', 0),
        'main_red_flags': main_pub.get('red_flags', []),
        'main_green_flags': main_pub.get('green_flags', []),
        'main_funding': main_pub.get('funding_sources', []),
        'main_conflicts': main_pub.get('conflicts_of_interest', []),
        'classification': claim_classification.get('classification'),
        'classification_warning': claim_classification.get('warning'),
        'classification_red_flags': claim_classification.get('red_flags', [])
    }
    
    if evidence:
        evidence_pub = evidence.get('publication', {})
        main_score = main_pub.get('credibility_score', 0)
        evidence_score = evidence_pub.get('credibility_score', 0)
        
        analysis['evidence_credibility'] = evidence_score
        analysis['evidence_red_flags'] = evidence_pub.get('red_flags', [])
        analysis['evidence_green_flags'] = evidence_pub.get('green_flags', [])
        analysis['evidence_funding'] = evidence_pub.get('funding_sources', [])
        analysis['evidence_conflicts'] = evidence_pub.get('conflicts_of_interest', [])
        analysis['credibility_difference'] = abs(main_score - evidence_score)
        analysis['evidence_label'] = evidence.get('label', 'Additional Evidence')
        
        main_funding_set = set([str(f).lower() for f in analysis['main_funding']])
        evidence_funding_set = set([str(f).lower() for f in analysis['evidence_funding']])
        
        if main_funding_set and evidence_funding_set:
            overlap = len(main_funding_set & evidence_funding_set)
            total = len(main_funding_set | evidence_funding_set)
            funding_overlap_pct = (overlap / total * 100) if total > 0 else 0
        else:
            funding_overlap_pct = 0
        
        analysis['funding_diversity'] = 100 - funding_overlap_pct
        
        classification = claim_classification.get('classification')
        
        if classification in ['MANUFACTURED_CONSENSUS', 'INDUSTRY_NARRATIVE']:
            if evidence_score > main_score:
                analysis['warning'] = "🚨 CRITICAL: Higher credibility source with different funding presents conflicting perspective"
                analysis['recommendation'] = "Strongly consider the independently funded source"
            else:
                analysis['warning'] = "⚠️ Industry conflicts detected in main source"
                analysis['recommendation'] = "Verify claims with independent sources"
        
        elif classification == 'ESTABLISHED_FACT_VERIFIED':
            analysis['warning'] = None
            analysis['recommendation'] = "Claim confirmed by multiple high-credibility independent sources"
        
        elif evidence_score > main_score + 2:
            analysis['warning'] = "Higher credibility source available"
            analysis['recommendation'] = "Consider evidence from more credible source"
        
        elif analysis['credibility_difference'] >= 1.5:
            analysis['warning'] = "Moderate credibility difference"
            analysis['recommendation'] = "Compare funding sources and methodology"
        
        else:
            analysis['warning'] = None
            analysis['recommendation'] = "Similar credibility - review both perspectives"
    
    else:
        analysis['evidence_credibility'] = None
        analysis['evidence_red_flags'] = []
        analysis['evidence_green_flags'] = []
        analysis['evidence_funding'] = []
        analysis['evidence_conflicts'] = []
        analysis['credibility_difference'] = 0
        analysis['funding_diversity'] = 0
        analysis['evidence_label'] = None
        
        classification = claim_classification.get('classification')
        
        if classification in ['MANUFACTURED_CONSENSUS', 'INDUSTRY_NARRATIVE']:
            analysis['warning'] = "⚠️ Industry conflicts detected - no independent alternative found"
            analysis['recommendation'] = "Search for independent sources manually"
        else:
            analysis['warning'] = "No additional evidence sources found"
            analysis['recommendation'] = "Verify claims independently"
    
    return analysis

def generate_missing_context(main_pub, evidence, claim_classification):
    """Generate list of missing context with classification awareness"""
    
    context = []
    
    if claim_classification.get('warning'):
        context.append(claim_classification['warning'])
    
    for flag in claim_classification.get('red_flags', [])[:2]:
        if flag not in context:
            context.append(flag)
    
    if main_pub.get('funding_transparency') in ['low', 'none', 'unknown']:
        context.append("Funding sources unclear or undisclosed")
    
    if main_pub.get('conflicts_of_interest'):
        conflicts = main_pub.get('conflicts_of_interest', [])
        if conflicts and str(conflicts[0]) not in str(context):
            context.append(f"Conflict: {conflicts[0]}")
    
    if not main_pub.get('primary_source_links'):
        context.append("Article may not link to original research")
    
    if evidence:
        evidence_pub = evidence.get('publication', {})
        evidence_cred = evidence_pub.get('credibility_score', 0)
        main_cred = main_pub.get('credibility_score', 0)
        
        if evidence_cred > main_cred + 2:
            context.append("Alternative source has significantly higher credibility")
        
        main_funding = set([str(f).lower() for f in main_pub.get('funding_sources', [])])
        evidence_funding = set([str(f).lower() for f in evidence_pub.get('funding_sources', [])])
        
        if 'independent' in ' '.join(evidence_funding) and 'independent' not in ' '.join(main_funding):
            context.append("Evidence source is independently funded")
    
    if len(context) < 3:
        context.extend([
            "Consider checking original research",
            "Look for independent verification"
        ])
    
    seen = set()
    unique_context = []
    for item in context:
        if item not in seen:
            seen.add(item)
            unique_context.append(item)
    
    return unique_context[:5]

if __name__ == '__main__':
    app.run(debug=True, port=5000)
