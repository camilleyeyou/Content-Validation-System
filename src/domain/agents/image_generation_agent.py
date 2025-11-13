# src/domain/agents/image_generation_agent.py
"""
Image Generation Agent - Visual Creative Director for Jesse A. Eisenbalm
"What if Apple sold mortality?"
Generates images that blend premium minimalism, existential dread, and corporate satire
Cost: $0.039 per image
"""

import os
import uuid
import time
import asyncio
import random
from typing import Dict, Any, Optional, List
from pathlib import Path
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.domain.models.post import LinkedInPost
import structlog

logger = structlog.get_logger(__name__)


class ImageGenerationAgent(BaseAgent):
    """Visual Creative Director - Generates images using Google Gemini 2.5 Flash Image"""
    
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
        
        # Initialize Jesse visual language components
        self._initialize_visual_language()
        
        self.logger.info(
            "ImageGenerationAgent initialized - Visual Creative Director",
            model=self.image_model,
            use_images=self.use_images,
            has_api_key=bool(self.google_api_key),
            output_dir=str(self.output_dir),
            visual_philosophy="what if Apple sold mortality?",
            has_custom_prompts=self.prompt_manager.has_custom_prompts("ImageGenerationAgent")
        )
        
        if not self.google_api_key:
            self.logger.warning(
                "No Google API key provided - image generation will fail. "
                "Set GOOGLE_API_KEY environment variable."
            )
    
    def _initialize_visual_language(self):
        """Initialize Jesse A. Eisenbalm visual language components"""
        
        # Brand color palette
        self.color_palette = {
            "navy": "deep navy blue (the color of 3 AM anxiety)",
            "gold": "rich gold accents (false hope)",
            "cream": "soft cream tones (the void)",
            "error_red": "occasional error message red (corporate alarm)"
        }
        
        # Lighting moods (10 options for variety)
        self.lighting_options = [
            "harsh fluorescent lighting (office reality)",
            "golden hour glow (what we're missing while working)",
            "soft diffused natural light through office blinds",
            "dramatic side lighting creating existential shadows)",
            "clean studio lighting with subtle wrongness",
            "blue-hour twilight filtering through glass",
            "overhead pendant lamp creating intimate pool of light",
            "backlit silhouette with rim lighting",
            "multiple light sources creating complex shadows",
            "soft box lighting with intentional lens flare"
        ]
        
        # Scene categories (12 unique scenarios)
        self.scene_categories = {
            "boardroom_mortality": "Conference tables as meditation spaces on mortality",
            "desk_shrine": "Lip balm as sacred object among corporate debris",
            "human_machine": "Hands applying balm while screens glow with AI content",
            "time_death": "Calendars, clocks, countdown timers, the passage of time",
            "sacred_mundane": "Elevating the lip balm to religious icon status",
            "inbox_zen": "Notification chaos surrounding the calm product",
            "floating_workspace": "Minimalist desk suspended in void-like space",
            "calendar_graveyard": "Expired meetings and cancelled syncs memorial",
            "coffee_ring_mandala": "Stains and spills creating sacred geometry",
            "zoom_fatigue_altar": "Camera-off sanctuary with product as centerpiece",
            "ai_confession_booth": "Product positioned between human and screen",
            "burnout_still_life": "Classical still life but with modern exhaustion elements"
        }
        
        # Style references
        self.aesthetic_references = [
            "Kinfolk magazine meets Black Mirror",
            "Medical diagram precision with Wes Anderson color stories",
            "Corporate stock photos but make them surreal",
            "LinkedIn screenshots as fine art",
            "Expensive therapy office aesthetic",
            "Apple product launch meets existential crisis",
            "Minimalist brutalism with soft edges"
        ]
        
        # Background variations (12 options)
        self.background_options = [
            "matte navy gradient fading to cream",
            "soft focus office environment out of focus",
            "geometric honeycomb pattern (subtle, background)",
            "clean white surface with subtle texture",
            "brushed metal desk surface with reflections",
            "soft fabric texture (linen or cotton)",
            "blurred cityscape through office window",
            "abstract navy and gold watercolor wash",
            "minimalist concrete texture",
            "soft gradient from navy to gold to cream",
            "frosted glass with soft bokeh lights",
            "paper texture with coffee ring stains"
        ]
        
        # Compositional styles (10 options)
        self.composition_styles = [
            "rule of thirds with product off-center left",
            "centered symmetry with breathing room",
            "diagonal composition creating dynamic tension",
            "product in foreground, context blurred behind",
            "overhead flat lay with surrounding elements",
            "low angle looking up at product (hero shot)",
            "close-up macro with selective focus",
            "negative space dominant with product small",
            "layered depth with foreground and background",
            "golden ratio spiral composition"
        ]
        
        # Camera angles (8 options)
        self.camera_angles = [
            "straight-on eye level (honest, direct)",
            "slight overhead 45-degree angle",
            "low angle hero shot (aspirational)",
            "extreme close-up macro detail",
            "three-quarter view showing depth",
            "overhead flat lay (editorial style)",
            "side profile with dramatic shadows",
            "Dutch angle (subtle unease)"
        ]
        
        # Texture variations (10 options)
        self.texture_elements = [
            "smooth matte finish with no reflection",
            "subtle sheen catching light beautifully",
            "soft fabric texture in background",
            "hard surface with soft object contrast",
            "paper texture with organic feel",
            "glass surface with subtle reflections",
            "wood grain adding warmth",
            "metal surface adding premium feel",
            "concrete adding brutalist edge",
            "mixed textures creating layered depth"
        ]
        
        # Color mood variations (8 options)
        self.color_moods = [
            "dominant navy with gold accents",
            "cream base with navy and gold highlights",
            "moody darks with single gold spotlight",
            "high key bright with navy shadows",
            "monochromatic navy variations",
            "complementary navy and warm gold",
            "desaturated with single color pop",
            "rich navy fading to ethereal cream"
        ]
        
        # Props with meaning
        self.symbolic_props = [
            "dying succulent (corporate life)",
            "coffee ring stains (time passing)",
            "unread notification badges (digital overwhelm)",
            "expired calendar entries (mortality)",
            "half-written resignation letter",
            "laptop with 47 open tabs",
            "empty inbox zero screenshot (false achievement)",
            "performance review document",
            "motivational poster (ironic)",
            "wellness app notification (ignored)"
        ]
    
    def _analyze_post_mood(self, post: LinkedInPost) -> str:
        """Analyze post content to determine mood for intelligent image matching"""
        content_lower = post.content.lower()
        
        # Detect themes in content
        if any(word in content_lower for word in ['ai', 'automated', 'algorithm', 'chatgpt']):
            return "tech_anxiety"
        elif any(word in content_lower for word in ['meeting', 'calendar', 'zoom', 'sync']):
            return "meeting_exhaustion"
        elif any(word in content_lower for word in ['email', 'slack', 'notification']):
            return "digital_overwhelm"
        elif any(word in content_lower for word in ['burnout', 'exhausted', 'tired']):
            return "burnout"
        elif any(word in content_lower for word in ['deadline', 'quarter', 'review']):
            return "time_pressure"
        elif any(word in content_lower for word in ['human', 'real', 'authentic']):
            return "humanity_seeking"
        else:
            return "existential_general"
    
    def _get_mood_appropriate_elements(self, mood: str) -> Dict[str, List[str]]:
        """Get elements that match the post mood for more coherent images"""
        
        mood_mappings = {
            "tech_anxiety": {
                "scenes": ["ai_confession_booth", "human_machine", "desk_shrine"],
                "props": ["laptop with 47 open tabs", "wellness app notification (ignored)", 
                         "unread notification badges (digital overwhelm)"],
                "compositions": ["product in foreground, context blurred behind",
                               "layered depth with foreground and background"]
            },
            "meeting_exhaustion": {
                "scenes": ["zoom_fatigue_altar", "calendar_graveyard", "boardroom_mortality"],
                "props": ["expired calendar entries (mortality)", "coffee ring stains (time passing)"],
                "compositions": ["overhead flat lay with surrounding elements",
                               "centered symmetry with breathing room"]
            },
            "digital_overwhelm": {
                "scenes": ["inbox_zen", "desk_shrine", "floating_workspace"],
                "props": ["unread notification badges (digital overwhelm)", 
                         "empty inbox zero screenshot (false achievement)"],
                "compositions": ["negative space dominant with product small",
                               "rule of thirds with product off-center left"]
            },
            "burnout": {
                "scenes": ["burnout_still_life", "zoom_fatigue_altar", "sacred_mundane"],
                "props": ["dying succulent (corporate life)", "coffee ring stains (time passing)",
                         "half-written resignation letter"],
                "compositions": ["close-up macro with selective focus",
                               "side profile with dramatic shadows"]
            },
            "time_pressure": {
                "scenes": ["time_death", "calendar_graveyard", "coffee_ring_mandala"],
                "props": ["expired calendar entries (mortality)", "performance review document"],
                "compositions": ["diagonal composition creating dynamic tension",
                               "Dutch angle (subtle unease)"]
            },
            "humanity_seeking": {
                "scenes": ["sacred_mundane", "desk_shrine", "floating_workspace"],
                "props": ["motivational poster (ironic)", "dying succulent (corporate life)"],
                "compositions": ["golden ratio spiral composition",
                               "low angle looking up at product (hero shot)"]
            },
            "existential_general": {
                "scenes": list(self.scene_categories.keys()),
                "props": self.symbolic_props,
                "compositions": self.composition_styles
            }
        }
        
        return mood_mappings.get(mood, mood_mappings["existential_general"])
        
        # Lighting moods (10 options for variety)
        self.lighting_options = [
            "harsh fluorescent lighting (office reality)",
            "golden hour glow (what we're missing while working)",
            "soft diffused natural light through office blinds",
            "dramatic side lighting creating existential shadows",
            "clean studio lighting with subtle wrongness",
            "blue-hour twilight filtering through glass",
            "overhead pendant lamp creating intimate pool of light",
            "backlit silhouette with rim lighting",
            "multiple light sources creating complex shadows",
            "soft box lighting with intentional lens flare"
        ]
        
        # Scene categories (12 unique scenarios)
        self.scene_categories = {
            "boardroom_mortality": "Conference tables as meditation spaces on mortality",
            "desk_shrine": "Lip balm as sacred object among corporate debris",
            "human_machine": "Hands applying balm while screens glow with AI content",
            "time_death": "Calendars, clocks, countdown timers, the passage of time",
            "sacred_mundane": "Elevating the lip balm to religious icon status",
            "inbox_zen": "Notification chaos surrounding the calm product",
            "floating_workspace": "Minimalist desk suspended in void-like space",
            "calendar_graveyard": "Expired meetings and cancelled syncs memorial",
            "coffee_ring_mandala": "Stains and spills creating sacred geometry",
            "zoom_fatigue_altar": "Camera-off sanctuary with product as centerpiece",
            "ai_confession_booth": "Product positioned between human and screen",
            "burnout_still_life": "Classical still life but with modern exhaustion elements"
        }
        
        # Style references
        self.aesthetic_references = [
            "Kinfolk magazine meets Black Mirror",
            "Medical diagram precision with Wes Anderson color stories",
            "Corporate stock photos but make them surreal",
            "LinkedIn screenshots as fine art",
            "Expensive therapy office aesthetic",
            "Apple product launch meets existential crisis",
            "Minimalist brutalism with soft edges"
        ]
        
        # Background variations (12 options)
        self.background_options = [
            "matte navy gradient fading to cream",
            "soft focus office environment out of focus",
            "geometric honeycomb pattern (subtle, background)",
            "clean white surface with subtle texture",
            "brushed metal desk surface with reflections",
            "soft fabric texture (linen or cotton)",
            "blurred cityscape through office window",
            "abstract navy and gold watercolor wash",
            "minimalist concrete texture",
            "soft gradient from navy to gold to cream",
            "frosted glass with soft bokeh lights",
            "paper texture with coffee ring stains"
        ]
        
        # Compositional styles (10 options)
        self.composition_styles = [
            "rule of thirds with product off-center left",
            "centered symmetry with breathing room",
            "diagonal composition creating dynamic tension",
            "product in foreground, context blurred behind",
            "overhead flat lay with surrounding elements",
            "low angle looking up at product (hero shot)",
            "close-up macro with selective focus",
            "negative space dominant with product small",
            "layered depth with foreground and background",
            "golden ratio spiral composition"
        ]
        
        # Camera angles (8 options)
        self.camera_angles = [
            "straight-on eye level (honest, direct)",
            "slight overhead 45-degree angle",
            "low angle hero shot (aspirational)",
            "extreme close-up macro detail",
            "three-quarter view showing depth",
            "overhead flat lay (editorial style)",
            "side profile with dramatic shadows",
            "Dutch angle (subtle unease)"
        ]
        
        # Texture variations (10 options)
        self.texture_elements = [
            "smooth matte finish with no reflection",
            "subtle sheen catching light beautifully",
            "soft fabric texture in background",
            "hard surface with soft object contrast",
            "paper texture with organic feel",
            "glass surface with subtle reflections",
            "wood grain adding warmth",
            "metal surface adding premium feel",
            "concrete adding brutalist edge",
            "mixed textures creating layered depth"
        ]
        
        # Color mood variations (8 options)
        self.color_moods = [
            "dominant navy with gold accents",
            "cream base with navy and gold highlights",
            "moody darks with single gold spotlight",
            "high key bright with navy shadows",
            "monochromatic navy variations",
            "complementary navy and warm gold",
            "desaturated with single color pop",
            "rich navy fading to ethereal cream"
        ]
        
        # Props with meaning
        self.symbolic_props = [
            "dying succulent (corporate life)",
            "coffee ring stains (time passing)",
            "unread notification badges (digital overwhelm)",
            "expired calendar entries (mortality)",
            "half-written resignation letter",
            "laptop with 47 open tabs",
            "empty inbox zero screenshot (false achievement)",
            "performance review document",
            "motivational poster (ironic)",
            "wellness app notification (ignored)"
        ]
    
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
                        scene_category=image_result.get("scene_category")
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
            prompt: Image description/prompt (Jesse brand-aligned)
            post: Optional post for context
            
        Returns:
            Dict with 'saved_path', 'prompt', 'generation_time_seconds', 'size_mb', 'cost'
        """
        start_time = time.time()
        
        try:
            # Enhance prompt with Jesse visual language
            enhanced_prompt = self._enhance_prompt_with_brand_language(prompt)
            
            self.logger.info(
                "Generating image with Jesse A. Eisenbalm visual language",
                model=self.image_model,
                prompt_length=len(enhanced_prompt),
                brand_aesthetic="what if Apple sold mortality?"
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
                "size_mb": round(size_mb, 3),
                "brand_aesthetic": "what if Apple sold mortality?",
                "scene_category": self._extract_scene_category(enhanced_prompt)
            }
            
            self.logger.info(
                "Jesse A. Eisenbalm image generated successfully",
                generation_time=result["generation_time_seconds"],
                size_mb=result["size_mb"],
                saved_path=saved_path,
                scene_category=result["scene_category"]
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
            
            # Generate filename with brand prefix
            if post and hasattr(post, 'id'):
                filename = f"jesse_{post.id}_{uuid.uuid4().hex[:8]}.png"
            else:
                filename = f"jesse_image_{uuid.uuid4().hex[:8]}.png"
            
            output_path = self.output_dir / filename
            
            # Open and save image
            image = Image.open(BytesIO(image_data))
            image.save(output_path, format='PNG')
            
            self.logger.info(f"Jesse A. Eisenbalm image saved to: {output_path}")
            
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
        """Build system prompt for Visual Creative Director"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("ImageGenerationAgent")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for ImageGenerationAgent")
            return custom_prompts["system_prompt"]
        
        # Default system prompt with full Jesse visual identity
        return """You are the Visual Creative Director for Jesse A. Eisenbalm, responsible for creating image prompts that capture our brand's unique position: premium minimalism meets existential dread meets corporate satire.

VISUAL PHILOSOPHY:
"What if Apple sold mortality?"
Clean, minimal, expensive-looking, but with subtle wrongness that creates cognitive dissonance. Every image should feel like it belongs in MoMA's gift shop and a therapist's waiting room simultaneously.

BRAND VISUAL LANGUAGE:
- COLOR PALETTE: Deep navy (the color of 3 AM anxiety), gold (false hope), cream (the void), with occasional "error message red"
- MOTIF: Honeycomb structure with pictures of Jesse A. Eisenbalm lip balm tube
- TEXTURE: Matte surfaces that suggest "premium depression"
- LIGHTING: Either harsh fluorescent (office reality) or golden hour (what we're missing while working)
- COMPOSITION: Symmetric when showing order, deliberately off-center when showing human chaos
- DESIGN ELEMENT: Occasional smear of lip balm creating visual texture

PROMPT CONSTRUCTION FRAMEWORK:
1. SETTING: Specify exact environment with psychological weight
2. PRODUCT PLACEMENT: Tube positioned as hero, savior, or ironic commentary
3. LIGHTING: Describe quality, direction, and emotional impact
4. PROPS: Minimal but loaded with meaning (dying succulents, error messages, coffee stains)
5. MOOD: The feeling between "everything is fine" and "nothing is fine"

STYLE REFERENCES:
- Kinfolk magazine meets Black Mirror
- Medical diagram precision with Wes Anderson color stories
- Corporate stock photos but make them surreal
- LinkedIn post screenshots as fine art
- The aesthetic of expensive therapy offices
- Apple product launches meets existential crisis

SCENE CATEGORIES:
- "Boardroom Mortality": Conference tables as meditation spaces
- "Desk Shrine": Lip balm among the corporate debris
- "Human/Machine Interface": Hands applying balm while AI generates content
- "Time Death": Calendars, clocks, countdown timers, expired passwords
- "Sacred Mundane": Elevating the lip balm to religious icon status

AVOID:
- Generic wellness imagery
- Obvious happiness
- Natural/organic clichés
- Typical beauty product shots
- Any suggestion that everything will be okay

Create prompts that are 150-200 words with precise visual detail, emotional subtext, and that perfect tension between "premium product" and "we're all slowly dying."
"""
    
    async def _create_image_prompt(self, post: LinkedInPost) -> str:
        """Create a detailed Jesse A. Eisenbalm image prompt from the post content"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("ImageGenerationAgent")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for ImageGenerationAgent")
            try:
                return custom_prompts["user_prompt_template"].format(
                    content=post.content[:300],
                    post_id=post.id
                )
            except Exception as e:
                self.logger.warning(f"Failed to format custom template: {e}, using default")
        
        try:
            system_prompt = self._build_system_prompt()
            
            # INTELLIGENT SELECTION: Analyze post mood for coherent image matching
            post_mood = self._analyze_post_mood(post)
            mood_elements = self._get_mood_appropriate_elements(post_mood)
            
            # Select from mood-appropriate options (70% match) or completely random (30% surprise)
            use_mood_matching = random.random() < 0.7
            
            if use_mood_matching and mood_elements:
                # Select from mood-appropriate elements
                scene_key = random.choice(mood_elements["scenes"])
                scene_category = self.scene_categories.get(scene_key, random.choice(list(self.scene_categories.values())))
                symbolic_prop = random.choice(mood_elements["props"])
                composition = random.choice(mood_elements["compositions"])
            else:
                # Full random for surprise and variety
                scene_category = random.choice(list(self.scene_categories.values()))
                symbolic_prop = random.choice(self.symbolic_props)
                composition = random.choice(self.composition_styles)
            
            # Always randomize these for maximum variety
            lighting_mood = random.choice(self.lighting_options)
            aesthetic_ref = random.choice(self.aesthetic_references)
            background = random.choice(self.background_options)
            camera_angle = random.choice(self.camera_angles)
            texture = random.choice(self.texture_elements)
            color_mood = random.choice(self.color_moods)
            
            self.logger.info(
                "Creating image with intelligent variety",
                post_mood=post_mood,
                mood_matching=use_mood_matching,
                scene=scene_key if use_mood_matching else "random",
                composition=composition[:30]
            )
            
            user_prompt = f"""Create a detailed image prompt for Jesse A. Eisenbalm product photography.

POST CONTENT CONTEXT:
{post.content[:300]}

POST MOOD DETECTED: {post_mood}

UNIQUE VISUAL DIRECTION FOR THIS IMAGE:

SCENE: {scene_category}

COMPOSITION: {composition}

CAMERA ANGLE: {camera_angle}

BACKGROUND: {background}

LIGHTING: {lighting_mood}

TEXTURE: {texture}

COLOR MOOD: {color_mood}

AESTHETIC REFERENCE: {aesthetic_ref}

SYMBOLIC PROP: {symbolic_prop}

BRAND REQUIREMENTS:
- Product: Jesse A. Eisenbalm lip balm tube (navy blue with gold honeycomb, pictures of Jesse)
- Color Palette: Deep navy, gold accents, cream tones, optional error red
- Mood: Between "everything is fine" and "nothing is fine"
- Style: Premium minimalism meets existential dread
- Design Element: Consider subtle lip balm smear as texture

CRITICAL: Create a UNIQUE image that has NEVER been created before by combining these elements in an unexpected way.

Generate a DETAILED image prompt (150-200 words) for professional product photography that captures:
1. Exact setting with psychological weight
2. Product positioned using the specified composition and camera angle
3. Specific lighting quality and emotional impact
4. Background that enhances without distracting
5. Textures that add depth and premium feel
6. Color mood that supports the brand tension
7. Minimal props loaded with meaning
8. The cognitive dissonance of luxury mortality

Remember: "What if Apple sold mortality?" Clean, expensive, but something is subtly wrong.

Make this image DISTINCTLY DIFFERENT from any other Jesse A. Eisenbalm image by using this unique combination of elements."""

            response = await self._call_ai(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="text"
            )
            
            image_prompt = response.get("content", "")
            
            if image_prompt and len(image_prompt) > 100:
                self.logger.info(
                    "Generated Jesse A. Eisenbalm image prompt via AI",
                    post_id=post.id,
                    prompt_length=len(image_prompt),
                    scene_category=scene_category
                )
                return image_prompt
            else:
                return self._create_branded_fallback_prompt(post, scene_category)
        
        except Exception as e:
            self.logger.warning(
                "Failed to generate AI image prompt, using branded fallback",
                error=str(e)
            )
            return self._create_branded_fallback_prompt(post)
    
    def _create_branded_fallback_prompt(
        self, 
        post: LinkedInPost, 
        scene_category: Optional[str] = None
    ) -> str:
        """Create a Jesse A. Eisenbalm branded fallback image prompt with dynamic variety"""
        
        if not scene_category:
            scene_category = random.choice(list(self.scene_categories.values()))
        
        # Select UNIQUE combination for this image
        lighting = random.choice(self.lighting_options)
        prop = random.choice(self.symbolic_props)
        aesthetic = random.choice(self.aesthetic_references)
        background = random.choice(self.background_options)
        composition = random.choice(self.composition_styles)
        camera_angle = random.choice(self.camera_angles)
        texture = random.choice(self.texture_elements)
        color_mood = random.choice(self.color_moods)
        
        return f"""Professional product photograph of Jesse A. Eisenbalm premium lip balm tube.

PRODUCT DETAILS: Navy blue tube with gold honeycomb pattern featuring pictures of Jesse. Premium matte finish suggesting "expensive minimalism meets mortality awareness."

SCENE: {scene_category}

COMPOSITION: {composition}

CAMERA ANGLE: {camera_angle}

BACKGROUND: {background}

PRODUCT PLACEMENT: Jesse A. Eisenbalm tube positioned as the hero object. {prop} visible in scene, creating narrative tension.

LIGHTING: {lighting}. Soft shadows creating depth. Subtle vignette drawing eye to product.

TEXTURE: {texture}. Subtle lip balm smear creating visual interest and catching light beautifully.

COLOR GRADING: {color_mood}

MOOD: The exact feeling between "everything is fine" and "nothing is fine." Professional corporate aesthetic with subtle existential undertones.

STYLE: {aesthetic}. Clean lines, minimal but loaded with meaning. Premium product photography that makes you question mortality.

TECHNICAL: 8K, ultra-detailed, commercial photography, professional studio quality, subtle depth of field, sophisticated color grading.

EMOTIONAL TONE: Calm surface tension. Expensive but honest. "What if Apple sold mortality?"

UNIQUENESS: This specific combination of composition ({composition}), camera angle ({camera_angle}), and background ({background}) creates a NEVER-BEFORE-SEEN image.
        """
    
    def _enhance_prompt_with_brand_language(self, prompt: str) -> str:
        """Enhance prompt with Jesse A. Eisenbalm brand visual language"""
        
        # Essential brand elements to ensure
        brand_elements = {
            "product_identity": "Jesse A. Eisenbalm premium lip balm",
            "brand_colors": "deep navy blue, rich gold accents, soft cream tones",
            "motif": "honeycomb pattern with pictures of Jesse",
            "texture": "premium matte finish",
            "philosophy": "what if Apple sold mortality? - clean, minimal, expensive with subtle wrongness"
        }
        
        # Check if essential elements are present
        has_product = any(term in prompt.lower() for term in ['jesse', 'lip balm', 'tube'])
        has_colors = any(color in prompt.lower() for color in ['navy', 'gold', 'cream'])
        has_mood = any(term in prompt.lower() for term in ['mortality', 'existential', 'corporate', 'anxiety'])
        
        # Add missing essential elements
        enhancements = []
        
        if not has_product:
            enhancements.append(
                f"Product: {brand_elements['product_identity']} tube with {brand_elements['motif']}"
            )
        
        if not has_colors:
            enhancements.append(
                f"Color palette: {brand_elements['brand_colors']}"
            )
        
        if not has_mood:
            enhancements.append(
                f"Visual philosophy: {brand_elements['philosophy']}"
            )
        
        # Always add technical quality
        quality_specs = [
            "8K resolution, ultra-detailed",
            "Professional commercial photography",
            "Sophisticated color grading",
            "Premium studio lighting",
            "Sharp focus with professional depth of field",
            "Subtle vignette and matte finish"
        ]
        
        # Combine original prompt with enhancements
        if enhancements:
            enhanced = f"{prompt}\n\nBRAND ESSENTIALS:\n" + "\n".join(enhancements)
        else:
            enhanced = prompt
        
        # Add technical specifications
        enhanced += "\n\nTECHNICAL SPECIFICATIONS:\n" + "\n".join(quality_specs)
        
        return enhanced
    
    def _extract_scene_category(self, prompt: str) -> str:
        """Extract which scene category was used in the prompt"""
        prompt_lower = prompt.lower()
        
        for category_key, category_desc in self.scene_categories.items():
            if category_key.replace("_", " ") in prompt_lower or category_desc.lower() in prompt_lower:
                return category_key
        
        return "custom_scene"
    
    def _create_image_description(self, post: LinkedInPost) -> str:
        """Create a user-facing description of what the image shows"""
        if hasattr(post, 'cultural_reference') and post.cultural_reference:
            ref = post.cultural_reference.reference
            return f"Jesse A. Eisenbalm: Premium minimalism meets existential awareness. Inspired by {ref}."
        
        return "Jesse A. Eisenbalm: What if Apple sold mortality? Professional product photography with subtle wrongness."

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
        """
        alt_text = self._create_image_description(post)

        # ---- Attempt 1: Keyword args with prompt (modern, likely) ----
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
            post.set_image(saved_path, image_prompt, alt_text, "google_gemini")
            self._maybe_attach_metadata_fields(post, image_result, saved_path)
            return True
        except TypeError as e:
            self.logger.warning("set_image(url, prompt, description, provider) positional not supported; retrying", error=str(e))

        # ---- Attempt 3: Minimal call then set attributes directly ----
        try:
            post.set_image(saved_path, image_prompt)
            self._maybe_attach_metadata_fields(post, image_result, saved_path)
            if hasattr(post, "image_description"):
                post.image_description = alt_text
            if hasattr(post, "image_provider"):
                post.image_provider = "google_gemini"
            if hasattr(post, "has_image"):
                post.has_image = True
            return True
        except TypeError as e:
            self.logger.error("All set_image attachment attempts failed", error=str(e))

        # Final fallback: set attributes directly
        try:
            if hasattr(post, "image_url"):
                post.image_url = saved_path
            if hasattr(post, "image_prompt"):
                post.image_prompt = image_prompt
            if hasattr(post, "image_description"):
                post.image_description = alt_text
            if hasattr(post, "image_provider"):
                post.image_provider = "google_gemini"
            if hasattr(post, "image_generation_time"):
                post.image_generation_time = image_result.get("generation_time_seconds")
            if hasattr(post, "image_size_mb"):
                post.image_size_mb = image_result.get("size_mb")
            if hasattr(post, "image_cost"):
                post.image_cost = image_result.get("cost", 0.039)
            if hasattr(post, "image_metadata"):
                meta = {
                    "model": image_result.get("model"),
                    "provider": image_result.get("provider"),
                    "saved_path": saved_path,
                    "original_prompt": image_result.get("original_prompt"),
                    "brand_aesthetic": "what if Apple sold mortality?",
                    "scene_category": image_result.get("scene_category")
                }
                if isinstance(post.image_metadata, dict):
                    post.image_metadata.update(meta)
                else:
                    setattr(post, "image_metadata", meta)
            if hasattr(post, "has_image"):
                post.has_image = True
            return bool(getattr(post, "image_url", None))
        except Exception as e:
            self.logger.error("Failed to set image fields directly on post", error=str(e))
            return False

    def _maybe_attach_metadata_fields(self, post: LinkedInPost, image_result: Dict[str, Any], saved_path: str) -> None:
        """Attach Jesse A. Eisenbalm image metadata to the post"""
        try:
            if hasattr(post, "image_url") and not getattr(post, "image_url", None):
                post.image_url = saved_path
            if hasattr(post, "image_generation_time") and image_result.get("generation_time_seconds") is not None:
                post.image_generation_time = image_result.get("generation_time_seconds")
            if hasattr(post, "image_size_mb") and image_result.get("size_mb") is not None:
                post.image_size_mb = image_result.get("size_mb")
            if hasattr(post, "image_cost") and image_result.get("cost") is not None:
                post.image_cost = image_result.get("cost")
            if hasattr(post, "image_metadata"):
                meta = {
                    "model": image_result.get("model"),
                    "provider": image_result.get("provider"),
                    "saved_path": saved_path,
                    "prompt_used": image_result.get("prompt"),
                    "original_prompt": image_result.get("original_prompt"),
                    "brand_aesthetic": "what if Apple sold mortality?",
                    "scene_category": image_result.get("scene_category"),
                    "visual_philosophy": "premium minimalism meets existential dread"
                }
                if isinstance(post.image_metadata, dict):
                    post.image_metadata.update(meta)
                else:
                    setattr(post, "image_metadata", meta)
            if hasattr(post, "has_image"):
                post.has_image = True
        except Exception as e:
            self.logger.warning("Non-fatal: failed to attach Jesse image metadata fields", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics including Jesse A. Eisenbalm branding info"""
        base_stats = super().get_stats()
        
        # Calculate total unique combinations possible
        total_combinations = (
            len(self.scene_categories) *
            len(self.lighting_options) *
            len(self.background_options) *
            len(self.composition_styles) *
            len(self.camera_angles) *
            len(self.texture_elements) *
            len(self.color_moods) *
            len(self.aesthetic_references) *
            len(self.symbolic_props)
        )
        
        base_stats.update({
            "image_model": self.image_model,
            "image_enabled": self.use_images,
            "has_google_api_key": bool(self.google_api_key),
            "image_cost_per_generation": 0.039,
            "output_directory": str(self.output_dir),
            "brand_visual_philosophy": "what if Apple sold mortality?",
            "variety_systems": {
                "scene_categories": len(self.scene_categories),
                "lighting_options": len(self.lighting_options),
                "backgrounds": len(self.background_options),
                "compositions": len(self.composition_styles),
                "camera_angles": len(self.camera_angles),
                "textures": len(self.texture_elements),
                "color_moods": len(self.color_moods),
                "aesthetic_refs": len(self.aesthetic_references),
                "symbolic_props": len(self.symbolic_props),
                "total_unique_combinations": f"{total_combinations:,}"
            },
            "intelligent_features": {
                "mood_detection": True,
                "content_aware_selection": True,
                "mood_matching_rate": "70%",
                "surprise_variation_rate": "30%"
            },
            "using_custom_prompts": self.prompt_manager.has_custom_prompts("ImageGenerationAgent")
        })
        
        return base_stats