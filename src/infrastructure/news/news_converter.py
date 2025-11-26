"""
News to Inspiration Converter
Converts news articles to InspirationBase format for wizard
"""

from typing import List, Dict, Any
from datetime import datetime


def news_to_inspiration_base(article: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert a news article to InspirationBase format
    
    Args:
        article: News article from NewsService
        
    Returns:
        Dict suitable for InspirationBase initialization
    """
    
    # Generate context that provides usage guidance
    context = _generate_news_context(article)
    
    return {
        "type": "news",
        "content": article["title"],
        "source": article["source"],
        "context": context,
        "metadata": {
            "url": article.get("url", ""),
            "published_at": article.get("published_at", ""),
            "description": article.get("description", ""),
            "author": article.get("author", "")
        }
    }


def _generate_news_context(article: Dict[str, Any]) -> str:
    """
    Generate helpful context for how to use this news in content
    """
    
    title = article["title"].lower()
    description = article.get("description", "").lower()
    
    # Detect topic/angle
    angles = []
    
    if any(word in title or word in description for word in ["ai", "artificial intelligence", "machine learning", "chatgpt", "automation"]):
        angles.append("AI workplace disruption angle")
    
    if any(word in title or word in description for word in ["regulation", "policy", "law", "senate", "congress"]):
        angles.append("Regulatory/policy implications")
    
    if any(word in title or word in description for word in ["startup", "funding", "vc", "raise", "investment"]):
        angles.append("Innovation/startup ecosystem")
    
    if any(word in title or word in description for word in ["layoff", "job", "hiring", "employment"]):
        angles.append("Workforce/career angle")
    
    if any(word in title or word in description for word in ["privacy", "security", "breach", "hack"]):
        angles.append("Privacy/security concerns")
    
    if not angles:
        angles.append("General tech/business commentary")
    
    # Build context string
    context_parts = [
        f"Published: {_format_publish_date(article.get('published_at', ''))}",
        f"Suggested angles: {', '.join(angles)}"
    ]
    
    if article.get("description"):
        context_parts.append(f"Summary: {article['description'][:150]}")
    
    return " | ".join(context_parts)


def _format_publish_date(published_at: str) -> str:
    """Format publish date to relative time"""
    if not published_at:
        return "Recently"
    
    try:
        pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        now = datetime.utcnow()
        diff = now - pub_date.replace(tzinfo=None)
        
        hours = diff.total_seconds() / 3600
        
        if hours < 1:
            return "Just now"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        elif hours < 48:
            return "Yesterday"
        else:
            days = int(hours / 24)
            return f"{days} days ago"
    
    except Exception:
        return "Recently"


def group_news_by_category(articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group news articles by detected category for easier wizard display
    
    Returns:
        Dict with categories as keys and lists of InspirationBase dicts as values
    """
    
    categories = {
        "ai_automation": [],
        "workforce": [],
        "innovation": [],
        "regulation": [],
        "general": []
    }
    
    for article in articles:
        title_lower = article["title"].lower()
        desc_lower = article.get("description", "").lower()
        
        inspiration = news_to_inspiration_base(article)
        
        # Categorize
        if any(word in title_lower or word in desc_lower 
               for word in ["ai", "artificial intelligence", "automation", "chatgpt", "ml"]):
            categories["ai_automation"].append(inspiration)
        
        elif any(word in title_lower or word in desc_lower
                 for word in ["job", "hiring", "layoff", "career", "workforce", "employee"]):
            categories["workforce"].append(inspiration)
        
        elif any(word in title_lower or word in desc_lower
                 for word in ["startup", "funding", "innovation", "founder", "vc"]):
            categories["innovation"].append(inspiration)
        
        elif any(word in title_lower or word in desc_lower
                 for word in ["regulation", "policy", "law", "government"]):
            categories["regulation"].append(inspiration)
        
        else:
            categories["general"].append(inspiration)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def format_news_for_wizard_display(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format news articles for wizard frontend display
    
    Returns:
        List of dicts with display-friendly format
    """
    
    display_items = []
    
    for article in articles:
        inspiration = news_to_inspiration_base(article)
        
        display_items.append({
            "id": f"news_{hash(article['title'])}",
            "type": "news",
            "title": article["title"],
            "source": article["source"],
            "description": article.get("description", "")[:200],
            "published": _format_publish_date(article.get("published_at", "")),
            "url": article.get("url", ""),
            "preview": f"📰 {article['source']}: {article['title'][:80]}...",
            "inspiration_data": inspiration  # Full data for submission
        })
    
    return display_items


def get_trending_keywords(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract trending keywords/topics from news articles
    
    Returns:
        List of keywords with counts
    """
    from collections import Counter
    
    # Common words to exclude
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "said", "says"
    }
    
    words = []
    
    for article in articles:
        title_words = article["title"].lower().split()
        desc_words = article.get("description", "").lower().split()
        
        for word in title_words + desc_words:
            # Clean word
            word = word.strip('.,!?;:"\'-()[]{}')
            
            # Filter
            if len(word) > 3 and word not in stopwords and word.isalpha():
                words.append(word)
    
    # Count and return top keywords
    counter = Counter(words)
    
    return [
        {"keyword": word, "count": count}
        for word, count in counter.most_common(20)
    ]