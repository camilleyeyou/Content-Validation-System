# portal/backend/app/cost_routes.py
"""
Cost Tracking API Routes
Exposes cost metrics and analytics
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Setup paths
CURRENT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = CURRENT_DIR.parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.parent.resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import cost tracker (will be available after you copy the file)
try:
    from cost_tracker import get_cost_tracker
    COST_TRACKING_ENABLED = True
except ImportError:
    COST_TRACKING_ENABLED = False
    print("⚠️ Cost tracking not available - cost_tracker.py not found")

router = APIRouter(prefix="/api/costs", tags=["costs"])


@router.get("/enabled")
async def cost_tracking_status():
    """Check if cost tracking is enabled"""
    return {"enabled": COST_TRACKING_ENABLED}


@router.get("/summary")
async def get_cost_summary():
    """Get overall cost statistics"""
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        tracker = get_cost_tracker()
        stats = tracker.get_stats()
        
        return {
            "ok": True,
            "stats": stats,
            "total_spent": tracker.get_total_spent()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/daily")
async def get_daily_costs(date: Optional[str] = None):
    """
    Get cost summary for a specific date
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        tracker = get_cost_tracker()
        
        if date:
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        summary = tracker.get_daily_summary(date)
        
        if not summary:
            return {
                "ok": True,
                "date": date or datetime.utcnow().strftime("%Y-%m-%d"),
                "summary": None,
                "message": "No data for this date"
            }
        
        return {
            "ok": True,
            "summary": {
                "date": summary.date,
                "total_cost": summary.total_cost,
                "openai_cost": summary.openai_cost,
                "gemini_cost": summary.gemini_cost,
                "text_generation_cost": summary.text_generation_cost,
                "image_generation_cost": summary.image_generation_cost,
                "posts_generated": summary.posts_generated,
                "images_generated": summary.images_generated,
                "api_calls": summary.api_calls,
                "total_tokens": summary.total_input_tokens + summary.total_output_tokens
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/range")
async def get_date_range_costs(days: int = 7):
    """
    Get cost summary for the last N days
    
    Args:
        days: Number of days to look back (default: 7, max: 90)
    """
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")
    
    try:
        tracker = get_cost_tracker()
        summary = tracker.get_date_range_summary(days)
        
        return {
            "ok": True,
            "summary": summary
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/posts")
async def get_post_costs(limit: int = 10):
    """
    Get recent post cost breakdowns
    
    Args:
        limit: Number of posts to return (default: 10, max: 100)
    """
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    try:
        tracker = get_cost_tracker()
        posts = tracker.get_post_costs(limit)
        
        return {
            "ok": True,
            "posts": [
                {
                    "batch_id": post.batch_id,
                    "post_number": post.post_number,
                    "timestamp": post.timestamp,
                    "total_cost": post.total_cost,
                    "content_generation_cost": post.content_generation_cost,
                    "image_generation_cost": post.image_generation_cost,
                    "validation_cost": post.validation_cost,
                    "feedback_cost": post.feedback_cost,
                    "total_tokens": post.total_tokens,
                    "api_calls": post.api_calls
                }
                for post in posts
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/by-agent")
async def get_costs_by_agent(days: int = 7):
    """
    Get cost breakdown by agent for the last N days
    
    Args:
        days: Number of days to look back (default: 7)
    """
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        tracker = get_cost_tracker()
        
        # Get calls for date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        relevant_calls = [
            call for call in tracker.api_calls
            if start_date.isoformat() <= call.timestamp <= end_date.isoformat()
        ]
        
        # Group by agent
        agent_costs = {}
        for call in relevant_calls:
            if call.agent_name not in agent_costs:
                agent_costs[call.agent_name] = {
                    "agent_name": call.agent_name,
                    "total_cost": 0.0,
                    "api_calls": 0,
                    "total_tokens": 0,
                    "images_generated": 0
                }
            
            agent_costs[call.agent_name]["total_cost"] += call.total_cost
            agent_costs[call.agent_name]["api_calls"] += 1
            agent_costs[call.agent_name]["total_tokens"] += call.total_tokens
            agent_costs[call.agent_name]["images_generated"] += call.image_count
        
        # Sort by cost
        sorted_agents = sorted(
            agent_costs.values(),
            key=lambda x: x["total_cost"],
            reverse=True
        )
        
        return {
            "ok": True,
            "period": f"Last {days} days",
            "agents": sorted_agents
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.get("/by-model")
async def get_costs_by_model(days: int = 7):
    """
    Get cost breakdown by model for the last N days
    
    Args:
        days: Number of days to look back (default: 7)
    """
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        tracker = get_cost_tracker()
        
        # Get calls for date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        relevant_calls = [
            call for call in tracker.api_calls
            if start_date.isoformat() <= call.timestamp <= end_date.isoformat()
        ]
        
        # Group by model
        model_costs = {}
        for call in relevant_calls:
            if call.model not in model_costs:
                model_costs[call.model] = {
                    "model": call.model,
                    "provider": call.provider,
                    "total_cost": 0.0,
                    "api_calls": 0,
                    "total_tokens": 0,
                    "images_generated": 0
                }
            
            model_costs[call.model]["total_cost"] += call.total_cost
            model_costs[call.model]["api_calls"] += 1
            model_costs[call.model]["total_tokens"] += call.total_tokens
            model_costs[call.model]["images_generated"] += call.image_count
        
        # Sort by cost
        sorted_models = sorted(
            model_costs.values(),
            key=lambda x: x["total_cost"],
            reverse=True
        )
        
        return {
            "ok": True,
            "period": f"Last {days} days",
            "models": sorted_models
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@router.post("/finalize-post")
async def finalize_post_cost(batch_id: str, post_number: int):
    """
    Finalize cost calculation for a completed post
    Groups all API calls for the post into a summary
    
    Args:
        batch_id: Batch ID
        post_number: Post number within batch
    """
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        tracker = get_cost_tracker()
        summary = tracker.finalize_post_cost(batch_id, post_number)
        
        if not summary:
            return {
                "ok": False,
                "message": f"No API calls found for post {batch_id}-{post_number}"
            }
        
        return {
            "ok": True,
            "summary": {
                "batch_id": summary.batch_id,
                "post_number": summary.post_number,
                "total_cost": summary.total_cost,
                "breakdown": {
                    "content_generation": summary.content_generation_cost,
                    "image_generation": summary.image_generation_cost,
                    "validation": summary.validation_cost,
                    "feedback": summary.feedback_cost
                },
                "api_calls": summary.api_calls,
                "total_tokens": summary.total_tokens
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )