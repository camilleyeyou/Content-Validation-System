# portal/backend/app/cost_routes.py
"""
Cost Tracking API Routes - DEBUG VERSION
Use this version to see detailed error information
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path
import traceback

# Setup paths
CURRENT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = CURRENT_DIR.parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.parent.resolve()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print(f"🔍 DEBUG: PROJECT_ROOT = {PROJECT_ROOT}")
print(f"🔍 DEBUG: sys.path includes PROJECT_ROOT = {str(PROJECT_ROOT) in sys.path}")

# Import cost tracker
try:
    from src.infrastructure.cost_tracking.cost_tracker import get_cost_tracker
    COST_TRACKING_ENABLED = True
    print("✅ Cost tracking module imported successfully")
except ImportError as e:
    COST_TRACKING_ENABLED = False
    print(f"❌ Failed to import cost tracking: {e}")
    traceback.print_exc()

router = APIRouter(prefix="/api/costs", tags=["costs"])


@router.get("/enabled")
async def cost_tracking_status():
    """Check if cost tracking is enabled"""
    return {"enabled": COST_TRACKING_ENABLED}


@router.get("/summary")
async def get_cost_summary():
    """Get overall cost statistics - DEBUG VERSION"""
    print("\n" + "="*80)
    print("🔍 DEBUG: /api/costs/summary endpoint called")
    print("="*80)
    
    if not COST_TRACKING_ENABLED:
        print("❌ Cost tracking not enabled")
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        print("📊 Step 1: Getting tracker instance...")
        tracker = get_cost_tracker()
        print(f"✅ Got tracker: {tracker}")
        print(f"   - api_calls count: {len(tracker.api_calls)}")
        print(f"   - post_costs count: {len(tracker.post_costs)}")
        
        print("\n📊 Step 2: Reloading data...")
        tracker.reload_data()
        print(f"✅ Reloaded data")
        print(f"   - api_calls count after reload: {len(tracker.api_calls)}")
        print(f"   - post_costs count after reload: {len(tracker.post_costs)}")
        
        print("\n📊 Step 3: Getting stats...")
        stats = tracker.get_stats()
        print(f"✅ Got stats: {stats}")
        
        print("\n📊 Step 4: Getting total spent...")
        total_spent = tracker.get_total_spent()
        print(f"✅ Got total_spent: ${total_spent}")
        
        print("\n📊 Step 5: Building response...")
        response = {
            "ok": True,
            "stats": stats,
            "total_spent": total_spent
        }
        print(f"✅ Response ready: {response}")
        print("="*80 + "\n")
        
        return response
        
    except Exception as e:
        print(f"\n❌ ERROR in get_cost_summary:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print("\n📋 Full traceback:")
        traceback.print_exc()
        print("="*80 + "\n")
        
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )


@router.get("/daily")
async def get_daily_costs(date: Optional[str] = None):
    """Get cost summary for a specific date - DEBUG VERSION"""
    print("\n" + "="*80)
    print(f"🔍 DEBUG: /api/costs/daily endpoint called (date={date})")
    print("="*80)
    
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        print("📊 Getting tracker and reloading data...")
        tracker = get_cost_tracker()
        tracker.reload_data()
        print(f"✅ Tracker ready with {len(tracker.daily_costs)} daily summaries")
        
        if date:
            try:
                datetime.strptime(date, "%Y-%m-%d")
                print(f"✅ Date format valid: {date}")
            except ValueError:
                print(f"❌ Invalid date format: {date}")
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            date = datetime.utcnow().strftime("%Y-%m-%d")
            print(f"ℹ️  Using today's date: {date}")
        
        print(f"\n📊 Getting summary for {date}...")
        summary = tracker.get_daily_summary(date)
        
        if not summary:
            print(f"⚠️  No data found for {date}")
            return {
                "ok": True,
                "date": date,
                "summary": None,
                "message": "No data for this date"
            }
        
        print(f"✅ Found summary: {summary}")
        
        response = {
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
        print(f"✅ Response ready")
        print("="*80 + "\n")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ ERROR in get_daily_costs:")
        print(f"   Error: {str(e)}")
        traceback.print_exc()
        print("="*80 + "\n")
        
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e), "traceback": traceback.format_exc()}
        )


@router.get("/posts")
async def get_post_costs(limit: int = 10):
    """Get recent post cost breakdowns - DEBUG VERSION"""
    print("\n" + "="*80)
    print(f"🔍 DEBUG: /api/costs/posts endpoint called (limit={limit})")
    print("="*80)
    
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    try:
        print("📊 Getting tracker and reloading data...")
        tracker = get_cost_tracker()
        tracker.reload_data()
        print(f"✅ Tracker ready with {len(tracker.post_costs)} post summaries")
        
        print(f"\n📊 Getting {limit} most recent posts...")
        posts = tracker.get_post_costs(limit)
        print(f"✅ Retrieved {len(posts)} posts")
        
        if posts:
            print(f"   First post: batch={posts[0].batch_id}, post={posts[0].post_number}, cost=${posts[0].total_cost}")
        
        print("\n📊 Building response...")
        response = {
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
        print(f"✅ Response ready with {len(response['posts'])} posts")
        print("="*80 + "\n")
        return response
        
    except Exception as e:
        print(f"\n❌ ERROR in get_post_costs:")
        print(f"   Error: {str(e)}")
        traceback.print_exc()
        print("="*80 + "\n")
        
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e), "traceback": traceback.format_exc()}
        )


@router.get("/by-agent")
async def get_costs_by_agent(days: int = 7):
    """Get cost breakdown by agent - DEBUG VERSION"""
    print("\n" + "="*80)
    print(f"🔍 DEBUG: /api/costs/by-agent endpoint called (days={days})")
    print("="*80)
    
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        print("📊 Getting tracker and reloading data...")
        tracker = get_cost_tracker()
        tracker.reload_data()
        print(f"✅ Tracker ready with {len(tracker.api_calls)} API calls")
        
        # Get calls for date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        print(f"\n📊 Filtering calls from {start_date.date()} to {end_date.date()}...")
        relevant_calls = [
            call for call in tracker.api_calls
            if start_date.isoformat() <= call.timestamp <= end_date.isoformat()
        ]
        print(f"✅ Found {len(relevant_calls)} relevant calls")
        
        # Group by agent
        print("\n📊 Grouping by agent...")
        agent_costs = {}
        for call in relevant_calls:
            agent = call.agent_name
            if agent not in agent_costs:
                agent_costs[agent] = {
                    "agent": agent,
                    "total_cost": 0.0,
                    "api_calls": 0,
                    "total_tokens": 0,
                    "avg_cost_per_call": 0.0
                }
            
            agent_costs[agent]["total_cost"] += call.total_cost
            agent_costs[agent]["api_calls"] += 1
            agent_costs[agent]["total_tokens"] += call.total_tokens
        
        print(f"✅ Grouped into {len(agent_costs)} agents")
        
        # Calculate averages
        for agent in agent_costs.values():
            if agent["api_calls"] > 0:
                agent["avg_cost_per_call"] = round(
                    agent["total_cost"] / agent["api_calls"], 6
                )
            agent["total_cost"] = round(agent["total_cost"], 4)
        
        # Sort by total cost descending
        sorted_agents = sorted(
            agent_costs.values(),
            key=lambda x: x["total_cost"],
            reverse=True
        )
        
        response = {
            "ok": True,
            "period": f"Last {days} days",
            "agents": sorted_agents
        }
        print(f"✅ Response ready with {len(sorted_agents)} agents")
        print("="*80 + "\n")
        return response
        
    except Exception as e:
        print(f"\n❌ ERROR in get_costs_by_agent:")
        print(f"   Error: {str(e)}")
        traceback.print_exc()
        print("="*80 + "\n")
        
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e), "traceback": traceback.format_exc()}
        )


# Simplified versions of other endpoints for debugging
@router.get("/range")
async def get_date_range_costs(days: int = 7):
    """Get cost summary for date range"""
    if not COST_TRACKING_ENABLED:
        raise HTTPException(status_code=503, detail="Cost tracking not enabled")
    
    try:
        tracker = get_cost_tracker()
        tracker.reload_data()
        summary = tracker.get_date_range_summary(days)
        return {"ok": True, "summary": summary}
    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )