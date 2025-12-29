import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

class PublicationResearcher:
    
    def research(self, domain):
        """Hybrid: Web search + AI analysis with enhanced academic funding research"""
        
        is_academic = '.edu' in domain or self.is_university_domain(domain)
        is_government = '.gov' in domain or self.is_government_domain(domain)
        
        print(f"🔍 Step 1: Searching web for {domain}...")
        search_results = self.web_search(domain, is_academic, is_government)
        
        print(f"📄 Step 2: Scraping about page...")
        about_text = self.scrape_about_page(domain)
        
        # Enhanced academic funding research
        if is_academic:
            print(f"🎓 Step 2.5: Deep academic funding search...")
            academic_funding = self.search_academic_funding(domain)
            search_results.extend(academic_funding)
            print(f"   Found {len(academic_funding)} additional funding sources")
        
        # Enhanced government agency research
        if is_government:
            print(f"🏛️ Step 2.5: Checking government agency industry ties...")
            gov_conflicts = self.search_government_conflicts(domain)
            search_results.extend(gov_conflicts)
            print(f"   Found {len(gov_conflicts)} potential conflict sources")
        
        print(f"🤖 Step 3: AI analyzing data...")
        structured_data = self.analyze_with_ai(domain, search_results, about_text, is_academic, is_government)
        
        print(f"✅ AI analysis complete!")
        return structured_data
    
    def is_university_domain(self, domain):
        """Check if domain is from a university/college"""
        university_indicators = [
            'university', 'college', 'edu', 'academic', 'institute', 
            'school', 'campus', 'ac.uk', 'edu.au'
        ]
        domain_lower = domain.lower()
        return any(indicator in domain_lower for indicator in university_indicators)
    
    def is_government_domain(self, domain):
        """Check if domain is from a government agency"""
        return '.gov' in domain or domain.lower() in [
            'nih.gov', 'cdc.gov', 'fda.gov', 'usda.gov', 'who.int'
        ]
    
    def web_search(self, domain, is_academic=False, is_government=False):
        """Search the web for publication information"""
        
        base_queries = [
            f"{domain} ownership parent company corporate owner",
            f"{domain} funding sponsors pharmaceutical advertising revenue",
            f"{domain} conflicts of interest industry ties",
            f"{domain} primary sources citations studies research links",
            f"{domain} retractions corrections fact-checks credibility",
            f"{domain} editorial process peer review medical credentials"
        ]
        
        # Add academic-specific queries
        if is_academic:
            base_queries.extend([
                f"{domain} corporate partnerships industry collaboration",
                f"{domain} research grants corporate donors",
                f"{domain} endowment funding sources disclosure"
            ])
        
        # Add government-specific queries
        if is_government:
            base_queries.extend([
                f"{domain} industry influence revolving door",
                f"{domain} pharmaceutical industry ties advisory board",
                f"{domain} corporate lobbying conflicts"
            ])
        
        all_results = []
        for query in base_queries:
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
    
    def search_academic_funding(self, domain):
        """Deep search for academic funding sources"""
        
        university_info = self.parse_academic_domain(domain)
        uni_name = university_info['university_name']
        department = university_info['department']
        
        print(f"   University: {uni_name}")
        if department:
            print(f"   Department: {department}")
        
        funding_queries = []
        
        if department:
            funding_queries.extend([
                f'"{uni_name}" "{department} department" corporate funding donors',
                f'"{uni_name}" "{department}" industry partnerships grants',
                f"{domain} research funding sources sponsors",
                f'"{uni_name}" "{department}" endowment corporate donors'
            ])
        
        funding_queries.extend([
            f'"{uni_name}" corporate donors research funding',
            f'"{uni_name}" industry partnerships sponsored research',
            f"{domain} funded by sponsored by grant from",
            f'"{uni_name}" foundation donors corporate contributors'
        ])
        
        all_results = []
        
        for query in funding_queries[:6]:
            try:
                response = tavily_client.search(
                    query=query,
                    max_results=2,
                    search_depth="basic"
                )
                
                for result in response.get('results', []):
                    all_results.append({
                        'title': result.get('title', '') + ' [FUNDING]',
                        'content': result.get('content', ''),
                        'url': result.get('url', '')
                    })
            except Exception as e:
                print(f"   Academic funding search failed: {e}")
                continue
        
        return all_results
    
    def search_government_conflicts(self, domain):
        """Search for government agency industry conflicts"""
        
        agency_name = self.parse_government_domain(domain)
        print(f"   Agency: {agency_name}")
        
        conflict_queries = [
            f'"{agency_name}" revolving door pharmaceutical industry',
            f'"{agency_name}" industry advisory board conflicts',
            f'"{agency_name}" corporate lobbying influence',
            f'"{agency_name}" industry capture regulatory',
            f"{domain} industry ties conflicts of interest"
        ]
        
        all_results = []
        
        for query in conflict_queries[:5]:
            try:
                response = tavily_client.search(
                    query=query,
                    max_results=2,
                    search_depth="basic"
                )
                
                for result in response.get('results', []):
                    all_results.append({
                        'title': result.get('title', '') + ' [GOV_CONFLICTS]',
                        'content': result.get('content', ''),
                        'url': result.get('url', '')
                    })
            except Exception as e:
                print(f"   Government conflict search failed: {e}")
                continue
        
        return all_results
    
    def parse_government_domain(self, domain):
        """Extract agency name from government domain"""
        agency_map = {
            'nih.gov': 'National Institutes of Health (NIH)',
            'cdc.gov': 'Centers for Disease Control (CDC)',
            'fda.gov': 'Food and Drug Administration (FDA)',
            'usda.gov': 'U.S. Department of Agriculture (USDA)',
            'who.int': 'World Health Organization (WHO)',
            'cancer.gov': 'National Cancer Institute',
            'hhs.gov': 'Department of Health and Human Services'
        }
        
        for key, value in agency_map.items():
            if key in domain:
                return value
        
        return domain
    
    def parse_academic_domain(self, domain):
        """Extract university name and department from academic domain"""
        
        clean_domain = domain.replace('www.', '')
        parts = clean_domain.split('.')
        
        department = None
        university_part = None
        
        if len(parts) >= 3:
            potential_dept = parts[0]
            university_part = parts[1]
            
            dept_indicators = ['med', 'econ', 'bio', 'chem', 'psych', 'eng', 
                             'business', 'law', 'health', 'nursing', 'pharmacy']
            if any(indicator in potential_dept.lower() for indicator in dept_indicators):
                department = potential_dept
        else:
            university_part = parts[0]
        
        university_name_map = {
            'stanford': 'Stanford University',
            'harvard': 'Harvard University',
            'mit': 'Massachusetts Institute of Technology',
            'iastate': 'Iowa State University',
            'ucla': 'University of California Los Angeles',
            'berkeley': 'University of California Berkeley',
            'yale': 'Yale University',
            'princeton': 'Princeton University',
            'columbia': 'Columbia University',
            'upenn': 'University of Pennsylvania'
        }
        
        university_name = university_name_map.get(
            university_part.lower() if university_part else '', 
            f"{university_part.title()} University" if university_part else domain
        )
        
        return {
            'university_name': university_name,
            'department': department,
            'domain_parts': parts
        }
    
    def scrape_about_page(self, domain):
        """Try to scrape the publication's about page"""
        urls_to_try = [
            f"https://{domain}/about",
            f"https://{domain}/about-us",
            f"https://www.{domain}/about",
            f"https://www.{domain}/company",
            f"https://www.{domain}/editorial-policy",
            f"https://www.{domain}/ethics-policy",
            f"https://www.{domain}/funding",
            f"https://www.{domain}/donors"
        ]
        
        for url in urls_to_try:
            try:
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; Aletheia/1.0)'
                })
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    text = ' '.join(line for line in lines if line)
                    return text[:3000]
            except:
                continue
        
        return "About page not accessible"
    
    def analyze_with_ai(self, domain, search_results, about_text, is_academic=False, is_government=False):
        """Use AI to extract structured medical publication data - FUNDING-FIRST approach with GOVERNMENT SKEPTICISM"""
        
        search_summary = "\n\n".join([
            f"Source: {r['title']}\n{r['content'][:500]}"
            for r in search_results[:15]
        ])
        
        academic_instruction = ""
        government_instruction = ""
        
        if is_academic:
            university_info = self.parse_academic_domain(domain)
            academic_instruction = f"""

SPECIAL INSTRUCTION FOR ACADEMIC SOURCES:
This is an academic institution: {university_info['university_name']}
Department: {university_info['department'] or 'Not specified'}

CRITICAL: Academic ≠ Independent! Many universities receive massive corporate funding.

For academic sources, extract:
1. SPECIFIC CORPORATE DONORS if mentioned (e.g., "Pfizer funds cancer research", "Coca-Cola nutrition lab")
2. Industry partnerships and collaborations
3. Research grant sources (corporate vs government vs truly independent)
4. Endowment contributors if disclosed
5. Department-specific funding (which companies fund THIS department?)

Academic Funding Transparency Levels:
- "high": Specific corporate donors named with amounts
- "medium": General mentions of corporate support
- "low": Vague "private donors" or "corporate partnerships" without names
- "none": No funding information found

Academic Credibility Scoring:
START at 6.0 for .edu domains, then:

GOVERNMENT FUNDING (BE SKEPTICAL):
+1.0: Independent research grants (NSF basic science, non-health topics)
+0.5: NIH/CDC grants for basic research (can be influenced, but some independence)
+0.0: USDA nutrition research (heavily industry-captured)
-0.5: Industry-government partnerships
-1.0: Government agency writing guidelines that benefit industry

Note: Government funding ≠ independence. Check WHAT agency and WHAT topic.
- NIH cancer biology grant = somewhat independent (+0.5)
- USDA promoting dairy/meat = industry capture (0.0)
- FDA with pharma ties = captured (-0.5)

CORPORATE FUNDING:
- Corporate donors disclosed: -1.0 (influence) +0.5 (transparency) = -0.5 net
- "Corporate partners" unnamed: -2.0 (no transparency + influence)
- No funding info found: -1.5 (lack of transparency is suspicious)

TRUE INDEPENDENCE (rare):
+2.0: Independent nonprofit, no government/corporate ties, transparent funding
+1.5: Subscription-only, no ads or sponsors
+1.0: Crowdfunded with transparent disclosure

OTHER FACTORS:
- Department outside expertise (e.g., economics on medicine): -1.0
- Peer-reviewed journal: +1.0
- Full conflict disclosure: +1.0
- No conflict disclosure: -1.0

Funding Sources Examples:
- Good: ["Independent nonprofit - disclosed donors", "No corporate or government ties"]
- Moderate: ["NIH cancer research grant", "State university funding (no corporate ties found)"]
- Concerning: ["State funding", "Corporate donors (names not disclosed)", "USDA nutrition research"]
- Bad: ["Pharmaceutical company sponsorship", "Undisclosed funding"]
"""
        
        if is_government:
            agency_name = self.parse_government_domain(domain)
            government_instruction = f"""

SPECIAL INSTRUCTION FOR GOVERNMENT SOURCES:
This is a government agency: {agency_name}

CRITICAL: Government agencies CAN be captured by industry. Examples:
- USDA nutrition guidelines written by meat/dairy lobbyists
- FDA officials join pharma companies (revolving door)
- CDC with pharmaceutical industry ties
- Regulatory capture is REAL and common

Government Credibility Scoring:
START at 6.0 for .gov domains (slight trust), then:

CHECK FOR INDUSTRY CAPTURE:
-2.0: USDA nutrition/dietary guidelines (food industry writes them)
-1.5: FDA drug approvals during controversy (pharma revolving door)
-1.0: Agency officials with industry ties or revolving door employment
-1.0: Government-industry "partnerships" (usually industry-led)
-0.5: Advisory boards with corporate members
+0.5: Basic research publications (non-policy)
+1.0: Agency with strong independence record and no industry ties

SPECIFIC AGENCIES:
- USDA on nutrition: Start at 4.0 (heavily captured by food industry)
- FDA on pharma: Start at 5.0 (revolving door concerns)
- NIH basic research: Start at 7.0 (more independent)
- CDC on vaccines during controversy: Start at 5.0 (pharma ties)
- Cancer.gov basic info: Start at 7.0 (generally reliable)

Red Flags for Government:
- "Agency officials have industry ties/revolving door"
- "USDA dietary guidelines (food industry influence documented)"
- "Government-industry partnership (likely industry-led)"
- "Advisory board includes corporate representatives"
- "Policy/guideline that financially benefits specific industry"
- "Agency historically criticized for industry capture"

Green Flags for Government:
- "Basic research publication, not policy/guidelines"
- "No documented industry conflicts"
- "Strong independence record"
- "Transparent conflict disclosure"

Funding Sources for Government:
Instead of just "Federal government", be specific:
- ["Federal appropriations", "Some industry advisory board members (pharma)"]
- ["Government funding", "USDA (documented food industry lobbying influence)"]
- ["NIH research budget", "No direct industry funding found"]

Ownership Examples:
- "U.S. Department of Agriculture (documented food industry lobbying)"
- "Food and Drug Administration (pharma revolving door concerns)"
- "National Institutes of Health (generally independent for basic research)"
"""

        prompt = f"""
Analyze this health/medical publication with EXTREME SKEPTICISM about credentials AND government authority.

DOMAIN: {domain}

WEB SEARCH RESULTS:
{search_summary}

ABOUT PAGE TEXT:
{about_text[:2000]}

{academic_instruction}

{government_instruction}

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
    "last_updated": "2025-12-28"
}}

CREDIBILITY SCORING SYSTEM (0-10) - FUNDING MATTERS MORE THAN CREDENTIALS OR AUTHORITY:

FUNDING INDEPENDENCE HIERARCHY (Most to Least Trustworthy):

TIER 1 - HIGHLY INDEPENDENT (Score boost: +2.0):
- Independent nonprofit, transparent funding, no corporate/government ties
- Crowdfunded research with public donor disclosure
- Subscription-only publication, no ads, no sponsors
Examples: Truly independent research institutes

TIER 2 - MODERATELY INDEPENDENT (Score boost: +0.5 to +1.0):
- Basic science research grants (NSF, non-health topics)
- Academic research with full funding disclosure and no industry ties
- NIH basic research grants (not policy-related)
- Government basic research (not guidelines/policy)

TIER 3 - POTENTIALLY COMPROMISED (Score: Neutral 0.0 to -0.5):
- Government health agencies (NIH, CDC, FDA) - can have industry influence
- USDA (heavily industry-captured for nutrition/food)
- Academic institutions with undisclosed funding
- Mixed funding (government + some corporate)
- Government-industry "partnerships"

TIER 4 - INDUSTRY INFLUENCED (Score penalty: -1.0 to -2.0):
- Corporate donors named but presented as "independent"
- Government agency with documented industry ties
- USDA nutrition guidelines (food industry writes them)
- FDA during pharma controversies (revolving door)
- "Public-private partnerships" (usually industry-led)
- Vague "corporate sponsors" without names

TIER 5 - DIRECTLY COMPROMISED (Score penalty: -3.0 to -4.0):
- Owned by industry they cover
- Pharma/food/supplement company funding
- Undisclosed conflicts
- Hidden industry funding
- Revolving door documented

START SCORES:
- General sources: 5.0
- Academic (.edu): 6.0
- Government (.gov): 6.0 (but adjust heavily based on agency and capture evidence)
- Independent nonprofit: 7.0
- Commercial: 4.0

PRIMARY SOURCE VERIFICATION (Most Critical):
+2.0: Consistently links to peer-reviewed studies with DOIs
+1.0: Sometimes links to sources
-2.0: Rarely or never links to original research
-3.0: Makes claims without any citations

TRACK RECORD:
+1.0: Zero retractions, strong fact-check history
-2.0: History of retractions or corrections
-3.0: Multiple fact-checker warnings

TRANSPARENCY:
+1.0: Full disclosure of funding, conflicts, methodology
-1.0: Vague or missing disclosures

CREDENTIALS (Minor Weight):
+1.0: Peer-reviewed medical journal
+0.5: Medical credentials AND independent funding
+0.0: Medical credentials BUT corporate/captured-government funded
-0.5: No medical expertise for medical topics

CRITICAL RULES:
1. Government authority ≠ trustworthy (agencies can be captured)
2. USDA nutrition = food industry capture (start low)
3. FDA pharma = revolving door concerns (be skeptical)
4. Academic = often corporate-funded (check thoroughly)
5. A PhD funded by Pfizer = LOW credibility
6. Independent journalist linking to studies = HIGH credibility
7. Funding sources are THE #1 credibility factor
8. Extract ONLY verifiable facts from sources
9. Be EXPLICIT about lack of transparency
10. BE SKEPTICAL of authority - follow the money
11. Return ONLY the JSON object
"""
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a critical analyst of medical publications who is HIGHLY SKEPTICAL of both corporate AND government authority. Your job is to expose funding conflicts and industry bias wherever it exists - including in government agencies. 

Credentials (MD/PhD) mean NOTHING if funded by corporations. Government authority means NOTHING if the agency is captured by industry. The USDA is captured by food industry. The FDA has revolving door with pharma. Academic institutions take corporate money.

Prioritize funding transparency and source citations over impressive titles or government seals. Be skeptical of ALL authority - follow the money. For academic sources, dig deep into corporate funding. For government sources, check for industry capture, revolving doors, and lobbying influence."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            result['domain'] = domain
            result['research_sources'] = [r['url'] for r in search_results[:3]]
            result['last_updated'] = "2025-12-28"
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
            explanation.append("High credibility - strong independence and transparency")
        elif score >= 6:
            explanation.append("Moderate credibility - generally reliable with some concerns")
        elif score >= 4:
            explanation.append("Low credibility - significant conflicts or capture concerns")
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
            "last_updated": "2025-12-28",
            "research_sources": [],
            "credibility_explanation": "Unable to research - treat with caution"
        }
