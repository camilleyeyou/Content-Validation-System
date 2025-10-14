# portal/backend/app/prompts_routes.py
"""
API routes for prompt management
Fixed for deployment with ImageGenerationAgent support
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Setup paths (similar to main.py)
CURRENT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = CURRENT_DIR.parent.resolve()
PORTAL_DIR = BACKEND_DIR.parent.resolve()
PROJECT_ROOT = PORTAL_DIR.parent.resolve()

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Now import from src
from src.infrastructure.prompts.prompt_manager import get_prompt_manager

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

# Pydantic models
class PromptUpdate(BaseModel):
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None

class AgentPromptResponse(BaseModel):
    agent_name: str
    has_custom: bool
    system_prompt: str
    user_prompt_template: str
    default_system_prompt: str
    default_user_prompt_template: str

class AgentInfo(BaseModel):
    name: str
    description: str
    has_custom_prompts: bool


# Agent registry with ImageGenerationAgent
AGENT_REGISTRY = {
    "AdvancedContentGenerator": {
        "class": "AdvancedContentGenerator",
        "description": "Generates LinkedIn posts using multi-element combination"
    },
    "ImageGenerationAgent": {
        "class": "ImageGenerationAgent",
        "description": "Generates professional product images using Google Gemini 2.5 Flash"
    },
    "JordanParkValidator": {
        "class": "JordanParkValidator",
        "description": "Social media expert - validates engagement potential"
    },
    "SarahChenValidator": {
        "class": "SarahChenValidator",
        "description": "Customer perspective - validates authenticity"
    },
    "MarcusWilliamsValidator": {
        "class": "MarcusWilliamsValidator",
        "description": "Business perspective - validates brand positioning"
    },
    "FeedbackAggregator": {
        "class": "FeedbackAggregator",
        "description": "Aggregates validator feedback for improvements"
    },
    "RevisionGenerator": {
        "class": "RevisionGenerator",
        "description": "Generates revised posts based on feedback"
    }
}


def get_agent_default_prompts(agent_name: str) -> Dict[str, str]:
    """Get default prompts from agent class"""
    try:
        from src.domain.agents.base_agent import AgentConfig
        from src.infrastructure.config.config_manager import AppConfig
        
        # Mock AI client
        class MockAIClient:
            async def generate(self, **kwargs):
                return {"content": {}, "usage": {"total_tokens": 0}}
            async def generate_image(self, **kwargs):
                return {"image_data": b"mock", "saved_path": "mock.png"}
        
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        if agent_name == "AdvancedContentGenerator":
            from src.domain.agents.advanced_content_generator import AdvancedContentGenerator
            agent = AdvancedContentGenerator(agent_config, mock_client, app_config)
            return {
                "system_prompt": agent._build_system_prompt(),
                "user_prompt_template": "Generation prompt template (dynamic - varies by elements, arc, and length)"
            }
        
        elif agent_name == "ImageGenerationAgent":
            from src.domain.agents.image_generation_agent import ImageGenerationAgent
            from src.domain.models.post import LinkedInPost, CulturalReference
            agent = ImageGenerationAgent(agent_config, mock_client, app_config)
            dummy_post = LinkedInPost(
                id="dummy",
                batch_id="template_batch",
                post_number=1,
                content="Sample post about Jesse A. Eisenbalm premium lip balm for LinkedIn professionals.",
                hashtags=["Test", "Sample"],
                target_audience="Tech professionals",
                cultural_reference=CulturalReference(
                    category="workplace",
                    reference="Sample Reference",
                    context="test context"
                )
            )
            return {
                "system_prompt": agent._build_system_prompt(),
                "user_prompt_template": f"""Create a detailed image prompt for a professional product photograph.

Post content:
{{content}}

Product: Jesse A. Eisenbalm (premium lip balm)
Brand colors: Navy blue, gold accents, cream
Aesthetic: Luxury, professional, sophisticated

Create a DETAILED image prompt for professional product photography."""
            }
        
        elif agent_name == "JordanParkValidator":
            from src.domain.agents.validators.jordan_park_validator import JordanParkValidator
            from src.domain.models.post import LinkedInPost, CulturalReference
            agent = JordanParkValidator(agent_config, mock_client, app_config)
            dummy_post = LinkedInPost(
                id="dummy",
                batch_id="template_batch",
                post_number=1,
                content="Sample post content for template extraction. This needs to be at least 50 characters long to pass validation.",
                hashtags=["Test", "Sample"],
                target_audience="Tech professionals",
                cultural_reference=CulturalReference(
                    category="workplace",
                    reference="Sample Reference",
                    context="test context"
                )
            )
            return {
                "system_prompt": agent._build_system_prompt(),
                "user_prompt_template": agent._build_validation_prompt(dummy_post)
            }
        
        elif agent_name == "SarahChenValidator":
            from src.domain.agents.validators.sarah_chen_validator import SarahChenValidator
            from src.domain.models.post import LinkedInPost, CulturalReference
            agent = SarahChenValidator(agent_config, mock_client, app_config)
            dummy_post = LinkedInPost(
                id="dummy",
                batch_id="template_batch",
                post_number=1,
                content="Sample post content for template extraction. This needs to be at least 50 characters long.",
                hashtags=["Test"],
                target_audience="Tech professionals",
                cultural_reference=CulturalReference(
                    category="workplace",
                    reference="Sample Reference",
                    context="test"
                )
            )
            return {
                "system_prompt": agent._build_system_prompt(),
                "user_prompt_template": agent._build_validation_prompt(dummy_post)
            }
        
        elif agent_name == "MarcusWilliamsValidator":
            from src.domain.agents.validators.marcus_williams_validator import MarcusWilliamsValidator
            from src.domain.models.post import LinkedInPost, CulturalReference
            agent = MarcusWilliamsValidator(agent_config, mock_client, app_config)
            dummy_post = LinkedInPost(
                id="dummy",
                batch_id="template_batch",
                post_number=1,
                content="Sample post content for template extraction. This needs to be at least 50 characters long.",
                hashtags=["Test"],
                target_audience="Tech professionals",
                cultural_reference=CulturalReference(
                    category="workplace",
                    reference="Sample Reference",
                    context="test"
                )
            )
            return {
                "system_prompt": agent._build_system_prompt(),
                "user_prompt_template": agent._build_validation_prompt(dummy_post)
            }
        
        elif agent_name == "FeedbackAggregator":
            from src.domain.agents.feedback_aggregator import FeedbackAggregator
            from src.domain.models.post import LinkedInPost
            agent = FeedbackAggregator(agent_config, mock_client, app_config)
            dummy_post = LinkedInPost(
                id="dummy",
                batch_id="template_batch",
                post_number=1,
                content="Sample post content for template extraction. This needs to be at least 50 characters long.",
                hashtags=["Test"],
                target_audience="Tech professionals"
            )
            return {
                "system_prompt": agent._build_system_prompt(),
                "user_prompt_template": agent._build_aggregation_prompt(dummy_post)
            }
        
        elif agent_name == "RevisionGenerator":
            from src.domain.agents.revision_generator import RevisionGenerator
            from src.domain.models.post import LinkedInPost
            agent = RevisionGenerator(agent_config, mock_client, app_config)
            dummy_post = LinkedInPost(
                id="dummy",
                batch_id="template_batch",
                post_number=1,
                content="Sample post content for template extraction. This needs to be at least 50 characters long.",
                hashtags=["Test"],
                target_audience="Tech professionals"
            )
            dummy_feedback = {
                "main_issues": ["Issue 1", "Issue 2"],
                "priority_fix": "Fix hook",
                "specific_improvements": {"hook": "Make stronger"},
                "keep_these_elements": ["Brand voice"],
                "revised_hook_suggestion": "Try this hook",
                "tone_adjustment": "More casual"
            }
            return {
                "system_prompt": agent._build_system_prompt(),
                "user_prompt_template": agent._build_revision_prompt(dummy_post, dummy_feedback)
            }
        
        else:
            return {
                "system_prompt": "Agent not found",
                "user_prompt_template": "Agent not found"
            }
    
    except Exception as e:
        import traceback
        error_detail = f"Error loading agent: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        return {
            "system_prompt": f"Error loading agent: {str(e)}",
            "user_prompt_template": f"Error loading agent: {str(e)}"
        }


@router.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all available agents"""
    prompt_manager = get_prompt_manager()
    agents_with_custom = prompt_manager.list_agents_with_custom_prompts()
    
    return [
        AgentInfo(
            name=name,
            description=info["description"],
            has_custom_prompts=name in agents_with_custom
        )
        for name, info in AGENT_REGISTRY.items()
    ]


@router.get("/{agent_name}", response_model=AgentPromptResponse)
async def get_agent_prompts(agent_name: str):
    """Get prompts for a specific agent"""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    prompt_manager = get_prompt_manager()
    custom_prompts = prompt_manager.get_agent_prompts(agent_name)
    default_prompts = get_agent_default_prompts(agent_name)
    
    return AgentPromptResponse(
        agent_name=agent_name,
        has_custom=prompt_manager.has_custom_prompts(agent_name),
        system_prompt=custom_prompts.get("system_prompt") or default_prompts["system_prompt"],
        user_prompt_template=custom_prompts.get("user_prompt_template") or default_prompts["user_prompt_template"],
        default_system_prompt=default_prompts["system_prompt"],
        default_user_prompt_template=default_prompts["user_prompt_template"]
    )


@router.put("/{agent_name}")
async def update_agent_prompts(agent_name: str, prompts: PromptUpdate):
    """Update custom prompts for an agent"""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    prompt_manager = get_prompt_manager()
    
    update_dict = {}
    if prompts.system_prompt is not None:
        update_dict["system_prompt"] = prompts.system_prompt
    if prompts.user_prompt_template is not None:
        update_dict["user_prompt_template"] = prompts.user_prompt_template
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No prompts provided")
    
    try:
        prompt_manager.set_agent_prompts(agent_name, update_dict)
        return {"success": True, "message": f"Updated prompts for {agent_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_name}")
async def reset_agent_prompts(agent_name: str):
    """Reset agent to use default prompts"""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
    
    prompt_manager = get_prompt_manager()
    
    if prompt_manager.reset_agent_prompts(agent_name):
        return {"success": True, "message": f"Reset {agent_name} to default prompts"}
    else:
        return {"success": True, "message": f"{agent_name} was already using default prompts"}


@router.get("/")
async def list_all_prompts():
    """List all agents and their custom prompt status"""
    prompt_manager = get_prompt_manager()
    return {
        "agents": list(AGENT_REGISTRY.keys()),
        "custom_prompts": prompt_manager.get_all_prompts()
    }