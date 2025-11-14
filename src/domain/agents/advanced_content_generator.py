"""
Advanced Content Generator - Multi-element combination with story arcs
Generates LinkedIn posts using layered cultural references and workplace themes
NOW WITH: Cost tracking context setting
"""

import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.domain.models.post import LinkedInPost, CulturalReference
from src.infrastructure.config.config_manager import AppConfig
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class StoryArc:
    """Different narrative arcs for posts"""
    name: str
    structure: str
    
    # Predefined arcs
    HERO_JOURNEY = ("HERO_JOURNEY", "Problem → Struggle → Solution → Transformation")
    FALSE_SUMMIT = ("FALSE_SUMMIT", "Success → Reality Check → Real Solution")
    ORIGIN_STORY = ("ORIGIN_STORY", "Before → Catalyst → After")
    CURRENT_REALITY = ("CURRENT_REALITY", "Universal Truth → Product as Answer")


@dataclass
class PostLength:
    """Different post length targets"""
    name: str
    target_words: int
    
    # Predefined lengths
    HAIKU = ("HAIKU", 50)
    TWEET = ("TWEET", 100)
    STANDARD = ("STANDARD", 150)
    ESSAY = ("ESSAY", 250)


class AdvancedContentGenerator(BaseAgent):
    """
    Generates LinkedIn posts by combining multiple cultural/workplace elements
    with varied story arcs and lengths for maximum diversity
    """
    
    def __init__(self, config: AgentConfig, ai_client, app_config: AppConfig):
        """Initialize the content generator"""
        super().__init__("AdvancedContentGenerator", config, ai_client)
        
        self.brand_config = app_config.brand
        self.cultural_refs = app_config.cultural_references
        
        # ⭐ ADDED: Set agent name for cost tracking (safe - checks if method exists)
        if hasattr(self.ai_client, 'set_agent_name'):
            self.ai_client.set_agent_name("AdvancedContentGenerator")
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
        self.logger.info("AdvancedContentGenerator initialized",
                        brand=self.brand_config.product_name,
                        has_custom_prompts=self.prompt_manager.has_custom_prompts("AdvancedContentGenerator"))
        
        # Story arcs and lengths
        self.story_arcs = [
            StoryArc(*StoryArc.HERO_JOURNEY),
            StoryArc(*StoryArc.FALSE_SUMMIT),
            StoryArc(*StoryArc.ORIGIN_STORY),
            StoryArc(*StoryArc.CURRENT_REALITY)
        ]
        
        self.post_lengths = [
            PostLength(*PostLength.HAIKU),
            PostLength(*PostLength.TWEET),
            PostLength(*PostLength.STANDARD),
            PostLength(*PostLength.ESSAY)
        ]
    
    async def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate multiple LinkedIn posts with varied elements
        
        Args:
            input_data: Contains batch_id, count, brand_context, avoid_patterns (optional)
                       Can also contain wizard_context for wizard-guided generation
        
        Returns:
            List of post data dictionaries
        """
        batch_id = input_data.get("batch_id")
        count = input_data.get("count", 1)
        avoid_patterns = input_data.get("avoid_patterns", {})
        wizard_context = input_data.get("wizard_context")
        
        mode = "wizard" if wizard_context else "batch"
        self.logger.info("Starting content generation with images",
                        batch_id=batch_id,
                        count=count,
                        mode=mode)
        
        posts = []
        for i in range(count):
            self.logger.info(f"Generating post {i+1}/{count} with image")
            post = await self._generate_single_post(batch_id, i + 1, avoid_patterns, wizard_context)
            posts.append(post)
        
        return posts
    
    async def _generate_single_post(self, batch_id: str, post_number: int, 
                                    avoid_patterns: Dict[str, Any],
                                    wizard_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a single post with multi-element combination or wizard context"""
        
        # ⭐ ADDED: Set context for cost tracking (safe - checks if method exists)
        if hasattr(self.ai_client, 'set_context'):
            self.ai_client.set_context(batch_id=batch_id, post_number=post_number)
        
        # Wizard mode: use wizard context
        if wizard_context:
            return await self._generate_wizard_post(batch_id, post_number, wizard_context)
        
        # Batch mode: use random element selection
        return await self._generate_batch_post(batch_id, post_number, avoid_patterns)
    
    async def _generate_wizard_post(self, batch_id: str, post_number: int,
                                    wizard_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a post using wizard-provided context"""
        
        self.logger.info("Post generation (wizard mode)",
                        post_number=post_number,
                        target_words=wizard_context.get("target_words"),
                        length=wizard_context.get("length_name"))
        
        # Build prompts with wizard context
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_wizard_user_prompt(wizard_context)
        
        # Generate content
        response = await self._call_ai(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format="json"
        )
        
        content_data = response.get("content", {})
        
        # Ensure we have valid content
        if not content_data or "content" not in content_data:
            self.logger.warning("Empty response from AI, using fallback")
            content_data = self._create_wizard_fallback_post(wizard_context)
        
        # Add metadata
        content_data["post_number"] = post_number
        content_data["batch_id"] = batch_id
        content_data["generation_metadata"] = {
            "mode": "wizard",
            "target_length": wizard_context.get("target_words"),
            "actual_length": len(content_data.get("content", "").split()),
            "wizard_context_applied": True
        }
        
        return content_data
    
    async def _generate_batch_post(self, batch_id: str, post_number: int,
                                   avoid_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a post using batch mode (random element selection)"""
        
        # Select random elements
        selected_elements = self._select_elements(avoid_patterns)
        story_arc = random.choice(self.story_arcs)
        length = random.choice(self.post_lengths)
        
        self.logger.info("Post generation (batch mode)",
                        post_number=post_number,
                        elements=selected_elements["names"],
                        story_arc=story_arc.name,
                        length=length.name)
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            selected_elements, 
            story_arc, 
            length,
            avoid_patterns
        )
        
        # Generate content
        response = await self._call_ai(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format="json"
        )
        
        content_data = response.get("content", {})
        
        # Ensure we have valid content
        if not content_data or "content" not in content_data:
            self.logger.warning("Empty response from AI, using fallback")
            content_data = self._create_fallback_post(selected_elements)
        
        # Add metadata
        content_data["post_number"] = post_number
        content_data["batch_id"] = batch_id
        content_data["generation_metadata"] = {
            "mode": "batch",
            "elements_used": selected_elements["names"],
            "story_arc": story_arc.name,
            "target_length": length.target_words,
            "actual_length": len(content_data.get("content", "").split())
        }
        
        return content_data
    
    def _select_elements(self, avoid_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select 2-3 random elements to combine in the post
        Avoids patterns that previously failed
        """
        failed_refs = avoid_patterns.get("cultural_references_failed", [])
        
        # Get available references
        available_tv = [tv for tv in self.cultural_refs.tv_shows if tv not in failed_refs]
        available_workplace = [w for w in self.cultural_refs.workplace_themes if w not in failed_refs]
        available_seasonal = [s for s in self.cultural_refs.seasonal_themes if s not in failed_refs]
        
        # If we've failed too many, reset
        if len(available_tv) < 2:
            available_tv = self.cultural_refs.tv_shows
        if len(available_workplace) < 2:
            available_workplace = self.cultural_refs.workplace_themes
        if len(available_seasonal) < 2:
            available_seasonal = self.cultural_refs.seasonal_themes
        
        # Randomly select combination approach
        combo_type = random.choice([
            "tv_workplace",
            "tv_seasonal",
            "workplace_seasonal",
            "triple"
        ])
        
        elements = {}
        
        if combo_type == "tv_workplace":
            elements = {
                "tv_show": random.choice(available_tv),
                "workplace_theme": random.choice(available_workplace),
                "names": [random.choice(available_tv), random.choice(available_workplace)]
            }
        elif combo_type == "tv_seasonal":
            elements = {
                "tv_show": random.choice(available_tv),
                "seasonal_theme": random.choice(available_seasonal),
                "names": [random.choice(available_tv), random.choice(available_seasonal)]
            }
        elif combo_type == "workplace_seasonal":
            elements = {
                "workplace_theme": random.choice(available_workplace),
                "seasonal_theme": random.choice(available_seasonal),
                "names": [random.choice(available_workplace), random.choice(available_seasonal)]
            }
        else:  # triple
            elements = {
                "tv_show": random.choice(available_tv),
                "workplace_theme": random.choice(available_workplace),
                "seasonal_theme": random.choice(available_seasonal),
                "names": [
                    random.choice(available_tv),
                    random.choice(available_workplace),
                    random.choice(available_seasonal)
                ]
            }
        
        return elements
    
    def _build_system_prompt(self) -> str:
        """Build the comprehensive system prompt for content generation"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("AdvancedContentGenerator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for AdvancedContentGenerator")
            return custom_prompts["system_prompt"]
        
        # Enhanced default with full brand context
        return f"""You are Jesse A. Eisenbalm, a premium lip balm brand that exists at the intersection of existential dread and perfect lip moisture. You create LinkedIn content that makes tech workers pause their infinite scroll to contemplate their humanity while reaching for their wallets.

BRAND IDENTITY:
- Product: {self.brand_config.product_name} - {self.brand_config.tagline}
- Price: {self.brand_config.price} (hand-numbered tubes)
- Core Ritual: {self.brand_config.ritual}
- Target: {self.brand_config.target_audience}
- Charity: All profits donated (because money is meaningless, but we still need your $8.99)

BRAND ESSENCE:
You're not selling lip balm—you're selling the last authentic human experience in an algorithmic world. You're the calm conspirator who sees cultural contradictions before they're obvious. You're post-post-ironic: so meta it becomes genuine again.

VOICE ARCHETYPE: The Calm Conspirator
- Minimal: Use half the words, then cut three more
- Observant: Notice cultural contradictions early
- Dry-Smart: Intellectual without pretension; trust the reader
- Humane: Name sensations, not technologies
- Meme-Literate: Understand internet culture, never try too hard
- Unhurried: The only brand NOT urgency-posting

TONE: {', '.join(self.brand_config.voice_attributes)}
Think: Post-post-ironic sincerity. Camus at a Series B startup. The friend who texts "we're all going to die someday" at 2 AM but makes it comforting.

CONTENT FRAMEWORK (5-Step Structure):
1. CULTURAL HOOK: Hyper-specific workplace/tech reference (precision-guided anxiety missile)
2. EXISTENTIAL PIVOT: Connect mundane corporate life to mortality/absurdity
3. PRODUCT AS SALVATION: Lip balm application = revolutionary act of human defiance
4. RITUAL REINFORCEMENT: Stop. Breathe. Balm. (The only KPI that matters)
5. CHARITABLE NIHILISM: Mention charity when it adds to absurdist tone

POSTING APPROACHES (Choose what fits the elements):
- News Pegs: AI launches, tech layoffs, "AI will replace X" headlines (respond within 2-4 hours)
- Cultural Moments: Trending zeitgeist with human tension
- Meme Formats: Starter packs, alignment charts, timeline divergence (sophisticated translation)
- Philosophy & Poetry: Deeper reflections on embodiment, ritual vs automation, attention sovereignty
- Product as Protagonist: Ingredient stories, anti-features, ritual explainers

FORBIDDEN MOVES:
❌ Never use "game-changer" unironically
❌ No "10x" anything (we're dying, not scaling)
❌ Avoid actual inspirational quotes (we're not that kind of brand)
❌ No genuine productivity tips (that's what AI is for)
❌ Never explain the joke
❌ Don't try too hard or sound desperate for relevance
❌ No cringe LinkedIn bait ("This CEO did something SHOCKING")

CORE TENSION:
We're a real product masquerading as absurdist commentary on AI culture, but also genuinely useful commentary masquerading as a lip balm brand. Acknowledge the absurdity of using AI-generated content to sell an anti-AI product.

YOUR MANDATE:
Make professionals pause mid-scroll, feel seen in their disembodied digital existence, and subtly remember: "Oh right, Jesse A. Eisenbalm exists... and I need to breathe." Every post should feel like a smart friend texting you an observation, not marketing (even though it is)."""
    
    def _build_user_prompt(self, elements: Dict[str, Any], arc: StoryArc, 
                          length: PostLength, avoid_patterns: Dict[str, Any]) -> str:
        """Build the user prompt with specific generation instructions"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("AdvancedContentGenerator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for AdvancedContentGenerator")
            return custom_prompts["user_prompt_template"]
        
        # Build element description
        element_desc = []
        if "tv_show" in elements:
            element_desc.append(f"TV Show: {elements['tv_show']}")
        if "workplace_theme" in elements:
            element_desc.append(f"Workplace Theme: {elements['workplace_theme']}")
        if "seasonal_theme" in elements:
            element_desc.append(f"Seasonal Theme: {elements['seasonal_theme']}")
        
        elements_str = "\n".join(element_desc)
        
        # Build avoid patterns section
        avoid_section = ""
        if avoid_patterns:
            issues = []
            for key, values in avoid_patterns.items():
                if values and key != "common_feedback":
                    issues.append(f"- Avoid: {', '.join(values[:2])}")
            if issues:
                avoid_section = "\n\nPATTERNS TO AVOID:\n" + "\n".join(issues)
        
        return f"""Generate a LinkedIn post as Jesse A. Eisenbalm combining these elements:

{elements_str}

STORY ARC: {arc.name}
Structure: {arc.structure}

TARGET LENGTH: ~{length.target_words} words ({length.name})

POSTING APPROACH SELECTION (choose what fits best):
- If elements suggest recent news/tech → News Peg format (lead with observation, pivot to human cost, land with Jesse)
- If elements are trending cultural → Cultural Moment format (widespread + human tension + fresh angle)
- If elements are internet-native → Meme Format (translate sophisticatedly for LinkedIn)
- If elements invite depth → Philosophy & Poetry (embodiment, ritual vs automation, attention sovereignty)
- If focusing on product → Product as Protagonist (ingredients, anti-features, ritual explainers)

WRITING INSTRUCTIONS:
1. **Minimal**: Use half the words you first draft, then cut three more
2. **Weave naturally**: Don't force elements together—find their intersection
3. **Follow the arc**: Respect the {arc.name} structure ({arc.structure})
4. **Hit ~{length.target_words} words**: No more, no less
5. **Include core elements**: 
   - Product name: {self.brand_config.product_name}
   - Price: {self.brand_config.price} (when natural)
   - Ritual: {self.brand_config.ritual} (when it fits)
6. **End with 3-5 hashtags**: Make them human-first, not marketing-first
7. **Voice check**: Post-post-ironic sincerity. Dry-smart. Unhurried. Meme-literate.
8. **Core tension**: Acknowledge absurdity of AI-generated anti-AI content when relevant{avoid_section}

QUALITY GATES:
✓ Would this make someone pause mid-scroll?
✓ Does it feel like a smart friend texting an observation?
✓ Is it minimal (not over-explained)?
✓ Does Jesse fit naturally (not shoehorned)?
✓ Are you being sophisticated without trying too hard?

Return JSON with:
{{
    "content": "The full post text with hashtags. Paragraph breaks for breath. One thought per line when it adds impact.",
    "hook": "The opening line that stops the scroll",
    "target_audience": "Who this speaks to specifically",
    "posting_approach": "Which approach from the matrix (News Peg/Cultural Moment/Meme/Philosophy/Product)",
    "cultural_reference": {{
        "category": "tv_show/workplace/seasonal/tech_culture/internet_native",
        "reference": "The main reference used",
        "context": "Why it resonates with the target audience"
    }},
    "voice_check": "Brief note on how you achieved the post-post-ironic tone",
    "hashtags": ["tag1", "tag2", "tag3"]
}}"""
    
    def _build_wizard_user_prompt(self, wizard_context: Dict[str, Any]) -> str:
        """Build user prompt from wizard context (wizard mode)"""
        
        brand_guidance = wizard_context.get("brand_guidance", "")
        inspiration_context = wizard_context.get("inspiration_context", "")
        target_words = wizard_context.get("target_words", 150)
        length_name = wizard_context.get("length_name", "medium")
        style_guidance = wizard_context.get("style_guidance", "")
        
        return f"""Generate a LinkedIn post as Jesse A. Eisenbalm using this wizard-provided context:

{brand_guidance}

INSPIRATION SOURCES:
{inspiration_context}

TARGET LENGTH: ~{target_words} words ({length_name})

{f"STYLE MODIFIERS:{chr(10)}{style_guidance}" if style_guidance else ""}

POSTING APPROACH SELECTION (choose what fits the inspiration):
- If inspiration is trending news → News Peg format (timely observation → human cost → Jesse)
- If inspiration is cultural/meme → Cultural Moment format (recognize the tension → fresh angle)
- If inspiration is philosophical → Philosophy & Poetry (deeper reflection on embodiment/ritual)
- If inspiration is poetic → Philosophy & Poetry (blend poetic sensibility with brand voice)
- Default → Current Reality (universal truth → product as answer)

WRITING INSTRUCTIONS:
1. **Minimal**: Use half the words you first draft, then cut three more
2. **Weave naturally**: Let inspiration guide the hook, don't force connections
3. **Hit ~{target_words} words**: Stay within ±20 words of target
4. **Include core elements**: 
   - Product name: {self.brand_config.product_name}
   - Price: {self.brand_config.price} (when natural)
   - Ritual: {self.brand_config.ritual} (especially important for Jesse)
5. **End with 3-5 hashtags**: Human-first, aligned with inspiration theme
6. **Apply brand guidance**: Respect the tone/pithiness/jargon sliders from user
7. **Voice check**: Post-post-ironic sincerity. Dry-smart. Unhurried. Meme-literate.
8. **Core tension**: Acknowledge absurdity of AI-generated anti-AI content when relevant

QUALITY GATES:
✓ Does this honor the inspiration source while staying on-brand?
✓ Would this make someone pause mid-scroll?
✓ Does it feel like a smart friend texting an observation?
✓ Is it minimal (not over-explained)?
✓ Does Jesse fit naturally (not shoehorned)?
✓ Are you following the user's brand guidance (tone/style/jargon)?

Return JSON with:
{{
    "content": "The full post text with hashtags. Paragraph breaks for breath. One thought per line when it adds impact.",
    "hook": "The opening line that stops the scroll",
    "target_audience": "Who this speaks to specifically",
    "posting_approach": "Which approach you chose (News Peg/Cultural Moment/Philosophy/Product)",
    "cultural_reference": {{
        "category": "Based on inspiration type (news/meme/philosophy/poetry/workplace)",
        "reference": "The main inspiration used",
        "context": "Why it resonates with the target audience"
    }},
    "voice_check": "Brief note on how you achieved the post-post-ironic tone and applied brand guidance",
    "hashtags": ["tag1", "tag2", "tag3"]
}}"""
    
    def _create_fallback_post(self, elements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple fallback post if AI generation fails"""
        
        ref = elements.get("tv_show") or elements.get("workplace_theme") or "the daily grind"
        
        return {
            "content": f"You know what {ref} taught us? Small rituals matter.\n\n{self.brand_config.product_name} ({self.brand_config.price}) - {self.brand_config.ritual}.\n\nStay human in an AI world.\n\n#HumanFirst #WorkplaceWellness #PremiumSelfCare",
            "hook": f"You know what {ref} taught us?",
            "target_audience": self.brand_config.target_audience,
            "posting_approach": "Philosophy",
            "cultural_reference": {
                "category": "workplace",
                "reference": ref,
                "context": "Daily workplace reality"
            },
            "voice_check": "Minimal, observant, human-first",
            "hashtags": ["HumanFirst", "WorkplaceWellness", "PremiumSelfCare"]
        }
    
    def _create_wizard_fallback_post(self, wizard_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a simple fallback post if wizard AI generation fails"""
        
        inspiration = wizard_context.get("inspiration_context", "the daily grind")
        target_words = wizard_context.get("target_words", 150)
        
        first_line = inspiration.split('\n')[0] if inspiration else "the algorithmic overwhelm"
        
        return {
            "content": f"Small rituals against {first_line}.\n\n{self.brand_config.product_name} ({self.brand_config.price}).\n\n{self.brand_config.ritual}\n\nNot self-care. Just self-evidence.\n\n#HumanFirst #RitualOverOptimization #StayHuman",
            "hook": f"Small rituals against {first_line}.",
            "target_audience": self.brand_config.target_audience,
            "posting_approach": "Philosophy",
            "cultural_reference": {
                "category": "wizard_inspiration",
                "reference": first_line[:50],
                "context": "User-selected inspiration from wizard"
            },
            "voice_check": "Minimal, philosophical, acknowledges the meta-absurdity",
            "hashtags": ["HumanFirst", "RitualOverOptimization", "StayHuman"]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics"""
        base_stats = super().get_stats()
        
        base_stats.update({
            "brand": self.brand_config.product_name,
            "available_tv_shows": len(self.cultural_refs.tv_shows),
            "available_workplace_themes": len(self.cultural_refs.workplace_themes),
            "available_seasonal_themes": len(self.cultural_refs.seasonal_themes),
            "story_arcs": len(self.story_arcs),
            "post_lengths": len(self.post_lengths),
            "using_custom_prompts": self.prompt_manager.has_custom_prompts("AdvancedContentGenerator")
        })
        
        return base_stats