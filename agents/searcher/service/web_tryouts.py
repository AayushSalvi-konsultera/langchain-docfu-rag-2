from time import sleep
from bs4 import BeautifulSoup
from requests import get, Session
from urllib.parse import unquote, urlparse
from random import randint
from typing import Iterator, Union, List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchResult:
    def __init__(self, url: str, title: str, description: str):
        self.url = url
        self.title = title
        self.description = description

    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title}, description={self.description})"

    def to_dict(self) -> Dict[str, str]:
        return {
            "url": self.url,
            "title": self.title,
            "description": self.description
        }

class GoogleSearch:
    def __init__(self, 
                 session: Optional[Session] = None,
                 proxies: Optional[Dict[str, str]] = None,
                 timeout: int = 10,
                 max_retries: int = 3):
        """
        Enhanced Google Search API
        
        Args:
            session: Optional requests Session object
            proxies: Proxy configuration (e.g., {'http': 'http://proxy:port'})
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.session = session or Session()
        self.proxies = proxies
        self.timeout = timeout
        self.max_retries = max_retries
        self._configure_session()

    def _configure_session(self):
        """Configure the requests session with headers and cookies"""
        self.session.headers.update({
            "User-Agent": self._generate_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        # Bypass consent cookies
        self.session.cookies.update({
            'CONSENT': 'PENDING+' + str(randint(100, 999)),
            'SOCS': 'CAESEwgDEgk0ODAwMDAwMjIaAmVuIAEaBgiA_LSeBg'
        })

    def _generate_user_agent(self) -> str:
        """Generate a random modern user agent"""
        chrome_versions = [
            (90, 0, 4430),
            (91, 0, 4472),
            (92, 0, 4515),
            (93, 0, 4577),
            (94, 0, 4606),
            (95, 0, 4638),
            (96, 0, 4664),
            (97, 0, 4692),
            (98, 0, 4758),
            (99, 0, 4844),
            (100, 0, 4896),
            (101, 0, 4951),
            (102, 0, 5005),
            (103, 0, 5060),
            (104, 0, 5112),
            (105, 0, 5195),
            (106, 0, 5249),
            (107, 0, 5304),
            (108, 0, 5359),
            (109, 0, 5414),
            (110, 0, 5481),
            (111, 0, 5563),
            (112, 0, 5615),
            (113, 0, 5676),
            (114, 0, 5735),
            (115, 0, 5790),
            (116, 0, 5845),
            (117, 0, 5938),
            (118, 0, 5993),
            (119, 0, 6045),
            (120, 0, 6099),
            (121, 0, 6155),
            (122, 0, 6261),
            (123, 0, 6312)
        ]
        major, minor, build = chrome_versions[randint(0, len(chrome_versions)-1)]
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major}.{minor}.{build} Safari/537.36"

    def _make_request(self, term: str, num_results: int, lang: str, start: int, safe: str, region: str) -> str:
        """Make the Google search request with retries"""
        for attempt in range(self.max_retries + 1):
            try:
                resp = self.session.get(
                    url="https://www.google.com/search",
                    params={
                        "q": term,
                        "num": num_results + 2,  # Buffer to prevent pagination
                        "hl": lang,
                        "start": start,
                        "safe": safe,
                        "gl": region,
                    },
                    proxies=self.proxies,
                    timeout=self.timeout
                )
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                if attempt == self.max_retries:
                    raise
                sleep(2 ** attempt)  # Exponential backoff

    def _parse_results(self, html: str) -> List[Dict[str, str]]:
        """Parse Google search results page"""
        soup = BeautifulSoup(html, "html.parser")
        results = []
        
        # Multiple selectors to handle different Google layouts
        result_blocks = soup.find_all("div", class_=["ezO2md", "g", "tF2Cxc", "MjjYud"])
        
        for result in result_blocks:
            try:
                # Try multiple selector patterns for each component
                link_tag = (result.find("a", href=True) or 
                           result.find("div", class_="yuRUbf").find("a", href=True) if result.find("div", class_="yuRUbf") else None)
                
                title_tag = (result.find("h3") or 
                            result.find("div", class_="DKV0Md") or 
                            result.find("span", class_="CVA68e") or
                            result.find("div", role="heading"))
                
                desc_tag = (result.find("div", class_=["VwiC3b", "MUxGbd", "aCOpRe", "yDYNvb"]) or 
                           result.find("span", class_=["aCOpRe", "FrIlee"]) or
                           result.find("div", class_="lyLwlc"))
                
                if not all([link_tag, title_tag]):
                    continue
                
                # Extract and clean URL
                url = unquote(link_tag["href"].split("&")[0].replace("/url?q=", ""))
                if not url.startswith(("http://", "https://")):
                    continue
                
                # Filter out Google domains
                if any(d in urlparse(url).netloc for d in ["google.com", "youtube.com"]):
                    continue
                
                results.append({
                    "url": url,
                    "title": title_tag.get_text(),
                    "description": desc_tag.get_text() if desc_tag else ""
                })
                
            except Exception as e:
                logger.debug(f"Error parsing result: {str(e)}")
                continue
                
        return results

    def search(self, 
              term: str, 
              num_results: int = 10, 
              lang: str = "en",
              advanced: bool = False,
              safe: str = "active",
              region: str = "us",
              sleep_interval: float = 2.5,
              unique: bool = True) -> Iterator[Union[str, SearchResult]]:
        """
        Search Google with enhanced reliability
        
        Args:
            term: Search term
            num_results: Number of results to return
            lang: Language code
            advanced: Return SearchResult objects if True, else URLs
            safe: Safe search level ('active', 'off')
            region: Geographic region code
            sleep_interval: Delay between requests
            unique: Return only unique URLs
            
        Yields:
            SearchResult objects or URLs depending on 'advanced' parameter
        """
        start = 0
        fetched = 0
        seen_urls = set()
        
        while fetched < num_results:
            try:
                html = self._make_request(term, num_results - fetched, lang, start, safe, region)
                batch = self._parse_results(html)
                
                if not batch:
                    logger.info(f"No more results found after {fetched} items")
                    break
                
                for result in batch:
                    if unique and result["url"] in seen_urls:
                        continue
                        
                    seen_urls.add(result["url"])
                    fetched += 1
                    
                    if advanced:
                        yield SearchResult(**result)
                    else:
                        yield result["url"]
                    
                    if fetched >= num_results:
                        break
                
                start += len(batch)
                if sleep_interval > 0 and fetched < num_results:
                    sleep(sleep_interval)
                    
            except Exception as e:
                logger.error(f"Search failed: {str(e)}")
                break

    def search_with_content(self,
                          term: str,
                          num_results: int = 5,
                          max_content_length: int = 5000,
                          **kwargs) -> Iterator[Dict[str, str]]:
        """
        Enhanced search that also fetches page content
        
        Args:
            term: Search term
            num_results: Number of results to return
            max_content_length: Maximum content length to retrieve
            **kwargs: Additional arguments for search()
            
        Yields:
            Dictionaries with url, title, description, and content
        """
        for result in self.search(term, num_results, advanced=True, **kwargs):
            try:
                content = self._fetch_page_content(result.url, max_content_length)
                yield {
                    **result.to_dict(),
                    "content": content
                }
            except Exception as e:
                logger.warning(f"Failed to fetch content for {result.url}: {str(e)}")
                yield {
                    **result.to_dict(),
                    "content": ""
                }

    def _fetch_page_content(self, url: str, max_length: int) -> str:
        """Fetch and clean page content"""
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "iframe", "header"]):
                element.decompose()
            
            # Get clean text
            text = soup.get_text(separator=" ", strip=True)
            return text[:max_length]
            
        except Exception as e:
            logger.debug(f"Content fetch failed for {url}: {str(e)}")
            return ""

# Example usage
if __name__ == "__main__":
    searcher = GoogleSearch(timeout=15)
    
    # Basic search
    print("=== Basic Search ===")
    for i, url in enumerate(searcher.search("what is EBITA", num_results=3), 1):
        print(f"{i}. {url}")
    
    # Advanced search with content
    print("\n=== Advanced Search with Content ===")
    for result in searcher.search_with_content("what is EBITA", num_results=2):
        print(f"\nTitle: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Content Preview: {result['content'][:200]}...")