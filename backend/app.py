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

def should_reresearch(domain, publication):
    """
    Determine if cached publication needs re-research
    
    YOUR VISION: We only re-research if data is from OLD SYSTEM (before funding-first)
    We NEVER re-research because "the score seems too low for a prestigious source"
    
    Prestigious sources with conflicts SHOULD get low scores - that's the whole point
    """
    
    if not publication:
        return True
    
    # Check if this is old format data (before funding-first approach)
    is_old_format = False
    
    # Old data won't have these new fields
    if not publication.get('credibility_explanation'):
        is_old_format = True
        print(f"  🔄 Old data format (missing credibility_explanation) - re-researching")
        return True
    
    if not publication.get('funding_sources'):
        is_old_format = True
        print(f"  🔄 Old data format (missing funding_sources) - re-researching")
        return True
    
    if not publication.get('funding_transparency'):
        is_old_format = True
        print(f"  🔄 Old data format (missing funding_transparency) - re-researching")
        return True
    
    # If it has new format, TRUST THE SCORE
    # Even if Harvard gets 4.0/10 because they're pharma-funded - that's CORRECT
    print(f"  ✅ Using cached data (funding-first format)")
    return False

def is_publication_complete(publication):
    """Check if publication data is complete"""
    if not publication:
        return False
    
    required_fields = ['name', 'domain', 'credibility_score']
    for field in required_fields:
        if field not in publication or not publication[field]:
            return False
    
    if publication.get('credibility_score', 0) <= 0 or publication.get('credibility_score', 0) > 10:
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
    """
    Get publication from cache or research it
    
    YOUR VISION: Check if cached data uses funding-first approach
    If yes: use it (trust the score even if "low" for prestigious sources)
    If no: re-research with funding-first
    """
    if not domain:
        return None
    
    # Check cache
    cached_pub = None
    for pub in PUBLICATIONS:
        if pub.get('domain') == domain:
            cached_pub = pub
            break
    
    # Determine if we should use cache
    if cached_pub:
        if not is_publication_complete(cached_pub):
            print(f"🔄 Cached data incomplete for {domain}, re-researching...")
        elif should_reresearch(domain, cached_pub):
            # Will re-research (old format)
            pass
        else:
            # Use cache (new format, trust the score)
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
    """
    Quick filtering score - NOT final credibility
    
    YOUR VISION:
    - Start neutral (5.0)
    - Heavy penalties for obvious spam/commercial
    - Small boosts for initial filtering (gov/edu/journals)
    - Deep research determines REAL credibility (funding-first)
    
    This is just to avoid wasting time researching viagra-pills.com
    """
    score = 5.0
    
    # Check cache FIRST
    for pub in PUBLICATIONS:
        if pub.get('domain') == domain:
            # Only use cache if it's new format
            if pub.get('credibility_explanation') and pub.get('funding_sources'):
                cached_score = pub.get('credibility_score', 0)
                print(f"  ✅ Cached: {domain} = {cached_score}/10")
                return cached_score
    
    domain_lower = domain.lower()
    title_lower = result.get('title', '').lower()
    content_lower = result.get('content', '').lower()
    
    # SMALL boosts for initial filtering (NOT final credibility judgment)
    # These just help prioritize which sources to research deeply first
    
    if any(x in domain_lower for x in ['nih.gov', 'cdc.gov', 'cancer.gov', 'who.int']):
        score += 1.0  # Worth researching, but may be captured
        print(f"  +1.0 Gov health (worth checking): {domain}")
    
    if any(x in domain_lower for x in ['pmc.ncbi', 'pubmed', 'ncbi.nlm']):
        score += 1.0  # Archive of papers, quality varies
        print(f"  +1.0 Paper archive: {domain}")
    
    if any(x in domain_lower for x in ['nejm.org', 'thelancet.com', 'jamanetwork.com', 'nature.com', 'science.org', 'bmj.com']):
        score += 1.5  # Peer-reviewed journals worth checking
        print(f"  +1.5 Major journal: {domain}")
    
    if any(x in domain_lower for x in ['mayoclinic.org', 'clevelandclinic.org', 'hopkinsmedicine.org']):
        score += 0.5  # Medical centers, check funding
        print(f"  +0.5 Medical center: {domain}")
    
    if any(x in domain_lower for x in ['snopes.com', 'factcheck.org', 'sciencebasedmedicine.org', 'healthfeedback.org']):
        score += 1.0  # Fact-checkers worth checking
        print(f"  +1.0 Fact-checker: {domain}")
    
    if '.edu' in domain_lower:
        score += 0.3  # Academic, but check corporate funding
        print(f"  +0.3 Academic: {domain}")
    
    # HEAVY PENALTIES for obviously bad sources (don't waste research time)
    
    if any(x in domain_lower for x in ['shop', 'store', 'buy', 'order', 'supplement', 'pills', 'cbd', 'vitamin']):
        score = 0
        print(f"  🚫 Commercial/supplement: {domain}")
        return score
    
    if any(x in domain_lower for x in ['facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'tiktok.com', 'youtube.com', 'reddit.com']):
        score = 0
        print(f"  🚫 Social media: {domain}")
        return score
    
    if any(x in domain_lower for x in ['wordpress.com', 'blogspot', 'wix.com', 'medium.com', 'substack.com']):
        score -= 1.0
        print(f"  -1.0 Blog platform: {domain}")
    
    if any(x in domain_lower for x in ['naturalnews', 'infowars', 'mercola', 'beforeitsnews', 'davidwolfe']):
        score = 0
        print(f"  🚫 Known disinfo: {domain}")
        return score
    
    # Content signals (minor)
    
    if any(x in content_lower for x in ['peer-reviewed', 'clinical trial', 'randomized controlled']):
        score += 0.5
        print(f"  +0.5 Peer-review mentioned")
    
    if any(x in content_lower for x in ['independent', 'nonprofit', 'non-profit']):
        score += 0.5
        print(f"  +0.5 Independent mentioned")
    
    if any(x in title_lower for x in ['secret', 'doctors hate', 'shocking', 'miracle', 'cure', 'they dont want']):
        score -= 2.0
        print(f"  -2.0 Clickbait: {domain}")
    
    if any(x in content_lower for x in ['sponsored', 'partner content', 'affiliate', 'paid promotion']):
        score -= 1.0
        print(f"  -1.0 Sponsored: {domain}")
    
    return min(10, max(0, score))

def extract_key_topics(title):
    """Extract key health topics from title for focused evidence search"""
    
    # Remove common filler words
    stop_words = [
        'the', 'and', 'or', 'what', 'you', 'need', 'to', 'know', 
        'a', 'an', 'is', 'are', 'how', 'why', 'when', 'where',
        'for', 'with', 'about', 'from', 'your', 'that', 'this',
        'can', 'may', 'should', 'will', 'does', 'has', 'have'
    ]
    
    # Clean and split
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
    
    # Take 3-4 most relevant words
    topic_phrase = ' '.join(unique_words[:4])
    
    print(f"  🔎 Extracted topics: '{topic_phrase}'")
    
    return topic_phrase

def find_adaptive_evidence(title, main_domain, main_pub, claim_classification, article_content=""):
    """
    ADAPTIVE EVIDENCE SEARCH - Strategy depends on funding conflicts
    
    YOUR VISION: If main source has conflicts, search for independently funded alternatives
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
    """Build queries for basic fact confirmation"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} medical research peer-reviewed",
        f"{topic_phrase} scientific evidence consensus",
        f"{topic_phrase} health organization guidelines"
    ]

def build_independent_funding_queries(title, main_pub):
    """
    Build queries seeking DIFFERENT funding sources
    
    YOUR VISION: If main source is pharma-funded, find independent analysis
    """
    
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} independent research nonprofit",
        f"{topic_phrase} academic study university research",
        f"{topic_phrase} scientific analysis peer-reviewed"
    ]

def build_debunking_queries(title):
    """Build queries for evidence-based analysis"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} scientific evidence analysis",
        f"{topic_phrase} medical research review",
        f"{topic_phrase} peer-reviewed study findings"
    ]

def build_research_summary_queries(title):
    """Build queries for research summaries"""
    topic_phrase = extract_key_topics(title)
    
    return [
        f"{topic_phrase} systematic review meta-analysis",
        f"{topic_phrase} recent research peer-reviewed",
        f"{topic_phrase} clinical evidence summary"
    ]

def build_independent_research_queries(title, main_pub):
    """Build queries for independent research"""
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
    """
    Execute evidence search with funding-aware filtering
    
    YOUR VISION: Evidence source should be MORE credible than main source
    OR at least have DIFFERENT funding (to provide alternative perspective)
    """
    
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
                
                # Early exit if found good candidate
                if any(c['promise_score'] >= 6.5 for c in all_candidates):
                    print(f"  ✅ Found promising candidate, stopping search")
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
        
        if best['promise_score'] < 3.5:
            print(f"\n⚠️ Best candidate score too low ({best['promise_score']}/10), skipping")
            return None
        
        print(f"\n🎯 Best candidate: {best['domain']} (score: {best['promise_score']}/10)")
        
        # Deep research on best candidate
        evidence_pub = get_or_research_publication(best['domain'])
        
        if evidence_pub:
            evidence_score = evidence_pub.get('credibility_score', 0)
            main_score = main_pub.get('credibility_score', 0)
            
            # YOUR VISION: Evidence should be MORE credible OR have different funding
            
            is_basic_fact = classification in ['LIKELY_ESTABLISHED', 'ESTABLISHED_FACT_VERIFIED']
            has_conflicts = classification in ['INDUSTRY_NARRATIVE', 'MANUFACTURED_CONSENSUS', 'CONTESTED_WITH_CONFLICTS']
            
            # Determine minimum threshold
            if is_basic_fact:
                # For basic facts, accept equal credibility
                min_threshold = max(4.5, main_score - 0.5)
                print(f"  ℹ️ Basic fact - threshold = {min_threshold}/10")
            elif has_conflicts:
                # For conflicts, we want BETTER source OR different funding
                min_threshold = max(5.0, main_score)
                print(f"  ℹ️ Conflicts detected - need >= {min_threshold}/10 OR different funding")
                
                # Check funding diversity
                main_funding = set([str(f).lower() for f in main_pub.get('funding_sources', [])])
                evidence_funding = set([str(f).lower() for f in evidence_pub.get('funding_sources', [])])
                
                if main_funding and evidence_funding:
                    overlap = len(main_funding & evidence_funding)
                    total = len(main_funding | evidence_funding)
                    overlap_pct = (overlap / total * 100) if total > 0 else 0
                    
                    if overlap_pct < 40:  # Less than 40% overlap = different funding
                        print(f"  ✅ Different funding sources ({100-overlap_pct:.0f}% diversity) - acceptable despite lower score")
                        min_threshold = max(4.0, main_score - 1.0)  # Allow lower score if funding is different
                
            else:
                # For confirmation, want higher credibility
                min_threshold = max(5.5, main_score + 0.5)
                print(f"  ℹ️ Confirmation search - threshold = {min_threshold}/10")
            
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
    
    # 1. Analyze main publication (FUNDING FIRST)
    print("📊 Step 1: Analyzing main publication (FUNDING-FIRST approach)...")
    main_publication = get_or_research_publication(domain)
    
    # 2. FUNDING-AWARE CLAIM CLASSIFICATION
    print("\n🔬 Step 2: Funding-aware claim classification...")
    claim_classification = claim_analyzer.analyze_claim(title, article_content, main_publication)
    
    # 3. Detect myths
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
    print("\n🔄 Step 4: Adaptive evidence search (seeking independent sources)...")
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
    """
    Generate comparative analysis - FUNDING MATTERS MOST
    
    YOUR VISION: Highlight funding conflicts and diversity
    """
    
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
        
        # Calculate funding diversity (YOUR VISION: This is critical)
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
        
        # YOUR VISION: Warn about conflicts prominently
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
        
        elif evidence_score > main_score + 1.5:
            analysis['warning'] = "Higher credibility source available"
            analysis['recommendation'] = "Consider evidence from more credible source"
        
        elif analysis['credibility_difference'] >= 1.0:
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
    """Generate list of missing context - FUNDING FOCUSED"""
    
    context = []
    
    # Classification warnings first
    if claim_classification.get('warning'):
        context.append(claim_classification['warning'])
    
    for flag in claim_classification.get('red_flags', [])[:2]:
        if flag not in context:
            context.append(flag)
    
    # Funding transparency (YOUR VISION: Critical)
    if main_pub.get('funding_transparency') in ['low', 'none', 'unknown']:
        context.append("Funding sources unclear or undisclosed")
    
    # Conflicts
    if main_pub.get('conflicts_of_interest'):
        conflicts = main_pub.get('conflicts_of_interest', [])
        if conflicts and str(conflicts[0]) not in str(context):
            context.append(f"Conflict: {conflicts[0]}")
    
    # Primary sources
    if not main_pub.get('primary_source_links'):
        context.append("Article may not link to original research")
    
    # Evidence comparison
    if evidence:
        evidence_pub = evidence.get('publication', {})
        evidence_cred = evidence_pub.get('credibility_score', 0)
        main_cred = main_pub.get('credibility_score', 0)
        
        if evidence_cred > main_cred + 1.5:
            context.append("Alternative source has significantly higher credibility")
        
        main_funding = set([str(f).lower() for f in main_pub.get('funding_sources', [])])
        evidence_funding = set([str(f).lower() for f in evidence_pub.get('funding_sources', [])])
        
        if 'independent' in ' '.join(evidence_funding) and 'independent' not in ' '.join(main_funding):
            context.append("Evidence source is independently funded")
    
    # Fill with general advice if needed
    if len(context) < 3:
        context.extend([
            "Consider checking original research",
            "Look for independent verification"
        ])
    
    # Remove duplicates
    seen = set()
    unique_context = []
    for item in context:
        if item not in seen:
            seen.add(item)
            unique_context.append(item)
    
    return unique_context[:5]

if __name__ == '__main__':
    app.run(debug=True, port=5000)
