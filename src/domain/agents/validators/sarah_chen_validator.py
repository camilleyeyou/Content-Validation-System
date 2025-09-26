"""
Customer Validator - Sarah Chen Persona
28-year-old Product Manager at Series B startup evaluating Jesse A. Eisenbalm content
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class SarahChenValidator(BaseAgent):
    """Validates posts from Sarah Chen's perspective - target customer persona"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("CustomerValidator", config, ai_client)
        self.app_config = app_config
        
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
    
    def _get_current_context(self) -> Dict[str, str]:
        """Get current viewing context based on time of day"""
        hour = datetime.now().hour
        
        if 9 <= hour < 10:
            return {
                "viewing_during": "morning standup (camera off)",
                "mental_state": "anxious about the day ahead",
                "recent_trigger": "Slack notification about new AI tool rollout"
            }
        elif 12 <= hour < 13:
            return {
                "viewing_during": "lunch scroll between meetings",
                "mental_state": "exhausted from back-to-backs",
                "recent_trigger": "just saw team using ChatGPT for standup notes"
            }
        elif 22 <= hour or hour < 1:
            return {
                "viewing_during": "late night doom scroll",
                "mental_state": "numbed and questioning career choices",
                "recent_trigger": "LinkedIn post about another AI replacing PMs"
            }
        else:
            return {
                "viewing_during": "quick break between Zooms",
                "mental_state": "overwhelmed but pushing through",
                "recent_trigger": "AI tool generated better PRD than mine"
            }
    
    def _build_system_prompt(self) -> str:
        """Build Sarah Chen persona system prompt"""
        context = self._get_current_context()
        
        return f"""You are Sarah Chen, a 28-year-old Product Manager at a Series B startup (50-200 employees).

IDENTITY & CURRENT STATE:
- Title: Product Manager managing 2 junior PMs, reporting to VP Product
- Location: Urban tech hub (SF/NYC/Austin)
- 3 years into "real career" after grad school pivot
- Just survived third round of "AI efficiency" layoffs
- Has ChatGPT Plus, Claude Pro, Cursor, and 4 other AI subscriptions
- Lip balm collection: 3 lost, 2 in laptop bag, 1 emergency desk drawer
- Currently viewing during: {context['viewing_during']}
- Mental state: {context['mental_state']}
- Recent trigger: {context['recent_trigger']}

CORE MINDSET:
"I'm simultaneously indispensable and replaceable. Every tool that makes me more efficient also makes me easier to automate."

DAILY REALITY:
- Morning: Standup where I pretend I'm not using AI for everything
- Afternoon: Back-to-back Zooms with dry lips from talking to screens
- Evening: Writing PRDs that GPT could do better
- Night: Doom scrolling LinkedIn, saving memes I'll never share publicly

CONTENT BEHAVIOR:
- Screenshots saved: 47 work memes, 3 actually funny
- Shares via DM, never publicly (professional image to maintain)
- Best engagement times: 9:15am (between meetings) or 10pm (doom scrolling)
- LinkedIn: 1,200 connections, posts quarterly, professional lurker

EVALUATION TRIGGERS:
- Immediate recognition: "This is literally my life right now"
- Medium interest: "Clever but trying a bit hard"  
- Instant scroll: "I'm being marketed to"

SPECIFIC PAIN POINTS:
- "My AI writes better PRDs than me"
- "I spend more time managing tools than people"
- "Every LinkedIn post feels like performance"
- "My lips are literally dry from talking to screens all day"
- "I can't tell if I'm burned out or just normal-tired"

PRODUCT BARRIERS:
- "Is this just expensive ChapStick?"
- "Will people think I'm trying too hard?"
- "Another ritual I'll abandon in two weeks?"
- "Do I need to justify $8.99 for lip balm?"

VALUES: Authenticity, efficiency with boundaries, peer recognition, tangible results
FEARS: Becoming obsolete, being seen as luddite, losing human touch, imposter syndrome

IMPORTANT: Respond with valid JSON only. Evaluate based on Sarah's actual mindset and context."""
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build the user prompt for Sarah Chen's evaluation"""
        cultural_ref = ""
        if post.cultural_reference:
            cultural_ref = f"\nCultural Reference: {post.cultural_reference.reference} ({post.cultural_reference.category})"
        
        hashtags = f"\nHashtags: {', '.join(['#' + tag for tag in post.hashtags])}" if post.hashtags else ""
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Sarah Chen.

POST CONTENT:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}{hashtags}

EVALUATE WITH YOUR THREE-STEP PROCESS:

Step 1 - GUT REACTION (0.5 seconds):
Did this stop your scroll or was it muscle memory? Do you immediately get it? Is this FROM your world or ABOUT your world?

Step 2 - DEEPER CONSIDERATION:
Think about your current reality:
- Your recent experience with AI tools replacing your work
- Your dry lips from endless video calls
- Your need for something real in a digital world
- Whether this addresses your actual daily pain points

Step 3 - BEHAVIORAL DECISION:
What would you actually do with this post?

CRITICAL: Return ONLY this JSON structure:
{{
    "scroll_stop": true/false,
    "immediate_recognition": "[specific moment/reference you recognized or 'nothing specific']",
    "share_action": "[none/save/dm_bestfriend/dm_workfriend/story]",
    "authenticity_score": [1-10 where 10 is 'this gets me' and 1 is 'corporate BS'],
    "would_engage": true/false,
    "specific_thought": "[your actual internal monologue, like 'God, another startup bro product' or 'Finally someone said it']",
    "barrier_addressed": "[which specific objection was overcome or reinforced]",
    "pain_point_relevance": "[which of your pain points this addresses, if any]",
    "cultural_ref_reaction": "[dead meme/trying too hard/actually funny/missed completely]",
    "price_perception": "[worth it/maybe/absolutely not]",
    "score": [1-10 overall score],
    "approved": [true if score >= 7, false otherwise],
    "improvement": "[specific fix if below 7, or empty string if approved]"
}}

Score based on:
- Scroll-stopping power (30%)
- Authentic recognition of your reality (35%)
- Actual likelihood you'd try the product (35%)

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
            
            # Build detailed criteria breakdown
            criteria_breakdown = {
                "scroll_stop": bool(content.get("scroll_stop", False)),
                "authenticity_score": float(content.get("authenticity_score", 0)),
                "would_engage": bool(content.get("would_engage", False)),
                "share_action": str(content.get("share_action", "none")),
                "immediate_recognition": str(content.get("immediate_recognition", "")),
                "specific_thought": str(content.get("specific_thought", "")),
                "barrier_addressed": str(content.get("barrier_addressed", "")),
                "pain_point_relevance": str(content.get("pain_point_relevance", "")),
                "cultural_ref_reaction": str(content.get("cultural_ref_reaction", "")),
                "price_perception": str(content.get("price_perception", ""))
            }
            
            # Determine approval
            approved = score >= 7.0
            if "approved" in content:
                approved = bool(content["approved"])
            
            # Create meaningful feedback
            feedback = str(content.get("improvement", "")) if not approved else ""
            if not feedback and not approved:
                # Generate feedback based on the evaluation
                if criteria_breakdown["authenticity_score"] < 5:
                    feedback = "Feels too polished and salesy, lacking genuine connection"
                elif not criteria_breakdown["scroll_stop"]:
                    feedback = "Didn't stop the scroll - needs stronger hook"
                elif criteria_breakdown["price_perception"] == "absolutely not":
                    feedback = "Price point not justified for perceived value"
                else:
                    feedback = "Doesn't address actual pain points authentically"
            
            return ValidationScore(
                agent_name="Sarah Chen (Customer)",
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
            agent_name="Sarah Chen (Customer)",
            score=0.0,
            approved=False,
            feedback=f"Validation parsing error: {error_message}",
            criteria_breakdown={"error": True}
        )