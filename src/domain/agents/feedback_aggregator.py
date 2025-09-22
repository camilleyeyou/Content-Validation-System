"""
Feedback Aggregator Agent - Analyzes validation failures and creates improvement instructions
"""

import json
from typing import Dict, Any, List
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost

class FeedbackAggregator(BaseAgent):
    """Aggregates feedback from validators and creates improvement instructions"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("FeedbackAggregator", config, ai_client)
        self.app_config = app_config
        
    async def process(self, post: LinkedInPost) -> Dict[str, Any]:
        """Analyze validation failures and create improvement plan"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_aggregation_prompt(post)
        
        response = await self._call_ai(user_prompt, system_prompt)
        
        return self._parse_aggregation_response(response)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for feedback aggregation"""
        return f"""You are a Content Strategy Expert analyzing why LinkedIn posts fail validation.

YOUR ROLE:
Synthesize feedback from multiple validators to create specific, actionable improvement instructions.

BRAND CONTEXT:
- Product: {self.app_config.brand.product_name} ({self.app_config.brand.price})
- Positioning: "{self.app_config.brand.tagline}"
- Voice: {', '.join(self.app_config.brand.voice_attributes)}

YOUR TASK:
1. Identify the core issues preventing approval
2. Prioritize what needs fixing most urgently
3. Provide specific rewriting instructions
4. Maintain brand voice while addressing concerns

FOCUS ON:
- Specific phrases or sections to change
- How to strengthen weak areas
- What to keep (don't throw out what's working)
- Concrete examples of improvements"""
    
    def _build_aggregation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for feedback aggregation"""
        # Compile all feedback
        feedback_summary = []
        for score in post.validation_scores:
            if not score.approved:
                feedback_summary.append(f"""
{score.agent_name} (Score: {score.score}/10):
- Feedback: {score.feedback}
- Breakdown: {json.dumps(score.criteria_breakdown, indent=2)}
""")
        
        return f"""Analyze why this LinkedIn post failed validation and create improvement instructions:

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}

VALIDATION FEEDBACK:
{' '.join(feedback_summary)}

Create specific improvement instructions:

OUTPUT FORMAT (JSON):
{{
    "main_issues": [
        "List of 2-3 core problems"
    ],
    "specific_improvements": {{
        "hook": "How to improve the opening line",
        "authenticity": "How to make it feel more genuine",
        "value_proposition": "How to better justify $8.99",
        "cultural_reference": "How to better integrate the reference",
        "call_to_action": "How to improve engagement"
    }},
    "keep_these_elements": [
        "What's working and should be preserved"
    ],
    "revised_hook_suggestion": "Specific example of improved opening",
    "tone_adjustment": "How to adjust the overall tone",
    "priority_fix": "The ONE thing to fix first"
}}"""
    
    def _parse_aggregation_response(self, response: Dict) -> Dict[str, Any]:
        """Parse the aggregation response"""
        try:
            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            
            return {
                "main_issues": content.get("main_issues", []),
                "specific_improvements": content.get("specific_improvements", {}),
                "keep_these_elements": content.get("keep_these_elements", []),
                "revised_hook_suggestion": content.get("revised_hook_suggestion", ""),
                "tone_adjustment": content.get("tone_adjustment", ""),
                "priority_fix": content.get("priority_fix", "")
            }
            
        except Exception as e:
            self.logger.error("Failed to parse aggregation response", error=str(e))
            return {
                "main_issues": ["Failed to parse feedback"],
                "specific_improvements": {},
                "priority_fix": "Unable to generate improvements"
            }