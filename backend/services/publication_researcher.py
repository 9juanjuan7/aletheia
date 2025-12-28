import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup

load_dotenv()

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

class PublicationResearcher:
    
    def research(self, domain):
        """Hybrid: Web search + AI analysis"""
        print(f"🔍 Step 1: Searching web for {domain}...")
        search_results = self.web_search(domain)
        
        print(f"📄 Step 2: Scraping about page...")
        about_text = self.scrape_about_page(domain)
        
        print(f"🤖 Step 3: AI analyzing data...")
        structured_data = self.analyze_with_ai(domain, search_results, about_text)
        
        print(f"✅ AI analysis complete!")
        return structured_data
    
    def web_search(self, domain):
        """Search the web for publication information"""
        queries = [
            f"{domain} ownership parent company corporate owner",
            f"{domain} funding sponsors pharmaceutical advertising revenue",
            f"{domain} conflicts of interest industry ties",
            f"{domain} primary sources citations studies research links",
            f"{domain} retractions corrections fact-checks credibility",
            f"{domain} editorial process peer review medical credentials"
        ]
        
        all_results = []
        for query in queries:
            try:
                response = tavily_client.search(
                    query=query,
                    max_results=3,
                    search_depth="basic"
                )
                
                for result in response.get('results', []):
                    all_results.append({
                        'title': result.get('title', ''),
                        'content': result.get('content', ''),
                        'url': result.get('url', '')
                    })
            except Exception as e:
                print(f"Search failed for '{query}': {e}")
        
        return all_results
    
    def scrape_about_page(self, domain):
        """Try to scrape the publication's about page"""
        urls_to_try = [
            f"https://{domain}/about",
            f"https://{domain}/about-us",
            f"https://www.{domain}/about",
            f"https://www.{domain}/company",
            f"https://www.{domain}/editorial-policy",
            f"https://www.{domain}/ethics-policy"
        ]
        
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; Aletheia/1.0)'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove scripts and styles
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text()
                    
                    # Clean up whitespace
                    lines = (line.strip() for line in text.splitlines())
                    text = ' '.join(line for line in lines if line)
                    
                    return text[:3000]  # Limit to 3000 chars
            except:
                continue
        
        return "About page not accessible"
    
    def analyze_with_ai(self, domain, search_results, about_text):
        """Use AI to extract structured medical publication data - FUNDING-FIRST approach"""
        
        # Format search results for AI
        search_summary = "\n\n".join([
            f"Source: {r['title']}\n{r['content'][:500]}"
            for r in search_results[:8]
        ])
        
        prompt = f"""
Analyze this health/medical publication with EXTREME SKEPTICISM about credentials.

DOMAIN: {domain}

WEB SEARCH RESULTS:
{search_summary}

ABOUT PAGE TEXT:
{about_text[:2000]}

Return ONLY valid JSON with this exact structure:

{{
  "name": "Publication name",
  "domain": "{domain}",
  
  "credibility_score": 5.0,
  "primary_source_links": true,
  "funding_transparency": "high",
  
  "ownership": "Parent company name",
  "funding_sources": ["Advertising", "Pharmaceutical sponsorship"],
  "conflicts_of_interest": ["Owned by pharma company X"],
  "industry_ties": ["Food industry", "Supplement industry"],
  
  "author_credentials": "Staff writers, some MD review",
  "peer_reviewed": false,
  "editorial_standards": "Basic fact-checking",
  
  "retraction_history": 0,
  "fact_check_rating": "Mixed",
  
  "red_flags": ["Pharma-funded", "No source links"],
  "green_flags": ["Discloses funding", "Links to studies"],
  
  "expertise_areas": ["health", "nutrition"],
  "last_updated": "2025-12-27"
}}

CREDIBILITY SCORING SYSTEM (0-10) - FUNDING MATTERS MORE THAN CREDENTIALS:

START AT 5/10 (NEUTRAL), THEN ADJUST:

PRIMARY SOURCE VERIFICATION (Most Critical):
  +2.0 points: Consistently links to peer-reviewed studies with DOIs
  +1.0 points: Sometimes links to sources
  -2.0 points: Rarely or never links to original research
  -3.0 points: Makes claims without any citations

FUNDING & CONFLICTS (Most Critical):
  +2.0 points: Independent/nonprofit, no corporate ties
  +1.5 points: Subscription-based, no advertising
  +0.5 points: Advertising but discloses all sponsors
  -1.0 points: Heavy advertising, limited disclosure
  -2.0 points: Pharmaceutical/supplement company sponsorship
  -3.0 points: Owned by industry they cover (e.g., pharma-owned health site)
  -4.0 points: Hidden conflicts, undisclosed financial ties

TRACK RECORD:
  +1.0 points: Zero retractions, strong fact-check history
  -2.0 points: History of retractions or corrections
  -3.0 points: Multiple fact-checker warnings

TRANSPARENCY:
  +1.0 points: Full disclosure of funding, conflicts, methodology
  -1.0 points: Vague or missing disclosures

CREDENTIALS (Minor Weight - Can Be Bought):
  +1.0 points: Peer-reviewed medical journal
  +0.5 points: Medical credentials (MD/PhD) AND independent funding
  +0.0 points: Medical credentials BUT corporate-funded (credentials don't matter if bought)
  -0.5 points: No medical expertise for medical topics

EXAMPLES OF SCORING:

Score 9-10 (Highly Credible):
- Independent nonprofit medical journal
- Peer-reviewed publication
- Always links to primary sources
- Zero industry funding
- Example: New England Journal of Medicine (independent articles)

Score 7-8 (Credible):
- Established medical site with MD review
- Regularly links to studies
- Subscription or mixed funding model
- Minimal conflicts disclosed
- Example: Mayo Clinic, Cleveland Clinic

Score 5-6 (Moderate):
- General health site
- Some source links
- Ad-supported but transparent
- Some medical oversight
- Example: Healthline (if disclosing sponsors)

Score 3-4 (Low Credibility):
- Pharma/supplement sponsored
- Rarely links to sources
- Conflicts not disclosed
- Clickbait headlines
- PhDs/MDs who are industry-paid

Score 1-2 (Very Low):
- Owned by company they cover
- No citations or sources
- History of misinformation
- Hidden industry funding

Score 0 (Not Credible):
- Known misinformation source
- Multiple retractions/corrections
- Proven false claims
- Industry propaganda site

FIELD DEFINITIONS:

CRITICAL FIELDS (Prioritized):
- credibility_score: 0-10 based on formula above (FUNDING > CREDENTIALS)
- primary_source_links: true/false - Does site link to original research?
- funding_transparency: "high" / "medium" / "low" / "none"

FUNDING & CONFLICTS (Critical):
- ownership: Ultimate parent company (trace full corporate ownership)
- funding_sources: Array - ["Advertising", "Pharma sponsorship", "Grants from X", "Subscription"]
- conflicts_of_interest: Array - Specific conflicts ["Owned by Pfizer", "Board member works for Coca-Cola"]
- industry_ties: Array - Which industries they have relationships with

CREDENTIALS (Lower Priority):
- author_credentials: Typical qualifications (note: means little if funded by industry)
- peer_reviewed: true only if actual peer-reviewed journal
- editorial_standards: Description of review process

TRACK RECORD:
- retraction_history: Number of retracted articles (0 if none/unknown)
- fact_check_rating: "Strong" / "Mixed" / "Poor" / "Unknown"

RED & GREEN FLAGS:
- red_flags: Array of concerning patterns ["No source citations", "Pharma-funded", "Undisclosed conflicts"]
- green_flags: Array of positive patterns ["Links to studies", "Independent funding", "Full transparency"]

CRITICAL RULES:
1. A PhD funded by Pfizer writing about vaccines = LOW credibility
2. Independent journalist linking to 5 studies = HIGH credibility
3. Funding sources are THE #1 credibility factor
4. Credentials mean NOTHING without funding independence
5. Extract ONLY verifiable facts from sources
6. If info not found: "Unknown" for strings, [] for arrays, false for booleans, 5.0 for credibility
7. BE SKEPTICAL - assume conflicts exist unless proven otherwise
8. Return ONLY the JSON object
"""
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a critical analyst of medical publications. Your job is to expose funding conflicts and industry bias. Credentials (MD/PhD) mean NOTHING if the person is funded by corporations. Prioritize funding transparency and source citations over impressive titles. Be skeptical of industry-funded 'experts'."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Ensure required fields
            result['domain'] = domain
            result['research_sources'] = [r['url'] for r in search_results[:3]]
            result['last_updated'] = "2025-12-27"
            
            # Calculate credibility explanation
            result['credibility_explanation'] = self.generate_credibility_explanation(result)
            
            return result
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return self.fallback_response(domain)
    
    def generate_credibility_explanation(self, data):
        """Generate human-readable explanation of credibility score"""
        score = data.get('credibility_score', 5.0)
        red_flags = data.get('red_flags', [])
        green_flags = data.get('green_flags', [])
        
        explanation = []
        
        if score >= 8:
            explanation.append("High credibility - strong editorial standards and independence")
        elif score >= 6:
            explanation.append("Moderate credibility - generally reliable with some concerns")
        elif score >= 4:
            explanation.append("Low credibility - significant conflicts or lack of sourcing")
        else:
            explanation.append("Very low credibility - major red flags present")
        
        if green_flags:
            explanation.append(f"Strengths: {', '.join(green_flags[:3])}")
        
        if red_flags:
            explanation.append(f"Concerns: {', '.join(red_flags[:3])}")
        
        return " | ".join(explanation)
    
    def fallback_response(self, domain):
        """Return minimal data if research fails"""
        return {
            "domain": domain,
            "name": domain,
            
            "credibility_score": 5.0,
            "primary_source_links": False,
            "funding_transparency": "unknown",
            
            "ownership": "Unknown",
            "funding_sources": [],
            "conflicts_of_interest": [],
            "industry_ties": [],
            
            "author_credentials": "Unknown",
            "peer_reviewed": False,
            "editorial_standards": "Unknown",
            
            "retraction_history": 0,
            "fact_check_rating": "Unknown",
            
            "red_flags": ["Unable to verify"],
            "green_flags": [],
            
            "expertise_areas": [],
            "last_updated": "2025-12-27",
            "research_sources": [],
            "credibility_explanation": "Unable to research - treat with caution"
        }
