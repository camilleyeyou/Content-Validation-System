"""
Social Media Validator Agent - Evaluates from LinkedIn engagement specialist perspective
"""

import json
from typing import Dict, Any
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class SocialMediaValidator(BaseAgent):
    """Validates posts from a LinkedIn engagement specialist perspective"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("SocialMediaValidator", config, ai_client)
        self.app_config = app_config
        
    async def process(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from social media perspective"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_validation_prompt(post)
        
        response = await self._call_ai(user_prompt, system_prompt)
        
        return self._parse_validation_response(response)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for social media validation"""
        return """You are a LinkedIn Engagement Specialist who's managed 100+ brand accounts.

YOUR REALITY:
"LinkedIn users scroll past 99% of content. Only exceptional posts stop the scroll. Most brand content gets ignored."

YOUR EXPERTISE:
- Know LinkedIn's algorithm inside out
- Managed viral B2B campaigns
- Understand professional audience psychology
- Track what actually drives engagement vs. vanity metrics

SCORING CRITERIA (0-10):
1. Hook Effectiveness (40%): Will this stop the scroll in under 2 seconds?
2. Engagement Potential (35%): Will professionals actually interact?
3. Shareability (25%): Would someone risk their professional reputation to share this?

KEY EVALUATION POINTS:
- First 2 lines make or break the post
- Cultural references must land instantly
- LinkedIn rewards dwell time and meaningful comments
- Hashtag strategy and discoverability
- The "cringe test" - would professionals share this?

APPROVAL THRESHOLD: Score 7+ means this could actually perform well on LinkedIn."""
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for validation"""
        hashtags = " ".join([f"#{tag}" for tag in post.hashtags]) if post.hashtags else "No hashtags"
        
        return f"""Evaluate this LinkedIn post for engagement potential:

POST CONTENT:
{post.content}

HASHTAGS: {hashtags}
TARGET: {post.target_audience}
HOOK: {post.hook if hasattr(post, 'hook') else 'First line of content'}

Evaluate as a LinkedIn Engagement Specialist. Score based on:
1. Hook Effectiveness (0-10): Will this stop the scroll?
2. Engagement Potential (0-10): Will people interact?
3. Shareability (0-10): Would professionals share this?

OUTPUT FORMAT (JSON):
{{
    "score": [weighted average 0-10],
    "approved": [true if score >= 7],
    "hook_effectiveness": [0-10],
    "engagement_potential": [0-10],
    "shareability": [0-10],
    "feedback": "[Specific improvement needed if score < 7]",
    "predicted_engagement_rate": "[percentage estimate]",
    "scroll_stop_rating": ["weak", "moderate", "strong"],
    "hashtag_strategy": ["poor", "adequate", "excellent"],
    "viral_potential": [true/false]
}}"""
    
    def _parse_validation_response(self, response: Dict) -> ValidationScore:
        """Parse the validation response"""
        try:
            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            
            score = float(content.get("score", 0))
            
            # Separate numeric and non-numeric fields for criteria_breakdown
            criteria_breakdown = {}
            
            # Add numeric fields
            for field in ["hook_effectiveness", "engagement_potential", "shareability"]:
                if field in content:
                    criteria_breakdown[field] = float(content[field])
            
            # Add non-numeric fields as separate metadata
            if "predicted_engagement_rate" in content:
                criteria_breakdown["predicted_engagement_rate_text"] = content["predicted_engagement_rate"]
            if "scroll_stop_rating" in content:
                criteria_breakdown["scroll_stop_rating_value"] = content["scroll_stop_rating"]
            if "hashtag_strategy" in content:
                criteria_breakdown["hashtag_strategy_rating"] = content["hashtag_strategy"]
            if "viral_potential" in content:
                criteria_breakdown["viral_potential_flag"] = content["viral_potential"]
            
            return ValidationScore(
                agent_name=self.name,
                score=score,
                approved=score >= 7.0,
                feedback=content.get("feedback", ""),
                criteria_breakdown=criteria_breakdown
            )
        except Exception as e:
            self.logger.error("Failed to parse validation response", error=str(e))
            return ValidationScore(
                agent_name=self.name,
                score=0.0,
                approved=False,
                feedback=f"Validation parsing error: {str(e)}"
            )
