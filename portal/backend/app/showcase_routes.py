# portal/backend/app/showcase_routes.py
"""
Showcase Routes - Daily featured posts for the Inspiration Gallery
Displays 3 diverse approved posts with images that update once per day
"""

from fastapi import APIRouter, HTTPException
from datetime import date
from typing import Dict, Any, List, Optional
import random

router = APIRouter()

# Global cache for showcase posts (updates once per day)
# In production, consider using Redis or a database table
showcase_cache: Dict[str, Any] = {
    "posts": [],
    "date": None
}


def select_diverse_posts(posts: List[Dict[str, Any]], count: int = 3) -> List[Dict[str, Any]]:
    """
    Select diverse posts from the approved queue.
    Aims for variety by choosing from different time periods.
    
    Args:
        posts: List of approved posts
        count: Number of posts to select (default 3)
    
    Returns:
        List of selected posts
    """
    if len(posts) <= count:
        return posts
    
    # Strategy: Pick from different sections for variety
    # - Recent (newest)
    # - Middle (mid-range)  
    # - Older (from further back)
    indices = []
    
    if len(posts) >= 3:
        # First post (newest)
        indices.append(0)
        # Middle post
        indices.append(len(posts) // 2)
        # Older post
        indices.append(len(posts) - 1)
    else:
        indices = list(range(len(posts)))
    
    # Shuffle to randomize which position shows which era
    random.shuffle(indices)
    
    # Select the posts
    selected = [posts[idx] for idx in indices[:count]]
    
    return selected


def refresh_showcase(approved_queue: List[Dict[str, Any]]) -> None:
    """
    Refresh the showcase with new posts from the approved queue.
    Only includes posts that have images.
    
    Args:
        approved_queue: The global APPROVED_QUEUE from main.py
    """
    # Filter to only posts with images
    posts_with_images = [
        post for post in approved_queue 
        if post.get("has_image") or post.get("image_url")
    ]
    
    if len(posts_with_images) < 3:
        # Not enough posts with images
        showcase_cache["posts"] = []
        showcase_cache["date"] = date.today()
        return
    
    # Select 3 diverse posts
    selected_posts = select_diverse_posts(posts_with_images, count=3)
    
    # Store in cache
    showcase_cache["posts"] = selected_posts
    showcase_cache["date"] = date.today()


@router.get("/api/showcase")
async def get_showcase_posts(
    # We'll get APPROVED_QUEUE via dependency injection in main.py
    # For now, we'll access it through the router's state
) -> Dict[str, Any]:
    """
    Get today's showcase posts for the Inspiration Gallery.
    Returns 3 diverse approved posts with images.
    Updates once per day automatically.
    
    Returns:
        {
            "posts": [...],  # List of 3 showcase posts
            "last_updated": "2025-11-25"  # ISO date string
        }
    """
    today = date.today()
    
    # Import here to avoid circular import
    from .main import APPROVED_QUEUE
    
    # Check if we need to refresh
    if showcase_cache["date"] != today or not showcase_cache["posts"]:
        refresh_showcase(APPROVED_QUEUE)
    
    return {
        "posts": showcase_cache["posts"],
        "last_updated": showcase_cache["date"].isoformat() if showcase_cache["date"] else None,
        "count": len(showcase_cache["posts"])
    }


@router.post("/api/showcase/refresh")
async def force_refresh_showcase() -> Dict[str, Any]:
    """
    Manually refresh the showcase posts.
    Useful for:
    - Testing
    - Immediately updating after generating new posts
    - Admin controls
    
    Returns:
        {
            "message": "Showcase refreshed",
            "posts_count": 3,
            "date": "2025-11-25"
        }
    """
    # Import here to avoid circular import
    from .main import APPROVED_QUEUE
    
    refresh_showcase(APPROVED_QUEUE)
    
    return {
        "message": "Showcase refreshed successfully",
        "posts_count": len(showcase_cache["posts"]),
        "date": showcase_cache["date"].isoformat() if showcase_cache["date"] else None,
        "has_enough_posts": len(showcase_cache["posts"]) >= 3
    }


@router.get("/api/showcase/stats")
async def get_showcase_stats() -> Dict[str, Any]:
    """
    Get statistics about the showcase system.
    Useful for debugging and monitoring.
    
    Returns:
        Stats about current showcase state and available posts
    """
    from .main import APPROVED_QUEUE
    
    posts_with_images = [
        post for post in APPROVED_QUEUE 
        if post.get("has_image") or post.get("image_url")
    ]
    
    return {
        "cache_date": showcase_cache["date"].isoformat() if showcase_cache["date"] else None,
        "cache_is_today": showcase_cache["date"] == date.today() if showcase_cache["date"] else False,
        "cached_posts_count": len(showcase_cache["posts"]),
        "total_approved_posts": len(APPROVED_QUEUE),
        "posts_with_images": len(posts_with_images),
        "ready_for_showcase": len(posts_with_images) >= 3,
        "showcase_needs_refresh": showcase_cache["date"] != date.today() if showcase_cache["date"] else True
    }