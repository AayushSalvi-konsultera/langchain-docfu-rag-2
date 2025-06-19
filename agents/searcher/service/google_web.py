# search.py
import requests
import logging
from typing import List, Dict
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSearcher:
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        """
        Initialize with your Google Custom Search API credentials.
        You can get these from Google Cloud Console.
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept-Language": "en-US,en;q=0.5"
        })
        
        # Get credentials from environment variables if not provided
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not self.api_key or not self.search_engine_id:
            logger.error("Google API key and search engine ID must be provided")

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """Search using Google Custom Search API and return titles and links"""
        try:
            results = self._api_search(query, num_results)
            return results[:num_results]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _api_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """Use Google's Custom Search JSON API"""
        try:
            # Google API returns up to 10 results per request
            # For more than 10, we'd need to implement pagination
            items_per_request = min(num_results, 10)
            
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": items_per_request
            }
            
            response = self.session.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return [{
                "title": item["title"],
                "link": item["link"]
            } for item in data.get("items", [])]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return []
        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            return []
        except Exception as e:
            logger.error(f"API search failed: {e}")
            return []

# Usage
# if __name__ == "__main__":
#     # Initialize with your credentials or set them as environment variables
#     searcher = GoogleSearcher()
#     results = searcher.search("what is EBITA", 10)
    
#     for i, result in enumerate(results, 1):
#         print(f"{i}. {result['title']}")
#         print(f"   {result['link']}\n")