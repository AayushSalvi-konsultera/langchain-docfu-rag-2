
# import requests
# from bs4 import BeautifulSoup
# import logging
# from typing import List, Dict
# from summarizer import summarizer
# import asyncio

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class Search:
#     def __init__(self):
#         self.session = requests.Session()
#         self.session.headers.update({
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
#             "Accept-Language": "en-US,en;q=0.5"
#         })

#     async def search_with_summaries(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
#         """Search and return results with summaries"""
#         try:
#             # Get search results
#             results = self.search(query, num_results)
            
#             # Add summaries to each result
#             summarized_results = []
#             for result in results:
#                 try:
#                     # Get page content
#                     content = self.get_page_content(result['link'])
#                     if not content:
#                         continue
                        
#                     # Generate summary
#                     summary = await summarizer.summarize_content(content, query)
                    
#                     # Add to results
#                     summarized_results.append({
#                         "title": result['title'],
#                         "link": result['link'],
#                         "snippet": result['snippet'],
#                         "summary": summary
#                     })
#                 except Exception as e:
#                     logger.warning(f"Failed to summarize {result['link']}: {e}")
#                     continue
                    
#             return summarized_results
            
#         except Exception as e:
#             logger.error(f"Search with summaries failed: {e}")
#             return []

#     def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
#         """Search DuckDuckGo without browser automation"""
#         try:
#             # Option 1: Direct HTML scraping
#             results = self._scrape_html_results(query, num_results)
            
#             # Option 2: Fallback to API if scraping fails
#             if not results:
#                 results = self._api_search(query, num_results)
            
#             return results[:num_results]
            
#         except Exception as e:
#             logger.error(f"Search failed: {e}")
#             return []

#     def _scrape_html_results(self, query: str, num_results: int) -> List[Dict[str, str]]:
#         """Scrape results from HTML version"""
#         try:
#             url = f"https://html.duckduckgo.com/html/?q={query}"
#             response = self.session.get(url, timeout=10)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.text, 'html.parser')
#             results = []
            
#             for result in soup.select('.result')[:num_results]:
#                 try:
#                     title = result.select_one('h2 a').text
#                     link = result.select_one('a.result__url')['href']
#                     snippet = result.select_one('.result__snippet').text
                    
#                     # Clean the link (DDG adds redirects)
#                     if link.startswith('//duckduckgo.com/l/?uddg='):
#                         link = link.split('uddg=')[1].split('&')[0]
#                         link = requests.utils.unquote(link)
                    
#                     results.append({
#                         "title": title,
#                         "link": link,
#                         "snippet": snippet
#                     })
#                 except Exception as e:
#                     logger.warning(f"Skipping result: {e}")
#                     continue
                    
#             return results
            
#         except Exception as e:
#             logger.warning(f"HTML scrape failed: {e}")
#             return []

#     def _api_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
#         """Use DDG's JSON API"""
#         try:
#             params = {
#                 "q": query,
#                 "format": "json",
#                 "no_html": 1,
#                 "no_redirect": 1,
#                 "t": "myapp"
#             }
#             response = self.session.get(
#                 "https://api.duckduckgo.com/",
#                 params=params,
#                 timeout=10
#             )
#             data = response.json()
            
#             return [{
#                 "title": r["Text"],
#                 "link": r["FirstURL"],
#                 "snippet": r.get("Result", "")
#             } for r in data.get("RelatedTopics", []) if "FirstURL" in r][:num_results]
            
#         except Exception as e:
#             logger.error(f"API search failed: {e}")
#             return []

#     def get_page_content(self, url: str) -> str:
#         """Get page content with proper headers"""
#         try:
#             response = self.session.get(url, timeout=10)
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Remove unwanted elements
#             for element in soup(['script', 'style', 'nav', 'footer']):
#                 element.decompose()
                
#             return soup.get_text(separator=' ', strip=True)
            
#         except Exception as e:
#             logger.error(f"Content fetch failed: {e}")
#             return ""

# # Usage
# async def main():
#     searcher = Search()
#     query = "what are the current news about RBI and also give me date"
#     results = await searcher.search_with_summaries(query, 3)
    
#     for i, result in enumerate(results, 3):
#         print(f"{i}. {result['title']}")
#         print(f"   Link: {result['link']}")
#         print(f"   Snippet: {result['snippet'][:100]}...")
#         print(f"   Summary: {result['summary']}\n")

# if __name__ == "__main__":
#     asyncio.run(main())


# search.py
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Searcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept-Language": "en-US,en;q=0.5"
        })

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """Search DuckDuckGo and return only titles and links"""
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
                    
                    # Clean the link (DDG adds redirects)
                    if link.startswith('//duckduckgo.com/l/?uddg='):
                        link = link.split('uddg=')[1].split('&')[0]
                        link = requests.utils.unquote(link)
                    
                    results.append({
                        "title": title,
                        "link": link
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
                "link": r["FirstURL"]
            } for r in data.get("RelatedTopics", []) if "FirstURL" in r][:num_results]
            
        except Exception as e:
            logger.error(f"API search failed: {e}")
            return []

# Usage
# if __name__ == "__main__":
#     searcher = Searcher()
#     results = searcher.search("what is EBITA", 10)
    
#     for i, result in enumerate(results, 1):
#         print(f"{i}. {result['title']}")
#         print(f"   {result['link']}\n")