"""
Phase 2 Test Suite - Test AI Agents Implementation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock

# Import configurations
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.logging.logger_config import configure_logging, get_logger
from src.domain.agents.base_agent import AgentConfig

# Import agents
from src.domain.agents.content_generator import ContentGenerator
from domain.agents.validators.sarah_chen_validator import CustomerValidator
from domain.agents.validators.marcus_williams_validator import BusinessValidator
from domain.agents.validators.jordan_park_validator import SocialMediaValidator
from src.domain.agents.feedback_aggregator import FeedbackAggregator
from src.domain.agents.revision_generator import RevisionGenerator

# Import models
from src.domain.models.post import LinkedInPost, PostStatus, ValidationScore, CulturalReference

# Configure logging
configure_logging(level="DEBUG")
logger = get_logger("test_phase2")

class MockAIClient:
    """Mock AI client for testing"""
    
    def __init__(self, mock_responses=None):
        self.mock_responses = mock_responses or {}
        self.call_count = 0
        
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs):
        """Mock generate method"""
        self.call_count += 1
        
        # Return different responses based on the calling agent
        if "Generate" in prompt and "LinkedIn posts" in prompt:
            return self._get_generation_response()
        elif "Evaluate this LinkedIn post" in prompt:
            if "skeptical 28-year-old" in prompt:
                return self._get_customer_validation_response()
            elif "Marketing Executive" in prompt:
                return self._get_business_validation_response()
            elif "engagement potential" in prompt:
                return self._get_social_validation_response()
        elif "Analyze why this LinkedIn post failed" in prompt:
            return self._get_feedback_response()
        elif "Revise this LinkedIn post" in prompt:
            return self._get_revision_response()
        
        # Default response
        return {
            "content": {"message": "Mock response"},
            "usage": {"total_tokens": 100}
        }
    
    def _get_generation_response(self):
        """Mock content generation response"""
        return {
            "content": {
                "posts": [
                    {
                        "content": "Remember when Jim from The Office pranked Dwight with the vending machine? That's the energy we need on Monday mornings. But unlike Jim's elaborate schemes, staying human in our AI-driven workplace is simple. Stop. Breathe. Apply. Jesse A. Eisenbalm - because your lips deserve better than another automated response. $8.99 for a daily ritual that reminds you: you're not a machine, even if your calendar thinks otherwise.",
                        "hook": "Remember when Jim from The Office pranked Dwight with the vending machine?",
                        "target_audience": "Tech professionals dealing with automation",
                        "cultural_reference": {
                            "category": "tv_show",
                            "reference": "The Office",
                            "context": "Jim's pranks as metaphor for staying human"
                        },
                        "hashtags": ["HumanFirst", "LinkedInLife", "TechWellness", "MondayMotivation", "LipCare"]
                    }
                ]
            },
            "usage": {"total_tokens": 150}
        }
    
    def _get_customer_validation_response(self):
        """Mock customer validation response"""
        return {
            "content": {
                "score": 7.5,
                "approved": True,
                "workplace_relevance": 8,
                "authenticity": 7,
                "value_perception": 7.5,
                "feedback": "Good workplace reference, authentic tone",
                "would_engage": True,
                "first_impression": "Actually made me smile"
            },
            "usage": {"total_tokens": 80}
        }
    
    def _get_business_validation_response(self):
        """Mock business validation response"""
        return {
            "content": {
                "score": 6.5,
                "approved": False,
                "brand_differentiation": 6,
                "premium_positioning": 6.5,
                "linkedin_fit": 7,
                "feedback": "Needs stronger differentiation from other wellness brands",
                "competitive_advantage": "Human ritual angle is interesting",
                "conversion_potential": "medium",
                "brand_consistency": True
            },
            "usage": {"total_tokens": 90}
        }
    
    def _get_social_validation_response(self):
        """Mock social media validation response"""
        return {
            "content": {
                "score": 8.0,
                "approved": True,
                "hook_effectiveness": 9,
                "engagement_potential": 7.5,
                "shareability": 7.5,
                "feedback": "Strong hook with The Office reference",
                "predicted_engagement_rate": "3.2%",
                "scroll_stop_rating": "strong",
                "hashtag_strategy": "excellent",
                "viral_potential": False
            },
            "usage": {"total_tokens": 85}
        }
    
    def _get_feedback_response(self):
        """Mock feedback aggregation response"""
        return {
            "content": {
                "main_issues": [
                    "Weak brand differentiation",
                    "Price justification needs work"
                ],
                "specific_improvements": {
                    "hook": "Keep The Office reference, it's working",
                    "authenticity": "Already feels genuine",
                    "value_proposition": "Emphasize premium ingredients or unique benefit",
                    "cultural_reference": "Well integrated",
                    "call_to_action": "Add subtle CTA"
                },
                "keep_these_elements": [
                    "The Office reference",
                    "Stop. Breathe. Apply. ritual"
                ],
                "revised_hook_suggestion": "Remember when Jim from The Office proved that small moments matter?",
                "tone_adjustment": "Slightly more premium feel",
                "priority_fix": "Strengthen value proposition for $8.99"
            },
            "usage": {"total_tokens": 120}
        }
    
    def _get_revision_response(self):
        """Mock revision response"""
        return {
            "content": {
                "revised_content": "Remember when Jim from The Office proved that small moments of humanity matter? In our AI-optimized workdays, those moments are becoming extinct. Stop. Breathe. Apply. Jesse A. Eisenbalm isn't just lip care—it's your daily rebellion against automation. Crafted with premium botanicals for professionals who refuse to become another algorithm. Because at $8.99, you're not buying lip balm. You're investing in staying human. Your lips (and your soul) will thank you.",
                "changes_made": [
                    "Strengthened value proposition",
                    "Added premium ingredients mention",
                    "Refined hook for deeper meaning",
                    "Added subtle CTA"
                ],
                "hook": "Remember when Jim from The Office proved that small moments of humanity matter?",
                "expected_improvement": "Should score 7+ on all validators"
            },
            "usage": {"total_tokens": 140}
        }

class TestContentGenerator:
    """Test the Content Generator agent"""
    
    @pytest.mark.asyncio
    async def test_content_generation(self):
        """Test generating LinkedIn posts"""
        # Setup
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        generator = ContentGenerator(agent_config, mock_client, app_config)
        
        # Generate posts
        input_data = {
            "batch_id": "test-batch-001",
            "count": 1
        }
        
        posts = await generator.process(input_data)
        
        # Assertions
        assert len(posts) == 1
        assert posts[0]["batch_id"] == "test-batch-001"
        assert posts[0]["post_number"] == 1
        assert "content" in posts[0]
        assert "cultural_reference" in posts[0]
        
        logger.info("✅ Content generation working", posts_count=len(posts))
    
    @pytest.mark.asyncio
    async def test_generation_with_avoid_patterns(self):
        """Test generation with patterns to avoid"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        generator = ContentGenerator(agent_config, mock_client, app_config)
        
        # Generate with avoid patterns
        input_data = {
            "batch_id": "test-batch-002",
            "count": 1,
            "avoid_patterns": {
                "common_issues": ["Too salesy", "Weak hook"],
                "cultural_references_failed": ["Friends", "Seinfeld"]
            }
        }
        
        posts = await generator.process(input_data)
        
        assert len(posts) == 1
        assert mock_client.call_count == 1
        logger.info("✅ Generation with avoid patterns working")

class TestValidators:
    """Test all three validator agents"""
    
    @pytest.mark.asyncio
    async def test_customer_validator(self):
        """Test customer validator"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        validator = CustomerValidator(agent_config, mock_client, app_config)
        
        # Create test post with enough content (>50 chars)
        post = LinkedInPost(
            batch_id="test-batch",
            post_number=1,
            content="Test post content about Jesse A. Eisenbalm lip balm that helps professionals stay human in an AI-driven world. This is a longer test content to meet the minimum character requirement.",
            target_audience="Tech professionals"
        )
        
        # Validate
        score = await validator.process(post)
        
        # Assertions
        assert isinstance(score, ValidationScore)
        assert score.agent_name == "CustomerValidator"
        assert score.score == 7.5
        assert score.approved == True
        assert "workplace_relevance" in score.criteria_breakdown
        
        logger.info("✅ Customer validator working", score=score.score)
    
    @pytest.mark.asyncio
    async def test_business_validator(self):
        """Test business validator"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        validator = BusinessValidator(agent_config, mock_client, app_config)
        
        # Create test post with enough content
        post = LinkedInPost(
            batch_id="test-batch",
            post_number=1,
            content="Marketing professionals need Jesse A. Eisenbalm lip balm for staying authentic in their daily grind. Stop. Breathe. Apply. A premium ritual for $8.99 that keeps you human.",
            target_audience="Marketing professionals"
        )
        
        # Validate
        score = await validator.process(post)
        
        # Assertions
        assert isinstance(score, ValidationScore)
        assert score.agent_name == "BusinessValidator"
        assert score.score == 6.5
        assert score.approved == False
        assert score.feedback != ""
        
        logger.info("✅ Business validator working", score=score.score)
    
    @pytest.mark.asyncio
    async def test_social_validator(self):
        """Test social media validator"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        validator = SocialMediaValidator(agent_config, mock_client, app_config)
        
        # Create test post with enough content
        post = LinkedInPost(
            batch_id="test-batch",
            post_number=1,
            content="LinkedIn professionals are drowning in AI automation. Jesse A. Eisenbalm offers a simple human ritual. Stop. Breathe. Apply. Because your lips deserve better than machine efficiency.",
            target_audience="LinkedIn professionals",
            hashtags=["Test", "LinkedIn"]
        )
        
        # Validate
        score = await validator.process(post)
        
        # Assertions
        assert isinstance(score, ValidationScore)
        assert score.agent_name == "SocialMediaValidator"
        assert score.score == 8.0
        assert score.approved == True
        assert "engagement_potential" in score.criteria_breakdown
        
        logger.info("✅ Social validator working", score=score.score)

class TestFeedbackAggregator:
    """Test feedback aggregation"""
    
    @pytest.mark.asyncio
    async def test_feedback_aggregation(self):
        """Test aggregating feedback from failed validations"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        aggregator = FeedbackAggregator(agent_config, mock_client, app_config)
        
        # Create post with validation scores
        post = LinkedInPost(
            batch_id="test-batch",
            post_number=1,
            content="This post needs improvement to better showcase Jesse A. Eisenbalm as the premium lip balm for professionals who value staying human in an AI world.",
            target_audience="Professionals"
        )
        
        # Add validation scores
        post.add_validation(ValidationScore(
            agent_name="CustomerValidator",
            score=6.0,
            approved=False,
            feedback="Not authentic enough"
        ))
        post.add_validation(ValidationScore(
            agent_name="BusinessValidator",
            score=5.5,
            approved=False,
            feedback="Weak brand differentiation"
        ))
        
        # Aggregate feedback
        feedback = await aggregator.process(post)
        
        # Assertions
        assert isinstance(feedback, dict)
        assert "main_issues" in feedback
        assert "specific_improvements" in feedback
        assert "priority_fix" in feedback
        assert len(feedback["main_issues"]) > 0
        
        logger.info("✅ Feedback aggregation working", issues=feedback["main_issues"])

class TestRevisionGenerator:
    """Test post revision generation"""
    
    @pytest.mark.asyncio
    async def test_revision_generation(self):
        """Test generating revised post based on feedback"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClient()
        
        generator = RevisionGenerator(agent_config, mock_client, app_config)
        
        # Create post and feedback
        post = LinkedInPost(
            batch_id="test-batch",
            post_number=1,
            content="Original post content that needs revision about Jesse A. Eisenbalm lip balm for professionals who want to stay human in the age of AI automation.",
            target_audience="Tech professionals"
        )
        
        feedback = {
            "main_issues": ["Weak hook", "No clear value prop"],
            "specific_improvements": {
                "hook": "Make it more engaging",
                "value_proposition": "Emphasize the $8.99 value"
            },
            "priority_fix": "Strengthen the hook"
        }
        
        # Generate revision
        revised_post = await generator.process((post, feedback))
        
        # Assertions
        assert isinstance(revised_post, LinkedInPost)
        assert revised_post.revision_count == 1
        assert revised_post.content != post.original_content
        assert revised_post.status == PostStatus.REVISED
        
        logger.info("✅ Revision generation working", revision_count=revised_post.revision_count)

def run_tests():
    """Run all Phase 2 tests"""
    print("\n" + "="*60)
    print("🧪 PHASE 2 AI AGENTS TESTS")
    print("="*60 + "\n")
    
    # Test Content Generator
    print("Testing Content Generator...")
    gen_tests = TestContentGenerator()
    asyncio.run(gen_tests.test_content_generation())
    asyncio.run(gen_tests.test_generation_with_avoid_patterns())
    print("✅ Content Generator tests passed!\n")
    
    # Test Validators
    print("Testing Validators...")
    val_tests = TestValidators()
    asyncio.run(val_tests.test_customer_validator())
    asyncio.run(val_tests.test_business_validator())
    asyncio.run(val_tests.test_social_validator())
    print("✅ All Validator tests passed!\n")
    
    # Test Feedback Aggregator
    print("Testing Feedback Aggregator...")
    feedback_tests = TestFeedbackAggregator()
    asyncio.run(feedback_tests.test_feedback_aggregation())
    print("✅ Feedback Aggregator tests passed!\n")
    
    # Test Revision Generator
    print("Testing Revision Generator...")
    revision_tests = TestRevisionGenerator()
    asyncio.run(revision_tests.test_revision_generation())
    print("✅ Revision Generator tests passed!\n")
    
    print("="*60)
    print("🎉 PHASE 2 COMPLETE - ALL AGENT TESTS PASSED!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Add your OpenAI API key to test with real API")
    print("2. Move on to Phase 3: Orchestration & Workflow")

if __name__ == "__main__":
    run_tests()
