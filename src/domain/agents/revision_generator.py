"""
Revision Generator Agent - Creates improved versions of posts based on feedback
"""

import json
from typing import Dict, Any, Tuple
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost

class RevisionGenerator(BaseAgent):
    """Generates revised versions of posts based on aggregated feedback"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("RevisionGenerator", config, ai_client)
        self.app_config = app_config
        
    async def process(self, input_data: Tuple[LinkedInPost, Dict[str, Any]]) -> LinkedInPost:
        """Generate a revised version of a post based on feedback"""
        post, feedback = input_data
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_revision_prompt(post, feedback)
        
        response = await self._call_ai(user_prompt, system_prompt)
        
        revised_content = self._parse_revision_response(response)
        
        # Create a revised version of the post
        post.create_revision(revised_content)
        
        return post
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for revision generation"""
        return f"""You are a Master Copy Editor specializing in LinkedIn content optimization.

BRAND CONTEXT:
- Product: {self.app_config.brand.product_name} ({self.app_config.brand.price})
- Positioning: "{self.app_config.brand.tagline}"
- Ritual: "{self.app_config.brand.ritual}"
- Voice: {', '.join(self.app_config.brand.voice_attributes)}

YOUR EXPERTISE:
- Turn failing content into engaging posts
- Maintain brand voice while addressing feedback
- Make surgical edits, not complete rewrites
- Strengthen hooks without clickbait
- Balance all validator perspectives

REVISION PRINCIPLES:
1. Address the priority issue first
2. Keep what's working
3. Strengthen without losing authenticity
4. Make every word earn its place
5. Ensure the cultural reference lands naturally

SUCCESS CRITERIA:
The revised post should score 7+ with all validators while maintaining the original's core message."""
    
    def _build_revision_prompt(self, post: LinkedInPost, feedback: Dict) -> str:
        """Build the user prompt for revision generation"""
        return f"""Revise this LinkedIn post based on specific feedback:

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}

FEEDBACK ANALYSIS:
Main Issues: {', '.join(feedback.get('main_issues', []))}
Priority Fix: {feedback.get('priority_fix', '')}

SPECIFIC IMPROVEMENTS NEEDED:
{json.dumps(feedback.get('specific_improvements', {}), indent=2)}

KEEP THESE ELEMENTS:
{', '.join(feedback.get('keep_these_elements', []))}

SUGGESTED HOOK:
{feedback.get('revised_hook_suggestion', '')}

TONE ADJUSTMENT:
{feedback.get('tone_adjustment', '')}

Create a revised version that:
1. Addresses all main issues
2. Maintains 150-200 word count
3. Keeps the cultural reference natural
4. Includes "Stop. Breathe. Apply." ritual
5. Ends with 3-5 hashtags

OUTPUT FORMAT (JSON):
{{
    "revised_content": "The complete revised post with improvements...",
    "changes_made": [
        "List of specific changes implemented"
    ],
    "hook": "The new opening line",
    "expected_improvement": "Why this version should score higher"
}}"""
    
    def _parse_revision_response(self, response: Dict) -> str:
        """Parse the revision response"""
        try:
            content = response.get("content", {})
            if isinstance(content, str):
                content = json.loads(content)
            
            revised_content = content.get("revised_content", "")
            
            # Log the changes made
            changes = content.get("changes_made", [])
            self.logger.info("Post revised", 
                           changes_count=len(changes),
                           expected_improvement=content.get("expected_improvement", ""))
            
            return revised_content
            
        except Exception as e:
            self.logger.error("Failed to parse revision response", error=str(e))
            # Return original content if revision fails
            return ""