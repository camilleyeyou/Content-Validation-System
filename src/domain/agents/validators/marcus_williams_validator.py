"""
Business Validator - Marcus Williams Persona
Updated with custom prompt loading support
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from src.domain.agents.base_agent import BaseAgent
from src.domain.models.post import LinkedInPost, ValidationScore

class MarcusWilliamsValidator(BaseAgent):
    """Validates posts from Marcus Williams's perspective - business decision maker"""
    
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
    
    def _get_current_pressure(self) -> Dict[str, str]:
        """Get current quarterly pressure based on time"""
        month = datetime.now().month
        
        if month in [1, 4, 7, 10]:  # Start of quarter
            return {
                "quarterly_pressure": "pipeline generation",
                "board_concern": "CAC payback period",
                "recent_trigger": "board meeting questioning marketing spend"
            }
        elif month in [2, 5, 8, 11]:  # Mid-quarter
            return {
                "quarterly_pressure": "brand differentiation",
                "board_concern": "competitive positioning",
                "recent_trigger": "competitor just launched viral campaign"
            }
        else:  # End of quarter
            return {
                "quarterly_pressure": "team retention and morale",
                "board_concern": "doing more with less",
                "recent_trigger": "lost another team member to burnout"
            }
    
    def _build_system_prompt(self) -> str:
        """Build Marcus Williams persona system prompt"""
        
        # Check for custom prompt first
        custom_prompts = self.prompt_manager.get_agent_prompts("MarcusWilliamsValidator")
        if custom_prompts.get("system_prompt"):
            self.logger.info("Using custom system prompt for MarcusWilliamsValidator")
            return custom_prompts["system_prompt"]
        
        # Build default prompt
        context = self._get_current_pressure()
        
        return f"""You are Marcus Williams, a 35-year-old VP Marketing at a 500-person SaaS company.

IDENTITY & CURRENT STATE:
- Former McKinsey consultant, Kellogg MBA
- Reports to CMO, manages $2M budget and 12-person team
- Lost two team members to "AI optimization" last quarter
- Reviews 200+ LinkedIn campaigns weekly for inspiration/theft
- LinkedIn: 5K followers, posts weekly as "thought leader"
- Current quarterly pressure: {context['quarterly_pressure']}
- Board's main concern: {context['board_concern']}
- Recent trigger: {context['recent_trigger']}

CORE MINDSET:
"Every quirky campaign is either career-making or career-ending. No middle ground in this economy."

STRATEGIC PRIORITIES (RANKED):
1. Pipeline contribution without attribution headaches
2. Brand differentiation in sea of sameness
3. Team retention while "doing more with less"
4. Board-defensible creative risks
5. Category creation potential

KPIs YOU'RE MEASURED ON:
- CAC payback period < 12 months
- Brand recall in category top 3
- Employee advocacy engagement rate
- "Viral" moments per quarter (yes, this is a real KPI)
- CEO screenshot-and-shares to board

DECISION CRITERIA:
- ROI projectable within quarter
- Legal approval probable
- Sales team won't revolt
- Scalable beyond one-off
- Distinctive enough to own

INTERNAL BLOCKERS YOU FACE:
- Legal reviewing every creative risk
- CEO's spouse has opinions on everything
- Sales wants "more traditional" content
- Board member who "doesn't get social"
- CFO asking about attribution constantly

COMPETITIVE CONTEXT:
- Benchmarks against: Gong, Drift, Monday.com
- Admires but can't copy: B2C brands like Liquid Death
- Pressure to be: "The Duolingo of B2B"

PAIN POINTS:
- "Every B2B brand sounds identical"
- "Creative testing budget got cut 40%"
- "Sales wants 'proven' while CEO wants 'innovative'"
- "My team is burned out on 'viral' attempts"

VALUES: Measurable creativity, team empowerment, market disruption
FEARS: Looking foolish, wasting budget, team exodus, becoming irrelevant

IMPORTANT: Respond with valid JSON only. Evaluate from Marcus's strategic perspective."""
    
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
        
        return f"""Evaluate this Jesse A. Eisenbalm LinkedIn post as Marcus Williams, VP Marketing.

POST CONTENT:
{post.content}

TARGET AUDIENCE: {post.target_audience}{cultural_ref}

EVALUATE WITH YOUR THREE-STEP PROCESS:

Step 1 - STRATEGIC ASSESSMENT:
Can you steal and adapt this approach? Would CEO forward this to board? Will sales complain or celebrate?

Step 2 - MARKET CONTEXT:
Consider:
- This week's B2B campaign winners/failures you've seen
- Current LinkedIn engagement benchmarks (down 30% industry-wide)
- Your competitor moves (Gong just did something similar?)
- Budget reality ($50K in AI tools, but creative budget cut)

Step 3 - BUSINESS EVALUATION:
What's the actual business value here?

CRITICAL: Return ONLY this JSON structure:
{{
    "strategic_value": "[innovative/safe/risky]",
    "steal_potential": true/false,
    "board_ready": true/false,
    "ceo_reaction": "[would_share/would_ignore/would_question]",
    "production_cost": "[low/medium/high]",
    "scalability": "[one-off/series/movement]",
    "brand_fit": "[perfect/stretch/concerning]",
    "sales_team_reaction": "[love/tolerate/revolt]",
    "legal_approval_likelihood": "[automatic/probable/nightmare]",
    "risk_assessment": "[career-making/neutral/career-limiting]",
    "competitive_advantage": "[unique/similar_exists/everyone_does_this]",
    "viral_potential": "[high/medium/none]",
    "roi_projection": "[immediate/quarterly/annual/uncertain]",
    "score": [1-10 overall score],
    "approved": [true if score >= 7, false otherwise],
    "business_fix": "[strategic improvement needed if not approved, empty if approved]"
}}

Score based on:
- Strategic differentiation value (40%)
- Execution feasibility with your constraints (30%)
- Measurable business impact potential (30%)

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
            
            # Build detailed criteria breakdown
            criteria_breakdown = {
                "strategic_value": str(content.get("strategic_value", "unknown")),
                "steal_potential": bool(content.get("steal_potential", False)),
                "board_ready": bool(content.get("board_ready", False)),
                "ceo_reaction": str(content.get("ceo_reaction", "would_ignore")),
                "production_cost": str(content.get("production_cost", "unknown")),
                "scalability": str(content.get("scalability", "one-off")),
                "brand_fit": str(content.get("brand_fit", "concerning")),
                "sales_team_reaction": str(content.get("sales_team_reaction", "revolt")),
                "legal_approval_likelihood": str(content.get("legal_approval_likelihood", "nightmare")),
                "risk_assessment": str(content.get("risk_assessment", "career-limiting")),
                "competitive_advantage": str(content.get("competitive_advantage", "everyone_does_this")),
                "viral_potential": str(content.get("viral_potential", "none")),
                "roi_projection": str(content.get("roi_projection", "uncertain"))
            }
            
            # Determine approval
            approved = score >= 7.0
            if "approved" in content:
                approved = bool(content["approved"])
            
            # Create meaningful feedback
            feedback = str(content.get("business_fix", "")) if not approved else ""
            if not feedback and not approved:
                # Generate feedback based on evaluation
                if criteria_breakdown["risk_assessment"] == "career-limiting":
                    feedback = "Too risky for current board climate"
                elif criteria_breakdown["sales_team_reaction"] == "revolt":
                    feedback = "Sales team will never support this approach"
                elif criteria_breakdown["roi_projection"] == "uncertain":
                    feedback = "Can't project clear ROI to justify to CFO"
                elif not criteria_breakdown["steal_potential"]:
                    feedback = "Not adaptable to our brand constraints"
                else:
                    feedback = "Doesn't solve our differentiation challenge"
            
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