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
        is_pmc_paper = 'pmc.ncbi' in domain or 'pubmed' in domain.lower()
        
        print(f"🔍 Step 1: Searching web for {domain}...")
        search_results = self.web_search(domain, is_academic, is_government, is_pmc_paper)
        
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
        
        # Enhanced PMC paper funding research
        if is_pmc_paper:
            print(f"📄 Step 2.5: Extracting individual paper funding...")
            paper_funding = self.search_pmc_paper_funding(domain)
            search_results.extend(paper_funding)
            print(f"   Found {len(paper_funding)} paper funding sources")
        
        print(f"🤖 Step 3: AI analyzing data...")
        structured_data = self.analyze_with_ai(domain, search_results, about_text, is_academic, is_government, is_pmc_paper)
        
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
        """
        Check if domain is from a government agency
        
        YOUR VISION: PMC/PubMed are NOT government agencies - they're paper archives
        Each paper has different authors/funding - treat individually
        """
        # Exclude PMC/PubMed - they're paper repositories, not agencies
        if 'pmc.ncbi' in domain or 'pubmed' in domain.lower():
            return False
        
        return '.gov' in domain or domain.lower() in [
            'nih.gov', 'cdc.gov', 'fda.gov', 'usda.gov', 'who.int'
        ]
    
    def web_search(self, domain, is_academic=False, is_government=False, is_pmc_paper=False):
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
        
        # Add PMC paper-specific queries
        if is_pmc_paper:
            base_queries.extend([
                f"{domain} author funding disclosure",
                f"{domain} study funding source pharmaceutical",
                f"{domain} research grant sponsor"
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
    
    def search_pmc_paper_funding(self, domain):
        """
        Search for individual PMC paper's funding disclosure
        
        YOUR VISION: PMC is just a hosting platform - score the PAPER's funding, not the platform
        """
        
        print(f"   PMC Paper: Extracting individual paper funding")
        
        funding_queries = [
            f"site:{domain} funding disclosure",
            f"site:{domain} author conflicts of interest",
            f"site:{domain} grant support pharmaceutical",
            f"site:{domain} study sponsor industry funding"
        ]
        
        all_results = []
        
        for query in funding_queries[:4]:
            try:
                response = tavily_client.search(
                    query=query,
                    max_results=2,
                    search_depth="basic"
                )
                
                for result in response.get('results', []):
                    all_results.append({
                        'title': result.get('title', '') + ' [PAPER_FUNDING]',
                        'content': result.get('content', ''),
                        'url': result.get('url', '')
                    })
            except Exception as e:
                print(f"   PMC paper funding search failed: {e}")
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
            'hhs.gov': 'Department of Health and Human Services',
            'ncbi.nlm.nih.gov': 'National Center for Biotechnology Information (NCBI)'
        }
        
        for key, value in agency_map.items():
            if key in domain:
                return value
        
        return domain
    
    def parse_academic_domain(self, domain):
        """Extract university name and department from academic domain - ENHANCED"""
        
        clean_domain = domain.replace('www.', '')
        parts = clean_domain.split('.')
        
        # Enhanced university name detection
        university_name_map = {
            'harvard': 'Harvard University',
            'stanford': 'Stanford University',
            'mit': 'Massachusetts Institute of Technology',
            'iastate': 'Iowa State University',
            'ucla': 'University of California Los Angeles',
            'berkeley': 'University of California Berkeley',
            'yale': 'Yale University',
            'princeton': 'Princeton University',
            'columbia': 'Columbia University',
            'upenn': 'University of Pennsylvania',
            'cornell': 'Cornell University',
            'duke': 'Duke University',
            'northwestern': 'Northwestern University',
            'uchicago': 'University of Chicago',
            'hopkins': 'Johns Hopkins University'
        }
        
        # Special department/school mappings
        department_map = {
            'hsph': 'School of Public Health',
            'nutritionsource': 'Nutrition Source',
            'med': 'Medical School',
            'law': 'Law School',
            'business': 'Business School',
            'econ': 'Economics Department',
            'engineering': 'Engineering School',
            'nursing': 'Nursing School',
            'pharmacy': 'Pharmacy School'
        }
        
        # Check entire domain for university name first
        domain_lower = clean_domain.lower()
        detected_university = None
        
        for key, name in university_name_map.items():
            if key in domain_lower:
                detected_university = name
                break
        
        # Extract department/school
        department = None
        if len(parts) >= 3:
            subdomain = parts[0].lower()
            
            # Check if subdomain matches known department
            for dept_key, dept_name in department_map.items():
                if dept_key in subdomain:
                    department = dept_name
                    break
            
            # If not found in map, use subdomain as-is
            if not department and subdomain not in ['www', '']:
                department = subdomain.replace('-', ' ').replace('_', ' ').title()
        
        # Combine for special cases
        if detected_university == 'Harvard University' and 'hsph' in domain_lower:
            detected_university = 'Harvard School of Public Health'
        
        # Fallback to parsing from parts
        if not detected_university:
            university_part = parts[1] if len(parts) >= 2 else parts[0]
            detected_university = university_name_map.get(
                university_part.lower(),
                f"{university_part.title()} University"
            )
        
        return {
            'university_name': detected_university,
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
    
    def analyze_with_ai(self, domain, search_results, about_text, is_academic=False, is_government=False, is_pmc_paper=False):
        """Use AI to extract structured medical publication data - FUNDING-FIRST approach with GOVERNMENT SKEPTICISM"""
        
        search_summary = "\n\n".join([
            f"Source: {r['title']}\n{r['content'][:500]}"
            for r in search_results[:15]
        ])
        
        academic_instruction = ""
        government_instruction = ""
        pmc_instruction = ""
        
        if is_academic:
            university_info = self.parse_academic_domain(domain)
            academic_instruction = f"""

SPECIAL INSTRUCTION FOR ACADEMIC SOURCES:
This is an academic institution: {university_info['university_name']}
Department: {university_info['department'] or 'Not specified'}

CRITICAL: Academic ≠ Independent! Many universities receive massive corporate funding.

For academic sources, extract:
1. SPECIFIC CORPORATE DONORS if mentioned
2. Industry partnerships and collaborations
3. Research grant sources (corporate vs government vs truly independent)
4. Endowment contributors if disclosed
5. Department-specific funding

Academic Funding Transparency:
- "high": Specific corporate donors named with amounts
- "medium": General mentions of corporate support
- "low": Vague "private donors" without names
- "none": No funding information found

Academic Credibility Scoring:
START at 6.0 for .edu domains, then:

BASIC HEALTH FACTS EXCEPTION:
If article discusses basic uncontroversial health facts (vegetables good, water necessary, exercise healthy):
+0.5: Even funded sources can state basic facts
Do NOT flag as industry narrative unless promoting specific products/brands

GOVERNMENT FUNDING (BE SKEPTICAL):
+1.0: Independent research grants (NSF basic science)
+0.5: NIH/CDC grants for basic research
+0.0: USDA nutrition research (industry-captured)
-0.5: Industry-government partnerships
-1.0: Guidelines that benefit industry

CORPORATE FUNDING:
- Corporate donors disclosed: -0.5 net (transparency +0.5, influence -1.0)
- "Corporate partners" unnamed: -2.0
- No funding info: -1.5

TRUE INDEPENDENCE:
+2.0: Independent nonprofit, no government/corporate ties
+1.5: Subscription-only, no ads
+1.0: Crowdfunded, transparent

OTHER:
- Outside expertise: -1.0
- Peer-reviewed: +1.0
- Full disclosure: +1.0
"""
        
        if is_government:
            agency_name = self.parse_government_domain(domain)
            
            government_instruction = f"""

SPECIAL INSTRUCTION FOR GOVERNMENT SOURCES:
This is a government agency: {agency_name}

YOUR VISION: All government agencies start equal - adjust based on EVIDENCE FOUND, not prestige.

Government Credibility Scoring:
START at 6.0 for ALL .gov domains (no exceptions based on agency name)

Then adjust based on EVIDENCE FOUND IN SEARCH RESULTS:

SEARCH FOR CONFLICTS (extract from search results):
-2.0: Search results document industry lobbying/influence (e.g., "USDA influenced by meat industry")
-1.5: Search results document revolving door employment (e.g., "FDA official joined Pfizer")
-1.0: Search results show industry advisory board members
-1.0: Search results show "public-private partnerships" with industry
-0.5: Search results show industry funding/grants

SEARCH FOR INDEPENDENCE (extract from search results):
+1.0: Search results show strong conflict disclosure + no ties found
+0.5: Search results show independent funding only
+0.5: Content is basic research publication (less industry pressure)

CONTENT TYPE (analyze what type of content this is):
-1.0: Dietary/nutrition guidelines (high lobbying target, e.g., USDA food pyramid)
-0.5: Drug/product approvals (revolving door risk, e.g., FDA drug approval pages)
0.0: General health information
+0.5: Basic science research publication (less direct industry pressure)

RED FLAGS TO EXTRACT FROM SEARCH:
- "Agency influenced by [industry] lobby"
- "Official joined [pharma/food company]"
- "Advisory board includes [industry representatives]"
- "Partnership with [corporate entity]"
- "Funded by industry"
- "Guidelines that benefit [industry financially]"

GREEN FLAGS TO EXTRACT FROM SEARCH:
- "Strong conflict of interest policies"
- "Independent review board"
- "No industry funding found"
- "Transparent disclosure"
- "Basic research, not policy"

CRITICAL RULES:
1. DO NOT give higher scores based on agency reputation (NIH, Cancer.gov, etc.)
2. DO give higher scores based on EVIDENCE of independence in search results
3. DO give lower scores based on EVIDENCE of capture in search results
4. Content type matters: Guidelines (high risk) vs Basic research (lower risk)

Example scoring logic:
- NIH basic research + no conflicts found in searches = 6.0 + 0.5 (research) + 0.5 (independent) = 7.0
- USDA dietary guideline + meat lobby documented = 6.0 - 1.0 (guideline) - 2.0 (lobbying) = 3.0
- FDA general drug info + no specific conflicts = 6.0 + 0.0 (general info) = 6.0
- CDC vaccine page + pharma ties found = 6.0 - 0.5 (approval type) - 1.0 (pharma ties) = 4.5
"""
        
        if is_pmc_paper:
            pmc_instruction = f"""

🚨 CRITICAL INSTRUCTION FOR PMC/PUBMED PAPERS:

This is a PAPER hosted on PubMed Central - NOT a government source.
PMC is just a HOSTING PLATFORM. Each paper has different authors, institutions, and funders.

YOUR VISION: Score the PAPER's funding, NOT the platform.

DO NOT give automatic high scores because it's on PMC.
PMC hosts BOTH independent research AND pharma-funded studies.

SCORING INSTRUCTIONS FOR PMC PAPERS:

START at 5.0 (neutral - platform doesn't determine credibility)

Then adjust based on PAPER'S FUNDING (extract from search results):

PAPER FUNDING DISCLOSED AS INDEPENDENT:
+2.0: NIH grant, no industry ties disclosed
+1.5: University grant, no conflicts
+1.0: Government basic research grant

PAPER FUNDING DISCLOSED AS CORPORATE:
-2.0: Pharma company funded/sponsored
-1.5: Food industry grant
-1.0: Medical device company funding
-0.5: "Unrestricted grant" from industry

NO FUNDING DISCLOSURE FOUND:
-1.0: Lack of transparency is a red flag

PEER REVIEW (Minor adjustment):
+0.5: Peer-reviewed publication (quality control)

AUTHOR CONFLICTS:
-1.0: Authors have disclosed pharma ties
-1.5: Authors work for industry
-0.5: Authors on pharma advisory boards

CRITICAL: A PMC paper funded by Pfizer = 3.0-4.0/10 (pharma conflict)
A PMC paper with independent NIH grant = 7.0-7.5/10 (independent)

PMC is NEUTRAL INFRASTRUCTURE. The paper's funding is what matters.

Extract paper funding from search results tagged [PAPER_FUNDING].
If funding not found in search results, score 5.0 (neutral, cannot verify).
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

{pmc_instruction}

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

YOUR VISION: Everyone starts equal - adjust based on EVIDENCE, not prestige/reputation

START SCORES (baseline, not final):
- General sources: 5.0
- Academic (.edu): 6.0
- Government (.gov): 6.0 (ALL agencies start at 6.0 - NO EXCEPTIONS for "prestigious" agencies)
- PMC/PubMed PAPERS: 5.0 (NEUTRAL - adjust based on PAPER'S funding, not platform)
- Independent nonprofit: 7.0
- Commercial: 4.0

PRIMARY SOURCE VERIFICATION:
+2.0: Consistently links to peer-reviewed studies
+1.0: Sometimes links to sources
-2.0: Rarely links
-3.0: No citations

FUNDING INDEPENDENCE (based on EVIDENCE found):
+2.0: Independent nonprofit, no corporate/gov ties, transparent
+1.5: Subscription-only, no ads
+1.0: Crowdfunded, transparent
+0.5-1.0: Government basic research (not policy) + no conflicts found
0.0 to -0.5: Government agencies with some capture evidence
-1.0 to -2.0: Corporate donors or captured government
-3.0 to -4.0: Owned by industry or hidden conflicts

TRACK RECORD:
+1.0: Zero retractions
-2.0: History of retractions
-3.0: Multiple fact-checker warnings

TRANSPARENCY:
+1.0: Full disclosure
-1.0: Vague or missing disclosures

CREDENTIALS (minor weight):
+1.0: Peer-reviewed journal
+0.5: Medical credentials AND independent funding
0.0: Medical credentials BUT corporate-funded
-0.5: No expertise for medical topics

CRITICAL RULES FOR YOUR VISION:
1. Government authority ≠ trustworthy (agencies can be captured)
2. Don't give NIH/Cancer.gov automatic high scores based on reputation
3. DO give high scores if search results show independence + no conflicts
4. PMC/PubMed = paper hosting platform (score individual PAPER's funding, not platform)
5. USDA/FDA don't get automatic low scores - adjust based on what search results show
6. Academic = often corporate-funded (check evidence)
7. Follow the money from search results, not credentials or agency names
8. Basic health facts (vegetables good) can be stated by funded sources - don't over-flag
9. Content type matters: Guidelines (high lobbying risk) vs basic research (lower risk)
10. Extract specific evidence from search results - don't assume based on names
11. Return ONLY the JSON object
"""
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a critical analyst highly skeptical of both corporate AND government authority. Expose funding conflicts and industry bias wherever it exists - including government agencies.

YOUR VISION: Everyone starts equal. Adjust based on EVIDENCE FOUND, not prestige or reputation.

Credentials mean NOTHING if funded by corporations. Government authority means NOTHING if captured by industry. 

Do NOT give NIH automatic high scores because "NIH = prestigious". 
Do NOT give USDA automatic low scores because "USDA = bad reputation".

Instead:
- Start all .gov at 6.0
- Search results show independence? Increase score.
- Search results show capture? Decrease score.
- Follow the EVIDENCE, not the NAME.

PMC/PubMed are PAPER HOSTING PLATFORMS - not credible sources themselves. Score the INDIVIDUAL PAPER's funding, not the platform. A Pfizer-funded paper on PMC = LOW score. An independent NIH-funded paper on PMC = HIGH score (because of funding evidence, not because "NIH = good").

For basic uncontroversial health facts (vegetables are healthy, water is necessary), don't over-flag as industry narrative unless promoting specific products.

Prioritize funding transparency over credentials. Be skeptical of ALL authority - follow the money found in search results."""
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
