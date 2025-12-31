"""
SearxNG Search Client for Aletheia

Replaces Tavily API with local SearxNG instance for unlimited free searches.
"""

import requests
from bs4 import BeautifulSoup
import os

SEARXNG_URL = os.getenv('SEARXNG_URL', 'http://localhost:8080')


def search(query: str, max_results: int = 5, search_depth: str = "basic") -> dict:
    """
    Search using SearxNG - compatible API with Tavily response format.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        search_depth: "basic" or "advanced" (ignored for SearxNG, kept for compatibility)
    
    Returns:
        {"results": [{"title": "...", "url": "...", "content": "..."}, ...]}
    """
    try:
        # Use HTML parsing (JSON format returns 403 on default SearxNG)
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params={"q": query},
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Parse SearxNG HTML results - try multiple selectors
        # Primary: article elements
        for result in soup.find_all('article', class_='result', limit=max_results * 2):
            title_elem = result.find('h3') or result.find('h4') or result.find('a', class_='url_header')
            url_elem = result.find('a', href=True)
            content_elem = result.find('p', class_='content') or result.find('p')
            
            if title_elem and url_elem:
                url = url_elem.get('href', '')
                # Skip internal SearxNG links
                if url and not url.startswith('/') and 'searxng' not in url.lower():
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "url": url,
                        "content": content_elem.get_text(strip=True) if content_elem else ""
                    })
        
        # Fallback: div.result elements
        if not results:
            for result in soup.find_all('div', class_='result', limit=max_results * 2):
                title_elem = result.find(['h3', 'h4', 'a'])
                url_elem = result.find('a', href=True)
                content_elem = result.find('p')
                
                if title_elem and url_elem:
                    url = url_elem.get('href', '')
                    if url and not url.startswith('/'):
                        results.append({
                            "title": title_elem.get_text(strip=True),
                            "url": url,
                            "content": content_elem.get_text(strip=True) if content_elem else ""
                        })
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in results:
            if r['url'] not in seen_urls:
                seen_urls.add(r['url'])
                unique_results.append(r)
        
        return {"results": unique_results[:max_results]}
        
    except requests.exceptions.ConnectionError:
        print(f"⚠️ SearxNG not available at {SEARXNG_URL}. Is Docker running?")
        return {"results": []}
    except requests.exceptions.Timeout:
        print(f"⚠️ SearxNG request timed out")
        return {"results": []}
    except Exception as e:
        print(f"⚠️ SearxNG search error: {e}")
        return {"results": []}


class SearxNGClient:
    """
    SearxNG client class - drop-in replacement for TavilyClient.
    Provides same interface for easier migration.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize SearxNG client.
        api_key is ignored (kept for compatibility with TavilyClient signature)
        """
        self.base_url = SEARXNG_URL
    
    def search(self, query: str, max_results: int = 5, search_depth: str = "basic") -> dict:
        """
        Search using SearxNG.
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            search_depth: Ignored (kept for Tavily compatibility)
        
        Returns:
            {"results": [{"title": "...", "url": "...", "content": "..."}, ...]}
        """
        return search(query, max_results, search_depth)
