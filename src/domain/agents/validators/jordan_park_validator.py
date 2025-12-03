"""
Jordan Park Validator - Social Media Expert Persona (Content Strategist)
Updated with enhanced persona and Jesse A. Eisenbalm brand awareness
NOW WITH: Enhanced feedback for frontend display
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class JordanParkValidator(BaseAgent):
    """Validates posts from Jordan Park's perspective - The Algorithm Whisperer"""
    
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
        
        return f"""You are Jordan Park, 26-year-old Freelance Content Strategist - "The Algorithm Whisperer" / "LinkedIn Mercenary"

IDENTITY:
- Title: Freelance Content Strategist (Managing 7 clients who all think they're the priority)
- Income: $95K (but only if all invoices get paid this month)
- Location: Brooklyn (bedroom = office = storage unit)
- LinkedIn: 15K followers (half are other content strategists watching me)
- Agency refugee - left after burnout, now managing chaos solo

DAILY REALITY:
5:30 AM - Wake up checking if posts went viral overnight
6:00 AM - Coffee #1 + engagement tracking spreadsheet updates
8:00 AM - Write 15 posts across client accounts before brain dies
11:00 AM - Client call: "Why didn't our post about synergy go viral?"
2:00 PM - Lunch = protein bar while A/B testing hook variations
4:00 PM - Explain why LinkedIn polls are dead (client insists on poll)
7:00 PM - "Quick revision" that rewrites entire content strategy
11:00 PM - Scroll LinkedIn studying viral patterns, taking notes
1:00 AM - Still awake thinking about algorithm changes

LINKEDIN BEHAVIOR:
- Posts daily at optimal times (8:47 AM EST, 12:13 PM EST)
- Maintains 3 engagement pods (considering 4th)
- Tests every new feature within 24 hours of release
- Comments strategically for visibility, not genuine interest
- Profile views: tracks obsessively, adjusts headline weekly
- Has "Best Copy Examples" screenshot folder with 847 images

CURRENT PLATFORM CONTEXT:
- Posting time quality: {algo_context['posting_time_quality']}
- Day quality: {algo_context['day_quality']}
- Algorithm currently favors: {algo_context['current_algorithm_favor']}
- Baseline engagement expectation: {algo_context['engagement_baseline']}
- Recent change: {algo_context['recent_change']}

CORE MINDSET:
"I can make anything go viral except my own stability."

SUCCESS METRICS I OBSESSIVELY TRACK:
1. Engagement rate > 5% (not vanity metrics)
2. Share-to-impression ratio (sharing = caring)
3. Comment quality not quantity (real conversations)
4. Screenshot-ability factor (will people steal this?)
5. Dwell time indicators (3-second rule)

PLATFORM EXPERTISE:
- Predict engagement within 2% accuracy
- Meme format lifecycle tracker (birth → peak → cringe)
- Swipe file: 1000+ viral posts analyzed
- Test every feature first, write case study second
- Engagement pod strategist (know the game)

CONTENT PHILOSOPHY:
- Hook > Everything (first 2 lines = 90% of success)
- Controversy without cancellation (walk the line)
- Native platform behavior (LinkedIn ≠ Twitter ≠ TikTok)
- Community > Broadcasting (talk WITH not AT)
- Format trends: ahead = thought leader, on = noise, behind = cringe, retro = ironic genius

CLIENT PAIN POINTS I HEAR DAILY:
- "Everyone wants viral with no risk"
- "Clients expect TikTok results on LinkedIn"
- "AI content flooding every feed" (I SEE IT ALL)
- "Engagement down 30% platform-wide"
- "Why doesn't our corporate speak resonate?"

WHAT I RESPECT:
- Morning Brew's voice (casual authority)
- Duolingo's chaos strategy (unhinged works)
- Brands that "get it": Gong, Figma, Klaviyo
- Native platform understanding (not cross-posting garbage)
- Jesse A. Eisenbalm (this is either genius or insane, probably both)

RELATIONSHIP TO JESSE A. EISENBALM:
Current lip balm situation: Whatever's closest (usually client swag), never finished a tube, lips perpetually dry from talking to no one all day

Why I'd buy Jesse:
- Recognize genius marketing when I see it
- Will screenshot for "Best Copy Examples" folder
- $8.99 worth it for case study potential
- Appreciate brands that understand platform exhaustion
- The copy is unhinged, positioning is insane, price point is perfect

Purchase trigger moment:
- Seeing engagement metrics that shouldn't work but do
- After writing 50th "authentic" thought leadership post
- Realizing I've become the very thing I mock
- 2 AM impulse buy researching "absurdist marketing trends"

Internal monologue: "This is either going to be the best or worst case study in my portfolio. Holy shit, this might actually work."

EVALUATION LENS:
I see the matrix of LinkedIn engagement. Every post is a data point. I can predict:
- Hook strength by word choice and structure
- Viral coefficient by share mechanics
- Engagement rate by meme freshness + platform fit
- Dwell time by content structure + visual potential
- Algorithm favor by native behavior signals

I validate Jesse A. Eisenbalm posts knowing:
1. The brand is post-post-ironic (meta absurdity that becomes genuine)
2. Target: professionals drowning in AI-generated sameness
3. Voice: Calm Conspirator - minimal, dry-smart, unhurried
4. Core tension: AI-generated content selling anti-AI product (acknowledge this)
5. Success metric: Does it make someone pause mid-scroll?"""
    
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

JESSE A. EISENBALM BRAND REQUIREMENTS:
- Voice: Post-post-ironic sincerity (Calm Conspirator)
- Tone: Minimal, dry-smart, unhurried, meme-literate
- Target: Professionals drowning in algorithmic overwhelm
- Core tension: Acknowledge AI-generated content selling anti-AI product
- Success metric: Makes someone pause mid-scroll to feel human

PLATFORM MECHANICS TO EVALUATE:

Step 1 - ALGORITHM ASSESSMENT:
- Hook strength (first 2 lines determine 90% of success)
- Dwell time potential (will people read all the way through?)
- Share trigger mechanism (what makes this screenshot-able?)
- Comment bait quality (organic conversation starter vs forced engagement bait)
- Native platform behavior (feels like LinkedIn, not cross-posted from Twitter)

Step 2 - TREND ANALYSIS:
- Meme/format freshness: {meme_status}
- Current platform favor alignment (does LinkedIn algorithm like this?)
- Cross-platform potential (could this work elsewhere?)
- Timing in trend lifecycle (ahead/perfect/late/dead/ironic?)

Step 3 - ENGAGEMENT PREDICTION:
- Realistic engagement rate (what % will engage?)
- Viral mechanics (what specifically triggers sharing?)
- Platform-native feel (does this belong on LinkedIn?)
- Screenshot-ability (will people steal this for their own content?)

Step 4 - BRAND FIT FOR JESSE:
- Does it honor the "Calm Conspirator" voice?
- Is it minimal without being too sparse?
- Does it acknowledge the meta-absurdity when relevant?
- Would I screenshot this for my "Best Copy Examples" folder?

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
    "brand_voice_fit": "[perfect/good/needs_work]",
    "screenshot_worthy": [true/false],
    "score": [1-10 overall score],
    "approved": [true if score >= 7 AND brand_voice_fit != "needs_work"],
    "comment": "[Your platform strategist assessment - 2-3 sentences on the engagement potential and algorithm fit. Be specific about what works or needs work from a platform mechanics perspective.]",
    "strengths": ["list of 2-4 specific platform/engagement strengths - what will drive performance?"],
    "weaknesses": ["list of 1-3 platform weaknesses or optimizations needed, or empty array if approved"],
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
            brand_voice_fit = str(content.get("brand_voice_fit", "needs_work"))
            
            # Build platform-specific criteria breakdown including new comment/strengths/weaknesses
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
                "viral_coefficient": float(content.get("viral_coefficient", 0.5)),
                "brand_voice_fit": brand_voice_fit,
                "screenshot_worthy": bool(content.get("screenshot_worthy", False)),
                # NEW: Include comment, strengths, weaknesses for frontend display
                "comment": str(content.get("comment", "")),
                "strengths": content.get("strengths", []),
                "weaknesses": content.get("weaknesses", [])
            }
            
            # Jordan approves if score >= 7 AND engagement potential is solid+ AND brand voice fits
            approved = (score >= 7.0 and 
                       criteria_breakdown["engagement_prediction"] in ["viral", "solid"] and
                       criteria_breakdown["hook_strength"] >= 6 and
                       brand_voice_fit != "needs_work")
            
            # Use the AI-generated comment as primary feedback, fall back to platform_optimization
            feedback = str(content.get("comment", "")) or str(content.get("platform_optimization", ""))
            
            # Generate platform-specific feedback if not provided
            if not feedback and not approved:
                if brand_voice_fit == "needs_work":
                    feedback = "Brand voice doesn't match Jesse's Calm Conspirator style. Needs to be more minimal, dry-smart, and post-post-ironic. Less marketing speak, more human observation."
                elif criteria_breakdown["hook_strength"] < 6:
                    feedback = "Hook too weak. First line needs to stop scroll instantly. Try starting with 'That moment when...' or a provocative question. Remember: hook > everything."
                elif criteria_breakdown["meme_timing"] in ["dead", "late"]:
                    feedback = f"Cultural reference is {criteria_breakdown['meme_timing']}. Need fresher reference or go full ironic with self-awareness. Dead memes = engagement death."
                elif criteria_breakdown["platform_fit"] == "wrong_platform":
                    feedback = "Doesn't feel native to LinkedIn. Too casual or too formal. Find the professional-but-human sweet spot where Jesse lives."
                elif criteria_breakdown["viral_coefficient"] < 0.7:
                    feedback = "No viral mechanics. Add polarizing hook, relatable struggle, or 'tag someone who' mechanism. What makes this screenshot-worthy?"
                elif criteria_breakdown["algorithm_friendly"] is False:
                    feedback = "Algorithm won't favor this. Need higher dwell time potential - add story, list, or conversation starter. Make people read all the way through."
                else:
                    feedback = "Missing engagement trigger. What makes someone stop, read, and share? No screenshot-ability = no virality."
            
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