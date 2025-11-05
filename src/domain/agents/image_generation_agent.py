# src/domain/agents/image_generation_agent.py
"""
Image Generation Agent - Google Gemini 2.5 Flash Image
Generates high-quality images for LinkedIn posts
Cost: $0.039 per image
"""

import os
import uuid
import time
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.domain.models.post import LinkedInPost
import structlog

logger = structlog.get_logger(__name__)


class ImageGenerationAgent(BaseAgent):
    """Generates images using Google Gemini 2.5 Flash Image"""
    
    def __init__(self, config: AgentConfig, ai_client, app_config):
        """
        Initialize Image Generation Agent
        
        Args:
            config: Agent configuration
            ai_client: AI client for text generation (prompt creation) and image generation
            app_config: Application configuration with Google settings
        """
        super().__init__("ImageGenerationAgent", config, ai_client)
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
        # Get Google configuration
        google_config = getattr(app_config, 'google', None)
        
        if google_config:
            self.google_api_key = getattr(google_config, 'api_key', '')
            self.image_model = getattr(google_config, 'image_model', 'gemini-2.5-flash-image')
            self.use_images = getattr(google_config, 'use_images', True)
        else:
            # Fallback defaults
            self.google_api_key = os.getenv('GOOGLE_API_KEY', '')
            self.image_model = 'gemini-2.5-flash-image'
            self.use_images = True
        
        # Setup output directory for images
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # Go up 4 levels
        self.output_dir = project_root / "data" / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            "ImageGenerationAgent initialized",
            model=self.image_model,
            use_images=self.use_images,
            has_api_key=bool(self.google_api_key),
            output_dir=str(self.output_dir),
            has_custom_prompts=self.prompt_manager.has_custom_prompts("ImageGenerationAgent")
        )
        
        if not self.google_api_key:
            self.logger.warning(
                "No Google API key provided - image generation will fail. "
                "Set GOOGLE_API_KEY environment variable."
            )
    
    async def process(self, post: LinkedInPost) -> LinkedInPost:
        """
        Main process method - generate image for a LinkedIn post
        
        Args:
            post: LinkedInPost object to attach image to
            
        Returns:
            LinkedInPost with image attached
        """
        if not self.use_images:
            self.logger.info("Image generation disabled in config", post_id=post.id)
            return post
        
        try:
            self.logger.info("Processing post for image generation", post_id=post.id)
            
            # Step 1: Create image prompt from post content
            image_prompt = await self._create_image_prompt(post)
            
            # Step 2: Generate image using Gemini
            image_result = await self.generate_image(image_prompt, post)
            
            # Step 3: Attach image to post (signature-safe)
            if image_result and image_result.get("saved_path"):
                attached = self._attach_image_to_post(
                    post=post,
                    saved_path=image_result["saved_path"],
                    image_prompt=image_prompt,
                    image_result=image_result,
                )
                if attached:
                    self.logger.info(
                        "Image attached to post",
                        post_id=post.id,
                        generation_time=image_result.get("generation_time_seconds"),
                        saved_path=image_result.get("saved_path"),
                    )
                else:
                    self.logger.error(
                        "Image was generated and saved, but could not be attached to post",
                        post_id=post.id,
                        saved_path=image_result.get("saved_path"),
                    )
            else:
                self.logger.warning("Image generation returned no file path", post_id=post.id)
            
            return post
            
        except Exception as e:
            self.logger.error(
                "Failed to generate image for post",
                post_id=post.id,
                error=str(e),
                exc_info=True
            )
            # Don't fail the post - return it without image
            return post
    
    async def generate_image(self, prompt: str, post: Optional[LinkedInPost] = None) -> Dict[str, Any]:
        """
        Generate image using Google Gemini 2.5 Flash Image API
        
        Args:
            prompt: Image description/prompt
            post: Optional post for context
            
        Returns:
            Dict with 'saved_path', 'prompt', 'generation_time_seconds', 'size_mb', 'cost'
        """
        start_time = time.time()
        
        try:
            # Enhance prompt for better image results
            enhanced_prompt = self._enhance_prompt_for_image(prompt)
            
            self.logger.info(
                "Generating image with Gemini 2.5 Flash Image",
                model=self.image_model,
                prompt_length=len(enhanced_prompt)
            )
            
            # Generate image using base agent's _generate_image method
            image_result = await self._generate_image(
                prompt=enhanced_prompt,
                base_image_path=None
            )
            
            generation_time = time.time() - start_time
            
            # Check if we got image data
            if not image_result or not image_result.get("image_data"):
                self.logger.error("No image data received from Gemini")
                return self._error_response(prompt, "No image data received")
            
            # Save image to file
            image_data = image_result["image_data"]
            saved_path = self._save_image_to_file(image_data, post)
            
            if not saved_path:
                return self._error_response(prompt, "Failed to save image")
            
            # Calculate file size
            file_size = os.path.getsize(saved_path)
            size_mb = file_size / (1024 * 1024)
            
            result = {
                "saved_path": saved_path,
                "prompt": enhanced_prompt,
                "original_prompt": prompt,
                "provider": "google_gemini",
                "model": self.image_model,
                "cost": 0.039,
                "generation_time_seconds": round(generation_time, 2),
                "size_mb": round(size_mb, 3)
            }
            
            self.logger.info(
                "Image generated successfully",
                generation_time=result["generation_time_seconds"],
                size_mb=result["size_mb"],
                saved_path=saved_path
            )
            
            return result
        
        except Exception as e:
            self.logger.error(
                "Image generation failed",
                error=str(e),
                exc_info=True
            )
            return self._error_response(prompt, str(e))
    
    def _save_image_to_file(self, image_data: bytes, post: Optional[LinkedInPost] = None) -> Optional[str]:
        """Save image bytes to file"""
        try:
            from PIL import Image
            from io import BytesIO
            
            # Generate filename
            if post and hasattr(post, 'id'):
                filename = f"{post.id}_{uuid.uuid4().hex[:8]}.png"
            else:
                filename = f"image_{uuid.uuid4().hex[:8]}.png"
            
            output_path = self.output_dir / filename
            
            # Open and save image
            image = Image.open(BytesIO(image_data))
            image.save(output_path, format='PNG')
            
            self.logger.info(f"Image saved to: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save image: {e}")
            return None
    
    def _error_response(self, prompt: str, error: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "saved_path": None,
            "prompt": prompt,
            "error": error,
            "provider": "google_gemini",
            "model": self.image_model,
            "cost": 0.0
        }
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for image prompt generation"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("ImageGenerationAgent")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for ImageGenerationAgent")
            return custom_prompts["system_prompt"]
        
        # Default system prompt
        return """You are a professional art director creating image prompts for AI image generation.
Your goal is to create DETAILED, VIVID image prompts for professional product photography.

Focus on:
- Product placement and composition
- Lighting (soft, natural, studio)
- Background and setting
- Color palette (navy, gold, cream, luxury tones)
- Professional aesthetic
- LinkedIn-appropriate visuals

Create prompts that are 100-150 words with rich visual detail."""
    
    async def _create_image_prompt(self, post: LinkedInPost) -> str:
        """Create a detailed image prompt from the post content"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("ImageGenerationAgent")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for ImageGenerationAgent")
            # Format the custom template with post data
            try:
                return custom_prompts["user_prompt_template"].format(
                    content=post.content[:300],
                    post_id=post.id
                )
            except Exception as e:
                self.logger.warning(f"Failed to format custom template: {e}, using default")
        
        try:
            system_prompt = self._build_system_prompt()
            
            user_prompt = f"""Create a detailed image prompt for a professional product photograph.

Post content:
{post.content[:300]}

Product: Jesse A. Eisenbalm (premium lip balm)
Brand colors: Navy blue, gold accents, cream
Aesthetic: Luxury, professional, sophisticated

Create a DETAILED image prompt for professional product photography."""

            response = await self._call_ai(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="text"
            )
            
            image_prompt = response.get("content", "")
            
            if image_prompt and len(image_prompt) > 50:
                self.logger.info(
                    "Generated image prompt via AI",
                    post_id=post.id,
                    prompt_length=len(image_prompt)
                )
                return image_prompt
            else:
                return self._create_fallback_image_prompt(post)
        
        except Exception as e:
            self.logger.warning(
                "Failed to generate AI image prompt, using fallback",
                error=str(e)
            )
            return self._create_fallback_image_prompt(post)
    
    def _create_fallback_image_prompt(self, post: LinkedInPost) -> str:
        """Create a simple fallback image prompt"""
        return """A luxury lip balm product (Jesse A. Eisenbalm) on a modern desk surface.
Professional product photography with soft, natural lighting.
Navy blue and gold color scheme with cream accents.
Minimalist, sophisticated composition.
Studio quality, high-end commercial aesthetic.
Clean background, subtle shadows, premium feel.
Suitable for LinkedIn professional audience."""
    
    def _enhance_prompt_for_image(self, prompt: str) -> str:
        """Enhance prompt for better image generation results"""
        quality_terms = [
            "Professional product photography",
            "Soft, diffused lighting with subtle highlights",
            "Clean, modern aesthetic",
            "High-quality commercial photography style",
            "Sharp focus with professional depth of field",
            "Studio quality lighting"
        ]
        
        has_quality = any(term.lower() in prompt.lower() for term in ['professional', 'studio', 'high-quality'])
        
        if not has_quality:
            prompt = f"{prompt}\n\n" + "\n".join(quality_terms)
        
        return prompt
    
    def _create_image_description(self, post: LinkedInPost) -> str:
        """Create a user-facing description of what the image shows"""
        if hasattr(post, 'cultural_reference') and post.cultural_reference:
            ref = post.cultural_reference.reference
            return f"Product showcase inspired by {ref}"
        
        return "Professional product photography showcasing Jesse A. Eisenbalm"

    def _attach_image_to_post(
        self,
        post: LinkedInPost,
        saved_path: str,
        image_prompt: str,
        image_result: Dict[str, Any],
    ) -> bool:
        """
        Try multiple signatures to attach an image, to stay compatible with different
        LinkedInPost.set_image() definitions across versions.
        Priority: use signatures that include the required 'prompt'.
        """
        alt_text = self._create_image_description(post)

        # ---- Attempt 1: Keyword args with prompt (modern, likely) ----
        # Try with all extras first
        try:
            post.set_image(
                url=saved_path,
                prompt=image_prompt,
                description=alt_text,
                provider="google_gemini",
                generation_time=image_result.get("generation_time_seconds"),
                size_mb=image_result.get("size_mb"),
                cost=image_result.get("cost", 0.039),
            )
            self._maybe_attach_metadata_fields(post, image_result, saved_path)
            return True
        except TypeError as e:
            # Retry without optional extras that might not be accepted
            self.logger.warning("set_image(url, prompt, description, provider, +extras) not supported; retrying", error=str(e))
            try:
                post.set_image(
                    url=saved_path,
                    prompt=image_prompt,
                    description=alt_text,
                    provider="google_gemini",
                )
                self._maybe_attach_metadata_fields(post, image_result, saved_path)
                return True
            except TypeError as e2:
                self.logger.warning("set_image(url, prompt, description, provider) not supported; retrying", error=str(e2))

        # ---- Attempt 2: Pure positional (very strict signature) ----
        try:
            # Assume signature: set_image(url, prompt, description=None, provider=None)
            post.set_image(saved_path, image_prompt, alt_text, "google_gemini")
            self._maybe_attach_metadata_fields(post, image_result, saved_path)
            return True
        except TypeError as e:
            self.logger.warning("set_image(url, prompt, description, provider) positional not supported; retrying", error=str(e))

        # ---- Attempt 3: Minimal call then set attributes directly ----
        try:
            # If even this fails, we'll set fields manually
            post.set_image(saved_path, image_prompt)  # if only (url, prompt) is required
            self._maybe_attach_metadata_fields(post, image_result, saved_path)
            # Fill nicer fields if present
            if hasattr(post, "image_description"):
                post.image_description = alt_text  # type: ignore[attr-defined]
            if hasattr(post, "image_provider"):
                post.image_provider = "google_gemini"  # type: ignore[attr-defined]
            if hasattr(post, "has_image"):
                post.has_image = True  # type: ignore[attr-defined]
            return True
        except TypeError as e:
            self.logger.error("All set_image attachment attempts failed", error=str(e))

        # Final fallback: set attributes directly (no set_image available/compatible)
        try:
            if hasattr(post, "image_url"):
                post.image_url = saved_path  # type: ignore[attr-defined]
            if hasattr(post, "image_prompt"):
                post.image_prompt = image_prompt  # type: ignore[attr-defined]
            if hasattr(post, "image_description"):
                post.image_description = alt_text  # type: ignore[attr-defined]
            if hasattr(post, "image_provider"):
                post.image_provider = "google_gemini"  # type: ignore[attr-defined]
            if hasattr(post, "image_generation_time"):
                post.image_generation_time = image_result.get("generation_time_seconds")  # type: ignore[attr-defined]
            if hasattr(post, "image_size_mb"):
                post.image_size_mb = image_result.get("size_mb")  # type: ignore[attr-defined]
            if hasattr(post, "image_cost"):
                post.image_cost = image_result.get("cost", 0.039)  # type: ignore[attr-defined]
            if hasattr(post, "image_metadata"):
                meta = {
                    "model": image_result.get("model"),
                    "provider": image_result.get("provider"),
                    "saved_path": saved_path,
                    "original_prompt": image_result.get("original_prompt"),
                }
                if isinstance(post.image_metadata, dict):
                    post.image_metadata.update(meta)  # type: ignore[attr-defined]
                else:
                    setattr(post, "image_metadata", meta)
            if hasattr(post, "has_image"):
                post.has_image = True  # type: ignore[attr-defined]
            # If we set an explicit URL field that orchestrator checks (image_url), return True
            return bool(getattr(post, "image_url", None))
        except Exception as e:
            self.logger.error("Failed to set image fields directly on post", error=str(e))
            return False

    def _maybe_attach_metadata_fields(self, post: LinkedInPost, image_result: Dict[str, Any], saved_path: str) -> None:
        """Attach useful telemetry to the post when available without breaking older models."""
        try:
            if hasattr(post, "image_url") and not getattr(post, "image_url", None):
                post.image_url = saved_path  # type: ignore[attr-defined]
            if hasattr(post, "image_generation_time") and image_result.get("generation_time_seconds") is not None:
                post.image_generation_time = image_result.get("generation_time_seconds")  # type: ignore[attr-defined]
            if hasattr(post, "image_size_mb") and image_result.get("size_mb") is not None:
                post.image_size_mb = image_result.get("size_mb")  # type: ignore[attr-defined]
            if hasattr(post, "image_cost") and image_result.get("cost") is not None:
                post.image_cost = image_result.get("cost")  # type: ignore[attr-defined]
            if hasattr(post, "image_metadata"):
                meta = {
                    "model": image_result.get("model"),
                    "provider": image_result.get("provider"),
                    "saved_path": saved_path,
                    "prompt_used": image_result.get("prompt"),
                    "original_prompt": image_result.get("original_prompt"),
                }
                if isinstance(post.image_metadata, dict):
                    post.image_metadata.update(meta)  # type: ignore[attr-defined]
                else:
                    setattr(post, "image_metadata", meta)
            if hasattr(post, "has_image"):
                post.has_image = True  # type: ignore[attr-defined]
        except Exception as e:
            self.logger.warning("Non-fatal: failed to attach image metadata fields", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics including image generation info"""
        base_stats = super().get_stats()
        
        base_stats.update({
            "image_model": self.image_model,
            "image_enabled": self.use_images,
            "has_google_api_key": bool(self.google_api_key),
            "image_cost_per_generation": 0.039,
            "output_directory": str(self.output_dir),
            "using_custom_prompts": self.prompt_manager.has_custom_prompts("ImageGenerationAgent")
        })
        
        return base_stats
