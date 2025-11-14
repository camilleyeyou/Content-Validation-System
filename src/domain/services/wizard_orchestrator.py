"""
Wizard Orchestrator - Guided single-post generation from wizard inputs
Reuses existing agents (content, image, validation) but with wizard-specific context building
"""

import uuid
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import structlog

from src.domain.models.post import LinkedInPost, CulturalReference
from src.domain.agents.advanced_content_generator import AdvancedContentGenerator
from src.domain.agents.image_generation_agent import ImageGenerationAgent
from src.domain.agents.validators.sarah_chen_validator import SarahChenValidator
from src.domain.agents.validators.marcus_williams_validator import MarcusWilliamsValidator
from src.domain.agents.validators.jordan_park_validator import JordanParkValidator
from src.domain.agents.feedback_aggregator import FeedbackAggregator
from src.domain.agents.revision_generator import RevisionGenerator
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.cost_tracking.cost_tracker import get_cost_tracker  # ⭐ ADDED FOR COST TRACKING

logger = structlog.get_logger()


@dataclass
class BrandSettings:
    """User's brand dial settings from Step 1"""
    tone_slider: int  # 0-100 (0=Wakadoo, 100=Formal)
    pithiness_slider: int  # 0-100 (0=Offensive, 100=Baroque)
    jargon_slider: int  # 0-100 (0=Low, 100=VC-speak)
    custom_additions: str  # Free-form brand additions
    
    def to_prompt_guidance(self) -> str:
        """Convert sliders to natural language guidance"""
        tone = "very playful and wacky" if self.tone_slider < 30 else \
               "professional but conversational" if self.tone_slider < 70 else \
               "highly formal and corporate"
        
        pithiness = "extremely concise and punchy" if self.pithiness_slider < 30 else \
                   "balanced brevity with detail" if self.pithiness_slider < 70 else \
                   "elaborate and verbose"
        
        jargon = "minimal jargon, speak plainly" if self.jargon_slider < 30 else \
                "moderate use of business terminology" if self.jargon_slider < 70 else \
                "heavy use of startup/VC jargon and buzzwords"
        
        guidance = f"""Brand Voice Guidance:
- Tone: {tone}
- Writing Style: {pithiness}
- Language Level: {jargon}"""

        if self.custom_additions.strip():
            guidance += f"\n- Additional Brand Notes: {self.custom_additions}"
        
        return guidance


@dataclass
class InspirationBase:
    """Selected inspiration source from Step 2"""
    type: str  # "news", "meme", "philosopher", "poet"
    content: str  # The actual content/quote/headline
    source: str  # Attribution
    context: str = ""  # Additional context/usage notes
    
    def to_prompt_context(self) -> str:
        """Convert to prompt-friendly context"""
        if self.type == "news":
            return f"Trending News: '{self.content}' (Source: {self.source})\nUse this as a timely hook or context for relevance."
        elif self.type == "meme":
            return f"Meme Reference: {self.source}\nContext: {self.context}\nContent: {self.content}"
        elif self.type == "philosopher":
            return f"Philosophical Reference: {self.source}\nQuote: \"{self.content}\"\nContext: {self.context}"
        elif self.type == "poet":
            return f"Poetic Reference: {self.source}\nExcerpt: \"{self.content}\"\nContext: {self.context}"
        return self.content


@dataclass
class BuyerPersona:
    """User-defined buyer persona from Step 4"""
    title: str
    company_size: str
    sector: str
    region: str = ""
    goals: List[str] = None
    risk_tolerance: str = ""  # "Conservative", "Moderate", "Aggressive"
    decision_criteria: List[str] = None
    personality: str = ""  # "Fun", "Angry", "Working on myself", "Super Chill", "Grinding"
    tone_resonance: str = ""  # "Analytical", "Visionary", "Skeptical", "Pragmatic"
    
    def __post_init__(self):
        if self.goals is None:
            self.goals = []
        if self.decision_criteria is None:
            self.decision_criteria = []
    
    def to_prompt_context(self) -> str:
        """Convert persona to validation context"""
        context = f"""Target Buyer Persona:
- Role: {self.title} at {self.company_size} company in {self.sector}
- Goals: {', '.join(self.goals) if self.goals else 'Professional growth'}
- Personality: {self.personality}
- Decision Style: {self.tone_resonance}"""

        if self.risk_tolerance:
            context += f"\n- Risk Tolerance: {self.risk_tolerance}"
        
        if self.decision_criteria:
            context += f"\n- Decides Based On: {', '.join(self.decision_criteria)}"
        
        return context


class WizardOrchestrator:
    """
    Orchestrates single-post generation from wizard inputs
    Reuses existing ValidationOrchestrator logic but adapted for wizard context
    """
    
    def __init__(self,
                 content_generator: AdvancedContentGenerator,
                 image_generator: ImageGenerationAgent,
                 validators: List[Any],
                 feedback_aggregator: FeedbackAggregator,
                 revision_generator: RevisionGenerator,
                 config: AppConfig):
        self.content_generator = content_generator
        self.image_generator = image_generator
        self.validators = validators
        self.feedback_aggregator = feedback_aggregator
        self.revision_generator = revision_generator
        self.config = config
        self.logger = logger.bind(component="wizard_orchestrator")
        
        # Stats
        self._total_generated = 0
        self._total_revised = 0
        self._total_with_persona = 0
    
    async def generate_from_wizard(
        self,
        brand_settings: BrandSettings,
        inspiration_bases: List[InspirationBase],
        length: str,  # "very_short", "short", "medium", "long"
        style_flags: List[str] = None,
        buyer_persona: Optional[BuyerPersona] = None
    ) -> Dict[str, Any]:
        """
        Generate a single post from wizard inputs
        
        Args:
            brand_settings: Brand tone/voice settings from sliders
            inspiration_bases: 1-3 selected inspiration sources
            length: Target post length
            style_flags: Optional style modifiers (contrarian, data-led, etc.)
            buyer_persona: Optional buyer persona for validation
        
        Returns:
            Dict with post, image_url, metadata
        """
        start_time = time.time()
        session_id = f"wizard_{uuid.uuid4().hex[:8]}"
        
        self.logger.info("wizard_generation_started",
                        session_id=session_id,
                        inspiration_count=len(inspiration_bases),
                        has_persona=buyer_persona is not None,
                        length=length)
        
        try:
            # Step 1: Build wizard context for content generation
            wizard_context = self._build_wizard_context(
                brand_settings,
                inspiration_bases,
                length,
                style_flags or []
            )
            
            # Step 2: Generate content using AdvancedContentGenerator
            post_data = await self._generate_content_with_context(
                session_id,
                wizard_context
            )
            
            # Step 3: Create LinkedInPost object
            post = LinkedInPost(
                batch_id=session_id,
                post_number=1,
                content=post_data.get("content", ""),
                target_audience=post_data.get("target_audience", "LinkedIn professionals"),
                cultural_reference=self._extract_cultural_reference(post_data),
                hashtags=post_data.get("hashtags", [])
            )
            
            # Step 4: Validate with personas (including buyer persona if provided)
            validation_result = await self._validate_with_personas(post, buyer_persona)
            
            # Step 5: Revise if needed and persona provided
            if buyer_persona and not validation_result["approved"]:
                self.logger.info("wizard_revision_needed",
                               session_id=session_id,
                               persona_feedback=validation_result.get("feedback", ""))
                post = await self._revise_for_persona(post, validation_result)
                self._total_revised += 1
            
            # Step 6: Generate image with enforced CTA
            await self._generate_image_with_cta(post)
            
            # Step 7: Build response
            generation_time = time.time() - start_time
            self._total_generated += 1
            if buyer_persona:
                self._total_with_persona += 1
            
            # Extract filename from full path and convert to public route
            image_url = None
            if post.image_url:
                # Extract just the filename (e.g., "48c8698c-15bd-4489-9965-251b46aa19ab_f6daa32a.png")
                from pathlib import Path
                filename = Path(post.image_url).name
                image_url = f"/images/{filename}"
            
            result = {
                "post": {
                    "id": post.id,
                    "content": post.content,
                    "hashtags": post.hashtags,
                    "image_url": image_url,
                    "image_description": getattr(post, 'image_description', None),
                    "image_prompt": getattr(post, 'image_prompt', None),
                    "cultural_reference": post.cultural_reference if isinstance(post.cultural_reference, dict) else None,
                    "target_audience": post.target_audience,
                },
                "validation": validation_result,
                "metadata": {
                    "session_id": session_id,
                    "generation_time_seconds": round(generation_time, 2),
                    "brand_settings": asdict(brand_settings),
                    "inspiration_sources": [b.source for b in inspiration_bases],
                    "length": length,
                    "style_flags": style_flags or [],
                    "persona_validated": buyer_persona is not None,
                    "revised": self._total_revised > 0,
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            self.logger.info("wizard_generation_completed",
                           session_id=session_id,
                           generation_time=generation_time,
                           has_image=bool(post.image_url),
                           validation_approved=validation_result["approved"])
            
            # ⭐⭐⭐ ADDED: Finalize post cost for dashboard tracking ⭐⭐⭐
            try:
                cost_tracker = get_cost_tracker()
                post_summary = cost_tracker.finalize_post_cost(
                    batch_id=session_id,
                    post_number=1
                )
                
                if post_summary:
                    self.logger.info(
                        "wizard_post_cost_finalized",
                        session_id=session_id,
                        total_cost=f"${post_summary.total_cost:.4f}",
                        content_cost=f"${post_summary.content_generation_cost:.4f}",
                        image_cost=f"${post_summary.image_generation_cost:.4f}",
                        validation_cost=f"${post_summary.validation_cost:.4f}",
                        api_calls=post_summary.api_calls
                    )
                else:
                    self.logger.warning(
                        "wizard_post_cost_not_found",
                        session_id=session_id,
                        message="No API calls found for this post - check batch_id/post_number matching"
                    )
            except Exception as e:
                # Don't let cost tracking break the workflow
                self.logger.warning(
                    "wizard_post_cost_finalization_failed",
                    session_id=session_id,
                    error=str(e)
                )
            # ⭐⭐⭐ END OF COST TRACKING CODE ⭐⭐⭐
            
            return result
        
        except Exception as e:
            self.logger.error("wizard_generation_failed",
                            session_id=session_id,
                            error=str(e),
                            exc_info=True)
            raise
    
    def _build_wizard_context(
        self,
        brand_settings: BrandSettings,
        inspiration_bases: List[InspirationBase],
        length: str,
        style_flags: List[str]
    ) -> Dict[str, Any]:
        """Build generation context from wizard inputs"""
        
        # Map length to word targets
        length_map = {
            "very_short": 50,
            "short": 100,
            "medium": 150,
            "long": 250
        }
        
        target_words = length_map.get(length, 150)
        
        # Build inspiration context
        inspiration_context = "\n\n".join([
            base.to_prompt_context() for base in inspiration_bases
        ])
        
        # Build style modifiers
        style_guidance = ""
        if "contrarian" in style_flags:
            style_guidance += "- Use a contrarian angle or challenge conventional wisdom\n"
        if "data_led" in style_flags:
            style_guidance += "- Lead with data, statistics, or research\n"
        if "story_first" in style_flags:
            style_guidance += "- Open with a compelling personal story or anecdote\n"
        if "human_potential" in style_flags:
            style_guidance += "- Focus on human growth and potential\n"
        if "outrageous_success" in style_flags:
            style_guidance += "- Celebrate bold success and achievement\n"
        if "pure_brag" in style_flags:
            style_guidance += "- Confident, unabashed celebration of wins\n"
        if "humble_brag" in style_flags:
            style_guidance += "- Subtle, humble approach to showcasing success\n"
        
        return {
            "brand_guidance": brand_settings.to_prompt_guidance(),
            "inspiration_context": inspiration_context,
            "target_words": target_words,
            "length_name": length,
            "style_guidance": style_guidance.strip(),
            "wizard_mode": True
        }
    
    async def _generate_content_with_context(
        self,
        session_id: str,
        wizard_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate content using wizard context"""
        
        # Build input for AdvancedContentGenerator
        # We'll override the prompt building with wizard context
        input_data = {
            "batch_id": session_id,
            "count": 1,
            "brand_context": {
                "product": self.config.brand.product_name,
                "price": self.config.brand.price,
                "tagline": self.config.brand.tagline,
                "ritual": self.config.brand.ritual,
                "audience": self.config.brand.target_audience
            },
            "wizard_context": wizard_context  # Pass wizard context
        }
        
        # Generate using existing content generator
        # Note: We may need to modify AdvancedContentGenerator to accept wizard_context
        # For now, we'll use the existing structure
        generated = await self.content_generator.process(input_data)
        
        return generated[0] if generated else {}
    
    def _extract_cultural_reference(self, post_data: Dict[str, Any]) -> Optional[CulturalReference]:
        """Extract cultural reference from generated post data"""
        ref_data = post_data.get("cultural_reference")
        if not ref_data:
            return None
        
        return CulturalReference(
            category=ref_data.get("category", "general"),
            reference=ref_data.get("reference", ""),
            context=ref_data.get("context", "")
        )
    
    async def _validate_with_personas(
        self,
        post: LinkedInPost,
        buyer_persona: Optional[BuyerPersona]
    ) -> Dict[str, Any]:
        """Validate post with existing personas and optional buyer persona"""
        
        # Run standard validators in parallel
        validation_scores = []
        for validator in self.validators:
            score = await validator.process(post)
            validation_scores.append(score)
        
        # Check approval (2/3 personas must approve)
        approved_count = sum(1 for score in validation_scores if score.approved)
        approved = approved_count >= 2
        
        # Aggregate feedback
        feedback_summary = []
        for score in validation_scores:
            if not score.approved:
                feedback_summary.append(f"{score.agent_name}: {score.feedback}")
        
        # Add buyer persona validation if provided
        persona_feedback = None
        if buyer_persona:
            persona_feedback = await self._validate_against_buyer_persona(post, buyer_persona)
            if not persona_feedback["resonates"]:
                approved = False
        
        return {
            "approved": approved,
            "validator_scores": [
                {
                    "agent": score.agent_name,
                    "score": score.score,
                    "approved": score.approved,
                    "feedback": score.feedback
                }
                for score in validation_scores
            ],
            "buyer_persona_feedback": persona_feedback,
            "feedback": " | ".join(feedback_summary) if feedback_summary else "All validators approved"
        }
    
    async def _validate_against_buyer_persona(
        self,
        post: LinkedInPost,
        persona: BuyerPersona
    ) -> Dict[str, Any]:
        """Validate if post resonates with buyer persona"""
        
        # Build persona validation prompt
        persona_context = persona.to_prompt_context()
        
        validation_prompt = f"""Analyze if this LinkedIn post will resonate with this specific buyer persona:

{persona_context}

POST CONTENT:
{post.content}

Evaluate:
1. Does this speak to their goals and challenges?
2. Does the tone match their personality and decision style?
3. Will this drive engagement from someone like them?
4. Does it address their risk tolerance level?

Return JSON:
{{
    "resonates": true/false,
    "resonance_score": 0-10,
    "why_it_works": "explanation if it works",
    "why_it_fails": "explanation if it doesn't",
    "improvement_suggestions": ["suggestion 1", "suggestion 2"]
}}"""

        # Use existing AI client through feedback aggregator's client
        response = await self.feedback_aggregator._call_ai(
            prompt=validation_prompt,
            system_prompt="You are an expert at buyer persona analysis and content resonance.",
            response_format="json"
        )
        
        return response.get("content", {
            "resonates": True,
            "resonance_score": 7,
            "why_it_works": "General professional appeal",
            "improvement_suggestions": []
        })
    
    async def _revise_for_persona(
        self,
        post: LinkedInPost,
        validation_result: Dict[str, Any]
    ) -> LinkedInPost:
        """Revise post based on persona feedback"""
        
        # Build feedback dict for revision generator
        feedback_dict = {
            "main_issues": [],
            "specific_improvements": {},
            "priority_fix": "Better persona alignment"
        }
        
        persona_feedback = validation_result.get("buyer_persona_feedback", {})
        if persona_feedback:
            if persona_feedback.get("why_it_fails"):
                feedback_dict["main_issues"].append(persona_feedback["why_it_fails"])
            
            if persona_feedback.get("improvement_suggestions"):
                feedback_dict["specific_improvements"]["persona_alignment"] = \
                    " | ".join(persona_feedback["improvement_suggestions"])
        
        # Add validator feedback
        for score_info in validation_result.get("validator_scores", []):
            if not score_info["approved"]:
                feedback_dict["main_issues"].append(
                    f"{score_info['agent']}: {score_info['feedback']}"
                )
        
        # Revise using existing revision generator
        revised_post = await self.revision_generator.process((post, feedback_dict))
        
        return revised_post
    
    async def _generate_image_with_cta(self, post: LinkedInPost) -> None:
        """Generate image with enforced 'Stop, Breathe, Balm' CTA"""
        
        try:
            # Before generating, enhance the post content to ensure CTA is mentioned
            # This guides the image generation to include the CTA
            original_content = post.content
            
            # Create a temporary enhanced description for image generation
            cta_note = "\n\nIMAGE REQUIREMENT: The product image MUST prominently display the text 'Stop, Breathe, Balm' and the price '$8.99' as a call-to-action overlay or text element on the image."
            
            # Temporarily modify post content to guide image generation
            if "Stop, Breathe, Balm" not in post.content:
                post.content = post.content + cta_note
            
            # Generate image with CTA-enhanced context
            await self.image_generator.process(post)
            
            # Restore original content
            post.content = original_content
            
            self.logger.info("wizard_image_generated",
                           post_id=post.id,
                           has_image=bool(post.image_url))
        
        except Exception as e:
            self.logger.error("wizard_image_generation_failed",
                            post_id=post.id,
                            error=str(e))
            # Don't fail the whole wizard - just proceed without image
    
    def get_stats(self) -> Dict[str, Any]:
        """Get wizard orchestrator statistics"""
        return {
            "total_generated": self._total_generated,
            "total_revised": self._total_revised,
            "total_with_persona": self._total_with_persona,
            "revision_rate": self._total_revised / self._total_generated 
                if self._total_generated > 0 else 0,
            "persona_usage_rate": self._total_with_persona / self._total_generated
                if self._total_generated > 0 else 0
        }