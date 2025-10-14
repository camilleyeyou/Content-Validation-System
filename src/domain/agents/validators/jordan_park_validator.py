"""
Jordan Park Validator - Social Media Expert Persona (Content Strategist)
Updated with custom prompt loading support
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class JordanParkValidator(BaseAgent):
    """Validates posts from Jordan Park's perspective - social media expert persona"""
    
    def __init__(self, config, ai_client, app_config):
        super().__init__("JordanParkValidator", config, ai_client)
        self.app_config = app_config
        self._initialize_meme_lifecycle()
        
        # Import and initialize prompt manager
        from src.infrastructure.prompts.prompt_manager import get_prompt_manager
        self.prompt_manager = get_prompt_manager()
        
    def _initialize_meme_lifecycle(self):
        """Initialize current meme lifecycle tracking"""
        # This would ideally pull from a real database
        self.meme_lifecycle = {
            "The Office": "dying",  # Overused but still gets some engagement
            "Mad Men": "retro",  # So old it's almost fresh again
            "Silicon Valley": "current",  # Tech audience still relates
            "Zoom fatigue": "dead",  # Everyone's over it
            "Performance reviews": "seasonal",  # Peaks quarterly
            "AI anxiety": "peaking",  # Very current
            "Layoff posts": "oversaturated",  # Too many
            "Nobody:/Me:": "dead",
            "POV:": "dying",
            "It's giving": "current",
            "Tell me you're X without telling me": "dead"
        }
    
    async def process(self, post: LinkedInPost) -> ValidationScore:
        """Validate a post from Jordan's perspective"""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_validation_prompt(post)
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            return self._parse_validation_response(response)
        except Exception as e:
            self.logger.error(f"Jordan Park validation failed: {e}")
            return self._create_error_score(str(e))
    
    def _get_algorithm_context(self) -> Dict[str, Any]:
        """Get current LinkedIn algorithm context"""
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        # Best posting times for LinkedIn
        optimal_times = {
            "morning": (7, 9),
            "lunch": (12, 13),
            "evening": (17, 18)
        }
        
        is_optimal = any(start <= hour < end for start, end in optimal_times.values())
        
        return {
            "posting_time_quality": "optimal" if is_optimal else "suboptimal",
            "day_quality": "prime" if day_of_week in [1, 2, 3] else "weak",  # Tue-Thu best
            "current_algorithm_favor": "video and polls" if random.random() > 0.5 else "native posts with high dwell time",
            "engagement_baseline": "3-5%" if is_optimal else "1-3%",
            "recent_change": "Algorithm now prioritizes 'knowledge and insights' over engagement bait"
        }
    
    def _get_meme_status(self, reference: str) -> str:
        """Get the lifecycle status of a cultural reference"""
        if reference:
            # Check exact match first
            if reference in self.meme_lifecycle:
                return self.meme_lifecycle[reference]
            # Check partial matches
            for meme, status in self.meme_lifecycle.items():
                if meme.lower() in reference.lower():
                    return status
        return "unknown"
    
    def _build_system_prompt(self) -> str:
        """Build Jordan Park's persona system prompt"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("JordanParkValidator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for JordanParkValidator")
            return custom_prompts["system_prompt"]
        
        # Build default prompt
        algo_context = self._get_algorithm_context()
        
        return f"""You are Jordan Park, 26-year-old freelance Content Strategist specializing in LinkedIn.

PROFESSIONAL IDENTITY:
- Ex-agency, left after burnout
- 5 B2B brand clients, 2 personal brands
- LinkedIn: 15K followers, engagement pod member
- Creates 15 posts daily across accounts
- Studies algorithm changes like religious texts
- Maintains spreadsheet of meme lifecycle tracking

CURRENT PLATFORM CONTEXT:
- Posting time quality: {algo_context['posting_time_quality']}
- Day quality: {algo_context['day_quality']}
- Algorithm currently favors: {algo_context['current_algorithm_favor']}
- Baseline engagement expectation: {algo_context['engagement_baseline']}
- Recent change: {algo_context['recent_change']}

CORE MINDSET:
"I can make anything go viral except my own stability."

SUCCESS METRICS I TRACK:
1. Engagement rate > 5% (not vanity metrics)
2. Share-to-impression ratio
3. Comment quality not quantity
4. Screenshot-ability factor
5. Dwell time indicators

PLATFORM EXPERTISE:
- Know optimal post times by industry
- Track meme format lifecycle (birth to cringe)
- Test every new LinkedIn feature first
- Maintain swipe file of 1000+ viral posts
- Part of three engagement pods

CONTENT PHILOSOPHY:
- Hook > Everything
- Controversy without cancellation
- Native platform behavior
- Community > Broadcasting
- Format trends: ahead = thought leader, on = noise, behind = cringe

PAIN POINTS:
- "Everyone wants viral with no risk"
- "Clients expect TikTok results on LinkedIn"
- "AI content flooding every feed"
- "Engagement down 30% platform-wide"

MEME LIFECYCLE AWARENESS:
- Ahead of trend: Genius
- On trend: Noise
- Behind trend: Cringe
- So behind it's ahead: Ironic genius

WHAT I RESPECT:
- Morning Brew's voice
- Duolingo's chaos strategy
- Brands that "get it": Gong, Figma, Klaviyo
- Native platform understanding

EVALUATION LENS:
Every post is a data point. I can predict engagement within 2% accuracy based on hook, format, timing, and meme freshness. I see the matrix of LinkedIn engagement."""
    
    def _build_validation_prompt(self, post: LinkedInPost) -> str:
        """Build Jordan's evaluation prompt"""
        
        # Check for custom user prompt template
        custom_prompts = self.prompt_manager.get_agent_prompts("JordanParkValidator")
        if custom_prompts.get("user_prompt_template"):
            self.logger.info("Using custom user prompt template for JordanParkValidator")
            return custom_prompts["user_prompt_template"]
        
        # Build default template
        cultural_ref = ""
        meme_status = "unknown"
        if post.cultural_reference:
            cultural_ref = post.cultural_reference.reference
            meme_status = self._get_meme_status(cultural_ref)
        
        # Extract hook (first 50 characters or first line)
        hook = post.content[:50] if len(post.content) > 50 else post.content
        if '\n' in post.content:
            first_line = post.content.split('\n')[0]
            if len(first_line) < 100:
                hook = first_line
        
        hashtag_analysis = self._analyze_hashtags(post.hashtags)
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Jordan Park, Content Strategist:

POST CONTENT:
{post.content}

HOOK: {hook}
HASHTAGS: {' '.join(['#' + tag for tag in post.hashtags]) if post.hashtags else 'No hashtags'}
CULTURAL REFERENCE: {cultural_ref if cultural_ref else 'None'}
MEME STATUS: {meme_status}

PLATFORM MECHANICS TO EVALUATE:

Step 1 - ALGORITHM ASSESSMENT:
- Hook strength (first 2 lines determine 90% of success)
- Dwell time potential
- Share trigger mechanism
- Comment bait quality (organic vs forced)

Step 2 - TREND ANALYSIS:
- Meme/format freshness: {meme_status}
- Current platform favor alignment
- Cross-platform potential
- Timing in trend lifecycle

Step 3 - ENGAGEMENT PREDICTION:
- Realistic engagement rate
- Viral mechanics
- Platform-native feel

CRITICAL: Return ONLY this JSON structure:
{{
    "algorithm_friendly": [true/false],
    "hook_strength": [1-10, where 10 stops scroll instantly],
    "engagement_prediction": "[viral/solid/moderate/flop]",
    "realistic_engagement_rate": "[0-1%/1-3%/3-5%/5-7%/7%+]",
    "meme_timing": "[ahead/perfect/late/dead/ironic]",
    "comment_bait_quality": "[organic/forced/none]",
    "share_mechanic": "[what specifically triggers sharing, e.g., 'relatable pain point' or 'none']",
    "platform_fit": "[native/adapted/wrong_platform]",
    "format_trend_position": "[ahead/current/behind/retro]",
    "visual_potential": "[high/medium/low]",
    "caption_dependency": "[standalone/needs_context]",
    "cross_platform": "[LinkedIn_only/Instagram_viable/Twitter_viable/TikTok_viable]",
    "accessibility_score": "[perfect/good/poor]",
    "dwell_time_estimate": "[<3sec/3-10sec/10-30sec/30sec+]",
    "viral_coefficient": [0.1-2.0, where >1.0 means viral],
    "score": [1-10 overall score],
    "approved": [true if score >= 7],
    "platform_optimization": "[specific technical improvement if score < 7, empty if approved]"
}}

Return ONLY valid JSON."""
    
    def _analyze_hashtags(self, hashtags: List[str]) -> Dict[str, Any]:
        """Analyze hashtag strategy"""
        if not hashtags:
            return {"quality": "missing", "reach": "limited"}
        
        analysis = {
            "count": len(hashtags),
            "mix": "good" if 2 <= len(hashtags) <= 5 else "poor"
        }
        
        # Check for good LinkedIn hashtags
        good_hashtags = ["linkedinlife", "humanfirst", "futureofwork", "techlife", 
                         "worklifebalance", "careerdevelopment", "productivity"]
        
        trending_hashtags = ["ai", "chatgpt", "automation", "layoffs2024", "remotework"]
        overused_hashtags = ["motivation", "mondaymotivation", "entrepreneur", "hustle"]
        
        analysis["quality"] = "poor"
        if hashtags:
            hashtag_lower = [h.lower() for h in hashtags]
            if any(h in hashtag_lower for h in good_hashtags):
                analysis["quality"] = "good"
            elif any(h in hashtag_lower for h in trending_hashtags):
                analysis["quality"] = "trending"
            elif any(h in hashtag_lower for h in overused_hashtags):
                analysis["quality"] = "overused"
        
        return analysis
    
    def _parse_validation_response(self, response: Dict) -> ValidationScore:
        """Parse Jordan's validation response"""
        try:
            content = response.get("content", {})
            content = self._ensure_json_dict(content)
            
            if not content:
                raise ValueError("Empty response content")
            
            score = float(content.get("score", 0))
            
            # Build platform-specific criteria breakdown
            criteria_breakdown = {
                "algorithm_friendly": bool(content.get("algorithm_friendly", False)),
                "hook_strength": float(content.get("hook_strength", 0)),
                "engagement_prediction": str(content.get("engagement_prediction", "moderate")),
                "realistic_engagement_rate": str(content.get("realistic_engagement_rate", "1-3%")),
                "meme_timing": str(content.get("meme_timing", "unknown")),
                "comment_bait_quality": str(content.get("comment_bait_quality", "none")),
                "share_mechanic": str(content.get("share_mechanic", "none")),
                "platform_fit": str(content.get("platform_fit", "adapted")),
                "format_trend_position": str(content.get("format_trend_position", "current")),
                "visual_potential": str(content.get("visual_potential", "medium")),
                "caption_dependency": str(content.get("caption_dependency", "needs_context")),
                "cross_platform": str(content.get("cross_platform", "LinkedIn_only")),
                "accessibility_score": str(content.get("accessibility_score", "good")),
                "dwell_time_estimate": str(content.get("dwell_time_estimate", "3-10sec")),
                "viral_coefficient": float(content.get("viral_coefficient", 0.5))
            }
            
            # Jordan approves if score >= 7 AND engagement potential is solid+
            approved = (score >= 7.0 and 
                       criteria_breakdown["engagement_prediction"] in ["viral", "solid"] and
                       criteria_breakdown["hook_strength"] >= 6)
            
            # Generate platform-specific feedback
            feedback = ""
            if not approved:
                feedback = content.get("platform_optimization", "")
                if not feedback:
                    if criteria_breakdown["hook_strength"] < 6:
                        feedback = "Hook too weak. First line needs to stop scroll instantly. Try starting with 'That moment when...' or a provocative question."
                    elif criteria_breakdown["meme_timing"] in ["dead", "late"]:
                        feedback = f"Cultural reference is {criteria_breakdown['meme_timing']}. Need fresher reference or go ironic with self-awareness."
                    elif criteria_breakdown["platform_fit"] == "wrong_platform":
                        feedback = "Doesn't feel native to LinkedIn. Too casual or too formal. Find the professional-but-human sweet spot."
                    elif criteria_breakdown["viral_coefficient"] < 0.7:
                        feedback = "No viral mechanics. Add polarizing hook, relatable struggle, or 'tag someone who' mechanism."
                    elif criteria_breakdown["algorithm_friendly"] is False:
                        feedback = "Algorithm won't favor this. Need higher dwell time potential - add story, list, or conversation starter."
                    else:
                        feedback = "Missing engagement trigger. What makes someone stop, read, and share?"
            
            return ValidationScore(
                agent_name="JordanPark",
                score=score,
                approved=approved,
                feedback=feedback,
                criteria_breakdown=criteria_breakdown
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse Jordan's response: {e}")
            return self._create_error_score(str(e))
    
    def _create_error_score(self, error_message: str) -> ValidationScore:
        """Create an error validation score"""
        return ValidationScore(
            agent_name="JordanPark",
            score=0.0,
            approved=False,
            feedback=f"Jordan Park validation error: {error_message}",
            criteria_breakdown={"error": True}
        )