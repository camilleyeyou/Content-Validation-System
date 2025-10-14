"""
Revision Generator - Creates improved versions based on feedback
Updated with custom prompt loading support
"""

from typing import Dict, Any, Tuple
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost

class RevisionGenerator(BaseAgent):
    """Generates revised post versions based on aggregated feedback"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("RevisionGenerator", config, ai_client)
        self.app_config = app_config
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
    async def process(self, input_data: Tuple[LinkedInPost, Dict[str, Any]]) -> LinkedInPost:
        """
        Generate revised version of post based on feedback
        
        Args:
            input_data: Tuple of (post, feedback_dict)
            
        Returns:
            Revised LinkedInPost
        """
        post, feedback = input_data
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_revision_prompt(post, feedback)
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            return self._apply_revision(post, response, feedback)
        except Exception as e:
            self.logger.error(f"Revision generation failed: {e}")
            return self._create_minimal_revision(post)
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for revision generation"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("RevisionGenerator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for RevisionGenerator")
            return custom_prompts["system_prompt"]
        
        # Default prompt
        return f"""You are an expert LinkedIn content editor for {self.app_config.brand.product_name}.

YOUR ROLE:
Revise LinkedIn posts based on validator feedback while maintaining brand voice and authenticity.

BRAND VOICE: {', '.join(self.app_config.brand.voice_attributes)}
PRODUCT: {self.app_config.brand.product_name} ({self.app_config.brand.price})
TAGLINE: {self.app_config.brand.tagline}
RITUAL: {self.app_config.brand.ritual}

YOUR PROCESS:
1. Address the priority fix first
2. Implement specific improvements
3. Keep elements that worked well
4. Maintain brand voice throughout
5. Ensure post flows naturally

PRINCIPLES:
- Fix issues without losing authenticity
- Preserve good elements
- Make changes feel organic, not forced
- Keep the human voice
- Maintain LinkedIn appropriateness

OUTPUT:
Provide revised post with:
- Improved content addressing feedback
- Same cultural references if they worked
- Enhanced hook if needed
- Clear call-to-action
- Appropriate hashtags

Be specific and authentic."""
    
    def _build_revision_prompt(self, post: LinkedInPost, feedback: Dict[str, Any]) -> str:
        """Build the revision prompt"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("RevisionGenerator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for RevisionGenerator")
            return custom_prompts["user_prompt_template"]
        
        # Build default template
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference}"
        
        return f"""Revise this LinkedIn post based on feedback.

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}

AGGREGATED FEEDBACK:
Priority Fix: {feedback.get('priority_fix', 'General improvement needed')}

Main Issues:
{self._format_list(feedback.get('main_issues', []))}

Specific Improvements Needed:
{self._format_dict(feedback.get('specific_improvements', {}))}

Keep These Elements:
{self._format_list(feedback.get('keep_these_elements', []))}

Suggested New Hook: {feedback.get('revised_hook_suggestion', 'Not provided')}

Tone Adjustment: {feedback.get('tone_adjustment', 'Maintain current tone')}

REQUIREMENTS:
1. Address the priority fix
2. Implement specific improvements
3. Keep working elements
4. Maintain brand voice ({', '.join(self.app_config.brand.voice_attributes)})
5. Include product name, price, and ritual
6. Keep appropriate hashtags

Return JSON:
{{
    "revised_content": "The complete revised post with hashtags",
    "changes_made": ["change 1", "change 2", "change 3"],
    "hook": "The new opening line",
    "kept_elements": ["element 1", "element 2"],
    "cultural_reference": {{
        "category": "tv_show/workplace/seasonal",
        "reference": "The reference used",
        "context": "Why it works"
    }},
    "hashtags": ["tag1", "tag2", "tag3"]
}}

Make it authentic, engaging, and on-brand."""
    
    def _format_list(self, items: list) -> str:
        """Format list items for prompt"""
        if not items:
            return "- None specified"
        return "\n".join([f"- {item}" for item in items])
    
    def _format_dict(self, items: dict) -> str:
        """Format dict items for prompt"""
        if not items:
            return "- None specified"
        return "\n".join([f"- {key}: {value}" for key, value in items.items() if value])
    
    def _apply_revision(self, post: LinkedInPost, response: Dict, feedback: Dict) -> LinkedInPost:
        """Apply the revision to the post"""
        try:
            content = response.get("content", {})
            content = self._ensure_json_dict(content)
            
            if not content or "revised_content" not in content:
                self.logger.warning("No revised content in response, using minimal revision")
                return self._create_minimal_revision(post)
            
            # Update post content
            post.content = content.get("revised_content", post.content)
            
            # Update hashtags if provided
            if "hashtags" in content and content["hashtags"]:
                post.hashtags = content["hashtags"]
            
            # Update cultural reference if provided
            if "cultural_reference" in content and content["cultural_reference"]:
                from src.domain.models.post import CulturalReference
                ref_data = content["cultural_reference"]
                post.cultural_reference = CulturalReference(
                    category=ref_data.get("category", "workplace"),
                    reference=ref_data.get("reference", ""),
                    context=ref_data.get("context", "")
                )
            
            # Increment revision count
            post.revision_count += 1
            
            # Store revision metadata
            post.revision_history = getattr(post, 'revision_history', [])
            post.revision_history.append({
                "revision_number": post.revision_count,
                "changes_made": content.get("changes_made", []),
                "feedback_addressed": feedback.get("priority_fix", "")
            })
            
            self.logger.info(
                "Post revised successfully",
                post_id=post.id,
                revision_count=post.revision_count,
                changes=len(content.get("changes_made", []))
            )
            
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to apply revision: {e}")
            return self._create_minimal_revision(post)
    
    def _create_minimal_revision(self, post: LinkedInPost) -> LinkedInPost:
        """Create a minimal revision if AI fails"""
        # Just add revision count and return
        post.revision_count += 1
        self.logger.warning(f"Created minimal revision for post {post.id}")
        return post