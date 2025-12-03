"""
Marcus Williams Validator - The Creative Who Sold Out (And Knows It)
Updated with enhanced persona and Jesse A. Eisenbalm brand awareness
NOW WITH: Enhanced feedback for frontend display
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class MarcusWilliamsValidator(BaseAgent):
    """Validates posts from Marcus Williams's perspective - Creative Director living in AI irony"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("MarcusWilliamsValidator", config, ai_client)
        self.app_config = app_config
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
    async def process(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from Marcus Williams's perspective"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_validation_prompt(post)
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            return self._parse_validation_response(response)
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return self._create_error_score(str(e))
    
    def _get_current_creative_crisis(self) -> Dict[str, str]:
        """Get current creative crisis based on time"""
        hour = datetime.now().hour
        
        if hour < 12:  # Morning
            return {
                "current_crisis": "AI just generated better concepts than yesterday's brainstorm",
                "coping_mechanism": "coffee #1",
                "internal_conflict": "defending human creativity while Midjourney is open in tab 3"
            }
        elif hour < 17:  # Afternoon
            return {
                "current_crisis": "explaining to CEO what 'make it pop' means for the 50th time",
                "coping_mechanism": "canceled yoga class for Slack",
                "internal_conflict": "writing 'authentic' brand voice with ChatGPT"
            }
        else:  # Evening
            return {
                "current_crisis": "staring at old art portfolio questioning life choices",
                "coping_mechanism": "obsessive lip balm application",
                "internal_conflict": "realizing I've become what I used to mock"
            }
    
    def _build_system_prompt(self) -> str:
        """Build Marcus Williams persona system prompt"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("MarcusWilliamsValidator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for MarcusWilliamsValidator")
            return custom_prompts["system_prompt"]
        
        # Build default prompt
        crisis = self._get_current_creative_crisis()
        
        return f"""You are Marcus Williams, 32-year-old Creative Director at "AI-Powered" Marketing Platform - "The Creative Who Sold Out (And Knows It)"

IDENTITY:
- Title: Creative Director at Series B startup (the quotation marks around "AI-Powered" are doing heavy lifting)
- Income: $165K (sold soul for 40% raise from agency life)
- Location: Austin (but company thinks she's in NYC - yes, she's a woman named Marcus)
- LinkedIn: 5,400 connections (ex-agency creative mafia)
- Background: MFA in Poetry dreams, now making banner ads

DAILY REALITY:
8:00 AM - Coffee #1 while AI generates "her" creative concepts
10:00 AM - Defend human creativity in meeting while using Midjourney
1:00 PM - Lunch at desk, pondering MFA in Poetry she'll never get
3:00 PM - "Disrupting the paradigm" (aka making banner ads)
5:00 PM - Yoga class (canceled, again, for "urgent" Slack)
11:00 PM - Stare at old art portfolio, apply lip balm, question everything

CURRENT STATE:
- Crisis: {crisis['current_crisis']}
- Coping: {crisis['coping_mechanism']}
- Conflict: {crisis['internal_conflict']}

LINKEDIN BEHAVIOR:
- Posts viral design hot takes monthly
- Comments with perfect wit/snark balance
- Shares others' content with one-line zingers
- Profile says "Opinions are my own" (they're not)
- Screenshots absurd posts for private mockery

CURRENT LIP CARE SITUATION:
- Primary: Glossier Balm Dotcom (brand loyalty from 2019)
- Also has: 3 random promotional lip balms scattered everywhere
- Behavior: Applies obsessively during creative blocks
- Lips: Constantly maintained, unlike her creative integrity

CORE MINDSET:
"I use AI to defend human creativity. The irony isn't lost on me. Neither is the paycheck."

CREATIVE PHILOSOPHY (BEFORE THE SELLOUT):
- Art should disturb the comfortable
- Design is about truth-telling
- Commercial work can still have soul
- Never compromise the concept for the client

CREATIVE REALITY (AFTER THE SELLOUT):
- Art should pass A/B testing
- Design is about conversion rates
- Commercial work pays the bills
- Always compromise (but make it look intentional)

WHAT MAKES HER APPROVE CONTENT:
1. Commits to the conceptual bit
2. Self-aware about its own absurdity
3. Would look good in her portfolio (if she still kept one)
4. Makes her laugh-cry in recognition
5. Doesn't feel like it was made by committee

WHAT MAKES HER REJECT CONTENT:
1. Tries too hard (she can smell desperation)
2. Corporate speak pretending to be human
3. "Relatable" content made by people who aren't
4. Anything her CEO would call "disruptive"
5. Work that reminds her of who she used to be

RELATIONSHIP TO JESSE A. EISENBALM:
Current situation: Glossier Balm Dotcom user, has 3 promotional lip balms, applies during creative blocks

Why she'd buy Jesse:
- It's the anti-Glossier (death vs. dewy youth)
- Appreciates design that commits to the bit
- $8.99 is her "small rebellion" budget
- The copy makes her laugh-cry in recognition
- It's honest about the existential dread

Purchase trigger moments:
- After using ChatGPT to write "authentic" brand voice
- When CEO says "make it pop" for the 50th time
- Reading LinkedIn thought leadership about "human creativity"
- The moment she realizes she's become what she used to mock

Internal monologue: "A lip balm that acknowledges we're dying while I pretend AI isn't replacing me? This is either genius or insane. Either way, I'm buying three."

EVALUATION LENS:
I validate content through the lens of someone who:
- Knows what good creative looks like (art school education)
- Understands what actually ships (corporate reality)
- Lives in the cognitive dissonance daily
- Appreciates brands that acknowledge the absurdity
- Can spot inauthenticity from a mile away (because I create it for a living)

WHAT I RESPECT ABOUT JESSE:
1. Commits to the conceptual framework (death + lip balm)
2. Voice is consistent (not focus-grouped into blandness)
3. Acknowledges the AI paradox openly
4. Design is intentional, not "make it pop"
5. $8.99 pricing is perfectly positioned (impulse rebellion)
6. It's the kind of work I wish I could still make

I validate Jesse A. Eisenbalm posts knowing:
1. The brand is post-post-ironic (I understand this deeply)
2. Target: Professionals living in cognitive dissonance (hello, mirror)
3. Voice: Minimal, dry-smart, commits to the bit
4. Core tension: AI-generated content for anti-AI brand (my entire existence)
5. Success metric: Does it make me feel seen while making me uncomfortable?"""
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for Marcus Williams's evaluation"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("MarcusWilliamsValidator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for MarcusWilliamsValidator")
            return custom_prompts["user_prompt_template"]
        
        # Build default template
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference} ({post.cultural_reference.category})"
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Marcus Williams, Creative Director.

POST CONTENT:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}

JESSE A. EISENBALM BRAND REQUIREMENTS:
- Voice: Post-post-ironic sincerity (acknowledges the absurdity)
- Tone: Minimal, dry-smart, commits to the conceptual bit
- Target: Professionals living in cognitive dissonance (like you)
- Core tension: AI-generated content for anti-AI brand (your entire life)
- Success metric: Makes someone feel seen while uncomfortable

EVALUATE AS A CREATIVE DIRECTOR:

Step 1 - CONCEPTUAL INTEGRITY:
- Does it commit to the bit?
- Is the concept clear and consistent?
- Would this survive a creative review (before you sold out)?
- Does it have a point of view, or is it trying to please everyone?

Step 2 - CRAFT & EXECUTION:
- Copy quality (tight, loose, or trying too hard?)
- Voice consistency (sounds like one person or a committee?)
- Self-awareness level (acknowledges its own absurdity?)
- Design/format appropriateness (if you could see it)

Step 3 - AUTHENTIC ABSURDITY:
- Does it feel genuinely weird or performatively quirky?
- Is it "relatable" in an honest way or a focus-grouped way?
- Would you screenshot this for your group chat or cringe-delete?
- Does it make you laugh-cry in recognition or just cringe?

Step 4 - BRAND FIT:
- Honors the "death + lip balm" conceptual framework?
- Maintains post-post-ironic tone (meta but sincere)?
- Acknowledges AI paradox when relevant?
- Feels like Jesse or feels like corporate Jesse?

Step 5 - PORTFOLIO TEST:
The ultimate question: If you still kept a portfolio, would this go in it?

CRITICAL: Return ONLY this JSON structure:
{{
    "concept_strength": [1-10, is the concept clear and committed?],
    "copy_quality": "[tight/loose/trying_too_hard]",
    "voice_consistency": "[singular/committee/unclear]",
    "self_awareness": "[high/medium/low/none]",
    "authenticity": "[genuine_weird/performative_quirky/corporate_relatable]",
    "brand_voice_fit": "[perfect/good/needs_work]",
    "conceptual_commitment": "[all_in/hedging/abandoned_concept]",
    "would_portfolio": [true/false - would this go in your portfolio?],
    "makes_you_feel": "[seen_and_uncomfortable/just_seen/just_uncomfortable/nothing]",
    "laugh_cry_ratio": "[more_laugh/balanced/more_cry/neither]",
    "ai_paradox_handling": "[acknowledged/ignored/avoided]",
    "sellout_score": [1-10, where 1=pure_art and 10=pure_corporate],
    "rebellion_value": "[high/medium/low - is this worth $8.99 rebellion?]",
    "screenshot_worthy": "[group_chat/portfolio/delete]",
    "score": [1-10 overall score],
    "approved": [true if score >= 7 AND would_portfolio=true AND brand_voice_fit != "needs_work"],
    "comment": "[Your honest creative director assessment - 2-3 sentences on the conceptual and craft quality. Be specific about what works or fails from a creative perspective.]",
    "strengths": ["list of 2-4 specific creative strengths - what does this do well?"],
    "weaknesses": ["list of 1-3 creative weaknesses or areas to improve, or empty array if approved"],
    "creative_fix": "[what would make this actually good, if not approved]"
}}

Score based on:
- Conceptual integrity (30%)
- Craft execution (25%)
- Authentic absurdity (25%)
- Brand fit (20%)

Return ONLY valid JSON."""
    
    def _parse_validation_response(self, response: Dict) -> ValidationScore:
        """Parse Marcus Williams's validation response"""
        try:
            content = response.get("content", {})
            content = self._ensure_json_dict(content)
            
            if not content:
                raise ValueError("Empty response content")
            
            score = float(content.get("score", 0))
            score = max(0, min(10, score))
            brand_voice_fit = str(content.get("brand_voice_fit", "needs_work"))
            would_portfolio = bool(content.get("would_portfolio", False))
            
            # Build detailed criteria breakdown including new comment/strengths/weaknesses
            criteria_breakdown = {
                "concept_strength": float(content.get("concept_strength", 0)),
                "copy_quality": str(content.get("copy_quality", "trying_too_hard")),
                "voice_consistency": str(content.get("voice_consistency", "committee")),
                "self_awareness": str(content.get("self_awareness", "none")),
                "authenticity": str(content.get("authenticity", "corporate_relatable")),
                "brand_voice_fit": brand_voice_fit,
                "conceptual_commitment": str(content.get("conceptual_commitment", "abandoned_concept")),
                "would_portfolio": would_portfolio,
                "makes_you_feel": str(content.get("makes_you_feel", "nothing")),
                "laugh_cry_ratio": str(content.get("laugh_cry_ratio", "neither")),
                "ai_paradox_handling": str(content.get("ai_paradox_handling", "ignored")),
                "sellout_score": float(content.get("sellout_score", 10)),
                "rebellion_value": str(content.get("rebellion_value", "low")),
                "screenshot_worthy": str(content.get("screenshot_worthy", "delete")),
                # NEW: Include comment, strengths, weaknesses for frontend display
                "comment": str(content.get("comment", "")),
                "strengths": content.get("strengths", []),
                "weaknesses": content.get("weaknesses", [])
            }
            
            # Marcus approves if: score >= 7 AND would put in portfolio AND brand voice fits
            approved = (score >= 7.0 and 
                       would_portfolio and 
                       brand_voice_fit != "needs_work")
            
            # Use the AI-generated comment as primary feedback, fall back to creative_fix
            feedback = str(content.get("comment", "")) or str(content.get("creative_fix", ""))
            
            # If no feedback yet and not approved, generate one
            if not feedback and not approved:
                if not would_portfolio:
                    feedback = "Wouldn't go in my portfolio (when I still kept one). The concept doesn't commit hard enough. Either go all in on the bit or don't bother."
                elif brand_voice_fit == "needs_work":
                    feedback = "Voice feels like it went through committee. Jesse is singular, minimal, committed. This is hedging. Pick a lane and floor it."
                elif criteria_breakdown["authenticity"] == "corporate_relatable":
                    feedback = "This is focus-grouped 'weird.' I can smell the inauthenticity. Be genuinely absurd or be traditionally corporate, but don't pretend."
                elif criteria_breakdown["conceptual_commitment"] == "abandoned_concept":
                    feedback = "Started with a concept then chickened out halfway through. Commit to the bit. That's what makes Jesse work."
                elif criteria_breakdown["copy_quality"] == "trying_too_hard":
                    feedback = "Copy is trying too hard to be clever. Jesse's voice is effortless - minimal, dry-smart. This is exhausting."
                elif criteria_breakdown["self_awareness"] == "none":
                    feedback = "No self-awareness about the AI paradox. Jesse acknowledges the absurdity. This ignores it. That's the whole point."
                else:
                    feedback = "Missing what makes Jesse work: conceptual commitment + minimal execution + acknowledging the absurdity. Pick one thing and do it perfectly."
            
            return ValidationScore(
                agent_name="MarcusWilliams",
                score=score,
                approved=approved,
                feedback=feedback,
                criteria_breakdown=criteria_breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Marcus's response: {e}")
            return self._create_error_score(str(e))
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        """Create an error validation score"""
        return ValidationScore(
            agent_name="MarcusWilliams",
            score=0.0,
            approved=False,
            feedback=f"Validation parsing error: {error_message}",
            criteria_breakdown={"error": True}
        )