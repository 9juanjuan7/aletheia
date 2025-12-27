import os
from openai import OpenAI
from tavily import TavilyClient
import requests
from bs4 import BeautifulSoup

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
        
        return structured_data
    
    def web_search(self, domain):
        """Search the web for ownership and funding info"""
        
        queries = [
            f"{domain} ownership parent company",
            f"{domain} funding revenue model advertising",
            f"{domain} about company information"
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
            f"https://www.{domain}/company"
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
        """Use AI to extract structured data - NO OPINIONS"""
        
        # Format search results for AI
        search_summary = "\n\n".join([
            f"Source: {r['title']}\n{r['content'][:500]}"
            for r in search_results[:5]
        ])
        
        prompt = f"""
Extract ONLY factual information about this publication. Do not make judgments.

DOMAIN: {domain}

WEB SEARCH RESULTS:
{search_summary}

ABOUT PAGE TEXT:
{about_text[:2000]}

Return ONLY valid JSON with FACTUAL data:

{{
  "name": "Publication name",
  "owner": "Parent company/owner (trace to ultimate corporate owner)",
  "funding_model": "Revenue source (advertising/subscription/nonprofit/grants)",
  "major_advertisers": ["List advertiser categories if found, otherwise empty"],
  "conflicts": ["List factual relationships only - e.g. 'Owned by pharmaceutical company X', 'Receives funding from Y foundation'"]
}}

CRITICAL RULES:
- Extract ONLY facts stated in the sources
- NO judgments about credibility, trustworthiness, or bias
- NO opinions about conflicts - just state the factual relationships
- If information not found, use "Unknown"
- List factual ties (ownership, funding) without characterizing them as good/bad
- Return ONLY the JSON object
"""
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a factual data extraction tool. Extract only verifiable facts from provided sources. Make no judgments or assessments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            result['domain'] = domain
            
            # Add metadata about sources
            result['sources'] = [r['url'] for r in search_results[:3]]
            
            return result
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return self.fallback_response(domain)
    
    def fallback_response(self, domain):
        """Return if research fails"""
        return {
            "domain": domain,
            "name": domain,
            "owner": "Research failed - unable to determine",
            "funding_model": "Unknown",
            "major_advertisers": [],
            "conflicts": [],
            "sources": []
        }
