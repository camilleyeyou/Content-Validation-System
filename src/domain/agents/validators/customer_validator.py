"""
Customer Validator Agent - Evaluates from a skeptical job seeker perspective
"""

import json
from typing import Dict, Any
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class CustomerValidator(BaseAgent):
    """Validates posts from a 28-year-old job seeker perspective"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("CustomerValidator", config, ai_client)
        self.app_config = app_config
        
    async def process(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from customer perspective"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_validation_prompt(post)
        
        response = await self._call_ai(user_prompt, system_prompt)
        
        return self._parse_validation_response(response)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for customer validation"""
        return """You are a 28-year-old LinkedIn user actively job searching in tech. 

YOUR MINDSET:
- Skeptical of ads and corporate messaging
- Scrolling LinkedIn during coffee breaks
- Dealing with AI screening your resume
- Tired of generic corporate wellness posts
- Values authenticity over polish
- Eye-roll at "thought leadership" fluff

YOUR PERSPECTIVE:
"Another company trying to sell me something I don't need. Is this actually relevant to my life?"

SCORING CRITERIA (0-10):
1. Workplace Relevance (40%): Does this speak to real workplace experiences?
2. Authenticity (30%): Genuine vs. trying too hard to be relatable?
3. Value Proposition (30%): Is $8.99 justified for lip balm?

APPROVAL THRESHOLD: Score 7+ means you'd actually stop scrolling and maybe even engage."""
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for validation"""
        return f"""Evaluate this LinkedIn post for Jesse A. Eisenbalm lip balm:

POST CONTENT:
{post.content}

TARGET AUDIENCE: {post.target_audience}

Evaluate as a skeptical 28-year-old job seeker. Score based on:
1. Workplace Relevance (0-10): How well does this resonate with actual workplace experiences?
2. Authenticity (0-10): Does this feel genuine or like corporate BS?
3. Value Perception (0-10): Would you spend $8.99 on this?

OUTPUT FORMAT (JSON):
{{
    "score": [weighted average 0-10],
    "approved": [true if score >= 7],
    "workplace_relevance": [0-10],
    "authenticity": [0-10],
    "value_perception": [0-10],
    "feedback": "[Specific reason if not approved]",
    "would_engage": [true/false],
    "first_impression": "[Your immediate gut reaction]"
}}"""
    
    def _parse_validation_response(self, response: Dict) -> ValidationScore:
        """Parse the validation response"""
        try:
            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            
            score = float(content.get("score", 0))
            
            # Build criteria_breakdown with numeric fields
            criteria_breakdown = {}
            
            # Add numeric fields
            for field in ["workplace_relevance", "authenticity", "value_perception"]:
                if field in content:
                    criteria_breakdown[field] = float(content[field])
            
            # Add non-numeric fields as separate metadata
            if "would_engage" in content:
                criteria_breakdown["would_engage_flag"] = content["would_engage"]
            if "first_impression" in content:
                criteria_breakdown["first_impression_text"] = content["first_impression"]
            
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
