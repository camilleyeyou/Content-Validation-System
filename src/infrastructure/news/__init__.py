# src/infrastructure/news/__init__.py

from .news_service import NewsService, get_news_service
from .news_converter import (
    news_to_inspiration_base,
    format_news_for_wizard_display,
    group_news_by_category,
    get_trending_keywords
)

__all__ = [
    "NewsService",
    "get_news_service",
    "news_to_inspiration_base",
    "format_news_for_wizard_display",
    "group_news_by_category",
    "get_trending_keywords"
]