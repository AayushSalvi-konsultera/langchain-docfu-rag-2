import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
import logging
from typing import List, Dict, Tuple, Optional
import re
import random
import json
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Search:
    def __init__(self) -> None:
        self.driver = None 
        self.session = None
        self.setup_session()
        # Don't setup driver immediately, only when needed
        
    def setup_session(self):
        """Setup requests session with rotating headers and proxy support"""
        self.session = requests.Session()
        
        # More realistic headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
        
        # Add timeout and retries
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def setup_driver_if_needed(self):
        """Setup Chrome driver only when needed"""
        if self.driver is not None:
            return True
            
        try:
            chrome_options = Options()
            
            # More comprehensive stealth options
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--window-size=1366,768")  # More common resolution
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            
            # Remove automation indicators
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Randomize user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(20)
            
            # Execute anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            logger.info("Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            self.driver = None
            return False

    def bing_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search using Bing (often more lenient than Google)
        """
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={num_results}"
            logger.info(f"Searching Bing for: {query}")
            
            # Add random delay
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parse Bing results
            result_divs = soup.find_all('li', class_='b_algo')
            
            for i, result_div in enumerate(result_divs[:num_results]):
                try:
                    title_element = result_div.find('h2')
                    if not title_element:
                        continue
                    
                    title_link = title_element.find('a')
                    if not title_link:
                        continue
                        
                    title = title_link.get_text(strip=True)
                    link = title_link.get('href')
                    
                    # Get snippet
                    snippet_element = result_div.find('p') or result_div.find('div', class_='b_caption')
                    snippet = snippet_element.get_text(strip=True) if snippet_element else "No description available"
                    
                    if not link or not self._is_valid_url(link):
                        continue

                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "rank": i + 1
                    })

                    logger.info(f"Extracted result {i+1}: {title}")

                except Exception as e:
                    logger.warning(f"Error extracting Bing result {i+1}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(results)} search results from Bing")
            return results

        except Exception as e:
            logger.error(f"Error performing Bing search: {e}")
            return []

    def searx_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search using SearXNG (open source search engine aggregator)
        """
        try:
            # List of public SearXNG instances
            searx_instances = [
                "https://searx.be",
                "https://search.bus-hit.me",
                "https://searx.tiekoetter.com",
                "https://search.sapti.me",
                "https://searx.work"
            ]
            
            for instance in searx_instances:
                try:
                    search_url = f"{instance}/search"
                    params = {
                        'q': query,
                        'format': 'json',
                        'categories': 'general'
                    }
                    
                    logger.info(f"Searching {instance} for: {query}")
                    
                    response = self.session.get(search_url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    results = []
                    
                    for i, result in enumerate(data.get('results', [])[:num_results]):
                        try:
                            title = result.get('title', '').strip()
                            link = result.get('url', '').strip()
                            snippet = result.get('content', '').strip() or "No description available"
                            
                            if not title or not link or not self._is_valid_url(link):
                                continue

                            results.append({
                                "title": title,
                                "link": link,
                                "snippet": snippet,
                                "rank": i + 1
                            })

                            logger.info(f"Extracted result {i+1}: {title}")

                        except Exception as e:
                            logger.warning(f"Error extracting SearX result {i+1}: {e}")
                            continue

                    if results:
                        logger.info(f"Successfully extracted {len(results)} search results from SearX")
                        return results
                        
                except Exception as e:
                    logger.warning(f"SearX instance {instance} failed: {e}")
                    continue
            
            logger.error("All SearX instances failed")
            return []

        except Exception as e:
            logger.error(f"Error performing SearX search: {e}")
            return []

    def duckduckgo_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Improved DuckDuckGo search with better parsing
        """
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&kl=us-en"
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            # Add more realistic headers for DDG
            headers = self.session.headers.copy()
            headers.update({
                'Referer': 'https://duckduckgo.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            })
            
            response = self.session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
            results = []
            
            # Multiple selectors for DDG results
            result_selectors = [
                'div.result',
                'div.web-result',
                '.result',
                '.web-result'
            ]
            
            result_divs = []
            for selector in result_selectors:
                result_divs = soup.select(selector)
                if result_divs:
                    break
            
            logger.info(f"Found {len(result_divs)} potential results with DuckDuckGo")
            
            for i, result_div in enumerate(result_divs[:num_results]):
                try:
                    # Try multiple title selectors
                    title_element = (
                        result_div.find('a', class_='result__a') or
                        result_div.find('h2', class_='result__title') or
                        result_div.find('a') or
                        result_div.find('h2')
                    )
                    
                    if not title_element:
                        continue
                        
                    title = title_element.get_text(strip=True)
                    link = title_element.get('href')
                    
                    if not title or not link:
                        continue
                    
                    # Get snippet with multiple approaches
                    snippet_element = (
                        result_div.find('a', class_='result__snippet') or
                        result_div.find('div', class_='result__snippet') or
                        result_div.find('span', class_='result__snippet') or
                        result_div.find('p')
                    )
                    
                    snippet = snippet_element.get_text(strip=True) if snippet_element else "No description available"
                    
                    if not self._is_valid_url(link):
                        continue

                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "rank": i + 1
                    })

                    logger.info(f"Extracted DDG result {i+1}: {title}")

                except Exception as e:
                    logger.warning(f"Error extracting DDG result {i+1}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(results)} search results from DuckDuckGo")
            return results

        except Exception as e:
            logger.error(f"Error performing DuckDuckGo search: {e}")
            return []

    def google_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Google search as last resort with Selenium
        """
        if not self.setup_driver_if_needed():
            logger.warning("WebDriver not available for Google search")
            return []
            
        try:
            time.sleep(random.uniform(2, 4))
            
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}&hl=en&gl=us"
            logger.info(f"Searching Google for: {query}")
            
            self.driver.get(search_url)
            
            # Wait and handle potential CAPTCHA or blocks
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.MjjYud, #search"))
                )
            except TimeoutException:
                logger.warning("Google search timed out or blocked")
                return []

            results = []
            selectors = ["div.MjjYud", "div.g", ".rc", "#search .g"]
            search_results = []
            
            for selector in selectors:
                search_results = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if search_results:
                    break
            
            if not search_results:
                logger.warning("No Google search results found")
                return []

            for i, result in enumerate(search_results[:num_results]):
                try:
                    title_element = None
                    for title_sel in ["h3", ".LC20lb", ".DKV0Md", "h3.LC20lb"]:
                        try:
                            title_element = result.find_element(By.CSS_SELECTOR, title_sel)
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not title_element:
                        continue
                        
                    title = title_element.text.strip()
                    if not title:
                        continue

                    link_element = result.find_element(By.CSS_SELECTOR, "a")
                    link = link_element.get_attribute("href")

                    snippet = "No description available"
                    for snippet_sel in [".VwiC3b", ".s3v9rd", ".st", "span.st"]:
                        try:
                            snippet_element = result.find_element(By.CSS_SELECTOR, snippet_sel)
                            snippet = snippet_element.text.strip()
                            break
                        except NoSuchElementException:
                            continue

                    if not link or not self._is_valid_url(link):
                        continue

                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "rank": i + 1
                    })

                    logger.info(f"Extracted Google result {i+1}: {title}")

                except Exception as e:
                    logger.warning(f"Error extracting Google result {i+1}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(results)} Google search results")
            return results

        except Exception as e:
            logger.error(f"Error performing Google search: {e}")
            return []

    def multi_engine_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Try multiple search engines in order of reliability
        """
        search_engines = [
            ("Bing", self.bing_search),
            ("SearX", self.searx_search),
            ("DuckDuckGo", self.duckduckgo_search),
            ("Google", self.google_search)
        ]
        
        for engine_name, search_func in search_engines:
            try:
                logger.info(f"Trying {engine_name} search...")
                results = search_func(query, num_results)
                
                if results:
                    logger.info(f"{engine_name} search successful with {len(results)} results")
                    return results
                else:
                    logger.warning(f"{engine_name} search returned no results")
                    
            except Exception as e:
                logger.error(f"{engine_name} search failed: {e}")
                continue
        
        logger.error("All search engines failed")
        return []

    def scrape_website_content(self, url: str, max_chars: int = 5000) -> str:
        """
        Enhanced website scraping with multiple fallback methods
        """
        try:
            logger.info(f"Scraping content from: {url}")
            
            # Method 1: Direct requests (fastest)
            try:
                time.sleep(random.uniform(0.5, 1.5))
                
                headers = self.session.headers.copy()
                headers.update({
                    'Referer': 'https://www.google.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                })
                
                response = self.session.get(url, headers=headers, timeout=15, allow_redirects=True)
                response.raise_for_status()
                
                # Handle different encodings
                if response.encoding is None:
                    response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.content, 'html.parser', from_encoding=response.encoding)
                
            except Exception as e:
                logger.warning(f"Direct requests failed for {url}: {e}")
                
                # Method 2: Selenium fallback
                if not self.setup_driver_if_needed():
                    return f"Error: Unable to scrape content - {str(e)}"
                
                try:
                    self.driver.get(url)
                    time.sleep(random.uniform(2, 4))
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                except Exception as selenium_e:
                    logger.error(f"Selenium also failed for {url}: {selenium_e}")
                    return f"Error scraping content: {str(e)}"
            
            # Enhanced content extraction
            for element in soup(["script", "style", "nav", "footer", "header", 
                               "aside", "iframe", "noscript", "meta", "link", "svg"]):
                element.decompose()
            
            # Try to find main content
            main_content = None
            content_selectors = [
                'main', 'article', '[role="main"]', '.main-content',
                '.content', '#content', '.post-content', '.entry-content',
                '.article-body', '.story-body', '.post', '.entry'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content and len(main_content.get_text(strip=True)) > 100:
                    break
            
            if not main_content:
                # Fallback to body or largest text container
                main_content = soup.find('body') or soup
            
            # Extract and clean text
            text = main_content.get_text(separator=' ', strip=True)
            
            # Advanced text cleaning
            text = re.sub(r'\s+', ' ', text)  # Multiple whitespace to single
            text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines
            text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)  # Remove special chars
            
            # Remove common noise
            noise_patterns = [
                r'Cookie.*?accept',
                r'Subscribe.*?newsletter',
                r'Share.*?social',
                r'Follow us on',
                r'Sign up.*?free'
            ]
            
            for pattern in noise_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
            # Limit length
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            logger.info(f"Successfully scraped {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return f"Error scraping content: {str(e)}"

    def _is_valid_url(self, url: str) -> bool:
        """Enhanced URL validation"""
        try:
            if not url or url.startswith(('#', 'javascript:', 'mailto:')):
                return False
                
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Skip problematic domains and file types
            skip_domains = [
                'google.com', 'youtube.com', 'facebook.com', 'twitter.com',
                'instagram.com', 'linkedin.com', 'pinterest.com', 'reddit.com'
            ]
            
            skip_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.rar', '.exe', '.dmg', '.mp3', '.mp4', '.avi'
            ]
            
            if any(domain in parsed.netloc.lower() for domain in skip_domains):
                return False
                
            if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
                return False
            
            return True
        except:
            return False

    def search_and_extract(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Main search and extraction with multi-engine support
        """
        try:
            # Use multi-engine search
            search_results = self.multi_engine_search(query, num_results)
            
            if not search_results:
                logger.warning("No search results found from any engine")
                return []
            
            # Extract content from results
            enhanced_results = []
            for result in search_results:
                try:
                    # Random delay between scraping
                    time.sleep(random.uniform(1, 2))
                    
                    content = self.scrape_website_content(result['link'])
                    
                    enhanced_result = {
                        "title": result['title'],
                        "link": result['link'],
                        "snippet": result['snippet'],
                        "content": content,
                        "rank": result['rank']
                    }
                    
                    enhanced_results.append(enhanced_result)
                    
                except Exception as e:
                    logger.error(f"Error processing result {result['link']}: {e}")
                    # Add result with snippet only
                    enhanced_result = {
                        "title": result['title'],
                        "link": result['link'],
                        "snippet": result['snippet'],
                        "content": result['snippet'],
                        "rank": result['rank']
                    }
                    enhanced_results.append(enhanced_result)
            
            logger.info(f"Successfully processed {len(enhanced_results)} results")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in search_and_extract: {e}")
            return []

    def __call__(self, user_q: str) -> Tuple[List[str], List[str]]:
        """
        Main callable method with better error handling
        """
        try:
            results = self.search_and_extract(user_q, num_results=7)
            
            links = []
            summaries = []
            
            for result in results:
                links.append(result['link'])
                
                # Create comprehensive summary
                summary = f"Title: {result['title']}\n"
                summary += f"Source: {urlparse(result['link']).netloc}\n"
                summary += f"Description: {result['snippet']}\n"
                
                # Add content preview if substantially longer than snippet
                if len(result['content']) > len(result['snippet']) + 100:
                    content_preview = result['content'][:500].strip()
                    if content_preview and content_preview != result['snippet']:
                        summary += f"Content Preview: {content_preview}..."
                
                summaries.append(summary)
            
            logger.info(f"Returning {len(links)} links and summaries")
            return links, summaries
            
        except Exception as e:
            logger.error(f"Error in __call__: {e}")
            return [], []

    def close(self):
        """Close all resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")
                
        if self.session:
            try:
                self.session.close()
                logger.info("Session closed")
            except Exception as e:
                logger.warning(f"Error closing session: {e}")

    def __del__(self):
        """Cleanup"""
        self.close()


# Enhanced usage example
if __name__ == "__main__":
    searcher = Search()
    try:
        query = "what is EBITDA"
        print(f"Searching for: '{query}'")
        print("=" * 60)
        
        links, summaries = searcher(query)
        
        if links:
            print(f"Found {len(links)} results:")
            for i, (link, summary) in enumerate(zip(links, summaries), 1):
                print(f"\n{'='*60}")
                print(f"Result {i}")
                print(f"{'='*60}")
                print(f"URL: {link}")
                print(f"Summary: {summary}")
        else:
            print("No results found. This might be due to:")
            print("1. Network restrictions")
            print("2. All search engines blocking requests")
            print("3. Firewall/proxy issues")
            print("4. Need for VPN or different IP")
            
    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
    except Exception as e:
        print(f"Error during search: {e}")
        logger.exception("Full error details:")
    finally:
        searcher.close()