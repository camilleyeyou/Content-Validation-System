"""
Wizard API Routes - Guided content creation endpoints
Provides progressive disclosure wizard for single-post generation
UPDATED: Now uses NewsAPI for real news headlines
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

# Import news service
from src.infrastructure.news import get_news_service, format_news_for_wizard_display

logger = structlog.get_logger()

# Create router
router = APIRouter(tags=["wizard"])

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
    type: str = Field(..., description="news, philosopher, or poet")
    selected_id: str = Field(..., description="ID of the selected item")
    preview: Optional[Dict[str, Any]] = Field(default=None, description="Preview data from frontend")


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
    from src.domain.services.wizard_orchestrator import InspirationBase
    
    inspiration_bases = []
    
    for selection in selections:
        try:
            # If frontend provided preview data, use it
            if selection.preview:
                if selection.type == "news":
                    inspiration_bases.append(InspirationBase(
                        type="news",
                        content=selection.preview.get("title", ""),
                        source=selection.preview.get("source", ""),
                        context=selection.preview.get("description", "")
                    ))
                
                elif selection.type == "philosopher":
                    # Use philosopher data from preview
                    inspiration_bases.append(InspirationBase(
                        type="philosopher",
                        content=f"Philosophical wisdom from {selection.preview.get('name', 'ancient thinker')}",
                        source=selection.preview.get("name", selection.selected_id),
                        context=selection.preview.get("bio", "")
                    ))
                
                elif selection.type == "poet":
                    # Use poet data from preview
                    inspiration_bases.append(InspirationBase(
                        type="poet",
                        content=f"Poetic inspiration from {selection.preview.get('name', 'renowned poet')}",
                        source=selection.preview.get("name", selection.selected_id),
                        context=selection.preview.get("style", "")
                    ))
            
            else:
                # Fallback: Try to fetch from databases (if they exist)
                logger.warning("No preview data provided", selection=selection.dict())
                inspiration_bases.append(InspirationBase(
                    type=selection.type,
                    content=f"Selected {selection.type}: {selection.selected_id}",
                    source=selection.selected_id,
                    context=""
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
    Returns: News (from NewsAPI), Philosophers, Poets
    """
    try:
        # Get news from NewsService (cached for 24 hours)
        news_service = get_news_service()
        
        # Fetch recent tech and AI news
        tech_news = await news_service.get_tech_headlines(limit=10)
        ai_news = await news_service.get_ai_news(limit=5)
        
        # Combine and remove duplicates
        all_news = tech_news + ai_news
        seen_titles = set()
        unique_news = []
        for article in all_news:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                unique_news.append(article)
        
        # Format for wizard display
        news_items = format_news_for_wizard_display(unique_news[:12])
        
        # Philosophers (static data)
        philosophers = [
            {
                "id": "seneca",
                "name": "Seneca",
                "era": "4 BC - 65 AD",
                "bio": "Roman Stoic philosopher, statesman. Wisdom on resilience, virtue, and self-mastery.",
                "quote_count": 8
            },
            {
                "id": "epictetus",
                "name": "Epictetus",
                "era": "50-135 AD",
                "bio": "Stoic philosopher. Taught that philosophy is a way of life, not just theory.",
                "quote_count": 6
            },
            {
                "id": "marcus",
                "name": "Marcus Aurelius",
                "era": "121-180 AD",
                "bio": "Roman Emperor and Stoic philosopher. Meditations on leadership and duty.",
                "quote_count": 10
            },
            {
                "id": "nietzsche",
                "name": "Friedrich Nietzsche",
                "era": "1844-1900",
                "bio": "German philosopher. Explored power, morality, and human potential.",
                "quote_count": 7
            },
            {
                "id": "kierkegaard",
                "name": "Søren Kierkegaard",
                "era": "1813-1855",
                "bio": "Danish philosopher. Father of existentialism, focus on individual choice.",
                "quote_count": 5
            },
            {
                "id": "aristotle",
                "name": "Aristotle",
                "era": "384-322 BC",
                "bio": "Greek philosopher. Ethics, logic, and the pursuit of excellence.",
                "quote_count": 9
            }
        ]
        
        # Poets (static data)
        poets = [
            {
                "id": "oliver",
                "name": "Mary Oliver",
                "bio": "American poet. Nature, mindfulness, and attention to the present moment.",
                "style": "Contemplative, accessible, nature-focused"
            },
            {
                "id": "rumi",
                "name": "Rumi",
                "bio": "13th-century Persian poet. Love, spirituality, and human connection.",
                "style": "Mystical, passionate, transcendent"
            },
            {
                "id": "dickinson",
                "name": "Emily Dickinson",
                "bio": "American poet. Brief, powerful verses on life, death, and nature.",
                "style": "Concise, introspective, unconventional"
            },
            {
                "id": "frost",
                "name": "Robert Frost",
                "bio": "American poet. Rural life, choices, and the human condition.",
                "style": "Accessible, metaphorical, conversational"
            },
            {
                "id": "angelou",
                "name": "Maya Angelou",
                "bio": "American poet. Resilience, identity, and the human spirit.",
                "style": "Powerful, uplifting, rhythmic"
            },
            {
                "id": "neruda",
                "name": "Pablo Neruda",
                "bio": "Chilean poet. Passion, politics, and the beauty of everyday life.",
                "style": "Sensual, political, celebratory"
            }
        ]
        
        logger.info("inspiration_sources_served",
                   news_count=len(news_items),
                   philosopher_count=len(philosophers),
                   poet_count=len(poets))
        
        return {
            "ok": True,
            "sources": {
                "news": news_items,
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
        
        # Graceful fallback - return static sources only
        return {
            "ok": True,
            "sources": {
                "news": [],  # Empty if news fails
                "philosophers": [],
                "poets": []
            },
            "warning": f"News unavailable: {str(e)}"
        }


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