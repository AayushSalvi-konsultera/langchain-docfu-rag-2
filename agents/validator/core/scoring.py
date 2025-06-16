from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix


def cosine_sim(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts using TF-IDF"""
    if not text1 or not text2:
        return 0.0
    
    vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
    try:
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        tfidf_matrix = csr_matrix(tfidf_matrix)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except:
        return 0.0

def score_rag_response(
    rag_response: str, 
    query: str, 
    rag_confidence: Optional[float] = None,
    response_length_penalty: bool = True
) -> Dict:
    """Score RAG response based on multiple factors"""
    
    # Base score from RAG system confidence (if available)
    if rag_confidence is not None:
        base_score = rag_confidence
    else:
        # Default confidence based on response quality indicators
        base_score = 0.6
    
    # Content relevance to query
    relevance_score = cosine_sim(rag_response, query)
    
    # Response completeness (length and structure indicators)
    completeness_score = min(len(rag_response) / 500, 1.0)  # Normalize to 0-1
    
    # Check for uncertainty indicators
    uncertainty_phrases = [
        "i don't know", "not sure", "unclear", "might be", 
        "possibly", "perhaps", "i think", "seems like"
    ]
    uncertainty_penalty = sum(1 for phrase in uncertainty_phrases 
                             if phrase in rag_response.lower()) * 0.1
    
    # Combine scores
    final_score = (
        0.4 * base_score +           # RAG system confidence
        0.3 * relevance_score +      # Content relevance
        0.2 * completeness_score +   # Response completeness
        0.1 * (1.0 - min(uncertainty_penalty, 0.5))  # Certainty bonus
    )
    
    return {
        "score": min(final_score, 1.0),
        "base_confidence": base_score,
        "relevance": relevance_score,
        "completeness": completeness_score,
        "uncertainty_penalty": uncertainty_penalty
    }

def score_web_results(web_results: List[Dict], query: str) -> Dict:
    """Score web search results based on multiple factors"""
    
    if not web_results:
        return {"score": 0.0, "details": [], "best_result": None}
    
    result_scores = []
    
    for i, result in enumerate(web_results):
        # Extract result fields safely
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        url = result.get('url', '')
        published_date = result.get('published_date', '')
        
        # Content relevance
        title_relevance = cosine_sim(title, query)
        snippet_relevance = cosine_sim(snippet, query)
        content_relevance = 0.6 * title_relevance + 0.4 * snippet_relevance
        
        # Recency score (prefer recent content for time-sensitive queries)
        recency_score = calculate_recency_score(published_date)
        
        # Position penalty (earlier results typically more relevant)
        position_penalty = max(0.9 - (i * 0.1), 0.5)
        
        # Combine scores (redistributed weights without domain scoring)
        final_score = (
            0.6 * content_relevance +    # Content match (increased from 0.4)
            0.3 * recency_score +        # Freshness (increased from 0.2)
            0.1 * position_penalty       # Search ranking (same)
        )
        
        result_detail = {
            "index": i,
            "score": final_score,
            "content_relevance": content_relevance,
            "recency_score": recency_score,
            "url": url,
            "title": title
        }
        result_scores.append(result_detail)
    
    # Find best result
    best_result = max(result_scores, key=lambda x: x["score"])
    
    return {
        "score": best_result["score"],
        "details": result_scores,
        "best_result": best_result
    }

def calculate_recency_score(published_date: str) -> float:
    """Calculate recency score based on publication date"""
    if not published_date:
        return 0.5  # Neutral score for unknown dates
    
    try:
        # Try to parse date (adjust format as needed)
        pub_date = datetime.strptime(published_date, '%Y-%m-%d')
        days_old = (datetime.now() - pub_date).days
        
        # Scoring logic: newer is better, but not critical beyond 30 days
        if days_old <= 1:
            return 1.0
        elif days_old <= 7:
            return 0.9
        elif days_old <= 30:
            return 0.8
        elif days_old <= 90:
            return 0.7
        elif days_old <= 365:
            return 0.6
        else:
            return 0.5
    except:
        return 0.5

def summarize_web_results(web_results: List[Dict], top_n: int = 3) -> str:
    """Create a summary from top web results"""
    if not web_results:
        return "No web results available."
    
    summaries = []
    for i, result in enumerate(web_results[:top_n]):
        title = result.get('title', 'Unknown')
        snippet = result.get('snippet', '')
        url = result.get('url', '')
        
        summary = f"Source {i+1}: {title}\n{snippet}\n[{url}]\n"
        summaries.append(summary)
    
    return "\n".join(summaries)

def validate_responses(
    rag_response: str,
    web_results: List[Dict],
    query: str,
    rag_confidence: Optional[float] = None
) -> Dict:
    """
    Enhanced validation comparing RAG vs Web results
    
    Args:
        rag_response: Response from RAG system
        web_results: List of web search results
        query: Original user query
        rag_confidence: Optional confidence score from RAG system
    
    Returns:
        Dictionary with best_source, rag_score, web_score, and selected_answer
    """
    
    # Score both sources
    rag_analysis = score_rag_response(rag_response, query, rag_confidence)
    web_analysis = score_web_results(web_results, query)
    
    rag_score = rag_analysis["score"]
    best_web_score = web_analysis["score"]
    
    # Return in the exact format required by your API
    return {
        "best_source": "web" if best_web_score > rag_score else "rag",
        "rag_score": rag_score,
        "web_score": best_web_score,
        "selected_answer": (
            summarize_web_results(web_results) 
            if best_web_score > rag_score 
            else rag_response
        )
    }

def generate_recommendation(rag_score: float, web_score: float, flags: List[str]) -> str:
    """Generate human-readable recommendation"""
    if "no_web_results" in flags:
        return "Using RAG response as no web results available"
    elif "low_rag_confidence" in flags and "low_web_relevance" in flags:
        return "Both sources have low confidence - consider rephrasing query"
    elif rag_score > 0.8:
        return "High confidence in RAG response"
    elif web_score > 0.8:
        return "High confidence in web results"
    elif abs(rag_score - web_score) < 0.1:
        return "Sources are equally reliable - consider combining both"
    else:
        return f"Preferred source: {'RAG' if rag_score > web_score else 'Web'}"

# Example usage
if __name__ == "__main__":
    # Sample data
    sample_rag_response = "Python is a high-level programming language known for its simplicity and readability."
    sample_web_results = [
        {
            "title": "Python Programming Language - Official",
            "snippet": "Python is an interpreted, high-level programming language with dynamic semantics.",
            "url": "https://python.org",
            "published_date": "2024-01-15"
        }
    ]
    sample_query = "What is Python programming language?"
    
    # Validate responses
    result = validate_responses(sample_rag_response, sample_web_results, sample_query)
    
    print("Validation Result:")
    print(f"Best Source: {result['best_source']}")
    print(f"RAG Score: {result['rag_score']:.3f}")
    print(f"Web Score: {result['web_score']:.3f}")
    print(f"Selected Answer: {result['selected_answer'][:100]}...")  # First 100 chars