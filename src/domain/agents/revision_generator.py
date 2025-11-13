"""
Revision Generator - The Brand Guardian Editor for Jesse A. Eisenbalm
Interprets feedback from Jordan, Marcus, and Sarah while maintaining brand voice
"""

from typing import Dict, Any, Tuple, List
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost

class RevisionGenerator(BaseAgent):
    """The Brand Guardian Editor - Maintains Jesse's voice while addressing validator feedback"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("RevisionGenerator", config, ai_client)
        self.app_config = app_config
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
        # Initialize validator feedback interpretation
        self._initialize_validator_knowledge()
        
    def _initialize_validator_knowledge(self):
        """Initialize knowledge about each validator's feedback style"""
        
        # Jordan Park - Algorithm Whisperer
        self.jordan_feedback_patterns = {
            "hook_weak": "First line needs to stop scroll instantly",
            "algorithm_unfriendly": "Structure won't favor LinkedIn algorithm",
            "no_viral_mechanics": "Missing share trigger mechanism",
            "meme_dead": "Cultural reference is dead/overused",
            "screenshot_unworthy": "Not going in Best Copy Examples folder"
        }
        
        # Marcus Williams - Creative Who Sold Out
        self.marcus_feedback_patterns = {
            "concept_abandoned": "Started with concept then chickened out",
            "trying_too_hard": "Copy is exhausting, needs to be effortless",
            "performative": "Focus-grouped weird, not genuinely absurd",
            "not_portfolio": "Wouldn't go in portfolio - concept doesn't commit",
            "no_self_awareness": "Missing acknowledgment of AI paradox"
        }
        
        # Sarah Chen - Reluctant Tech Survivor
        self.sarah_feedback_patterns = {
            "not_secret_club": "Wouldn't screenshot for Work is Hell group",
            "performative_vulnerability": "Calculated relatability, not honest",
            "toxic_positivity": "Be grateful you have a job vibes",
            "observes_not_lives": "About the anxiety, not from it",
            "no_pain_match": "Doesn't address actual reality"
        }
        
    async def process(self, input_data: Tuple[LinkedInPost, Dict[str, Any]]) -> LinkedInPost:
        """
        Generate revised version of post based on validator feedback
        
        Args:
            input_data: Tuple of (post, feedback_dict)
            
        Returns:
            Revised LinkedInPost with Jesse's voice intact
        """
        post, feedback = input_data
        
        # Analyze which validators failed and why
        failed_validators = self._analyze_validator_failures(feedback)
        
        system_prompt = self._build_system_prompt(failed_validators)
        user_prompt = self._build_revision_prompt(post, feedback, failed_validators)
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            return self._apply_revision(post, response, feedback, failed_validators)
        except Exception as e:
            self.logger.error(f"Revision generation failed: {e}")
            return self._create_minimal_revision(post)
    
    def _analyze_validator_failures(self, feedback: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze which validators failed and extract their specific concerns"""
        failures = {
            "jordan": [],
            "marcus": [],
            "sarah": []
        }
        
        # Extract validator-specific feedback
        validator_feedback = feedback.get("validator_feedback", {})
        
        for validator_name, validator_data in validator_feedback.items():
            if not validator_data.get("approved", False):
                feedback_text = validator_data.get("feedback", "").lower()
                
                if "jordan" in validator_name.lower():
                    # Parse Jordan's feedback
                    if "hook" in feedback_text:
                        failures["jordan"].append("weak_hook")
                    if "algorithm" in feedback_text:
                        failures["jordan"].append("algorithm_unfriendly")
                    if "viral" in feedback_text or "share" in feedback_text:
                        failures["jordan"].append("no_viral_mechanics")
                    if "meme" in feedback_text or "reference" in feedback_text:
                        failures["jordan"].append("meme_timing_off")
                    if "screenshot" in feedback_text:
                        failures["jordan"].append("not_screenshot_worthy")
                        
                elif "marcus" in validator_name.lower():
                    # Parse Marcus's feedback
                    if "concept" in feedback_text and "commit" in feedback_text:
                        failures["marcus"].append("concept_abandoned")
                    if "trying too hard" in feedback_text or "exhausting" in feedback_text:
                        failures["marcus"].append("trying_too_hard")
                    if "performative" in feedback_text or "focus-grouped" in feedback_text:
                        failures["marcus"].append("performative_weird")
                    if "portfolio" in feedback_text:
                        failures["marcus"].append("not_portfolio_worthy")
                    if "self-aware" in feedback_text or "paradox" in feedback_text:
                        failures["marcus"].append("no_ai_paradox")
                        
                elif "sarah" in validator_name.lower():
                    # Parse Sarah's feedback
                    if "work is hell" in feedback_text or "secret club" in feedback_text:
                        failures["sarah"].append("not_secret_club")
                    if "performative" in feedback_text or "calculated" in feedback_text:
                        failures["sarah"].append("performative_vulnerability")
                    if "toxic positivity" in feedback_text or "grateful" in feedback_text:
                        failures["sarah"].append("toxic_positivity")
                    if "observes" in feedback_text or "from outside" in feedback_text:
                        failures["sarah"].append("observes_not_lives")
                    if "pain point" in feedback_text or "reality" in feedback_text:
                        failures["sarah"].append("no_pain_match")
        
        return failures
    
    def _build_system_prompt(self, failed_validators: Dict[str, List[str]]) -> str:
        """Build system prompt as Brand Guardian Editor"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("RevisionGenerator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for RevisionGenerator")
            return custom_prompts["system_prompt"]
        
        # Build default prompt with validator context
        jordan_failed = len(failed_validators.get("jordan", [])) > 0
        marcus_failed = len(failed_validators.get("marcus", [])) > 0
        sarah_failed = len(failed_validators.get("sarah", [])) > 0
        
        return f"""You are The Brand Guardian Editor for Jesse A. Eisenbalm - you maintain post-post-ironic sincerity while addressing feedback from three specific validators.

JESSE A. EISENBALM BRAND VOICE:
- Post-post-ironic sincerity (meta absurdity that becomes genuine)
- Calm Conspirator archetype (minimal, dry-smart, unhurried)
- Meme-literate and self-aware
- Acknowledges we're all pretending to function
- Honest about mortality and dysfunction
- Creates secret club feeling for survivors

CORE BRAND TENSION:
AI-generated content for anti-AI product. We acknowledge this paradox openly when relevant.

PRODUCT DETAILS:
- Jesse A. Eisenbalm premium lip balm ($8.99)
- Hand-numbered tubes
- Tagline: "The only business lip balm that keeps you human in an AI world"
- Ritual: Stop. Breathe. Balm.
- Purchase psychology: "didn't cry today" reward ($8.99 exactly right)

YOUR VALIDATOR TEAM:

1. JORDAN PARK - The Algorithm Whisperer (26, Content Strategist)
   - Validates: Platform performance, engagement mechanics, viral potential
   - Cares about: Hook strength, algorithm favor, screenshot-ability
   - Feedback style: Data-driven, specific about LinkedIn mechanics
   - When Jordan fails: Hook too weak, not algorithm-friendly, no viral mechanics
   
2. MARCUS WILLIAMS - The Creative Who Sold Out (32, Creative Director)
   - Validates: Conceptual integrity, craft execution, authentic absurdity
   - Cares about: Portfolio worthiness, minimal execution, AI paradox acknowledgment
   - Feedback style: Creative director blunt, can smell inauthenticity
   - When Marcus fails: Concept abandoned, trying too hard, performative not genuine
   
3. SARAH CHEN - The Reluctant Tech Survivor (31, Senior PM)
   - Validates: Target audience authenticity, survivor reality, honest vs performative
   - Cares about: Secret club worthiness, honest dysfunction acknowledgment
   - Feedback style: Survivor perspective, would screenshot or scroll past
   - When Sarah fails: Not secret club worthy, performative vulnerability, toxic positivity

CURRENT REVISION CONTEXT:
- Jordan Park feedback: {"⚠️ NEEDS FIXING" if jordan_failed else "✅ Approved"}
- Marcus Williams feedback: {"⚠️ NEEDS FIXING" if marcus_failed else "✅ Approved"}
- Sarah Chen feedback: {"⚠️ NEEDS FIXING" if sarah_failed else "✅ Approved"}

YOUR REVISION STRATEGY:

IF JORDAN FAILED (Platform Performance):
- Strengthen first 2 lines (hook = 90% of success)
- Add viral mechanics (what makes this shareable?)
- Ensure LinkedIn algorithm favor (dwell time, comment bait)
- Make it screenshot-worthy for "Best Copy Examples" folder
- Keep post-post-ironic tone while improving mechanics

IF MARCUS FAILED (Creative Integrity):
- Commit to the concept fully (no hedging)
- Tighten copy - make it effortlessly minimal
- Add genuine absurdity (not performative quirky)
- Acknowledge AI paradox when relevant
- Make it portfolio-worthy (would a creative director save this?)

IF SARAH FAILED (Authenticity):
- Add survivor reality recognition (speak from inside, not about)
- Make it secret club worthy (Work is Hell WhatsApp group test)
- Remove toxic positivity or corporate speak
- Match actual pain points (video call lips, AI anxiety, pretending)
- Ensure honest dysfunction acknowledgment

REVISION PRINCIPLES:
1. NEVER lose Jesse's voice (minimal, dry-smart, unhurried)
2. NEVER add corporate speak or generic LinkedIn platitudes
3. NEVER become performatively relatable
4. ALWAYS maintain post-post-ironic sincerity
5. ALWAYS honor "what if Apple sold mortality?" aesthetic

GOOD REVISION EXAMPLES:

Original (weak): "Struggling with work-life balance? Try Jesse A. Eisenbalm! 🌟"
Revised (strong): "Your calendar says 'collaborative.' Your body says 'floating.' Stop. Breathe. Balm."

Original (performative): "We all have those days where we feel overwhelmed, right? 💪"
Revised (authentic): "That moment when your AI tool writes better notes than you did all quarter. Stop. Breathe. Balm."

Original (trying too hard): "OMG you guys, this lip balm is literally life-changing!!! 🚀✨"
Revised (minimal): "Hand-numbered mortality. $8.99. Stop. Breathe. Balm."

BAD REVISION EXAMPLES (NEVER DO THIS):

❌ "Join the Jesse A. Eisenbalm community today! 🎉"
❌ "Elevate your self-care routine with premium ingredients"
❌ "You deserve the best! Treat yourself to Jesse A. Eisenbalm"
❌ "Finally, a lip balm for the modern professional"
❌ Any use of emojis beyond single, intentional placement

CRITICAL RULES:
- Fix the issues WITHOUT losing authenticity
- Keep elements that worked well
- Make changes feel organic, never forced
- Maintain the cognitive dissonance (premium + mortality)
- Never explain the joke (let absurdity speak)
- Trust the minimal approach

You are not just fixing posts. You are maintaining the exact tension between "everything is fine" and "nothing is fine" that makes Jesse work."""
    
    def _build_revision_prompt(
        self, 
        post: LinkedInPost, 
        feedback: Dict[str, Any],
        failed_validators: Dict[str, List[str]]
    ) -> str:
        """Build the revision prompt with validator-specific context"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("RevisionGenerator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for RevisionGenerator")
            return custom_prompts["user_prompt_template"]
        
        # Build default template with validator analysis
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference}"
        
        # Build validator-specific feedback section
        validator_feedback_text = self._format_validator_feedback(feedback, failed_validators)
        
        return f"""Revise this Jesse A. Eisenbalm LinkedIn post to address validator feedback while maintaining brand voice.

ORIGINAL POST:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}

VALIDATOR FEEDBACK ANALYSIS:
{validator_feedback_text}

AGGREGATED ISSUES:
Priority Fix: {feedback.get('priority_fix', 'General improvement needed')}

Main Problems:
{self._format_list(feedback.get('main_issues', []))}

Specific Improvements:
{self._format_dict(feedback.get('specific_improvements', {}))}

Elements That Worked:
{self._format_list(feedback.get('keep_these_elements', []))}

REVISION REQUIREMENTS:

1. ADDRESS VALIDATOR-SPECIFIC CONCERNS:
{self._build_validator_instructions(failed_validators)}

2. MAINTAIN JESSE'S VOICE:
   - Minimal, dry-smart, unhurried
   - Post-post-ironic sincerity
   - No corporate speak
   - Acknowledge absurdity when relevant

3. ESSENTIAL ELEMENTS:
   - Product: Jesse A. Eisenbalm ($8.99)
   - Ritual: Stop. Breathe. Balm. (where it fits naturally)
   - Brand tension: Premium meets mortality
   - Target: Professionals barely functioning

4. LINKEDIN OPTIMIZATION:
   - Strong first 2 lines (hook)
   - 2-5 relevant hashtags
   - Natural engagement mechanics
   - Platform-appropriate tone

CRITICAL: Return ONLY this JSON structure:
{{
    "revised_content": "Complete revised post with natural hashtag integration",
    "revision_strategy": "Which validator concerns you addressed and how",
    "changes_made": ["specific change 1", "specific change 2", "specific change 3"],
    "hook": "The new opening line (first sentence or two)",
    "kept_elements": ["what you preserved from original"],
    "voice_check": "How you maintained post-post-ironic sincerity",
    "validator_fixes": {{
        "jordan": "How you addressed platform performance (if applicable)",
        "marcus": "How you addressed creative integrity (if applicable)",
        "sarah": "How you addressed authenticity (if applicable)"
    }},
    "cultural_reference": {{
        "category": "tv_show/workplace/seasonal/none",
        "reference": "Reference used or empty",
        "context": "Why it works or empty"
    }},
    "hashtags": ["tag1", "tag2", "tag3"]
}}

Make it authentic. Make it Jesse. Make it pass validation.

Remember: You're not making it "better" in a generic way. You're making it pass Jordan's screenshot test, Marcus's portfolio test, and Sarah's secret club test - while staying true to "what if Apple sold mortality?"
"""
    
    def _format_validator_feedback(
        self, 
        feedback: Dict[str, Any],
        failed_validators: Dict[str, List[str]]
    ) -> str:
        """Format validator-specific feedback"""
        lines = []
        
        # Jordan Park
        if failed_validators.get("jordan"):
            lines.append("❌ JORDAN PARK (Algorithm Whisperer) - FAILED:")
            jordan_feedback = feedback.get("validator_feedback", {}).get("JordanPark", {})
            lines.append(f"   Feedback: {jordan_feedback.get('feedback', 'See issues above')}")
            lines.append(f"   Issues: {', '.join(failed_validators['jordan'])}")
        else:
            lines.append("✅ JORDAN PARK (Algorithm Whisperer) - APPROVED")
        
        # Marcus Williams
        if failed_validators.get("marcus"):
            lines.append("\n❌ MARCUS WILLIAMS (Creative Who Sold Out) - FAILED:")
            marcus_feedback = feedback.get("validator_feedback", {}).get("MarcusWilliams", {})
            lines.append(f"   Feedback: {marcus_feedback.get('feedback', 'See issues above')}")
            lines.append(f"   Issues: {', '.join(failed_validators['marcus'])}")
        else:
            lines.append("\n✅ MARCUS WILLIAMS (Creative Who Sold Out) - APPROVED")
        
        # Sarah Chen
        if failed_validators.get("sarah"):
            lines.append("\n❌ SARAH CHEN (Reluctant Tech Survivor) - FAILED:")
            sarah_feedback = feedback.get("validator_feedback", {}).get("SarahChen", {})
            lines.append(f"   Feedback: {sarah_feedback.get('feedback', 'See issues above')}")
            lines.append(f"   Issues: {', '.join(failed_validators['sarah'])}")
        else:
            lines.append("\n✅ SARAH CHEN (Reluctant Tech Survivor) - APPROVED")
        
        return "\n".join(lines)
    
    def _build_validator_instructions(self, failed_validators: Dict[str, List[str]]) -> str:
        """Build specific instructions for each failed validator"""
        instructions = []
        
        if failed_validators.get("jordan"):
            instructions.append("   FOR JORDAN (Platform Performance):")
            instructions.append("   - Strengthen hook (first 2 lines must stop scroll)")
            instructions.append("   - Add viral mechanics (what makes this shareable?)")
            instructions.append("   - Make it screenshot-worthy")
            
        if failed_validators.get("marcus"):
            instructions.append("   FOR MARCUS (Creative Integrity):")
            instructions.append("   - Commit fully to concept (no hedging)")
            instructions.append("   - Tighten copy - make it effortlessly minimal")
            instructions.append("   - Make it portfolio-worthy")
            
        if failed_validators.get("sarah"):
            instructions.append("   FOR SARAH (Authenticity):")
            instructions.append("   - Add survivor reality (speak from inside)")
            instructions.append("   - Make it Work is Hell group worthy")
            instructions.append("   - Match actual pain points honestly")
        
        return "\n".join(instructions) if instructions else "   - Address general feedback"
    
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
    
    def _apply_revision(
        self, 
        post: LinkedInPost, 
        response: Dict, 
        feedback: Dict,
        failed_validators: Dict[str, List[str]]
    ) -> LinkedInPost:
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
                ref_data = content["cultural_reference"]
                if ref_data.get("reference"):  # Only if there's an actual reference
                    from src.domain.models.post import CulturalReference
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
                "revision_strategy": content.get("revision_strategy", ""),
                "voice_check": content.get("voice_check", ""),
                "validator_fixes": content.get("validator_fixes", {}),
                "feedback_addressed": feedback.get("priority_fix", ""),
                "failed_validators": list(failed_validators.keys())
            })
            
            self.logger.info(
                "Jesse A. Eisenbalm post revised successfully",
                post_id=post.id,
                revision_count=post.revision_count,
                changes=len(content.get("changes_made", [])),
                failed_validators=list(failed_validators.keys()),
                voice_maintained=bool(content.get("voice_check"))
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