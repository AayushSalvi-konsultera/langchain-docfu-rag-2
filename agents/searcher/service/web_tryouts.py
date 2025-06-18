import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Search:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept-Language": "en-US,en;q=0.5"
        })

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search DuckDuckGo without browser automation"""
        try:
            # Option 1: Direct HTML scraping
            results = self._scrape_html_results(query, num_results)
            
            # Option 2: Fallback to API if scraping fails
            if not results:
                results = self._api_search(query, num_results)
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _scrape_html_results(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Scrape results from HTML version"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for result in soup.select('.result')[:num_results]:
                try:
                    title = result.select_one('h2 a').text
                    link = result.select_one('a.result__url')['href']
                    snippet = result.select_one('.result__snippet').text
                    
                    # Clean the link (DDG adds redirects)
                    if link.startswith('//duckduckgo.com/l/?uddg='):
                        link = link.split('uddg=')[1].split('&')[0]
                        link = requests.utils.unquote(link)
                    
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet
                    })
                except Exception as e:
                    logger.warning(f"Skipping result: {e}")
                    continue
                    
            return results
            
        except Exception as e:
            logger.warning(f"HTML scrape failed: {e}")
            return []

    def _api_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Use DDG's JSON API"""
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "no_redirect": 1,
                "t": "myapp"
            }
            response = self.session.get(
                "https://api.duckduckgo.com/",
                params=params,
                timeout=10
            )
            data = response.json()
            
            return [{
                "title": r["Text"],
                "link": r["FirstURL"],
                "snippet": r.get("Result", "")
            } for r in data.get("RelatedTopics", []) if "FirstURL" in r][:num_results]
            
        except Exception as e:
            logger.error(f"API search failed: {e}")
            return []

    def get_page_content(self, url: str) -> str:
        """Get page content with proper headers"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
                
            return soup.get_text(separator=' ', strip=True)
            
        except Exception as e:
            logger.error(f"Content fetch failed: {e}")
            return ""

# Usage
if __name__ == "__main__":
    searcher = Search()
    results = searcher.search("what is EBITA", 10)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['link']}")

