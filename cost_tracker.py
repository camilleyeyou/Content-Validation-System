# src/infrastructure/cost_tracking/cost_tracker.py
"""
Cost Tracking Service for AI API Usage
Place this file at: Content-Validation-System/src/infrastructure/cost_tracking/cost_tracker.py
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger(__name__)


# --------------------------------------------------------------------------------------
# Pricing Constants (Updated for 2024-2025)
# --------------------------------------------------------------------------------------

@dataclass
class ModelPricing:
    """Pricing for a specific model"""
    name: str
    input_cost_per_1k: float
    output_cost_per_1k: float
    image_cost: Optional[float] = None


# OpenAI Pricing
OPENAI_PRICING = {
    "gpt-4o-mini": ModelPricing(
        name="gpt-4o-mini",
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006
    ),
    "gpt-4o": ModelPricing(
        name="gpt-4o",
        input_cost_per_1k=0.0025,
        output_cost_per_1k=0.01
    ),
    "gpt-4-turbo": ModelPricing(
        name="gpt-4-turbo",
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03
    ),
    "gpt-3.5-turbo": ModelPricing(
        name="gpt-3.5-turbo",
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.0015
    )
}

# Gemini Pricing
GEMINI_PRICING = {
    "gemini-2.5-flash": ModelPricing(
        name="gemini-2.5-flash",
        input_cost_per_1k=0.000075,
        output_cost_per_1k=0.0003
    ),
    "gemini-2.5-flash-image": ModelPricing(
        name="gemini-2.5-flash-image",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        image_cost=0.039
    ),
    "gemini-2.5-pro": ModelPricing(
        name="gemini-2.5-pro",
        input_cost_per_1k=0.001,
        output_cost_per_1k=0.005
    )
}


# --------------------------------------------------------------------------------------
# Cost Record Dataclasses
# --------------------------------------------------------------------------------------

@dataclass
class ApiCallCost:
    """Record of a single API call cost"""
    timestamp: str
    agent_name: str
    model: str
    provider: str
    call_type: str
    
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    image_count: int = 0
    
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    
    batch_id: Optional[str] = None
    post_number: Optional[int] = None
    generation_time_seconds: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class PostCostSummary:
    """Cost summary for a single post"""
    batch_id: str
    post_number: int
    timestamp: str
    
    content_generation_cost: float = 0.0
    image_generation_cost: float = 0.0
    validation_cost: float = 0.0
    feedback_cost: float = 0.0
    total_cost: float = 0.0
    
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    api_calls: int = 0


@dataclass
class DailyCostSummary:
    """Cost summary for a day"""
    date: str
    
    openai_cost: float = 0.0
    gemini_cost: float = 0.0
    total_cost: float = 0.0
    
    text_generation_cost: float = 0.0
    image_generation_cost: float = 0.0
    
    posts_generated: int = 0
    images_generated: int = 0
    api_calls: int = 0
    
    total_input_tokens: int = 0
    total_output_tokens: int = 0


# --------------------------------------------------------------------------------------
# Cost Tracker Service
# --------------------------------------------------------------------------------------

class CostTracker:
    """Tracks and calculates costs for all AI API usage"""
    
    def __init__(self, storage_dir: str = "data/costs"):
        """Initialize cost tracker"""
        # Get project root - we need to find Content-Validation-System directory
        current_file = Path(__file__).resolve()
        
        # Method 1: If we're in src/infrastructure/cost_tracking, go up to project root
        if "src" in current_file.parts and "infrastructure" in current_file.parts:
            # Find the 'src' directory and go up one level
            parts = current_file.parts
            src_index = parts.index("src")
            project_root = Path(*parts[:src_index])
            self.logger = logger.bind(component="cost_tracker")
            self.logger.info(f"Found project root via src path: {project_root}")
        else:
            # Method 2: Look for characteristic files/directories
            # Start from current directory and walk up
            search_path = Path.cwd()
            max_levels = 5
            
            for _ in range(max_levels):
                # Check if this looks like project root (has src/ and portal/ directories)
                if (search_path / "src").exists() and (search_path / "portal").exists():
                    project_root = search_path
                    self.logger = logger.bind(component="cost_tracker")
                    self.logger.info(f"Found project root via directory search: {project_root}")
                    break
                
                # Go up one level
                parent = search_path.parent
                if parent == search_path:  # Reached filesystem root
                    break
                search_path = parent
            else:
                # Fallback: use current directory
                project_root = Path.cwd()
                self.logger = logger.bind(component="cost_tracker")
                self.logger.warning(f"Could not find project root, using cwd: {project_root}")
        
        self.storage_dir = project_root / storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.calls_file = self.storage_dir / "api_calls.json"
        self.posts_file = self.storage_dir / "post_costs.json"
        self.daily_file = self.storage_dir / "daily_costs.json"
        
        self.api_calls: List[ApiCallCost] = []
        self.post_costs: List[PostCostSummary] = []
        self.daily_costs: Dict[str, DailyCostSummary] = {}
        
        self.logger = logger.bind(component="cost_tracker")
        
        self.logger.info("CostTracker initializing",
                        storage_dir=str(self.storage_dir),
                        calls_file=str(self.calls_file),
                        calls_file_exists=self.calls_file.exists())
        
        self._load_data()
        
        self.logger.info("CostTracker initialized", 
                        loaded_calls=len(self.api_calls),
                        loaded_posts=len(self.post_costs))
    
    def _load_data(self):
        """Load existing cost data from files"""
        try:
            if self.calls_file.exists():
                self.logger.info(f"Loading API calls from {self.calls_file}")
                with open(self.calls_file, 'r') as f:
                    data = json.load(f)
                    self.logger.info(f"Found {len(data)} API call records")
                    self.api_calls = [ApiCallCost(**item) for item in data]
                    self.logger.info(f"Loaded {len(self.api_calls)} API calls successfully")
            else:
                self.logger.info(f"No existing api_calls.json found at {self.calls_file}")
            
            if self.posts_file.exists():
                with open(self.posts_file, 'r') as f:
                    data = json.load(f)
                    self.post_costs = [PostCostSummary(**item) for item in data]
                    self.logger.info(f"Loaded {len(self.post_costs)} post cost summaries")
            
            if self.daily_file.exists():
                with open(self.daily_file, 'r') as f:
                    data = json.load(f)
                    self.daily_costs = {k: DailyCostSummary(**v) for k, v in data.items()}
                    self.logger.info(f"Loaded {len(self.daily_costs)} daily summaries")
        except Exception as e:
            self.logger.error(f"Failed to load cost data: {e}", exc_info=True)
            # Don't let loading errors break initialization
            self.api_calls = []
            self.post_costs = []
            self.daily_costs = {}
    
    def _save_data(self):
        """Save cost data to files"""
        try:
            with open(self.calls_file, 'w') as f:
                json.dump([asdict(call) for call in self.api_calls], f, indent=2)
            
            with open(self.posts_file, 'w') as f:
                json.dump([asdict(post) for post in self.post_costs], f, indent=2)
            
            with open(self.daily_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.daily_costs.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cost data: {e}")
    
    def calculate_text_cost(self, model: str, input_tokens: int, output_tokens: int, 
                           provider: str = "openai") -> Dict[str, float]:
        """Calculate cost for text generation"""
        if provider == "openai":
            pricing = OPENAI_PRICING.get(model)
            
            # Handle model names with date suffixes (e.g., gpt-4o-mini-2024-07-18)
            if not pricing:
                # Try matching base model name
                for base_model in OPENAI_PRICING.keys():
                    if model.startswith(base_model):
                        pricing = OPENAI_PRICING[base_model]
                        break
        else:
            pricing = GEMINI_PRICING.get(model)
            
            # Handle Gemini model names with suffixes
            if not pricing:
                for base_model in GEMINI_PRICING.keys():
                    if model.startswith(base_model):
                        pricing = GEMINI_PRICING[base_model]
                        break
        
        if not pricing:
            self.logger.warning(f"Unknown model: {model}, using default pricing")
            pricing = OPENAI_PRICING["gpt-4o-mini"]
        
        input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k
        output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6)
        }
    
    def calculate_image_cost(self, model: str = "gemini-2.5-flash-image", 
                            image_count: int = 1) -> float:
        """Calculate cost for image generation"""
        pricing = GEMINI_PRICING.get(model)
        
        # Handle model names with suffixes
        if not pricing:
            for base_model in GEMINI_PRICING.keys():
                if model.startswith(base_model):
                    pricing = GEMINI_PRICING[base_model]
                    break
        
        if not pricing or not pricing.image_cost:
            self.logger.warning(f"Unknown image model: {model}, using default Gemini pricing")
            return 0.039 * image_count
        
        return round(pricing.image_cost * image_count, 6)
    
    def track_api_call(self,
                       agent_name: str,
                       model: str,
                       provider: str,
                       call_type: str,
                       input_tokens: int = 0,
                       output_tokens: int = 0,
                       image_count: int = 0,
                       batch_id: Optional[str] = None,
                       post_number: Optional[int] = None,
                       generation_time: Optional[float] = None,
                       success: bool = True,
                       error_message: Optional[str] = None) -> ApiCallCost:
        """Track a single API call and calculate its cost"""
        
        if call_type == "text_generation":
            costs = self.calculate_text_cost(model, input_tokens, output_tokens, provider)
            input_cost = costs["input_cost"]
            output_cost = costs["output_cost"]
            total_cost = costs["total_cost"]
        else:
            input_cost = 0.0
            output_cost = 0.0
            total_cost = self.calculate_image_cost(model, image_count)
        
        record = ApiCallCost(
            timestamp=datetime.utcnow().isoformat() + "Z",
            agent_name=agent_name,
            model=model,
            provider=provider,
            call_type=call_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            image_count=image_count,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            batch_id=batch_id,
            post_number=post_number,
            generation_time_seconds=generation_time,
            success=success,
            error_message=error_message
        )
        
        self.api_calls.append(record)
        self._update_daily_summary(record)
        self._save_data()
        
        self.logger.info(
            f"Tracked API call",
            agent=agent_name,
            model=model,
            cost=f"${total_cost:.6f}",
            tokens=input_tokens + output_tokens if call_type == "text_generation" else 0,
            images=image_count if call_type == "image_generation" else 0
        )
        
        return record
    
    def _update_daily_summary(self, record: ApiCallCost):
        """Update daily cost summary with new record"""
        date = record.timestamp[:10]
        
        if date not in self.daily_costs:
            self.daily_costs[date] = DailyCostSummary(date=date)
        
        summary = self.daily_costs[date]
        summary.total_cost += record.total_cost
        
        if record.provider == "openai":
            summary.openai_cost += record.total_cost
        else:
            summary.gemini_cost += record.total_cost
        
        if record.call_type == "text_generation":
            summary.text_generation_cost += record.total_cost
            summary.total_input_tokens += record.input_tokens
            summary.total_output_tokens += record.output_tokens
        else:
            summary.image_generation_cost += record.total_cost
            summary.images_generated += record.image_count
        
        summary.api_calls += 1
    
    def finalize_post_cost(self, batch_id: str, post_number: int) -> Optional[PostCostSummary]:
        """Calculate total cost for a completed post"""
        post_calls = [
            call for call in self.api_calls
            if call.batch_id == batch_id and call.post_number == post_number
        ]
        
        if not post_calls:
            self.logger.warning(f"No API calls found for post {batch_id}-{post_number}")
            return None
        
        summary = PostCostSummary(
            batch_id=batch_id,
            post_number=post_number,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        for call in post_calls:
            summary.total_cost += call.total_cost
            summary.total_input_tokens += call.input_tokens
            summary.total_output_tokens += call.output_tokens
            summary.total_tokens += call.total_tokens
            summary.api_calls += 1
            
            if "content" in call.agent_name.lower() or "generator" in call.agent_name.lower():
                summary.content_generation_cost += call.total_cost
            elif "image" in call.agent_name.lower():
                summary.image_generation_cost += call.total_cost
            elif any(name in call.agent_name.lower() for name in ["sarah", "marcus", "jordan", "validator"]):
                summary.validation_cost += call.total_cost
            elif "feedback" in call.agent_name.lower() or "aggregator" in call.agent_name.lower():
                summary.feedback_cost += call.total_cost
        
        self.post_costs.append(summary)
        
        date = summary.timestamp[:10]
        if date in self.daily_costs:
            self.daily_costs[date].posts_generated += 1
        
        self._save_data()
        
        self.logger.info(
            f"Finalized post cost",
            batch_id=batch_id,
            post_number=post_number,
            total_cost=f"${summary.total_cost:.4f}",
            api_calls=summary.api_calls
        )
        
        return summary
    
    def get_total_spent(self) -> float:
        """Get total amount spent across all time"""
        return round(sum(call.total_cost for call in self.api_calls), 4)
    
    def get_daily_summary(self, date: Optional[str] = None) -> Optional[DailyCostSummary]:
        """Get cost summary for a specific date"""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        return self.daily_costs.get(date)
    
    def get_date_range_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for the last N days"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        relevant_calls = [
            call for call in self.api_calls
            if start_date.isoformat() <= call.timestamp <= end_date.isoformat()
        ]
        
        total_cost = sum(call.total_cost for call in relevant_calls)
        openai_cost = sum(call.total_cost for call in relevant_calls if call.provider == "openai")
        gemini_cost = sum(call.total_cost for call in relevant_calls if call.provider == "google")
        
        text_cost = sum(call.total_cost for call in relevant_calls if call.call_type == "text_generation")
        image_cost = sum(call.total_cost for call in relevant_calls if call.call_type == "image_generation")
        
        return {
            "period": f"Last {days} days",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_cost": round(total_cost, 4),
            "openai_cost": round(openai_cost, 4),
            "gemini_cost": round(gemini_cost, 4),
            "text_generation_cost": round(text_cost, 4),
            "image_generation_cost": round(image_cost, 4),
            "api_calls": len(relevant_calls),
            "avg_cost_per_call": round(total_cost / len(relevant_calls), 4) if relevant_calls else 0
        }
    
    def get_post_costs(self, limit: int = 10) -> List[PostCostSummary]:
        """Get recent post cost summaries"""
        return sorted(self.post_costs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        total_calls = len(self.api_calls)
        total_posts = len(self.post_costs)
        
        if total_calls == 0:
            return {
                "total_api_calls": 0,
                "total_posts": 0,
                "total_spent": 0.0,
                "avg_cost_per_post": 0.0,
                "avg_cost_per_call": 0.0
            }
        
        total_spent = self.get_total_spent()
        
        return {
            "total_api_calls": total_calls,
            "total_posts": total_posts,
            "total_spent": total_spent,
            "avg_cost_per_post": round(total_spent / total_posts, 4) if total_posts > 0 else 0.0,
            "avg_cost_per_call": round(total_spent / total_calls, 4),
            "openai_calls": sum(1 for c in self.api_calls if c.provider == "openai"),
            "gemini_calls": sum(1 for c in self.api_calls if c.provider == "google"),
            "text_generation_calls": sum(1 for c in self.api_calls if c.call_type == "text_generation"),
            "image_generation_calls": sum(1 for c in self.api_calls if c.call_type == "image_generation"),
            "total_tokens": sum(c.total_tokens for c in self.api_calls),
            "total_images": sum(c.image_count for c in self.api_calls)
        }


# Global singleton
_cost_tracker_instance: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    """Get or create the global cost tracker instance"""
    global _cost_tracker_instance
    
    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker()
    
    return _cost_tracker_instance