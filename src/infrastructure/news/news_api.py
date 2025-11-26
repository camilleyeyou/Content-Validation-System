"""
News API Endpoints for Wizard
Add these routes to your main FastAPI app
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import structlog

# Import the news service and converter
from src.infrastructure.news.news_service import get_news_service
from src.infrastructure.news.news_converter import (
     format_news_for_wizard_display,
     group_news_by_category,
    get_trending_keywords
 )

logger = structlog.get_logger()

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/tech")
async def get_tech_news(limit: int = Query(10, ge=1, le=20)):
    """
    Get technology news headlines for wizard inspiration
    Cached for 24 hours
    
    Returns:
        List of news items formatted for wizard display
    """
    try:
        news_service = get_news_service()
        articles = await news_service.get_tech_headlines(limit=limit)
        
        # Format for wizard display
        display_items = format_news_for_wizard_display(articles)
        
        logger.info("tech_news_served",
                   count=len(display_items),
                   from_cache=True)  # Will be True if cached
        
        return {
            "success": True,
            "count": len(display_items),
            "category": "technology",
            "news": display_items
        }
    
    except Exception as e:
        logger.error("tech_news_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch tech news: {str(e)}")


@router.get("/ai")
async def get_ai_news(limit: int = Query(10, ge=1, le=20)):
    """
    Get AI-specific news for wizard inspiration
    Cached for 24 hours
    """
    try:
        news_service = get_news_service()
        articles = await news_service.get_ai_news(limit=limit)
        
        display_items = format_news_for_wizard_display(articles)
        
        logger.info("ai_news_served", count=len(display_items))
        
        return {
            "success": True,
            "count": len(display_items),
            "category": "artificial_intelligence",
            "news": display_items
        }
    
    except Exception as e:
        logger.error("ai_news_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch AI news: {str(e)}")


@router.get("/business")
async def get_business_news(limit: int = Query(10, ge=1, le=20)):
    """
    Get business news headlines for wizard inspiration
    Cached for 24 hours
    """
    try:
        news_service = get_news_service()
        articles = await news_service.get_business_headlines(limit=limit)
        
        display_items = format_news_for_wizard_display(articles)
        
        logger.info("business_news_served", count=len(display_items))
        
        return {
            "success": True,
            "count": len(display_items),
            "category": "business",
            "news": display_items
        }
    
    except Exception as e:
        logger.error("business_news_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch business news: {str(e)}")


@router.get("/all")
async def get_all_news_grouped():
    """
    Get all cached news grouped by category
    Perfect for wizard inspiration selection
    """
    try:
        news_service = get_news_service()
        
        # Fetch all categories
        tech_articles = await news_service.get_tech_headlines(limit=10)
        ai_articles = await news_service.get_ai_news(limit=10)
        business_articles = await news_service.get_business_headlines(limit=10)
        
        # Combine and group by detected category
        all_articles = tech_articles + ai_articles + business_articles
        
        # Remove duplicates by title
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                unique_articles.append(article)
        
        # Group by category
        grouped = group_news_by_category(unique_articles)
        
        # Format for display
        result = {}
        for category, articles in grouped.items():
            result[category] = {
                "count": len(articles),
                "items": articles[:8]  # Limit per category
            }
        
        logger.info("grouped_news_served",
                   categories=list(result.keys()),
                   total_count=sum(g["count"] for g in result.values()))
        
        return {
            "success": True,
            "categories": result,
            "total_articles": len(unique_articles)
        }
    
    except Exception as e:
        logger.error("grouped_news_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch grouped news: {str(e)}")


@router.get("/search")
async def search_news(q: str = Query(..., min_length=2), limit: int = Query(5, ge=1, le=10)):
    """
    Search news by custom query
    Use sparingly - not cached, counts against API limit
    """
    try:
        news_service = get_news_service()
        articles = await news_service.search_custom(query=q, limit=limit)
        
        display_items = format_news_for_wizard_display(articles)
        
        logger.info("news_search_completed",
                   query=q,
                   count=len(display_items))
        
        return {
            "success": True,
            "query": q,
            "count": len(display_items),
            "news": display_items
        }
    
    except Exception as e:
        logger.error("news_search_failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to search news: {str(e)}")


@router.get("/trending")
async def get_trending_topics():
    """
    Get trending keywords/topics from recent news
    Useful for suggesting relevant content angles
    """
    try:
        news_service = get_news_service()
        
        # Get recent news from all categories
        tech = await news_service.get_tech_headlines(limit=15)
        ai = await news_service.get_ai_news(limit=15)
        
        all_articles = tech + ai
        
        # Extract trending keywords
        keywords = get_trending_keywords(all_articles)
        
        logger.info("trending_topics_served", count=len(keywords))
        
        return {
            "success": True,
            "trending_keywords": keywords[:15],
            "based_on_articles": len(all_articles)
        }
    
    except Exception as e:
        logger.error("trending_topics_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending topics: {str(e)}")


@router.post("/refresh")
async def refresh_news_cache():
    """
    Force refresh all news caches
    Use once per day or when cache is stale
    """
    try:
        news_service = get_news_service()
        
        # Clear old cache files
        for cache_file in news_service.cache_dir.glob("*.json"):
            cache_file.unlink()
        
        # Fetch fresh data
        results = await news_service.refresh_all_caches()
        
        logger.info("news_cache_refreshed", results=results)
        
        return {
            "success": True,
            "message": "News cache refreshed",
            "results": results
        }
    
    except Exception as e:
        logger.error("news_cache_refresh_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to refresh news cache: {str(e)}")


@router.get("/cache-stats")
async def get_cache_stats():
    """
    Get statistics about cached news
    """
    try:
        news_service = get_news_service()
        stats = news_service.get_cache_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        logger.error("cache_stats_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


# Add this to your main FastAPI app:
# app.include_router(router)