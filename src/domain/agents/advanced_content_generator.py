"""
Advanced Content Generator - Multi-element combination with story arcs
Generates LinkedIn posts using layered cultural references and workplace themes
"""

import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.domain.models.post import LinkedInPost, CulturalReference
from src.infrastructure.config.config_manager import AppConfig
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class StoryArc:
    """Different narrative arcs for posts"""
    name: str
    structure: str
    
    # Predefined arcs
    HERO_JOURNEY = ("HERO_JOURNEY", "Problem → Struggle → Solution → Transformation")
    FALSE_SUMMIT = ("FALSE_SUMMIT", "Success → Reality Check → Real Solution")
    ORIGIN_STORY = ("ORIGIN_STORY", "Before → Catalyst → After")
    CURRENT_REALITY = ("CURRENT_REALITY", "Universal Truth → Product as Answer")


@dataclass
class PostLength:
    """Different post length targets"""
    name: str
    target_words: int
    
    # Predefined lengths
    HAIKU = ("HAIKU", 50)  # Ultra-short, punchy
    TWEET = ("TWEET", 100)  # Twitter-length
    STANDARD = ("STANDARD", 150)  # LinkedIn sweet spot
    ESSAY = ("ESSAY", 250)  # Longer form


class AdvancedContentGenerator(BaseAgent):
    """
    Generates LinkedIn posts by combining multiple cultural/workplace elements
    with varied story arcs and lengths for maximum diversity
    """
    
    def __init__(self, config: AgentConfig, ai_client, app_config: AppConfig):
        """Initialize the content generator"""
        super().__init__("AdvancedContentGenerator", config, ai_client)
        
        self.brand_config = app_config.brand
        self.cultural_refs = app_config.cultural_references
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
        self.logger.info("AdvancedContentGenerator initialized",
                        brand=self.brand_config.product_name,
                        has_custom_prompts=self.prompt_manager.has_custom_prompts("AdvancedContentGenerator"))
        
        # Story arcs and lengths
        self.story_arcs = [
            StoryArc(*StoryArc.HERO_JOURNEY),
            StoryArc(*StoryArc.FALSE_SUMMIT),
            StoryArc(*StoryArc.ORIGIN_STORY),
            StoryArc(*StoryArc.CURRENT_REALITY)
        ]
        
        self.post_lengths = [
            PostLength(*PostLength.HAIKU),
            PostLength(*PostLength.TWEET),
            PostLength(*PostLength.STANDARD),
            PostLength(*PostLength.ESSAY)
        ]
    
    async def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate multiple LinkedIn posts with varied elements
        
        Args:
            input_data: Contains batch_id, count, brand_context, avoid_patterns (optional)
        
        Returns:
            List of post data dictionaries
        """
        batch_id = input_data.get("batch_id")
        count = input_data.get("count", 1)
        avoid_patterns = input_data.get("avoid_patterns", {})
        
        self.logger.info("Starting content generation with images",
                        batch_id=batch_id,
                        count=count)
        
        posts = []
        for i in range(count):
            self.logger.info(f"Generating post {i+1}/{count} with image")
            post = await self._generate_single_post(batch_id, i + 1, avoid_patterns)
            posts.append(post)
        
        return posts
    
    async def _generate_single_post(self, batch_id: str, post_number: int, 
                                    avoid_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single post with multi-element combination"""
        
        # Select random elements
        selected_elements = self._select_elements(avoid_patterns)
        story_arc = random.choice(self.story_arcs)
        length = random.choice(self.post_lengths)
        
        self.logger.info("Post generation parameters",
                        post_number=post_number,
                        elements=selected_elements["names"],
                        story_arc=story_arc.name,
                        length=length.name)
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            selected_elements, 
            story_arc, 
            length,
            avoid_patterns
        )
        
        # Generate content
        response = await self._call_ai(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format="json"
        )
        
        content_data = response.get("content", {})
        
        # Ensure we have valid content
        if not content_data or "content" not in content_data:
            self.logger.warning("Empty response from AI, using fallback")
            content_data = self._create_fallback_post(selected_elements)
        
        # Add metadata
        content_data["post_number"] = post_number
        content_data["batch_id"] = batch_id
        content_data["generation_metadata"] = {
            "elements_used": selected_elements["names"],
            "story_arc": story_arc.name,
            "target_length": length.target_words,
            "actual_length": len(content_data.get("content", "").split())
        }
        
        return content_data
    
    def _select_elements(self, avoid_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select 2-3 random elements to combine in the post
        Avoids patterns that previously failed
        """
        failed_refs = avoid_patterns.get("cultural_references_failed", [])
        
        # Get available references
        available_tv = [tv for tv in self.cultural_refs.tv_shows if tv not in failed_refs]
        available_workplace = [w for w in self.cultural_refs.workplace_themes if w not in failed_refs]
        available_seasonal = [s for s in self.cultural_refs.seasonal_themes if s not in failed_refs]
        
        # If we've failed too many, reset
        if len(available_tv) < 2:
            available_tv = self.cultural_refs.tv_shows
        if len(available_workplace) < 2:
            available_workplace = self.cultural_refs.workplace_themes
        if len(available_seasonal) < 2:
            available_seasonal = self.cultural_refs.seasonal_themes
        
        # Randomly select combination approach
        combo_type = random.choice([
            "tv_workplace",      # TV show + workplace theme
            "tv_seasonal",       # TV show + seasonal theme
            "workplace_seasonal", # Workplace + seasonal
            "triple"             # All three (rare)
        ])
        
        elements = {}
        
        if combo_type == "tv_workplace":
            elements = {
                "tv_show": random.choice(available_tv),
                "workplace_theme": random.choice(available_workplace),
                "names": [random.choice(available_tv), random.choice(available_workplace)]
            }
        elif combo_type == "tv_seasonal":
            elements = {
                "tv_show": random.choice(available_tv),
                "seasonal_theme": random.choice(available_seasonal),
                "names": [random.choice(available_tv), random.choice(available_seasonal)]
            }
        elif combo_type == "workplace_seasonal":
            elements = {
                "workplace_theme": random.choice(available_workplace),
                "seasonal_theme": random.choice(available_seasonal),
                "names": [random.choice(available_workplace), random.choice(available_seasonal)]
            }
        else:  # triple
            elements = {
                "tv_show": random.choice(available_tv),
                "workplace_theme": random.choice(available_workplace),
                "seasonal_theme": random.choice(available_seasonal),
                "names": [
                    random.choice(available_tv),
                    random.choice(available_workplace),
                    random.choice(available_seasonal)
                ]
            }
        
        return elements
    
    def _build_system_prompt(self) -> str:
        """Build the comprehensive system prompt for content generation"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("AdvancedContentGenerator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for AdvancedContentGenerator")
            return custom_prompts["system_prompt"]
        
        # Otherwise use default
        return f"""You are an expert LinkedIn content creator for {self.brand_config.product_name}.

BRAND CONTEXT:
- Product: {self.brand_config.product_name} - premium business lip balm
- Price: {self.brand_config.price}
- Tagline: {self.brand_config.tagline}
- Ritual: {self.brand_config.ritual}
- Target Audience: {self.brand_config.target_audience}

BRAND VOICE: {', '.join(self.brand_config.voice_attributes)}

YOUR MISSION:
Create LinkedIn posts that make professionals stop scrolling. Use cultural references (TV shows, workplace situations, seasonal themes) to create instant recognition and connection. The goal is to make expensive lip balm feel like a necessary business tool through absurdist modern luxury.

CONTENT STRATEGY:
1. Hook with cultural reference or workplace truth
2. Connect to the daily grind/struggle
3. Present the product as ritual/solution
4. End with human-first message

TONE: Wry, self-aware, premium but accessible. Think: "Mad Men meets Silicon Valley meets your group chat."

Remember: Balance authenticity with premium positioning. Make it feel human, not corporate."""
    
    def _build_user_prompt(self, elements: Dict[str, Any], arc: StoryArc, 
                          length: PostLength, avoid_patterns: Dict[str, Any]) -> str:
        """Build the user prompt with specific generation instructions"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("AdvancedContentGenerator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for AdvancedContentGenerator")
            # Use custom template (will need to format it with the variables)
            return custom_prompts["user_prompt_template"]
        
        # Build element description
        element_desc = []
        if "tv_show" in elements:
            element_desc.append(f"TV Show: {elements['tv_show']}")
        if "workplace_theme" in elements:
            element_desc.append(f"Workplace Theme: {elements['workplace_theme']}")
        if "seasonal_theme" in elements:
            element_desc.append(f"Seasonal Theme: {elements['seasonal_theme']}")
        
        elements_str = "\n".join(element_desc)
        
        # Build avoid patterns section
        avoid_section = ""
        if avoid_patterns:
            issues = []
            for key, values in avoid_patterns.items():
                if values and key != "common_feedback":
                    issues.append(f"- Avoid: {', '.join(values[:2])}")
            if issues:
                avoid_section = "\n\nPATTERNS TO AVOID:\n" + "\n".join(issues)
        
        return f"""Generate a LinkedIn post combining these elements:

{elements_str}

STORY ARC: {arc.name}
Structure: {arc.structure}

TARGET LENGTH: ~{length.target_words} words ({length.name})

REQUIREMENTS:
1. Weave the elements together naturally (don't force them)
2. Follow the {arc.name} arc structure
3. Keep it around {length.target_words} words
4. Include product name, price, and ritual
5. End with relevant hashtags (3-5)
6. Make it feel human, not like marketing{avoid_section}

Return JSON with:
{{
    "content": "The full post text with hashtags",
    "hook": "The opening line/hook",
    "target_audience": "Who this speaks to",
    "cultural_reference": {{
        "category": "tv_show/workplace/seasonal",
        "reference": "The main reference used",
        "context": "Why it resonates"
    }},
    "hashtags": ["tag1", "tag2", "tag3"]
}}"""
    
    def _create_fallback_post(self, elements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple fallback post if AI generation fails"""
        
        ref = elements.get("tv_show") or elements.get("workplace_theme") or "the daily grind"
        
        return {
            "content": f"You know what {ref} taught us? Small rituals matter. {self.brand_config.product_name} ({self.brand_config.price}) - {self.brand_config.ritual}. Stay human in an AI world.\n\n#HumanFirst #WorkplaceWellness #PremiumSelfCare",
            "hook": f"You know what {ref} taught us?",
            "target_audience": self.brand_config.target_audience,
            "cultural_reference": {
                "category": "workplace",
                "reference": ref,
                "context": "Daily workplace reality"
            },
            "hashtags": ["HumanFirst", "WorkplaceWellness", "PremiumSelfCare"]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics"""
        base_stats = super().get_stats()
        
        base_stats.update({
            "brand": self.brand_config.product_name,
            "available_tv_shows": len(self.cultural_refs.tv_shows),
            "available_workplace_themes": len(self.cultural_refs.workplace_themes),
            "available_seasonal_themes": len(self.cultural_refs.seasonal_themes),
            "story_arcs": len(self.story_arcs),
            "post_lengths": len(self.post_lengths),
            "using_custom_prompts": self.prompt_manager.has_custom_prompts("AdvancedContentGenerator")
        })
        
        return base_stats