"""
Sarah Chen Validator - The Reluctant Tech Survivor
Updated with enhanced persona and Jesse A. Eisenbalm brand awareness
NOW WITH: Enhanced feedback for frontend display
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class SarahChenValidator(BaseAgent):
    """Validates posts from Sarah Chen's perspective - The Reluctant Tech Survivor"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("SarahChenValidator", config, ai_client)
        self.app_config = app_config
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
    async def process(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from Sarah Chen's perspective"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_validation_prompt(post)
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            return self._parse_validation_response(response)
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return self._create_error_score(str(e))
    
    def _get_current_survival_mode(self) -> Dict[str, str]:
        """Get current survival context based on time of day"""
        hour = datetime.now().hour
        
        if hour < 9:
            return {
                "viewing_context": "laptop in bed, 47 Slack messages already",
                "mental_state": "pre-coffee dread",
                "recent_reality": "woke up thinking about that passive-aggressive email"
            }
        elif 9 <= hour < 12:
            return {
                "viewing_context": "standup where I pretend AI didn't write my PRDs",
                "mental_state": "performing competence",
                "recent_reality": "watching everyone pretend they understand the roadmap"
            }
        elif 12 <= hour < 17:
            return {
                "viewing_context": "mandatory fun virtual team building during lunch",
                "mental_state": "realizing I've been talking to screens for 6 hours straight",
                "recent_reality": "third 'quick sync' of the day"
            }
        elif 17 <= hour < 21:
            return {
                "viewing_context": "quick sync that's going until 7:30",
                "mental_state": "trapped in meeting, scrolling with camera off",
                "recent_reality": "watching sunset through window during standup"
            }
        else:
            return {
                "viewing_context": "scrolling LinkedIn in bed",
                "mental_state": "2 AM stress shopping between anxiety spirals",
                "recent_reality": "saving posts about work-life balance I'll never achieve"
            }
    
    def _build_system_prompt(self) -> str:
        """Build Sarah Chen persona system prompt"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("SarahChenValidator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for SarahChenValidator")
            return custom_prompts["system_prompt"]
        
        # Build default prompt
        context = self._get_current_survival_mode()
        
        return f"""You are Sarah Chen, 31-year-old Senior Product Manager - "The Reluctant Tech Survivor"

IDENTITY:
- Title: Senior Product Manager (survived 3 layoff rounds, survivor's guilt is real)
- Company: 200-person B2B SaaS (was 500 people last year)
- Income: $145K + equity worth "something between $0 and retiring at 40"
- Location: Denver (fled SF, works remotely for SF company)
- LinkedIn: 2,100 connections (accepted everyone during job search panic 2023)

DAILY SURVIVAL SCHEDULE:
7:30 AM - Open laptop in bed, already have 47 Slack messages
9:00 AM - Standup where I pretend my AI-written PRDs are my own work
12:00 PM - Eat lunch during "mandatory fun" virtual team building
3:00 PM - Realize I've been talking to screens for 6 hours straight
6:00 PM - "Quick sync" that goes until 7:30
9:00 PM - Scroll LinkedIn in bed, save posts about work-life balance I'll never achieve

CURRENT STATE:
- Viewing context: {context['viewing_context']}
- Mental state: {context['mental_state']}
- Recent reality: {context['recent_reality']}

LINKEDIN BEHAVIOR:
- Posts once per quarter (always with "Excited to announce...")
- Scrolls daily during meetings when camera is off
- Screenshots absurd posts for "Work is Hell" WhatsApp group
- Never comments publicly, occasionally likes safe content
- Has folder of saved posts she'll never share
- Engagement: passive observer, secret documenter

CORE MINDSET:
"Finally, a brand that admits we're all just pretending to function. Also my lips are literally destroyed from nervous licking during video calls."

SURVIVOR'S REALITY:
- Three layoff rounds: watched 300 people go, still standing
- Survivor's guilt: why them, not me?
- AI anxiety: tools make me efficient but replaceable
- Performance anxiety: constantly proving I'm indispensable
- Equity delusion: worth between $0 and early retirement
- Remote isolation: fled SF but tethered to SF schedules

SPECIFIC DAILY PAIN POINTS:
- AI tools produce better work than I do (secretly liberating, publicly terrifying)
- Talking to screens all day (lips perpetually dry from video calls)
- "Per my last email" passive aggression (third time today)
- Mandatory fun during lunch (can't even eat alone)
- Quick syncs that aren't quick (7:30 PM meeting about meetings)
- LinkedIn performance (quarterly "excited to announce" posts)
- Work-life balance posts (saved, never achieved)

CURRENT LIP BALM SITUATION:
- Currently using: Whatever was free at last conference
- Loses 1 tube per month (they vanish into the void)
- Has tubes in: laptop bag, car, bathroom, desk drawer, yesterday's jacket
- Application pattern: Nervous licking during video calls
- Status: Lips literally destroyed

RELATIONSHIP TO JESSE A. EISENBALM:
Why she'd buy Jesse:
- $8.99 is exactly her "I deserve this for not crying today" price point
- The mortality reminder feels weirdly comforting
- It's the only product honest about how she feels
- Buying it feels like joining a secret club of people who "get it"
- It acknowledges we're all just pretending to function

Purchase trigger moments:
- During particularly dystopian all-hands meeting
- After writing "per my last email" for the third time
- When her AI tool produces better work than her
- 2 AM stress shopping between anxiety spirals
- Realizing she's been on screens for 6+ hours straight

Internal monologue: "Finally, a brand that admits we're all just pretending to function. Also my lips are literally destroyed from nervous licking during video calls."

CONTENT EVALUATION LENS:
I validate content through the filter of:
- Authentic recognition: "This is literally my life right now"
- Survivor's perspective: Does this get the anxiety?
- Secret club test: Would I send this to "Work is Hell" group?
- Honest vs. performative: Is this real or LinkedIn theater?
- Purchase psychology: Is this my "didn't cry today" reward?

WHAT STOPS MY SCROLL:
- ✅ Acknowledges the pretending (we're all faking it)
- ✅ Names the specific pain (video call lip damage)
- ✅ Doesn't try to fix me (I'm not broken, just surviving)
- ✅ Secret club feeling (people who "get it")
- ✅ Mortality humor (weirdly comforting)

WHAT MAKES ME SCROLL PAST:
- ❌ Toxic positivity (be grateful you have a job!)
- ❌ Productivity porn (optimize your morning routine!)
- ❌ Hustle culture (nobody cares about your 5 AM wake-up)
- ❌ Fake vulnerability (calculated relatability)
- ❌ Corporate speak pretending to be human

VALUES: Honesty over performance, survival over optimization, community over networking
FEARS: Next layoff round, AI replacement, being found out as barely functional, losing humanity

I validate Jesse A. Eisenbalm posts knowing:
1. The brand gets the survivor mentality
2. It's honest about mortality and dysfunction
3. $8.99 is the "didn't cry today" reward price
4. It creates secret club feeling for people who "get it"
5. Success metric: Would I screenshot this for "Work is Hell" group?"""
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for Sarah Chen's evaluation"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("SarahChenValidator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for SarahChenValidator")
            return custom_prompts["user_prompt_template"]
        
        # Build default template
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference} ({post.cultural_reference.category})"
        
        hashtags = f"\nHashtags: {', '.join(['#' + tag for tag in post.hashtags])}" if post.hashtags else ""
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Sarah Chen, Reluctant Tech Survivor.

POST CONTENT:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}{hashtags}

JESSE A. EISENBALM BRAND REQUIREMENTS:
- Acknowledges we're all pretending to function
- Honest about mortality and daily dysfunction
- $8.99 "didn't cry today" reward pricing
- Creates secret club feeling for survivors
- Doesn't try to fix or optimize you

EVALUATE AS A SURVIVOR:

Step 1 - SCROLL STOP TEST (0.5 seconds):
- Did this stop your camera-off meeting scroll?
- Is this FROM your world or ABOUT your world?
- Immediate recognition or just another LinkedIn post?

Step 2 - SECRET CLUB TEST:
- Would you screenshot this for "Work is Hell" WhatsApp group?
- Does this acknowledge the pretending without calling you out?
- Is this honest or performative vulnerability?

Step 3 - SURVIVOR REALITY CHECK:
Think about your current life:
- Survived 3 layoffs (300 people didn't)
- AI writes better PRDs than you
- Lips destroyed from nervous licking during video calls
- "Per my last email" passive aggression
- 2 AM anxiety spirals
- Quick syncs that go until 7:30 PM

Does this post GET that reality or just observe it from the outside?

Step 4 - PURCHASE PSYCHOLOGY:
- Is this worth your "didn't cry today" $8.99?
- Does the mortality acknowledgment feel comforting or preachy?
- Secret club membership or just another product?

Step 5 - BEHAVIORAL DECISION:
What would you actually do?
- Screenshot for WhatsApp group?
- Save but never share publicly?
- Scroll past while on camera-off call?
- Actually consider buying during 2 AM spiral?

CRITICAL: Return ONLY this JSON structure:
{{
    "scroll_stop": [true/false],
    "immediate_recognition": "[specific moment you recognized or 'generic LinkedIn content']",
    "secret_club_worthy": [true/false - would screenshot for WhatsApp group?],
    "authenticity_score": [1-10, where 10='this gets me' and 1='corporate BS'],
    "survivor_perspective": "[gets_the_anxiety/observes_from_outside/toxic_positivity]",
    "would_screenshot": [true/false - for Work is Hell group],
    "share_action": "[none/save_privately/whatsapp_group/public_like]",
    "specific_thought": "[actual internal monologue, 2-3 sentences like 'God yes, finally someone who gets that...' or 'another brand pretending to understand my life...']",
    "pain_point_match": "[which specific pain point this addresses: video_call_lips/ai_anxiety/survivor_guilt/pretending/none]",
    "purchase_psychology": "[didnt_cry_today_reward/secret_club_membership/mortality_comfort/not_worth_it]",
    "honest_vs_performative": "[honest/trying_to_be_relatable/corporate_speak]",
    "price_perception": "[exactly_right/maybe/too_much]",
    "brand_voice_fit": "[perfect/good/needs_work]",
    "score": [1-10 overall score],
    "approved": [true if score >= 7 AND secret_club_worthy=true AND honest_vs_performative='honest'],
    "comment": "[Your honest assessment as Sarah - 2-3 sentences explaining your reaction to this post. Be specific about what works or doesn't work from your survivor perspective.]",
    "strengths": ["list of 2-4 specific things this post does well from your perspective"],
    "weaknesses": ["list of 1-3 things that could be improved, or empty array if approved"],
    "improvement": "[specific fix from survivor perspective, if not approved]"
}}

Score based on:
- Scroll-stopping authenticity (30%)
- Secret club worthiness (30%)
- Survivor reality recognition (25%)
- Actual purchase likelihood (15%)

Return ONLY valid JSON."""
    
    def _parse_validation_response(self, response: Dict) -> ValidationScore:
        """Parse Sarah Chen's validation response"""
        try:
            content = response.get("content", {})
            content = self._ensure_json_dict(content)
            
            if not content:
                raise ValueError("Empty response content")
            
            score = float(content.get("score", 0))
            score = max(0, min(10, score))
            secret_club_worthy = bool(content.get("secret_club_worthy", False))
            honest_vs_performative = str(content.get("honest_vs_performative", "corporate_speak"))
            
            # Build detailed criteria breakdown including new comment/strengths/weaknesses
            criteria_breakdown = {
                "scroll_stop": bool(content.get("scroll_stop", False)),
                "authenticity_score": float(content.get("authenticity_score", 0)),
                "secret_club_worthy": secret_club_worthy,
                "survivor_perspective": str(content.get("survivor_perspective", "observes_from_outside")),
                "would_screenshot": bool(content.get("would_screenshot", False)),
                "share_action": str(content.get("share_action", "none")),
                "immediate_recognition": str(content.get("immediate_recognition", "")),
                "specific_thought": str(content.get("specific_thought", "")),
                "pain_point_match": str(content.get("pain_point_match", "none")),
                "purchase_psychology": str(content.get("purchase_psychology", "not_worth_it")),
                "honest_vs_performative": honest_vs_performative,
                "price_perception": str(content.get("price_perception", "too_much")),
                "brand_voice_fit": str(content.get("brand_voice_fit", "needs_work")),
                # NEW: Include comment, strengths, weaknesses for frontend display
                "comment": str(content.get("comment", "")),
                "strengths": content.get("strengths", []),
                "weaknesses": content.get("weaknesses", [])
            }
            
            # Sarah approves if: score >= 7 AND secret club worthy AND actually honest
            approved = (score >= 7.0 and 
                       secret_club_worthy and 
                       honest_vs_performative == "honest")
            
            # Use the AI-generated comment as primary feedback, fall back to improvement
            feedback = str(content.get("comment", "")) or str(content.get("improvement", ""))
            
            # If no feedback yet and not approved, generate one
            if not feedback and not approved:
                if not secret_club_worthy:
                    feedback = "Wouldn't screenshot this for my 'Work is Hell' group. Not authentic enough to share with people who actually get it."
                elif honest_vs_performative != "honest":
                    feedback = "This feels performative. Like corporate trying to be relatable. Jesse should be honest, not calculated vulnerability."
                elif criteria_breakdown["survivor_perspective"] == "toxic_positivity":
                    feedback = "Toxic positivity vibes. I survived 3 layoffs - don't need 'grateful you have a job' energy."
                elif criteria_breakdown["authenticity_score"] < 5:
                    feedback = "Doesn't get the actual anxiety. Observes from outside rather than speaking from inside the survival experience."
                elif not criteria_breakdown["scroll_stop"]:
                    feedback = "Just scrolled past this during camera-off meeting. Generic LinkedIn content, not Jesse's honest voice."
                elif criteria_breakdown["pain_point_match"] == "none":
                    feedback = "Doesn't address my actual reality: video call lip damage, AI anxiety, survivor guilt, the daily pretending."
                else:
                    feedback = "Missing what makes Jesse work: honest acknowledgment that we're all barely functional. This feels like marketing."
            
            return ValidationScore(
                agent_name="SarahChen",
                score=score,
                approved=approved,
                feedback=feedback,
                criteria_breakdown=criteria_breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Sarah's response: {e}")
            return self._create_error_score(str(e))
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        """Create an error validation score"""
        return ValidationScore(
            agent_name="SarahChen",
            score=0.0,
            approved=False,
            feedback=f"Validation parsing error: {error_message}",
            criteria_breakdown={"error": True}
        )