"""
Wizard API Routes - Guided content creation endpoints
Provides progressive disclosure wizard for single-post generation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()

# Create router
router = APIRouter(prefix="/api/wizard", tags=["wizard"])

# ==================================================================================
# Pydantic Models for Request/Response
# ==================================================================================

class BrandSettingsRequest(BaseModel):
    """Step 1: Brand settings from user sliders"""
    tone_slider: int = Field(..., ge=0, le=100, description="0=Wakadoo, 100=Formal")
    pithiness_slider: int = Field(..., ge=0, le=100, description="0=Offensive, 100=Baroque")
    jargon_slider: int = Field(..., ge=0, le=100, description="0=Low jargon, 100=VC-speak")
    custom_additions: str = Field(default="", description="Free-form brand customization")


class InspirationSelection(BaseModel):
    """Step 2: User-selected inspiration base"""
    type: str = Field(..., description="news, meme, philosopher, or poet")
    selected_id: str = Field(..., description="ID of the selected item")


class StylePreferences(BaseModel):
    """Step 3: Length and style preferences"""
    length: str = Field(..., description="very_short, short, medium, or long")
    style_flags: List[str] = Field(
        default=[],
        description="Optional: contrarian, data_led, story_first, human_potential, etc."
    )


class BuyerPersonaRequest(BaseModel):
    """Step 4: Optional buyer persona for validation"""
    title: str = Field(..., description="Job title")
    company_size: str = Field(..., description="Startup, SMB, Enterprise, etc.")
    sector: str = Field(..., description="Tech, Finance, Healthcare, etc.")
    region: str = Field(default="", description="Geographic region")
    goals: List[str] = Field(default=[], description="Professional goals")
    risk_tolerance: str = Field(default="Moderate", description="Conservative, Moderate, Aggressive")
    decision_criteria: List[str] = Field(default=[], description="What drives their decisions")
    personality: str = Field(default="", description="Fun, Angry, Working on myself, Super Chill, Grinding")
    tone_resonance: str = Field(default="", description="Analytical, Visionary, Skeptical, Pragmatic")


class WizardGenerateRequest(BaseModel):
    """Complete wizard state for generation"""
    brand_settings: BrandSettingsRequest
    inspiration_selections: List[InspirationSelection] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="1-3 selected inspiration bases"
    )
    style_preferences: StylePreferences
    buyer_persona: Optional[BuyerPersonaRequest] = None


# ==================================================================================
# Helper Functions
# ==================================================================================

def _initialize_wizard_components():
    """
    Initialize wizard orchestrator and dependencies
    Lazy initialization to avoid circular imports
    """
    from src.infrastructure.config.config_manager import AppConfig
    from src.domain.agents.base_agent import AgentConfig
    from src.domain.services.wizard_orchestrator import WizardOrchestrator
    from src.domain.agents.advanced_content_generator import AdvancedContentGenerator
    from src.domain.agents.image_generation_agent import ImageGenerationAgent
    from src.domain.agents.validators.sarah_chen_validator import SarahChenValidator
    from src.domain.agents.validators.marcus_williams_validator import MarcusWilliamsValidator
    from src.domain.agents.validators.jordan_park_validator import JordanParkValidator
    from src.domain.agents.feedback_aggregator import FeedbackAggregator
    from src.domain.agents.revision_generator import RevisionGenerator
    
    # Check for real or mock AI client
    import os
    USE_REAL_API = os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your-openai-api-key-here"
    
    # Load configs
    app_config = AppConfig.from_yaml()
    agent_config = AgentConfig()
    
    # Create AI client
    if USE_REAL_API:
        from src.infrastructure.ai.openai_client import OpenAIClient
        ai_client = OpenAIClient(app_config)
    else:
        # Use mock client for development
        from tests.test_complete_system import MockAIClient
        ai_client = MockAIClient()
    
    # Initialize agents
    content_generator = AdvancedContentGenerator(agent_config, ai_client, app_config)
    image_generator = ImageGenerationAgent(agent_config, ai_client, app_config)
    
    validators = [
        SarahChenValidator(agent_config, ai_client, app_config),
        MarcusWilliamsValidator(agent_config, ai_client, app_config),
        JordanParkValidator(agent_config, ai_client, app_config)
    ]
    
    feedback_aggregator = FeedbackAggregator(agent_config, ai_client, app_config)
    revision_generator = RevisionGenerator(agent_config, ai_client, app_config)
    
    # Create wizard orchestrator
    orchestrator = WizardOrchestrator(
        content_generator=content_generator,
        image_generator=image_generator,
        validators=validators,
        feedback_aggregator=feedback_aggregator,
        revision_generator=revision_generator,
        config=app_config
    )
    
    return orchestrator


async def _fetch_inspiration_content(selections: List[InspirationSelection]) -> List[Any]:
    """Fetch actual content for selected inspiration bases"""
    from src.infrastructure.external.trending_fetcher import (
        TrendingNewsFetcher,
        TrendingMemeFetcher,
        PhilosophyDatabase,
        PoetryDatabase
    )
    from src.domain.services.wizard_orchestrator import InspirationBase
    
    news_fetcher = TrendingNewsFetcher()
    meme_fetcher = TrendingMemeFetcher()
    philosophy_db = PhilosophyDatabase()
    poetry_db = PoetryDatabase()
    
    inspiration_bases = []
    
    for selection in selections:
        try:
            if selection.type == "news":
                # Fetch all news and find the selected one
                all_news = await news_fetcher.fetch_trending()
                selected_news = next((n for n in all_news if n["id"] == selection.selected_id), None)
                
                if selected_news:
                    inspiration_bases.append(InspirationBase(
                        type="news",
                        content=selected_news["title"],
                        source=selected_news["source"],
                        context=selected_news.get("description", "")
                    ))
            
            elif selection.type == "meme":
                all_memes = await meme_fetcher.fetch_trending()
                selected_meme = next((m for m in all_memes if m["id"] == selection.selected_id), None)
                
                if selected_meme:
                    inspiration_bases.append(InspirationBase(
                        type="meme",
                        content=selected_meme["content"],
                        source=selected_meme["name"],
                        context=selected_meme["usage"]
                    ))
            
            elif selection.type == "philosopher":
                # Extract philosopher name from ID
                philosopher_name = selection.selected_id.replace("philosopher_", "").replace("_", " ").title()
                quotes = philosophy_db.get_philosopher_quotes(philosopher_name)
                
                if quotes:
                    # Use first quote or random
                    quote = quotes[0]
                    inspiration_bases.append(InspirationBase(
                        type="philosopher",
                        content=quote["text"],
                        source=philosopher_name,
                        context=quote["context"]
                    ))
            
            elif selection.type == "poet":
                # Extract poet name from ID
                poet_name = selection.selected_id.replace("poet_", "").replace("_", " ").title()
                excerpts = poetry_db.get_poet_excerpts(poet_name)
                
                if excerpts:
                    # Use first excerpt or random
                    excerpt = excerpts[0]
                    inspiration_bases.append(InspirationBase(
                        type="poet",
                        content=excerpt["text"],
                        source=poet_name,
                        context=excerpt["context"]
                    ))
        
        except Exception as e:
            logger.error(f"Failed to fetch inspiration content: {e}", selection=selection.dict())
            continue
    
    return inspiration_bases


# ==================================================================================
# API Routes
# ==================================================================================

@router.get("/inspiration-sources")
async def get_inspiration_sources():
    """
    Get all available inspiration sources for Step 2
    Returns: News, Memes, Philosophers, Poets
    """
    try:
        from src.infrastructure.external.trending_fetcher import (
            TrendingNewsFetcher,
            TrendingMemeFetcher,
            PhilosophyDatabase,
            PoetryDatabase
        )
        
        # Initialize fetchers
        news_fetcher = TrendingNewsFetcher()
        meme_fetcher = TrendingMemeFetcher()
        philosophy_db = PhilosophyDatabase()
        poetry_db = PoetryDatabase()
        
        # Fetch all sources
        news = await news_fetcher.fetch_trending(category="business", count=5)
        memes = await meme_fetcher.fetch_trending(count=8)
        philosophers = philosophy_db.get_all_philosophers()
        poets = poetry_db.get_all_poets()
        
        return {
            "ok": True,
            "sources": {
                "news": news,
                "memes": memes,
                "philosophers": philosophers,
                "poets": poets
            },
            "limits": {
                "min_selections": 1,
                "max_selections": 3
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch inspiration sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch inspiration sources: {str(e)}")


@router.get("/inspiration/{type}/{id}")
async def get_inspiration_detail(type: str, id: str):
    """
    Get detailed information about a specific inspiration source
    Useful for preview/expansion in the UI
    """
    try:
        from src.infrastructure.external.trending_fetcher import (
            TrendingNewsFetcher,
            TrendingMemeFetcher,
            PhilosophyDatabase,
            PoetryDatabase
        )
        
        if type == "news":
            fetcher = TrendingNewsFetcher()
            all_news = await fetcher.fetch_trending()
            item = next((n for n in all_news if n["id"] == id), None)
        
        elif type == "meme":
            fetcher = TrendingMemeFetcher()
            all_memes = await fetcher.fetch_trending()
            item = next((m for m in all_memes if m["id"] == id), None)
        
        elif type == "philosopher":
            db = PhilosophyDatabase()
            philosopher_name = id.replace("philosopher_", "").replace("_", " ").title()
            quotes = db.get_philosopher_quotes(philosopher_name)
            item = {"quotes": quotes, "name": philosopher_name} if quotes else None
        
        elif type == "poet":
            db = PoetryDatabase()
            poet_name = id.replace("poet_", "").replace("_", " ").title()
            excerpts = db.get_poet_excerpts(poet_name)
            item = {"excerpts": excerpts, "name": poet_name} if excerpts else None
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid inspiration type: {type}")
        
        if not item:
            raise HTTPException(status_code=404, detail=f"Inspiration source not found: {type}/{id}")
        
        return {"ok": True, "item": item}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch inspiration detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_wizard_post(request: WizardGenerateRequest):
    """
    Generate a single LinkedIn post from wizard inputs (Step 5)
    
    This is the main wizard endpoint that:
    1. Takes all wizard state (brand, inspiration, style, persona)
    2. Generates content using existing agents
    3. Validates with personas
    4. Generates image with CTA
    5. Returns complete post package
    """
    try:
        logger.info("wizard_generate_request_received",
                   inspiration_count=len(request.inspiration_selections),
                   length=request.style_preferences.length,
                   has_persona=request.buyer_persona is not None)
        
        # Initialize wizard orchestrator
        orchestrator = _initialize_wizard_components()
        
        # Fetch actual inspiration content
        inspiration_bases = await _fetch_inspiration_content(request.inspiration_selections)
        
        if not inspiration_bases:
            raise HTTPException(
                status_code=400,
                detail="No valid inspiration sources found. Please select at least one."
            )
        
        # Convert Pydantic models to dataclasses
        from src.domain.services.wizard_orchestrator import (
            BrandSettings,
            BuyerPersona
        )
        
        brand_settings = BrandSettings(
            tone_slider=request.brand_settings.tone_slider,
            pithiness_slider=request.brand_settings.pithiness_slider,
            jargon_slider=request.brand_settings.jargon_slider,
            custom_additions=request.brand_settings.custom_additions
        )
        
        buyer_persona = None
        if request.buyer_persona:
            buyer_persona = BuyerPersona(
                title=request.buyer_persona.title,
                company_size=request.buyer_persona.company_size,
                sector=request.buyer_persona.sector,
                region=request.buyer_persona.region,
                goals=request.buyer_persona.goals,
                risk_tolerance=request.buyer_persona.risk_tolerance,
                decision_criteria=request.buyer_persona.decision_criteria,
                personality=request.buyer_persona.personality,
                tone_resonance=request.buyer_persona.tone_resonance
            )
        
        # Generate post using wizard orchestrator
        result = await orchestrator.generate_from_wizard(
            brand_settings=brand_settings,
            inspiration_bases=inspiration_bases,
            length=request.style_preferences.length,
            style_flags=request.style_preferences.style_flags,
            buyer_persona=buyer_persona
        )
        
        logger.info("wizard_generate_success",
                   session_id=result["metadata"]["session_id"],
                   has_image=bool(result["post"]["image_url"]),
                   validation_approved=result["validation"]["approved"])
        
        return {
            "ok": True,
            **result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wizard generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/stats")
async def get_wizard_stats():
    """
    Get wizard usage statistics
    Useful for analytics dashboard
    """
    try:
        # This would normally query from a database or cache
        # For now, return placeholder stats
        return {
            "ok": True,
            "stats": {
                "total_generated": 0,
                "total_with_persona": 0,
                "revision_rate": 0.0,
                "average_generation_time": 0.0,
                "popular_inspiration_types": {
                    "news": 0,
                    "memes": 0,
                    "philosophers": 0,
                    "poets": 0
                }
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch wizard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brand-defaults")
async def get_brand_defaults():
    """
    Get default brand settings for Step 1
    Returns current brand configuration from AppConfig
    """
    try:
        from src.infrastructure.config.config_manager import AppConfig
        
        config = AppConfig.from_yaml()
        
        return {
            "ok": True,
            "brand": {
                "product_name": config.brand.product_name,
                "price": config.brand.price,
                "tagline": config.brand.tagline,
                "ritual": config.brand.ritual,
                "target_audience": config.brand.target_audience,
                "voice_attributes": config.brand.voice_attributes
            },
            "default_sliders": {
                "tone_slider": 50,  # Mid-range: balanced
                "pithiness_slider": 50,  # Mid-range: balanced
                "jargon_slider": 30  # Lower: keep it accessible
            }
        }
    except Exception as e:
        logger.error(f"Failed to fetch brand defaults: {e}")
        raise HTTPException(status_code=500, detail=str(e))