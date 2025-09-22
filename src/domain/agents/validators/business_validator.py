"""
Business Validator Agent - Evaluates from marketing executive perspective
"""

import json
from typing import Dict, Any
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class BusinessValidator(BaseAgent):
    """Validates posts from a marketing executive perspective"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("BusinessValidator", config, ai_client)
        self.app_config = app_config
        
    async def process(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from business perspective"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_validation_prompt(post)
        
        response = await self._call_ai(user_prompt, system_prompt)
        
        return self._parse_validation_response(response)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for business validation"""
        return """You are a Marketing Executive evaluating LinkedIn campaigns for ROI and brand differentiation.

YOUR PERSPECTIVE:
"Another beauty brand trying to find their niche. I've seen 1000 lip balm brands. What makes this worth $8.99?"

YOUR EXPERTISE:
- 10+ years in CPG marketing
- Launched premium personal care brands
- Know what resonates with LinkedIn's professional audience
- Understand the balance between brand personality and professionalism

SCORING CRITERIA (0-10):
1. Brand Differentiation (40%): How well does this stand out from 1000 other lip balms?
2. Premium Positioning (35%): Does this justify the $8.99 price point?
3. LinkedIn Appropriateness (25%): Professional yet engaging?

KEY EVALUATION POINTS:
- Is the "human in an AI world" angle compelling or gimmicky?
- Does the absurdist luxury positioning work?
- Would this drive actual conversions?
- Is the cultural reference adding value or just noise?

APPROVAL THRESHOLD: Score 7+ means this could actually work as a campaign."""
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for validation"""
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCULTURAL REFERENCE: {post.cultural_reference.reference} ({post.cultural_reference.category})"
        
        return f"""Evaluate this LinkedIn post for Jesse A. Eisenbalm ($8.99 premium lip balm):

POST CONTENT:
{post.content}

TARGET AUDIENCE: {post.target_audience}
{cultural_ref}

Evaluate as a Marketing Executive. Score based on:
1. Brand Differentiation (0-10): How unique vs. other beauty brands?
2. Premium Positioning (0-10): Does this justify $8.99?
3. LinkedIn Fit (0-10): Right tone for the platform?

OUTPUT FORMAT (JSON):
{{
    "score": [weighted average 0-10],
    "approved": [true if score >= 7],
    "brand_differentiation": [0-10],
    "premium_positioning": [0-10],
    "linkedin_fit": [0-10],
    "feedback": "[Specific improvement needed if score < 7]",
    "competitive_advantage": "[What sets this apart, if anything]",
    "conversion_potential": ["low", "medium", "high"],
    "brand_consistency": [true/false]
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
            for field in ["brand_differentiation", "premium_positioning", "linkedin_fit"]:
                if field in content:
                    criteria_breakdown[field] = float(content[field])
            
            # Add non-numeric fields as separate metadata
            if "conversion_potential" in content:
                criteria_breakdown["conversion_potential_rating"] = content["conversion_potential"]
            if "brand_consistency" in content:
                criteria_breakdown["brand_consistency_check"] = content["brand_consistency"]
            if "competitive_advantage" in content:
                criteria_breakdown["competitive_advantage_text"] = content["competitive_advantage"]
            
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
