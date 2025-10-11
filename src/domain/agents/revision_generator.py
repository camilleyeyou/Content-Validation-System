"""
Revision Generator Agent - Creates improved versions of posts based on feedback
Updated with custom prompt loading support
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
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            revised_content = self._parse_revision_response(response)
            
            if revised_content:
                # Create a revised version of the post
                post.create_revision(revised_content)
            else:
                self.logger.error("Failed to generate revision, keeping original")
                
        except Exception as e:
            self.logger.error(f"Revision generation failed: {e}")
            # Don't create a revision if generation fails
        
        return post
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for revision generation"""
        # Build default prompt
        default_prompt = f"""You are a Master Copy Editor specializing in LinkedIn content optimization.

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
The revised post should score 7+ with all validators while maintaining the original's core message.

IMPORTANT: Respond with valid JSON only."""
        
        # Return custom prompt if exists, otherwise default
        return self._get_system_prompt(default_prompt)
    
    def _build_revision_prompt(self, post: LinkedInPost, feedback: Dict) -> str:
        """Build the user prompt for revision generation"""
        # Extract specific improvements
        improvements = feedback.get('specific_improvements', {})
        improvement_list = []
        for key, value in improvements.items():
            if value:
                improvement_list.append(f"- {key}: {value}")
        
        # Build default template
        default_template = f"""Revise this LinkedIn post based on specific feedback:

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}

MAIN ISSUES TO FIX:
{chr(10).join('- ' + issue for issue in feedback.get('main_issues', []))}

PRIORITY FIX:
{feedback.get('priority_fix', 'Improve overall engagement')}

SPECIFIC IMPROVEMENTS NEEDED:
{chr(10).join(improvement_list)}

KEEP THESE ELEMENTS:
{', '.join(feedback.get('keep_these_elements', ['brand voice']))}

SUGGESTED HOOK:
{feedback.get('revised_hook_suggestion', 'Create stronger opening')}

TONE ADJUSTMENT:
{feedback.get('tone_adjustment', 'Make more authentic')}

Create a revised version that:
1. Addresses all main issues
2. Maintains 150-200 word count
3. Keeps the cultural reference natural
4. Includes "Stop. Breathe. Apply." ritual
5. Ends with 3-5 hashtags

CRITICAL: Return ONLY this JSON structure:
{{
    "revised_content": "The complete revised post with improvements and hashtags included...",
    "changes_made": [
        "List 3-5 specific changes implemented"
    ],
    "hook": "The new opening line",
    "expected_improvement": "Why this version should score higher"
}}

Return ONLY valid JSON."""
        
        # Return custom template if exists, otherwise default
        return self._get_user_prompt_template(default_template)
    
    def _parse_revision_response(self, response: Dict) -> str:
        """Parse the revision response with robust error handling"""
        try:
            content = response.get("content", {})
            
            # Ensure content is a dictionary
            content = self._ensure_json_dict(content)
            
            if not content:
                raise ValueError("Empty response content")
            
            # Extract revised content
            revised_content = content.get("revised_content", "")
            
            if not revised_content:
                self.logger.error("No revised content in response")
                return ""
            
            # Validate the revised content
            if len(revised_content) < 100:
                self.logger.warning("Revised content too short, likely incomplete")
                return ""
            
            # Log the changes made
            changes = content.get("changes_made", [])
            if changes:
                self.logger.info("Post revised", 
                               changes_count=len(changes),
                               expected_improvement=content.get("expected_improvement", ""))
            
            return revised_content
            
        except Exception as e:
            self.logger.error(f"Failed to parse revision response: {e}")
            return ""