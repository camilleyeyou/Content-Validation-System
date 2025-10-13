"""
Image Generation Agent - Dedicated agent for creating DALL-E images for posts
Separates concerns: content generation vs image generation
"""

from typing import Dict, Any, Optional
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.domain.models.post import LinkedInPost
from src.infrastructure.config.config_manager import AppConfig

class ImageGenerationAgent(BaseAgent):
    """Dedicated agent for generating images for LinkedIn posts"""
    
    def __init__(self, config: AgentConfig, ai_client, app_config: AppConfig):
        super().__init__("ImageGenerationAgent", config, ai_client)
        self.app_config = app_config
        self.brand = app_config.brand
    
    async def process(self, input_data: Any) -> LinkedInPost:
        """
        Generate image for a post
        Input: LinkedInPost object
        Output: Same LinkedInPost with image attached
        """
        post = input_data
        
        self.logger.info("Generating image for post",
                        post_id=post.id,
                        has_existing_image=bool(post.image_url))
        
        # If post already has an image, skip
        if post.image_url:
            self.logger.info("Post already has image, skipping generation")
            return post
        
        try:
            # Step 1: Analyze the post and create image prompt
            image_prompt = await self._create_image_prompt_for_post(post)
            
            # Step 2: Generate the image
            image_result = await self._generate_image(
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                style="vivid"
            )
            
            # Step 3: Attach image to post
            post.set_image(
                url=image_result.get("url"),
                prompt=image_prompt,
                description=self._create_image_description(post),
                revised_prompt=image_result.get("revised_prompt")
            )
            
            self.logger.info("Image generated and attached to post",
                           post_id=post.id,
                           image_url_length=len(image_result.get("url", "")))
            
            return post
            
        except Exception as e:
            self.logger.error(f"Failed to generate image for post: {e}", exc_info=True)
            # Return post without image - don't fail the entire post
            return post
    
    async def _create_image_prompt_for_post(self, post: LinkedInPost) -> str:
        """
        Analyze post content and create a detailed DALL-E prompt
        Uses GPT to create the perfect image prompt based on the post
        """
        analysis_prompt = f"""Analyze this LinkedIn post and create a DETAILED image prompt for DALL-E 3.

POST CONTENT:
{post.content}

BRAND: Jesse A. Eisenbalm - Premium $8.99 lip balm
TAGLINE: "The only business lip balm that keeps you human in an AI world"
BRAND COLORS: Navy blue and gold accents
STYLE: Modern, sophisticated, professional lifestyle photography

Create a DALL-E image prompt (200-400 characters) that:
1. Visually represents the post's core emotion/message
2. Shows the lip balm product in a relatable professional context
3. Uses warm, natural lighting and clean composition
4. Conveys sophistication and human moments in tech workplaces
5. NO text in the image (DALL-E struggles with text)

Return ONLY the image prompt text, nothing else."""

        try:
            response = await self._call_ai(
                prompt=analysis_prompt,
                system_prompt="You are an expert visual designer creating DALL-E prompts. Return only the prompt text.",
                response_format="text"
            )
            
            # Extract the prompt from response
            image_prompt = response.get("content", "").strip()
            
            # Fallback if response is too short or missing
            if len(image_prompt) < 50:
                self.logger.warning("Generated image prompt too short, using fallback")
                return self._create_fallback_image_prompt(post)
            
            self.logger.info("Image prompt created",
                           prompt_length=len(image_prompt),
                           prompt_preview=image_prompt[:100])
            
            return image_prompt
            
        except Exception as e:
            self.logger.error(f"Failed to create image prompt via GPT: {e}")
            return self._create_fallback_image_prompt(post)
    
    def _create_fallback_image_prompt(self, post: LinkedInPost) -> str:
        """Create a generic but high-quality fallback image prompt"""
        content_lower = post.content.lower()
        
        # Determine scene based on content keywords
        if any(word in content_lower for word in ["zoom", "video", "call", "meeting", "screen"]):
            scene = "video call workspace with laptop showing multiple meeting windows, person's silhouette facing screen"
            mood = "digital exhaustion meeting physical self-care"
        elif any(word in content_lower for word in ["desk", "office", "workspace", "laptop"]):
            scene = "modern minimalist office desk with laptop and organized workspace"
            mood = "professional calm and intentional pause"
        elif any(word in content_lower for word in ["coffee", "cafe", "morning"]):
            scene = "coffee shop workspace with laptop, coffee cup, and morning light"
            mood = "productive focus with self-care ritual"
        else:
            scene = "clean modern professional workspace with laptop and documents"
            mood = "sophisticated balance of work and wellness"
        
        return (
            f"Professional lifestyle photography of premium Jesse A. Eisenbalm lip balm "
            f"on a {scene}. Warm natural window lighting from left creating soft shadows, "
            f"shallow depth of field with lip balm in sharp focus in foreground, background softly blurred. "
            f"Sophisticated color palette: navy blue and gold accents with clean white surfaces. "
            f"The composition conveys {mood}. High-end product photography aesthetic, "
            f"modern and elegant, emphasizing human moments in digital workspaces."
        )
    
    def _create_image_description(self, post: LinkedInPost) -> str:
        """Create user-facing description of the image"""
        # Extract key theme from post
        content_lower = post.content.lower()
        
        if "zoom" in content_lower or "video" in content_lower or "meeting" in content_lower:
            return "Premium lip balm on a video call workspace, representing self-care during digital meetings"
        elif "ai" in content_lower or "automated" in content_lower:
            return "Lip balm as a grounding physical object amid AI-driven workplace automation"
        elif "stress" in content_lower or "anxiety" in content_lower:
            return "A moment of self-care pause on a busy professional's workspace"
        elif "monday" in content_lower or "friday" in content_lower:
            return "Jesse A. Eisenbalm on a modern workspace, marking a human ritual in the work week"
        else:
            return "Premium Jesse A. Eisenbalm lip balm on a sophisticated professional workspace"