"""
Feedback Aggregator - Combines validation feedback into actionable insights
Updated with custom prompt loading support
"""

from typing import Dict, Any, List
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class FeedbackAggregator(BaseAgent):
    """Aggregates feedback from multiple validators into coherent revision guidance"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("FeedbackAggregator", config, ai_client)
        self.app_config = app_config
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
    async def process(self, post: LinkedInPost) -> Dict[str, Any]:
        """
        Aggregate feedback from all validators
        
        Args:
            post: LinkedInPost with validation scores
            
        Returns:
            Dict with aggregated feedback and improvement suggestions
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_aggregation_prompt(post)
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            return self._parse_aggregation_response(response)
        except Exception as e:
            self.logger.error(f"Feedback aggregation failed: {e}")
            return self._create_fallback_feedback(post)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for feedback aggregation"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("FeedbackAggregator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for FeedbackAggregator")
            return custom_prompts["system_prompt"]
        
        # Default prompt
        return """You are an expert content strategist analyzing validator feedback.

YOUR ROLE:
Synthesize feedback from three validators (Sarah Chen - customer, Marcus Williams - business, Jordan Park - social media) into clear, actionable revision guidance.

YOUR PROCESS:
1. Identify the PRIMARY issue causing failure
2. Find patterns across validator feedback
3. Prioritize fixes by impact
4. Provide specific, actionable improvements
5. Preserve what's working

PRINCIPLES:
- One clear priority fix beats multiple vague suggestions
- Specific beats general ("Change hook to X" > "Improve hook")
- Preserve brand voice while addressing concerns
- Focus on root cause, not symptoms

OUTPUT FORMAT:
Provide structured JSON with:
- main_issues: Top 2-3 problems
- priority_fix: The ONE most important change
- specific_improvements: Concrete changes by element
- keep_these_elements: What's working well
- revised_hook_suggestion: Specific new hook if needed
- tone_adjustment: If voice needs tweaking

Be direct, specific, and actionable."""
    
    def _build_aggregation_prompt(self, post: LinkedInPost) -> str:
        """Build the aggregation prompt"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("FeedbackAggregator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for FeedbackAggregator")
            return custom_prompts["user_prompt_template"]
        
        # Build default template
        if not post.validation_scores:
            return "No validation scores available for aggregation."
        
        # Gather all feedback
        feedback_summary = []
        for score in post.validation_scores:
            feedback_summary.append(f"""
VALIDATOR: {score.agent_name}
Score: {score.score}/10
Approved: {score.approved}
Feedback: {score.feedback}
Key Issues: {self._extract_key_issues(score)}
""")
        
        feedback_text = "\n".join(feedback_summary)
        
        return f"""Analyze this feedback and provide aggregated revision guidance.

ORIGINAL POST:
{post.content}

VALIDATION FEEDBACK:
{feedback_text}

AVERAGE SCORE: {post.average_score:.1f}/10
APPROVED: {sum(1 for s in post.validation_scores if s.approved)}/{len(post.validation_scores)} validators

Provide aggregated feedback as JSON:
{{
    "main_issues": ["issue 1", "issue 2"],
    "priority_fix": "The single most important change needed",
    "specific_improvements": {{
        "hook": "Specific hook improvement",
        "value_proposition": "Specific value prop improvement",
        "cultural_reference": "Specific reference improvement",
        "call_to_action": "Specific CTA improvement"
    }},
    "keep_these_elements": ["element 1", "element 2"],
    "revised_hook_suggestion": "Specific new hook text",
    "tone_adjustment": "Specific tone guidance if needed"
}}

Focus on actionable, specific guidance."""
    
    def _extract_key_issues(self, score: ValidationScore) -> str:
        """Extract key issues from validation score criteria"""
        issues = []
        
        if hasattr(score, 'criteria_breakdown') and score.criteria_breakdown:
            breakdown = score.criteria_breakdown
            
            # Check for common issue indicators
            if breakdown.get('authenticity_score', 10) < 5:
                issues.append("Low authenticity")
            if breakdown.get('hook_strength', 10) < 6:
                issues.append("Weak hook")
            if breakdown.get('price_perception') == 'absolutely not':
                issues.append("Price not justified")
            if breakdown.get('risk_assessment') == 'career-limiting':
                issues.append("Too risky")
            if breakdown.get('meme_timing') in ['dead', 'late']:
                issues.append("Outdated reference")
        
        return ", ".join(issues) if issues else "No specific issues flagged"
    
    def _parse_aggregation_response(self, response: Dict) -> Dict[str, Any]:
        """Parse the aggregation response"""
        try:
            content = response.get("content", {})
            content = self._ensure_json_dict(content)
            
            if not content:
                raise ValueError("Empty response content")
            
            # Return the aggregated feedback
            return {
                "main_issues": content.get("main_issues", []),
                "priority_fix": content.get("priority_fix", ""),
                "specific_improvements": content.get("specific_improvements", {}),
                "keep_these_elements": content.get("keep_these_elements", []),
                "revised_hook_suggestion": content.get("revised_hook_suggestion", ""),
                "tone_adjustment": content.get("tone_adjustment", "")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse aggregation response: {e}")
            return {
                "main_issues": ["Failed to parse feedback"],
                "priority_fix": "Review and revise post",
                "specific_improvements": {},
                "keep_these_elements": [],
                "revised_hook_suggestion": "",
                "tone_adjustment": ""
            }
    
    def _create_fallback_feedback(self, post: LinkedInPost) -> Dict[str, Any]:
        """Create fallback feedback if aggregation fails"""
        return {
            "main_issues": ["Unable to aggregate feedback"],
            "priority_fix": "Review validator feedback and revise accordingly",
            "specific_improvements": {
                "hook": "Make more attention-grabbing",
                "value_proposition": "Clarify the benefit",
                "cultural_reference": "Ensure relevance",
                "call_to_action": "Make more clear"
            },
            "keep_these_elements": ["Brand voice"],
            "revised_hook_suggestion": "",
            "tone_adjustment": "Maintain professional but human tone"
        }