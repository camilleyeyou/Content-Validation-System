"""
Content Generator Agent - Creates LinkedIn posts with cultural references
"""

import json
import random
from typing import List, Dict, Any
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.domain.models.post import LinkedInPost, CulturalReference
from src.infrastructure.config.config_manager import AppConfig

class ContentGenerator(BaseAgent):
    """Generates LinkedIn posts with cultural references for Jesse A. Eisenbalm"""
    
    def __init__(self, config: AgentConfig, ai_client, app_config: AppConfig):
        super().__init__("ContentGenerator", config, ai_client)
        self.app_config = app_config
        self.brand = app_config.brand
        self.cultural_refs = app_config.cultural_references
        
    async def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a batch of LinkedIn posts"""
        batch_id = input_data.get("batch_id")
        count = input_data.get("count", 5)
        avoid_patterns = input_data.get("avoid_patterns", {})
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_generation_prompt(count, avoid_patterns)
        
        response = await self._call_ai(user_prompt, system_prompt)
        
        # Parse the response
        posts_data = self._parse_generation_response(response)
        
        # Enhance with metadata
        enhanced_posts = []
        for i, post_data in enumerate(posts_data, 1):
            post_data["batch_id"] = batch_id
            post_data["post_number"] = i
            enhanced_posts.append(post_data)
            
        return enhanced_posts
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for content generation"""
        return f"""You are an expert LinkedIn content creator for {self.brand.product_name}, a premium lip balm brand.

BRAND ESSENCE:
- Product: {self.brand.product_name} ({self.brand.price})
- Positioning: "{self.brand.tagline}"
- Ritual: "{self.brand.ritual}"
- Target: {self.brand.target_audience}
- Voice: {', '.join(self.brand.voice_attributes)}

YOUR MISSION:
Create LinkedIn posts that resonate with professionals dealing with AI workplace automation. Each post should:
1. Include a cultural reference that feels natural, not forced
2. Highlight the human ritual in an AI world
3. Be scroll-stopping without being salesy
4. Feel premium yet approachable
5. Include subtle product placement

CULTURAL REFERENCE CATEGORIES:
- TV Shows: {', '.join(self.cultural_refs.tv_shows)}
- Workplace: {', '.join(self.cultural_refs.workplace_themes)}
- Seasonal: {', '.join(self.cultural_refs.seasonal_themes)}

TONE: Wry, absurdist modern luxury, human-first, never preachy or overly promotional."""
    
    def _build_generation_prompt(self, count: int, avoid_patterns: Dict) -> str:
        """Build the user prompt for post generation"""
        avoid_section = ""
        if avoid_patterns:
            avoid_section = f"""
IMPORTANT - AVOID THESE PATTERNS:
- Common issues: {', '.join(avoid_patterns.get('common_issues', [])[:3])}
- Failed references: {', '.join(avoid_patterns.get('cultural_references_failed', [])[:3])}
"""
        
        return f"""Generate {count} LinkedIn posts for Jesse A. Eisenbalm lip balm.
{avoid_section}
REQUIREMENTS FOR EACH POST:
- Length: 150-200 words
- Include 1 cultural reference (subtle, natural)
- Start with engaging hook (no questions)
- Include the ritual "Stop. Breathe. Apply." naturally
- Mention price ({self.brand.price}) where appropriate
- End with 3-5 relevant hashtags
- Target different professional segments

OUTPUT FORMAT (valid JSON):
{{
    "posts": [
        {{
            "content": "Full post text with natural flow...",
            "hook": "The opening line that stops scrolling",
            "target_audience": "Specific professional segment",
            "cultural_reference": {{
                "category": "tv_show|workplace|seasonal",
                "reference": "The specific reference used",
                "context": "How it relates to the message"
            }},
            "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
        }}
    ]
}}

Create {count} unique, engaging posts that make professionals stop and think about staying human in an AI world."""
    
    def _parse_generation_response(self, response: Dict) -> List[Dict[str, Any]]:
        """Parse the AI response into post data"""
        try:
            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            
            posts = content.get("posts", [])
            
            # Validate and clean each post
            cleaned_posts = []
            for post in posts:
                cleaned_post = {
                    "content": post.get("content", ""),
                    "hook": post.get("hook", ""),
                    "target_audience": post.get("target_audience", "LinkedIn professionals"),
                    "hashtags": post.get("hashtags", []),
                    "cultural_reference": None
                }
                
                # Process cultural reference
                if "cultural_reference" in post:
                    ref = post["cultural_reference"]
                    cleaned_post["cultural_reference"] = CulturalReference(
                        category=ref.get("category", "workplace"),
                        reference=ref.get("reference", ""),
                        context=ref.get("context", "")
                    )
                
                cleaned_posts.append(cleaned_post)
            
            return cleaned_posts
            
        except Exception as e:
            self.logger.error("Failed to parse generation response", error=str(e))
            return []