"""
Feedback Aggregator Agent - Analyzes validation failures and creates improvement instructions
Fixed version with robust JSON handling
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
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            return self._parse_aggregation_response(response)
        except Exception as e:
            self.logger.error(f"Feedback aggregation failed: {e}")
            return self._create_fallback_feedback(post)
    
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
- Concrete examples of improvements

IMPORTANT: Respond with valid JSON only."""
    
    def _build_aggregation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for feedback aggregation"""
        # Compile all feedback
        feedback_summary = []
        for score in post.validation_scores:
            if not score.approved:
                feedback_summary.append(f"""
{score.agent_name} (Score: {score.score}/10):
- Feedback: {score.feedback}
- Key Issues: {self._extract_key_issues(score.criteria_breakdown)}
""")
        
        return f"""Analyze why this LinkedIn post failed validation and create improvement instructions:

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}

VALIDATION FEEDBACK:
{' '.join(feedback_summary)}

Create specific improvement instructions.

CRITICAL: Return ONLY this JSON structure:
{{
    "main_issues": [
        "List exactly 3 core problems"
    ],
    "specific_improvements": {{
        "hook": "Specific way to improve the opening line",
        "authenticity": "How to make it feel more genuine",
        "value_proposition": "How to better justify $8.99",
        "cultural_reference": "How to better integrate the reference",
        "call_to_action": "How to improve engagement"
    }},
    "keep_these_elements": [
        "List 2-3 things that are working"
    ],
    "revised_hook_suggestion": "Specific example of improved opening line",
    "tone_adjustment": "How to adjust the overall tone",
    "priority_fix": "The ONE thing to fix first"
}}

Return ONLY valid JSON."""
    
    def _extract_key_issues(self, criteria_breakdown: Dict) -> str:
        """Extract key issues from criteria breakdown"""
        issues = []
        for key, value in criteria_breakdown.items():
            if isinstance(value, (int, float)) and value < 5:
                issues.append(f"{key}: {value}/10")
        return ", ".join(issues) if issues else "No specific scores below 5"
    
    def _parse_aggregation_response(self, response: Dict) -> Dict[str, Any]:
        """Parse the aggregation response with robust error handling"""
        try:
            content = response.get("content", {})
            
            # Ensure content is a dictionary
            content = self._ensure_json_dict(content)
            
            if not content:
                raise ValueError("Empty response content")
            
            # Validate and extract fields with defaults
            result = {
                "main_issues": content.get("main_issues", ["Post needs improvement"]),
                "specific_improvements": content.get("specific_improvements", {}),
                "keep_these_elements": content.get("keep_these_elements", []),
                "revised_hook_suggestion": content.get("revised_hook_suggestion", ""),
                "tone_adjustment": content.get("tone_adjustment", ""),
                "priority_fix": content.get("priority_fix", "Improve overall clarity")
            }
            
            # Ensure specific_improvements has all required keys
            default_improvements = {
                "hook": "Make opening more attention-grabbing",
                "authenticity": "Add more genuine personal touch",
                "value_proposition": "Better explain the $8.99 value",
                "cultural_reference": "Integrate reference more naturally",
                "call_to_action": "Add clear engagement prompt"
            }
            
            for key, default_value in default_improvements.items():
                if key not in result["specific_improvements"]:
                    result["specific_improvements"][key] = default_value
            
            # Ensure lists are actually lists
            if not isinstance(result["main_issues"], list):
                result["main_issues"] = [str(result["main_issues"])]
            
            if not isinstance(result["keep_these_elements"], list):
                result["keep_these_elements"] = [str(result["keep_these_elements"])]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to parse aggregation response: {e}")
            return self._create_fallback_feedback(None)
    
    def _create_fallback_feedback(self, post: LinkedInPost = None) -> Dict[str, Any]:
        """Create fallback feedback when parsing fails"""
        main_issues = ["Failed to parse feedback"]
        
        if post and post.validation_scores:
            # Try to extract main issues from scores
            low_scores = []
            for score in post.validation_scores:
                if score.score < 5:
                    low_scores.append(f"{score.agent_name}: {score.score}/10")
            
            if low_scores:
                main_issues = [
                    f"Low scores from validators: {', '.join(low_scores)}",
                    "Content needs stronger hook",
                    "Brand positioning unclear"
                ]
        
        return {
            "main_issues": main_issues,
            "specific_improvements": {
                "hook": "Start with a compelling question or statement",
                "authenticity": "Add personal experience or insight",
                "value_proposition": "Clearly state why $8.99 is worth it",
                "cultural_reference": "Make reference more relevant to audience",
                "call_to_action": "End with clear engagement prompt"
            },
            "keep_these_elements": ["Brand mention", "Price point"],
            "revised_hook_suggestion": "Start with: 'Ever notice how...' or 'That moment when...'",
            "tone_adjustment": "Make more conversational and less sales-focused",
            "priority_fix": "Improve the opening hook to grab attention"
        }