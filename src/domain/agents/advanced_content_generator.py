"""
Advanced Content Generator - Creates LinkedIn posts using multi-element combination protocol
Updated with custom prompt loading support
"""

import json
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.domain.models.post import LinkedInPost, CulturalReference
from src.infrastructure.config.config_manager import AppConfig

class AdvancedContentGenerator(BaseAgent):
    """Generates LinkedIn posts using two-element combination strategy"""
    
    def __init__(self, config: AgentConfig, ai_client, app_config: AppConfig):
        super().__init__("AdvancedContentGenerator", config, ai_client)
        self.app_config = app_config
        self.brand = app_config.brand
        self._initialize_elements()
        
    def _initialize_elements(self):
        """Initialize the 25 content elements"""
        self.content_elements = [
            "trending_event",           # Current trending event from past 48 hours
            "ai_workplace_cliche",      # ChatGPT wrote my email, etc.
            "mindfulness_wisdom",       # Breathwork, presence, meditation
            "nihilism",                 # Nothing matters but moisturized lips
            "dad_joke",                 # Groan-worthy puns
            "yiddish_wisdom",          # Old world truth meets new chaos
            "cultural_moment",          # Super Bowl, tax season, etc.
            "overheard_at_tech",       # Anonymous insider moments
            "linkedin_algorithm",       # Platform changes (real or imagined)
            "quarterly_anxiety",        # Earnings, reviews, planning
            "day_specific_emotion",     # Monday dread through Friday relief
            "gen_z_millennial_friction", # Generational workplace tension
            "return_to_office_drama",   # RTO conflicts
            "therapy_speak_corporate",  # Mental health language in business
            "productivity_backlash",    # Against productivity influencers
            "slack_teams_chaos",        # Communication platform disasters
            "meeting_mishaps",          # Zoom/Teams failures
            "job_title_inflation",      # Absurd title escalation
            "coffee_shop_theater",      # Performative productivity
            "employment_data",          # Job market reality
            "vc_prediction",            # Tech prophecies
            "layoff_tracker",           # Current layoff updates
            "ai_tool_graveyard",        # Failed AI products
            "tech_nostalgia",           # When email was enough
            "office_supply_romance"     # Love for physical objects
        ]
        
        self.story_arcs = {
            "FALSE_SUMMIT": "Achievement → Plot twist → Real lesson",
            "INNOCENT_ABROAD": "Expectation → Reality slap → Wisdom",
            "RITUAL_DISRUPTED": "Routine → Chaos → New normal",
            "TROJAN_HORSE": "Safe surface → Subversive middle → Truth bomb",
            "GROUNDHOG_DAY": "Cycle → Recognition → Break/Accept → Reset"
        }
        
        self.post_lengths = {
            "MICRO": (1, 30),           # 1-30 words
            "HAIKU": (30, 50),          # 30-50 words
            "MEME": (50, 80),           # 50-80 words
            "SHORT_STORY": (100, 150),  # 100-150 words
            "FULL_NARRATIVE": (200, 250) # 200-250 words
        }
    
    async def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a batch of LinkedIn posts using element combination strategy"""
        batch_id = input_data.get("batch_id")
        count = input_data.get("count", 5)
        avoid_patterns = input_data.get("avoid_patterns", {})
        
        posts = []
        for i in range(count):
            # Generate each post with unique element combination
            post = await self._generate_single_post(batch_id, i + 1, avoid_patterns)
            if post:
                posts.append(post)
        
        # If we didn't get enough posts, fill with fallbacks
        while len(posts) < count:
            posts.append(self._create_fallback_post(batch_id, len(posts) + 1))
        
        return posts
    
    async def _generate_single_post(self, batch_id: str, post_number: int, avoid_patterns: Dict) -> Dict[str, Any]:
        """Generate a single post using the protocol"""
        # Step 1: Select two elements
        elements = self._select_elements(avoid_patterns)
        
        # Step 2: Choose story arc based on elements
        story_arc = self._choose_story_arc(elements)
        
        # Step 3: Determine length
        length_type = self._determine_length()
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_generation_prompt(elements, story_arc, length_type)
        
        try:
            response = await self._call_ai(user_prompt, system_prompt, response_format="json")
            post_data = self._parse_generation_response(response)
            
            if post_data:
                post_data["batch_id"] = batch_id
                post_data["post_number"] = post_number
                post_data["elements_used"] = elements
                post_data["story_arc"] = story_arc
                post_data["length_type"] = length_type
                return post_data
                
        except Exception as e:
            self.logger.error(f"Failed to generate post: {e}")
            
        return None
    
    def _select_elements(self, avoid_patterns: Dict) -> Tuple[str, str]:
        """Select two elements, avoiding failed patterns"""
        available_elements = self.content_elements.copy()
        
        # Remove elements that have failed before
        if "failed_elements" in avoid_patterns:
            for failed in avoid_patterns["failed_elements"]:
                if failed in available_elements:
                    available_elements.remove(failed)
        
        # Ensure we have enough elements
        if len(available_elements) < 2:
            available_elements = self.content_elements.copy()
        
        # Select two random elements
        selected = random.sample(available_elements, 2)
        return tuple(selected)
    
    def _choose_story_arc(self, elements: Tuple[str, str]) -> str:
        """Choose story arc based on element combination"""
        element1, element2 = elements
        
        # Strategic arc selection based on elements
        if "nihilism" in elements or "ai_tool_graveyard" in elements:
            return "GROUNDHOG_DAY"
        elif "trending_event" in elements or "cultural_moment" in elements:
            return "INNOCENT_ABROAD"
        elif "mindfulness_wisdom" in elements:
            return "RITUAL_DISRUPTED"
        elif "dad_joke" in elements or "yiddish_wisdom" in elements:
            return "TROJAN_HORSE"
        else:
            return "FALSE_SUMMIT"
    
    def _determine_length(self) -> str:
        """Randomly determine post length for variety"""
        # Weight towards medium-length posts
        weights = {
            "MICRO": 0.15,
            "HAIKU": 0.20,
            "MEME": 0.25,
            "SHORT_STORY": 0.25,
            "FULL_NARRATIVE": 0.15
        }
        
        return random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for advanced content generation"""
        # Build default prompt
        default_prompt = f"""You are a LinkedIn content creator for Jesse A. Eisenbalm, a premium lip balm brand.

BRAND ESSENCE: 
A physical, analog product that bridges the gap between digital overwhelm and human presence. 
The absurdist answer to "What makes us irreplaceably human?"

PRODUCT DETAILS:
- Price: $8.99
- Key ingredients: organic beeswax, pocket-sized
- Ritual: "Stop. Breathe. Apply."
- Tagline: "The only business lip balm that keeps you human in an AI world"

VOICE REQUIREMENTS:
- Absurdist but not nonsensical
- Corporate satire that still feels professional
- Vulnerable without therapy-posting
- Premium but self-aware
- Wry observations that sting with truth

MANDATORY COMPONENTS FOR EVERY POST:
1. One specific reference from the last 7 days
2. One "confession" professionals think but don't post
3. The moment where lip balm becomes necessary
4. Subtle product integration

You MUST respond with valid JSON format only."""
        
        # Return custom prompt if exists, otherwise default
        return self._get_system_prompt(default_prompt)
    
    def _build_generation_prompt(self, elements: Tuple[str, str], story_arc: str, length_type: str) -> str:
        """Build the user prompt for post generation"""
        element_descriptions = self._get_element_descriptions(elements)
        arc_structure = self.story_arcs[story_arc]
        min_words, max_words = self.post_lengths[length_type]
        format_template = self._get_format_template(length_type)
        
        # Build default template
        default_template = f"""Generate a LinkedIn post for Jesse A. Eisenbalm using this exact protocol:

ELEMENTS TO COMBINE:
1. {element_descriptions[0]}
2. {element_descriptions[1]}

STORY ARC: {story_arc}
Structure: {arc_structure}

LENGTH: {length_type} ({min_words}-{max_words} words)

FORMAT TEMPLATE:
{format_template}

CURRENT CONTEXT:
- Date: {datetime.now().strftime('%B %d, %Y')}
- Day: {datetime.now().strftime('%A')}
- Recent event to reference: Use a real trending topic from this week

REQUIREMENTS:
- Combine both elements naturally
- Follow the story arc structure
- Stay within word count ({min_words}-{max_words} words)
- Include specific moment where dry lips become the breaking point
- Mention $8.99 price naturally if possible
- End with 2-4 hashtags (mix professional with one absurdist)

CRITICAL: Return ONLY this JSON structure:
{{
    "content": "The complete post text with hashtags...",
    "hook": "The opening line that stops scroll",
    "confession": "The unspoken professional truth included",
    "lip_balm_moment": "Where the product naturally enters",
    "cultural_reference": {{
        "category": "which element category",
        "reference": "specific reference used",
        "context": "how it connects to AI workplace anxiety"
    }},
    "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
    "target_audience": "specific professional segment",
    "emotional_trigger": "what feeling this targets"
}}

Generate the post now. Return ONLY valid JSON."""
        
        # Return custom template if exists, otherwise default
        return self._get_user_prompt_template(default_template)
    
    def _get_element_descriptions(self, elements: Tuple[str, str]) -> Tuple[str, str]:
        """Get detailed descriptions for selected elements"""
        descriptions = {
            "trending_event": "Current trending event from past 48 hours (check actual news)",
            "ai_workplace_cliche": "Clichéd AI scenario (ChatGPT wrote my email, AI screening resume)",
            "mindfulness_wisdom": "Mindfulness/meditation wisdom meets corporate chaos",
            "nihilism": "Nihilistic observation (nothing matters but moisturized lips do)",
            "dad_joke": "Groan-worthy pun about lips/work/AI",
            "yiddish_wisdom": "Old world Yiddish truth meets new world chaos",
            "cultural_moment": "Current cultural moment (Super Bowl, tax season, daylight savings)",
            "overheard_at_tech": "'Overheard at [Tech Company]' anonymous moment",
            "linkedin_algorithm": "LinkedIn algorithm update (real or imagined)",
            "quarterly_anxiety": "Quarterly business anxiety (earnings, reviews, planning)",
            "day_specific_emotion": "Day-specific emotion (Monday dread, Friday relief)",
            "gen_z_millennial_friction": "Gen Z vs Millennial workplace friction",
            "return_to_office_drama": "Return-to-office conflict or absurdity",
            "therapy_speak_corporate": "Therapy language invading corporate speak",
            "productivity_backlash": "Backlash against productivity influencers",
            "slack_teams_chaos": "Slack/Teams communication disaster",
            "meeting_mishaps": "Zoom/Teams meeting failure (mute, background, etc)",
            "job_title_inflation": "Absurd job title inflation observation",
            "coffee_shop_theater": "Coffee shop productivity theater",
            "employment_data": "Current employment data reality check",
            "vc_prediction": "VC prediction or tech prophecy",
            "layoff_tracker": "Current layoff tracker update",
            "ai_tool_graveyard": "Failed AI product observation",
            "tech_nostalgia": "Nostalgia for simpler tech times",
            "office_supply_romance": "Romance with physical office supplies"
        }
        
        return (descriptions.get(elements[0], elements[0]), 
                descriptions.get(elements[1], elements[1]))
    
    def _get_format_template(self, length_type: str) -> str:
        """Get the format template for the specified length"""
        templates = {
            "MICRO": """[Shocking truth] + [Jesse A. Eisenbalm as only response]
Example: 'My AI assistant just asked if I'm okay. Time for Jesse A. Eisenbalm.'""",
            
            "HAIKU": """Line 1: [Element 1 sets scene]
Line 2: [Element 2 creates tension]  
Line 3: [Lip balm wisdom]""",
            
            "MEME": """Nobody:
[Element 1]: [expected behavior]
[Element 2]: [chaos injection]
Me: [applying lip balm while world burns]""",
            
            "SHORT_STORY": """Opening: [Relatable workplace moment]
Complication: [AI/modern work intrusion]
Physical need: [Dry lips as metaphor]
Resolution: [Ritual as rebellion]""",
            
            "FULL_NARRATIVE": """Setup: [Detailed scene with Element 1]
Rising action: [Element 2 enters]
Climax: [Absurdist collision point]
Human moment: [Physical sensation grounding]
Brand philosophy: [Why this matters]
Call to action: [Join the resistance]"""
        }
        
        return templates.get(length_type, templates["SHORT_STORY"])
    
    def _parse_generation_response(self, response: Dict) -> Dict[str, Any]:
        """Parse the AI response into post data"""
        try:
            content = response.get("content", {})
            content = self._ensure_json_dict(content)
            
            if not content or "content" not in content:
                self.logger.error("Response missing content field")
                return None
            
            # Extract and validate required fields
            post_content = content.get("content", "").strip()
            if len(post_content) < 20:
                self.logger.error("Generated content too short")
                return None
            
            # Build post data
            post_data = {
                "content": post_content,
                "hook": content.get("hook", post_content[:50]),
                "confession": content.get("confession", ""),
                "lip_balm_moment": content.get("lip_balm_moment", ""),
                "target_audience": content.get("target_audience", "Tech professionals"),
                "emotional_trigger": content.get("emotional_trigger", "workplace anxiety"),
                "hashtags": content.get("hashtags", ["HumanFirst", "LinkedInLife"]),
                "cultural_reference": None
            }
            
            # Process cultural reference
            if content.get("cultural_reference"):
                ref = content["cultural_reference"]
                if isinstance(ref, dict):
                    post_data["cultural_reference"] = CulturalReference(
                        category=ref.get("category", "workplace"),
                        reference=ref.get("reference", "modern work"),
                        context=ref.get("context", "AI anxiety")
                    )
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Failed to parse response: {e}")
            return None
    
    def _create_fallback_post(self, batch_id: str, post_number: int) -> Dict[str, Any]:
        """Create a fallback post when generation fails"""
        fallback_posts = [
            {
                "content": """That moment when your AI assistant schedules a "sync on syncing" and you realize: this is it. This is the meeting that breaks you.

Stop. Breathe. Apply Jesse A. Eisenbalm.

Because while machines optimize your calendar into oblivion, your lips deserve $8.99 worth of organic beeswax rebellion.

#HumanFirst #MeetingMadness #LinkedInLife #LipBalmResistance""",
                "elements": ["meeting_mishaps", "ai_workplace_cliche"],
                "story_arc": "FALSE_SUMMIT"
            },
            {
                "content": """Nobody:
LinkedIn algorithm: "Engagement is down 30%"
My ChatGPT: "I can write your posts!"
Me: *applies Jesse A. Eisenbalm while typing this myself*

Some things should stay human. Starting with your lips. $8.99.

#StayHuman #AlgorithmBlues #AuthenticContent""",
                "elements": ["linkedin_algorithm", "ai_workplace_cliche"],
                "story_arc": "GROUNDHOG_DAY"
            },
            {
                "content": """Overheard in Zoom waiting room:
"Is this AI generated?"
"Everything is."
"Even this conversation?"
"Especially this conversation."

*reaches for Jesse A. Eisenbalm*

The only thing that's definitely not artificial? Dry lips from talking to screens all day.

#ZoomLife #RealMoments #DigitalFatigue""",
                "elements": ["overheard_at_tech", "meeting_mishaps"],
                "story_arc": "INNOCENT_ABROAD"
            }
        ]
        
        selected = random.choice(fallback_posts)
        
        return {
            "batch_id": batch_id,
            "post_number": post_number,
            "content": selected["content"],
            "target_audience": "Tech professionals",
            "hashtags": ["HumanFirst", "LinkedInLife", "StayHuman"],
            "cultural_reference": CulturalReference(
                category="workplace",
                reference=selected["elements"][0],
                context="AI workplace anxiety"
            ),
            "elements_used": selected["elements"],
            "story_arc": selected["story_arc"],
            "length_type": "SHORT_STORY"
        }