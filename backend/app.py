from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from services.publication_researcher import PublicationResearcher
from services.claim_analyzer import ClaimAnalyzer
from services.claim_verification import ClaimAnalyzer as ClaimVerifier
from services.scoring import (
    calculate_funding_independence_score,
    calculate_claim_accuracy_score,
    calculate_source_quality_score,
    calculate_nuanced_recommendation,
    analyze_research_support_pattern
)
from tavily import TavilyClient
import re
import queue
import threading

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
claim_verifier = ClaimVerifier()
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

# Progress tracking
progress_queues = {}

def send_progress(session_id, message, submessage=None):
    """Send progress update to frontend"""
    if session_id and session_id in progress_queues:
        progress_data = {'message': message}
        if submessage:
            progress_data['submessage'] = submessage
        progress_queues[session_id].put(json.dumps(progress_data))

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

def get_or_research_publication(domain, session_id=None):
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
            send_progress(session_id, f"🔍 Researching {domain}", "Cached data incomplete")
        elif should_reresearch(domain, cached_pub):
            # Will re-research (old format)
            send_progress(session_id, f"🔍 Researching {domain}", "Updating funding data")
        else:
            # Use cache (new format, trust the score)
            print(f"✅ Using cached data for {domain}")
            send_progress(session_id, f"🔍 Analyzing {domain}", "Using cached data")
            score = cached_pub.get('credibility_score', 0)
            funding = cached_pub.get('funding_sources', [])
            if funding:
                send_progress(session_id, f"🔍 Analyzing {domain}", f"→ Credibility: {score}/10")
            return cached_pub
    else:
        send_progress(session_id, f"🔍 Researching {domain}", "First time analyzing this source")
    
    # Research needed
    print(f"🔍 Researching new source: {domain}...")
    new_pub = researcher.research(domain)
    
    # Send credibility result
    score = new_pub.get('credibility_score', 0)
    funding = new_pub.get('funding_sources', [])
    if funding:
        send_progress(session_id, f"🔍 Researching {domain}", "→ Found funding sources")
    send_progress(session_id, f"🔍 Researching {domain}", f"→ Credibility: {score}/10")
    
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
    """
    Extract key health topics from title for focused evidence search
    
    YOUR VISION: Extract what the article is ABOUT, not where it's FROM
    User searches "red meat health", not "red meat anderson"
    """
    
    # Remove site branding (everything after | or -)
    title_clean = title.lower()
    for separator in [' | ', ' - ', ' – ', ' — ', ' : ']:
        if separator in title_clean:
            title_clean = title_clean.split(separator)[0].strip()
            break
    
    print(f"  📝 Title cleaned: '{title_clean}'")
    
    # Remove punctuation
    title_clean = re.sub(r'[^\w\s]', ' ', title_clean)
    
    # Remove common filler words only (keep health terms)
    stop_words = {
        'the', 'and', 'or', 'what', 'you', 'need', 'to', 'know',
        'a', 'an', 'is', 'are', 'how', 'why', 'when', 'where',
        'for', 'with', 'about', 'from', 'your', 'that', 'this',
        'can', 'may', 'should', 'will', 'does', 'has', 'have', 'be'
    }
    
    words = [w for w in title_clean.split() if w not in stop_words and len(w) > 2]
    
    # Take first 4-5 words for context
    topic_phrase = ' '.join(words[:5])
    
    print(f"  🔎 Search topic: '{topic_phrase}'")
    
    return topic_phrase

def find_adaptive_evidence(title, main_domain, main_pub, claim_classification, article_content="", session_id=None):
    """
    ADAPTIVE EVIDENCE SEARCH - Strategy depends on funding conflicts
    
    YOUR VISION: If main source has conflicts, search for independently funded alternatives
    """
    
    strategy = claim_classification.get('search_strategy', 'search_independently_funded_analysis')
    classification = claim_classification.get('classification')
    
    print(f"\n🎯 ADAPTIVE EVIDENCE SEARCH")
    print(f"  Classification: {classification}")
    print(f"  Strategy: {strategy}")
    
    send_progress(session_id, "🔎 Finding alternative sources")
    send_progress(session_id, "🔎 Finding alternative sources", "→ Searching peer-reviewed research...")
    
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
    evidence = execute_evidence_search(queries, main_domain, main_pub, strategy, classification, session_id)
    
    if evidence:
        evidence['label'] = label
        evidence['classification'] = classification
        evidence_name = evidence['publication'].get('name', 'Unknown source')
        evidence_score = evidence['publication'].get('credibility_score', 0)
        send_progress(session_id, "🔎 Finding alternative sources", f"→ Found: {evidence_name}")
        send_progress(session_id, "🔎 Finding alternative sources", f"→ Evidence credibility: {evidence_score}/10")
    else:
        send_progress(session_id, "🔎 Finding alternative sources", "→ No higher-quality sources found")
    
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

def execute_evidence_search(queries, main_domain, main_pub, strategy, classification, session_id=None):
    """
    Execute evidence search with funding-aware filtering
    
    YOUR VISION SIMPLIFIED: If evidence source has equal or better credibility, use it.
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
        evidence_pub = get_or_research_publication(best['domain'], session_id)
        
        if evidence_pub:
            evidence_score = evidence_pub.get('credibility_score', 0)
            main_score = main_pub.get('credibility_score', 0)
            
            print(f"  📊 Main source: {main_score}/10")
            print(f"  📊 Evidence source: {evidence_score}/10")
            
            # YOUR VISION: Simple rule - equal or better = use it
            if evidence_score >= main_score:
                print(f"  ✅ Evidence source credibility equal or better ({evidence_score} >= {main_score}) - ACCEPTED")
                
                return {
                    'article': {
                        'title': best['result'].get('title', 'Unknown'),
                        'url': best['result'].get('url', ''),
                        'snippet': best['result'].get('content', '')[:200]
                    },
                    'publication': evidence_pub
                }
            else:
                print(f"  ❌ Evidence source credibility lower ({evidence_score} < {main_score}) - REJECTED")
                
                # Try next candidates
                print(f"  🔄 Trying next candidates...")
                
                for next_candidate in all_candidates[1:4]:  # Try up to 3 more
                    if next_candidate['promise_score'] < 3.5:
                        continue
                    
                    print(f"\n🎯 Trying: {next_candidate['domain']} (promise: {next_candidate['promise_score']}/10)")
                    
                    next_pub = get_or_research_publication(next_candidate['domain'], session_id)
                    if next_pub:
                        next_score = next_pub.get('credibility_score', 0)
                        
                        print(f"  📊 Candidate credibility: {next_score}/10")
                        
                        # Simple rule: equal or better
                        if next_score >= main_score:
                            print(f"  ✅ Accepted: {next_score} >= {main_score}")
                            return {
                                'article': {
                                    'title': next_candidate['result'].get('title', 'Unknown'),
                                    'url': next_candidate['result'].get('url', ''),
                                    'snippet': next_candidate['result'].get('content', '')[:200]
                                },
                                'publication': next_pub
                            }
                        else:
                            print(f"  ❌ Rejected: {next_score} < {main_score}")
                
                print(f"  ⚠️ No evidence sources with equal/better credibility found")
                return None
        
        return None
        
    except Exception as e:
        print(f"❌ Evidence search failed: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/analyze-stream', methods=['POST'])
def analyze_stream():
    """Stream analysis progress to frontend"""
    data = request.json
    url = data.get('url', '')
    title = data.get('title', '')
    session_id = data.get('session_id', 'default')
    
    # Create progress queue for this session
    progress_queues[session_id] = queue.Queue()
    
    def generate():
        try:
            # Run analysis in background thread
            result = {'data': None, 'error': None}
            
            def analyze_background():
                try:
                    result['data'] = analyze_with_progress(url, title, session_id)
                except Exception as e:
                    result['error'] = str(e)
                    import traceback
                    traceback.print_exc()
            
            thread = threading.Thread(target=analyze_background)
            thread.start()
            
            # Stream progress updates
            while thread.is_alive() or not progress_queues[session_id].empty():
                try:
                    progress = progress_queues[session_id].get(timeout=0.1)
                    yield f"data: {progress}\n\n"
                except queue.Empty:
                    continue
            
            thread.join()
            
            # Send final result
            if result['error']:
                yield f"data: {json.dumps({'error': result['error']})}\n\n"
            else:
                yield f"data: {json.dumps({'complete': True, 'result': result['data']})}\n\n"
            
        finally:
            # Cleanup
            if session_id in progress_queues:
                del progress_queues[session_id]
    
    return Response(generate(), mimetype='text/event-stream')

def analyze_with_progress(url, title, session_id):
    """Analyze article with progress updates and multi-dimensional scoring"""
    article_content = ""
    domain = extract_domain(url)
    
    if not domain:
        raise ValueError('Invalid URL')
    
    # 1. Analyze main publication
    send_progress(session_id, f"🔍 Researching {domain}")
    main_publication = get_or_research_publication(domain, session_id)
    
    # 2. Extract and verify claims
    send_progress(session_id, "🔬 Analyzing health claims")
    claims = claim_verifier.extract_claims(title, article_content)
    claims_analysis = []
    
    for claim in claims[:2]:  # Limit to 2 claims to stay under API budget
        claim_data = claim_verifier.verify_claim(claim.get('claim', ''), claim.get('type', 'efficacy'))
        claims_analysis.append(claim_data)
        send_progress(session_id, "🔬 Analyzing health claims", f"→ Verified: {claim.get('claim', '')[:40]}...")
    
    # 3. Claim classification
    send_progress(session_id, "💰 Analyzing funding conflicts")
    claim_classification = claim_analyzer.analyze_claim(title, article_content, main_publication)
    
    classification_name = claim_classification['classification'].replace('_', ' ').title()
    send_progress(session_id, "💰 Analyzing funding conflicts", f"→ Classification: {classification_name}")
    
    # Check for conflicts
    if claim_classification.get('red_flags'):
        conflict_count = len(claim_classification['red_flags'])
        send_progress(session_id, "💰 Analyzing funding conflicts", f"→ {conflict_count} potential conflict(s) detected")
    else:
        send_progress(session_id, "💰 Analyzing funding conflicts", "→ No major conflicts detected")
    
    # 4. Detect myths
    detected_myths = []
    title_lower = title.lower()
    for myth in MYTHS:
        for keyword in myth['keywords']:
            if keyword.lower() in title_lower:
                detected_myths.append(myth)
                break
    
    # 5. Detect debate status
    send_progress(session_id, "🔄 Detecting debate status")
    debate_analysis = claim_verifier.detect_debate(claims_analysis)
    send_progress(session_id, "🔄 Detecting debate status", f"→ {debate_analysis['debate_status']}")
    
    # 6. Calculate three-dimensional scores (funding + quality) and research support pattern
    send_progress(session_id, "📊 Analyzing credibility dimensions")
    funding_score = calculate_funding_independence_score(main_publication)
    quality_score = calculate_source_quality_score(main_publication)
    research_pattern = analyze_research_support_pattern(claims_analysis)
    
    send_progress(session_id, "📊 Analyzing credibility dimensions", 
                  f"→ Funding: {funding_score:.1f}/10 | Quality: {quality_score:.1f}/10 | Research: {research_pattern['pattern']}")
    
    # 7. Evidence search
    evidence = find_adaptive_evidence(
        title, domain, main_publication, claim_classification, article_content, session_id
    )
    
    # Add three-dimensional scores to evidence source if found
    if evidence and evidence.get('publication'):
        evidence_pub = evidence['publication']
        evidence_funding_score = calculate_funding_independence_score(evidence_pub)
        evidence_accuracy_score = calculate_claim_accuracy_score(claims_analysis)  # Same claims, different source
        evidence_quality_score = calculate_source_quality_score(evidence_pub)
        
        evidence['multi_dimensional_scores'] = {
            'funding_independence_score': evidence_funding_score,
            'claim_accuracy_score': evidence_accuracy_score,
            'source_quality_score': evidence_quality_score
        }
    
    # 8. Generate nuanced recommendation
    # Calculate an accuracy score for the recommendation function (backwards compat)
    accuracy_score = calculate_claim_accuracy_score(claims_analysis)
    recommendation = calculate_nuanced_recommendation(
        funding_score, accuracy_score, quality_score, debate_analysis['debate_status']
    )
    
    # 9. Generate analysis
    send_progress(session_id, "✅ Analysis ready!")
    analysis = generate_analysis(main_publication, evidence, claim_classification)
    
    return {
        'main_publication': main_publication,
        'claim_classification': claim_classification,
        'myths': detected_myths,
        'evidence': evidence,
        'analysis': analysis,
        'missing_context': generate_missing_context(main_publication, evidence, claim_classification),
        'multi_dimensional_analysis': {
            'funding_independence_score': funding_score,
            'research_support_pattern': research_pattern,
            'source_quality_score': quality_score,
            'debate_status': debate_analysis['debate_status'],
            'debate_description': debate_analysis['description'],
            'claims': claims_analysis,
            'recommendation': recommendation
        }
    }

@app.route('/analyze', methods=['POST'])
def analyze():
    """Original non-streaming endpoint for backwards compatibility"""
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
    
    # 2. Extract and verify claims
    print("\n🔬 Step 2: Extracting and verifying health claims...")
    claims = claim_verifier.extract_claims(title, article_content)
    claims_analysis = []
    
    for claim in claims[:2]:  # Limit to 2 claims
        claim_data = claim_verifier.verify_claim(claim.get('claim', ''), claim.get('type', 'efficacy'))
        claims_analysis.append(claim_data)
        print(f"  ✓ Verified: {claim.get('claim', '')[:50]}...")
    
    # 3. FUNDING-AWARE CLAIM CLASSIFICATION
    print("\n🔍 Step 3: Funding-aware claim classification...")
    claim_classification = claim_analyzer.analyze_claim(title, article_content, main_publication)
    
    # 4. Detect myths
    print("\n🔍 Step 4: Checking for common health myths...")
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
    
    # 5. Detect debate status
    print("\n🔄 Step 5: Detecting debate status...")
    debate_analysis = claim_verifier.detect_debate(claims_analysis)
    print(f"  → {debate_analysis['debate_status']}: {debate_analysis['description'][:60]}...")
    
    # 6. Calculate three-dimensional scores and research support pattern
    print("\n📊 Step 6: Analyzing credibility dimensions...")
    funding_score = calculate_funding_independence_score(main_publication)
    quality_score = calculate_source_quality_score(main_publication)
    research_pattern = analyze_research_support_pattern(claims_analysis)
    print(f"  → Funding Independence: {funding_score:.1f}/10")
    print(f"  → Research Support: {research_pattern['pattern']}")
    print(f"  → Source Quality: {quality_score:.1f}/10")
    
    # 7. ADAPTIVE EVIDENCE SEARCH
    print("\n🔄 Step 7: Adaptive evidence search (seeking independent sources)...")
    evidence = find_adaptive_evidence(
        title,
        domain,
        main_publication,
        claim_classification,
        article_content
    )
    
    # Add three-dimensional scores to evidence source if found
    if evidence and evidence.get('publication'):
        evidence_pub = evidence['publication']
        evidence_funding_score = calculate_funding_independence_score(evidence_pub)
        evidence_research_pattern = analyze_research_support_pattern(claims_analysis)  # Same claims, different source
        evidence_quality_score = calculate_source_quality_score(evidence_pub)
        
        evidence['multi_dimensional_scores'] = {
            'funding_independence_score': evidence_funding_score,
            'research_support_pattern': evidence_research_pattern,
            'source_quality_score': evidence_quality_score
        }
        
        print(f"\n  Evidence Source Analysis:")
        print(f"    → Funding Independence: {evidence_funding_score:.1f}/10")
        print(f"    → Research Support: {evidence_research_pattern['pattern']}")
        print(f"    → Source Quality: {evidence_quality_score:.1f}/10")
    
    # 8. Generate nuanced recommendation
    accuracy_score = calculate_claim_accuracy_score(claims_analysis)  # For recommendation function
    recommendation = calculate_nuanced_recommendation(
        funding_score, accuracy_score, quality_score, debate_analysis['debate_status']
    )
    
    # 9. Generate analysis
    print("\n📊 Step 9: Generating comparative analysis...")
    analysis = generate_analysis(main_publication, evidence, claim_classification)
    
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE")
    print(f"  Classification: {claim_classification['classification']}")
    print(f"  Funding Independence: {funding_score:.1f}/10")
    print(f"  Research Support: {research_pattern['pattern']}")
    print(f"  Source Quality: {quality_score:.1f}/10")
    print(f"  Debate Status: {debate_analysis['debate_status']}")
    if evidence:
        evidence_name = evidence['publication'].get('name', 'Unknown')
        print(f"  Evidence source: {evidence_name}")
    else:
        print(f"  Evidence source: Not found")
    print(f"{'='*60}\n")
    
    return jsonify({
        'main_publication': main_publication,
        'claim_classification': claim_classification,
        'myths': detected_myths,
        'evidence': evidence,
        'analysis': analysis,
        'missing_context': generate_missing_context(main_publication, evidence, claim_classification),
        'multi_dimensional_analysis': {
            'funding_independence_score': funding_score,
            'research_support_pattern': research_pattern,
            'source_quality_score': quality_score,
            'debate_status': debate_analysis['debate_status'],
            'debate_description': debate_analysis['description'],
            'claims': claims_analysis,
            'recommendation': recommendation
        }
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
    
    # NEW: Always provide something useful even if no red flags
    if len(context) == 0:
        classification = claim_classification.get('classification')
        
        if classification == 'ACTIVE_RESEARCH':
            context.append("Active area of research - findings may evolve")
            context.append("Consider checking for recent peer-reviewed studies")
        elif classification == 'ESTABLISHED_FACT_VERIFIED':
            context.append("Well-established scientific consensus")
            context.append("Multiple independent sources confirm this information")
        elif classification in ['MANUFACTURED_CONSENSUS', 'INDUSTRY_NARRATIVE']:
            context.append("Industry influence detected - seek independent sources")
            context.append("Follow the money - check who funded this research")
        elif classification == 'CONTESTED_SCIENCE':
            context.append("Scientific debate ongoing - examine evidence from both sides")
            context.append("Look for funding sources behind competing claims")
        elif classification == 'FRINGE':
            context.append("Claims lack mainstream scientific support")
            context.append("Verify with established medical sources")
        else:
            context.append("Consider checking original research")
            context.append("Look for independent verification")
    
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
