"""
News Service - Fetches and caches news headlines for wizard inspiration
Uses NewsAPI.org free tier (100 requests/day)
"""

import os
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import structlog
import httpx

logger = structlog.get_logger()


class NewsService:
    """
    Service for fetching tech news headlines from NewsAPI
    Caches results to minimize API calls (free tier: 100/day)
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/news_cache"):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        if not self.api_key:
            logger.warning("news_api_key_missing", 
                         message="Set NEWS_API_KEY environment variable to enable news integration")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://newsapi.org/v2"
        self.cache_duration_hours = 24  # Refresh once per day
        
        self.logger = logger.bind(component="news_service")
    
    async def get_tech_headlines(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get technology news headlines (cached for 24 hours)
        
        Args:
            limit: Number of headlines to return
            
        Returns:
            List of news articles with title, source, url, description
        """
        cache_file = self.cache_dir / "tech_headlines.json"
        
        # Check cache first
        cached = self._load_from_cache(cache_file)
        if cached:
            self.logger.info("news_loaded_from_cache", 
                           count=len(cached), 
                           category="technology")
            return cached[:limit]
        
        # Fetch fresh data
        if not self.api_key:
            self.logger.warning("news_api_disabled", 
                              message="NEWS_API_KEY not set, returning empty list")
            return []
        
        try:
            articles = await self._fetch_top_headlines(
                category="technology",
                country="us",
                page_size=limit
            )
            
            # Cache the results
            self._save_to_cache(cache_file, articles)
            
            self.logger.info("news_fetched_from_api",
                           count=len(articles),
                           category="technology")
            
            return articles
        
        except Exception as e:
            self.logger.error("news_fetch_failed", 
                            error=str(e),
                            exc_info=True)
            return []
    
    async def get_ai_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get AI-specific news (searched by keyword)
        Cached for 24 hours
        """
        cache_file = self.cache_dir / "ai_news.json"
        
        cached = self._load_from_cache(cache_file)
        if cached:
            self.logger.info("news_loaded_from_cache",
                           count=len(cached),
                           query="artificial intelligence")
            return cached[:limit]
        
        if not self.api_key:
            return []
        
        try:
            articles = await self._search_news(
                query="artificial intelligence OR AI OR machine learning",
                sort_by="publishedAt",
                page_size=limit
            )
            
            self._save_to_cache(cache_file, articles)
            
            self.logger.info("news_fetched_from_api",
                           count=len(articles),
                           query="AI")
            
            return articles
        
        except Exception as e:
            self.logger.error("news_fetch_failed",
                            query="AI",
                            error=str(e))
            return []
    
    async def get_business_headlines(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get business news headlines"""
        cache_file = self.cache_dir / "business_headlines.json"
        
        cached = self._load_from_cache(cache_file)
        if cached:
            return cached[:limit]
        
        if not self.api_key:
            return []
        
        try:
            articles = await self._fetch_top_headlines(
                category="business",
                country="us",
                page_size=limit
            )
            
            self._save_to_cache(cache_file, articles)
            return articles
        
        except Exception as e:
            self.logger.error("news_fetch_failed",
                            category="business",
                            error=str(e))
            return []
    
    async def search_custom(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for news by custom query (not cached)
        Use sparingly due to API limits
        """
        if not self.api_key:
            return []
        
        try:
            articles = await self._search_news(
                query=query,
                sort_by="publishedAt",
                page_size=limit
            )
            
            self.logger.info("news_custom_search",
                           query=query,
                           count=len(articles))
            
            return articles
        
        except Exception as e:
            self.logger.error("news_custom_search_failed",
                            query=query,
                            error=str(e))
            return []
    
    async def _fetch_top_headlines(
        self,
        category: str,
        country: str = "us",
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch top headlines from NewsAPI"""
        
        url = f"{self.base_url}/top-headlines"
        params = {
            "apiKey": self.api_key,
            "category": category,
            "country": country,
            "pageSize": page_size
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            return self._format_articles(data.get("articles", []))
    
    async def _search_news(
        self,
        query: str,
        sort_by: str = "publishedAt",
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Search news by keyword"""
        
        url = f"{self.base_url}/everything"
        params = {
            "apiKey": self.api_key,
            "q": query,
            "sortBy": sort_by,
            "pageSize": page_size,
            "language": "en"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            
            return self._format_articles(data.get("articles", []))
    
    def _format_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """Format articles to consistent structure"""
        formatted = []
        
        for article in articles:
            # Skip articles without titles
            if not article.get("title"):
                continue
            
            formatted.append({
                "title": article["title"],
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "description": article.get("description", ""),
                "published_at": article.get("publishedAt", ""),
                "author": article.get("author", ""),
                "image_url": article.get("urlToImage", ""),
                "content_preview": article.get("content", "")[:200] if article.get("content") else ""
            })
        
        return formatted
    
    def _load_from_cache(self, cache_file: Path) -> Optional[List[Dict[str, Any]]]:
        """Load articles from cache if not expired"""
        
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is expired
            file_age = time.time() - cache_file.stat().st_mtime
            max_age = self.cache_duration_hours * 3600
            
            if file_age > max_age:
                self.logger.info("news_cache_expired",
                               cache_file=cache_file.name,
                               age_hours=round(file_age / 3600, 1))
                return None
            
            # Load and return cached data
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            return data.get("articles", [])
        
        except Exception as e:
            self.logger.warning("news_cache_load_failed",
                              cache_file=cache_file.name,
                              error=str(e))
            return None
    
    def _save_to_cache(self, cache_file: Path, articles: List[Dict[str, Any]]) -> None:
        """Save articles to cache"""
        
        try:
            cache_data = {
                "cached_at": datetime.utcnow().isoformat() + "Z",
                "articles": articles
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.logger.info("news_cache_saved",
                           cache_file=cache_file.name,
                           count=len(articles))
        
        except Exception as e:
            self.logger.warning("news_cache_save_failed",
                              cache_file=cache_file.name,
                              error=str(e))
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cached news"""
        
        stats = {
            "cache_dir": str(self.cache_dir),
            "cached_categories": []
        }
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                cached_at = data.get("cached_at", "unknown")
                article_count = len(data.get("articles", []))
                
                # Calculate age
                if cached_at != "unknown":
                    cached_time = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
                    age_hours = (datetime.utcnow() - cached_time.replace(tzinfo=None)).total_seconds() / 3600
                else:
                    age_hours = -1
                
                stats["cached_categories"].append({
                    "category": cache_file.stem,
                    "count": article_count,
                    "cached_at": cached_at,
                    "age_hours": round(age_hours, 1),
                    "expired": age_hours > self.cache_duration_hours if age_hours >= 0 else False
                })
            
            except Exception as e:
                self.logger.warning("cache_stats_file_error",
                                  file=cache_file.name,
                                  error=str(e))
        
        return stats
    
    async def refresh_all_caches(self) -> Dict[str, int]:
        """Force refresh all cached news categories"""
        
        self.logger.info("news_cache_refresh_started")
        
        results = {
            "tech": 0,
            "ai": 0,
            "business": 0
        }
        
        try:
            tech = await self.get_tech_headlines(limit=15)
            results["tech"] = len(tech)
        except Exception as e:
            self.logger.error("tech_refresh_failed", error=str(e))
        
        try:
            ai = await self.get_ai_news(limit=15)
            results["ai"] = len(ai)
        except Exception as e:
            self.logger.error("ai_refresh_failed", error=str(e))
        
        try:
            business = await self.get_business_headlines(limit=15)
            results["business"] = len(business)
        except Exception as e:
            self.logger.error("business_refresh_failed", error=str(e))
        
        self.logger.info("news_cache_refresh_completed", results=results)
        
        return results


# Singleton instance
_news_service: Optional[NewsService] = None

def get_news_service(api_key: Optional[str] = None) -> NewsService:
    """Get or create singleton NewsService instance"""
    global _news_service
    
    if _news_service is None:
        _news_service = NewsService(api_key=api_key)
    
    return _news_service