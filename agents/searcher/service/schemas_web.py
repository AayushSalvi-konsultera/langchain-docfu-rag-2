from dataclasses import dataclass, asdict
from typing import Optional, List

@dataclass
class SearchResult:
    """Represents a single search result"""
    url: str
    title: str
    snippet: str
    rank:int 
    domain: str


@dataclass
class ScrapedContent:
    """Represents scraped content from a website"""
    url: str 
    title : str 
    content: str 
    status: str 
    error_message: Optional[str] = None 

@dataclass
class SummarizedResult:
    """Final Result with link and summary"""
    url: str 
    title: str 
    summary: str 
    key_points: List[str] 
    relevance_score: float
    rank: int
    domain: str

    
