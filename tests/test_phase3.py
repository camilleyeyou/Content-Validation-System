"""
Phase 3 Test Suite - Test Orchestration and Workflow
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Import configurations
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.logging.logger_config import configure_logging, get_logger
from src.domain.agents.base_agent import AgentConfig

# Import orchestration
from src.domain.services.validation_orchestrator import ValidationOrchestrator
from src.domain.services.workflow_controller import WorkflowController

# Import agents
from src.domain.agents.content_generator import ContentGenerator
from domain.agents.validators.sarah_chen_validator import CustomerValidator
from domain.agents.validators.marcus_williams_validator import BusinessValidator
from domain.agents.validators.jordan_park_validator import SocialMediaValidator
from src.domain.agents.feedback_aggregator import FeedbackAggregator
from src.domain.agents.revision_generator import RevisionGenerator

# Import models
from src.domain.models.post import LinkedInPost, PostStatus, ValidationScore
from src.domain.models.batch import Batch

# Configure logging
configure_logging(level="DEBUG")
logger = get_logger("test_phase3")

class MockAIClientOrchestration:
    """Mock AI client for orchestration testing"""
    
    def __init__(self):
        self.call_count = 0
        self.generation_count = 0
        self.validation_count = 0
        
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs):
        """Mock generate method with varied responses"""
        self.call_count += 1
        
        # Content generation
        if "Generate" in prompt and "LinkedIn posts" in prompt:
            self.generation_count += 1
            return self._get_generation_response()
        
        # Validation responses with varied scores
        elif "Evaluate this LinkedIn post" in prompt:
            self.validation_count += 1
            if "skeptical 28-year-old" in prompt:
                # Customer validator - sometimes approve, sometimes not
                return self._get_customer_validation_response(self.validation_count)
            elif "Marketing Executive" in prompt:
                # Business validator - harder to please
                return self._get_business_validation_response(self.validation_count)
            elif "engagement potential" in prompt:
                # Social validator - generally positive
                return self._get_social_validation_response(self.validation_count)
        
        # Feedback aggregation
        elif "Analyze why this LinkedIn post failed" in prompt:
            return self._get_feedback_response()
        
        # Revision generation
        elif "Revise this LinkedIn post" in prompt:
            return self._get_revision_response()
        
        return {"content": {"message": "Mock response"}, "usage": {"total_tokens": 100}}
    
    def _get_generation_response(self):
        """Generate multiple posts with varying quality"""
        posts = []
        
        # Mix of good and bad posts
        for i in range(5):
            if i % 2 == 0:  # Even posts are good
                posts.append({
                    "content": f"Post {i+1}: Remember when Jim from The Office proved that humanity matters? In our AI-driven workplace, Jesse A. Eisenbalm ($8.99) is your daily reminder to Stop. Breathe. Apply. Because staying human isn't automated. Your lips deserve this premium ritual that keeps you grounded when everything else is algorithms.",
                    "hook": f"Remember when Jim from The Office proved that humanity matters?",
                    "target_audience": "Tech professionals",
                    "cultural_reference": {
                        "category": "tv_show",
                        "reference": "The Office",
                        "context": "Jim as humanity metaphor"
                    },
                    "hashtags": ["HumanFirst", "LinkedInLife", "LipCare"]
                })
            else:  # Odd posts need work
                posts.append({
                    "content": f"Post {i+1}: Buy Jesse A. Eisenbalm lip balm now! It's the best lip balm ever made for professionals. Only $8.99 for this amazing product. You need this in your life. Stop what you're doing and buy it. Limited time offer. Act now!",
                    "hook": "Buy Jesse A. Eisenbalm lip balm now!",
                    "target_audience": "Everyone",
                    "cultural_reference": None,
                    "hashtags": ["BuyNow", "Sale", "LimitedOffer"]
                })
        
        return {
            "content": {"posts": posts},
            "usage": {"total_tokens": 200}
        }
    
    def _get_customer_validation_response(self, count):
        """Customer validation with varied scores"""
        if count % 3 == 0:  # Every third validation is positive
            return {
                "content": {
                    "score": 7.5,
                    "approved": True,
                    "workplace_relevance": 8,
                    "authenticity": 7,
                    "value_perception": 7.5,
                    "feedback": "Good authentic tone"
                },
                "usage": {"total_tokens": 80}
            }
        else:
            return {
                "content": {
                    "score": 5.5,
                    "approved": False,
                    "workplace_relevance": 5,
                    "authenticity": 4,
                    "value_perception": 6,
                    "feedback": "Too salesy, not authentic"
                },
                "usage": {"total_tokens": 80}
            }
    
    def _get_business_validation_response(self, count):
        """Business validation - harder to please"""
        if count % 4 == 0:  # Every fourth validation passes
            return {
                "content": {
                    "score": 7.2,
                    "approved": True,
                    "brand_differentiation": 7,
                    "premium_positioning": 7.5,
                    "linkedin_fit": 7,
                    "feedback": "Good brand positioning"
                },
                "usage": {"total_tokens": 90}
            }
        else:
            return {
                "content": {
                    "score": 5.8,
                    "approved": False,
                    "brand_differentiation": 5,
                    "premium_positioning": 6,
                    "linkedin_fit": 6,
                    "feedback": "Weak differentiation"
                },
                "usage": {"total_tokens": 90}
            }
    
    def _get_social_validation_response(self, count):
        """Social validation - generally positive"""
        if count % 2 == 0:  # Every other validation passes
            return {
                "content": {
                    "score": 8.0,
                    "approved": True,
                    "hook_effectiveness": 8.5,
                    "engagement_potential": 7.5,
                    "shareability": 8,
                    "feedback": "Strong hook"
                },
                "usage": {"total_tokens": 85}
            }
        else:
            return {
                "content": {
                    "score": 6.2,
                    "approved": False,
                    "hook_effectiveness": 5,
                    "engagement_potential": 6,
                    "shareability": 6.5,
                    "feedback": "Weak hook, won't stop scroll"
                },
                "usage": {"total_tokens": 85}
            }
    
    def _get_feedback_response(self):
        """Feedback aggregation response"""
        return {
            "content": {
                "main_issues": ["Too promotional", "Weak hook"],
                "specific_improvements": {
                    "hook": "Make it more engaging",
                    "authenticity": "Less salesy tone",  
                    "value_proposition": "Better justify price"
                },
                "keep_these_elements": ["Price mention"],
                "priority_fix": "Reduce promotional tone"
            },
            "usage": {"total_tokens": 120}
        }
    
    def _get_revision_response(self):
        """Revision that should pass validation"""
        return {
            "content": {
                "revised_content": "That moment when you realize you've been on back-to-back Zooms for 4 hours... Stop. Breathe. Apply. Jesse A. Eisenbalm isn't just lip care—it's your $8.99 investment in staying human. Premium botanicals meet purposeful pause. Because in a world of endless automation, your lips (and sanity) deserve better.",
                "changes_made": ["Improved hook", "Added authenticity", "Better value prop"],
                "hook": "That moment when you realize you've been on back-to-back Zooms for 4 hours...",
                "expected_improvement": "Should score 7+ on all validators"
            },
            "usage": {"total_tokens": 140}
        }

class TestValidationOrchestrator:
    """Test the validation orchestrator"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create agents
        generator = ContentGenerator(agent_config, mock_client, app_config)
        validators = [
            CustomerValidator(agent_config, mock_client, app_config),
            BusinessValidator(agent_config, mock_client, app_config),
            SocialMediaValidator(agent_config, mock_client, app_config)
        ]
        feedback = FeedbackAggregator(agent_config, mock_client, app_config)
        revision = RevisionGenerator(agent_config, mock_client, app_config)
        
        # Create orchestrator
        orchestrator = ValidationOrchestrator(
            generator, validators, feedback, revision, app_config
        )
        
        assert orchestrator is not None
        assert len(orchestrator.validators) == 3
        assert orchestrator.config == app_config
        logger.info("✅ Orchestrator initialization working")
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test processing a batch of posts"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create orchestrator with all agents
        generator = ContentGenerator(agent_config, mock_client, app_config)
        validators = [
            CustomerValidator(agent_config, mock_client, app_config),
            BusinessValidator(agent_config, mock_client, app_config),
            SocialMediaValidator(agent_config, mock_client, app_config)
        ]
        feedback = FeedbackAggregator(agent_config, mock_client, app_config)
        revision = RevisionGenerator(agent_config, mock_client, app_config)
        
        orchestrator = ValidationOrchestrator(
            generator, validators, feedback, revision, app_config
        )
        
        # Process a batch
        batch = await orchestrator.process_batch(batch_size=2)
        
        # Assertions
        assert isinstance(batch, Batch)
        assert batch.status == "completed"
        assert len(batch.posts) >= 2
        assert batch.metrics.total_posts >= 2
        
        # Check that some posts were processed
        approved_posts = batch.get_approved_posts()
        rejected_posts = batch.get_rejected_posts()
        
        assert len(approved_posts) + len(rejected_posts) > 0
        
        logger.info("✅ Batch processing working",
                   total_posts=batch.metrics.total_posts,
                   approved=len(approved_posts),
                   rejected=len(rejected_posts))
    
    @pytest.mark.asyncio
    async def test_parallel_validation(self):
        """Test parallel validation of posts"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create validators
        validators = [
            CustomerValidator(agent_config, mock_client, app_config),
            BusinessValidator(agent_config, mock_client, app_config),
            SocialMediaValidator(agent_config, mock_client, app_config)
        ]
        
        # Create orchestrator
        orchestrator = ValidationOrchestrator(
            ContentGenerator(agent_config, mock_client, app_config),
            validators,
            FeedbackAggregator(agent_config, mock_client, app_config),
            RevisionGenerator(agent_config, mock_client, app_config),
            app_config
        )
        
        # Create test post
        post = LinkedInPost(
            batch_id="test-batch",
            post_number=1,
            content="Test post content about Jesse A. Eisenbalm lip balm that helps professionals stay human in an AI world. Stop. Breathe. Apply. Your daily ritual for just $8.99.",
            target_audience="Tech professionals"
        )
        
        # Validate in parallel
        scores = await orchestrator._validate_post_parallel(post)
        
        assert len(scores) == 3  # Three validators
        assert all(isinstance(s, ValidationScore) for s in scores)
        assert scores[0].agent_name == "CustomerValidator"
        assert scores[1].agent_name == "BusinessValidator"
        assert scores[2].agent_name == "SocialMediaValidator"
        
        logger.info("✅ Parallel validation working", validator_count=len(scores))
    
    @pytest.mark.asyncio
    async def test_revision_flow(self):
        """Test that posts go through revision when needed"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create orchestrator
        orchestrator = ValidationOrchestrator(
            ContentGenerator(agent_config, mock_client, app_config),
            [
                CustomerValidator(agent_config, mock_client, app_config),
                BusinessValidator(agent_config, mock_client, app_config),
                SocialMediaValidator(agent_config, mock_client, app_config)
            ],
            FeedbackAggregator(agent_config, mock_client, app_config),
            RevisionGenerator(agent_config, mock_client, app_config),
            app_config
        )
        
        # Process batch - should trigger some revisions
        batch = await orchestrator.process_batch(batch_size=3)
        
        # Check for revisions
        revised_posts = [p for p in batch.posts if p.revision_count > 0]
        
        assert len(revised_posts) > 0
        logger.info("✅ Revision flow working", 
                   revised_count=len(revised_posts),
                   total_posts=len(batch.posts))

class TestWorkflowController:
    """Test the workflow controller"""
    
    @pytest.mark.asyncio
    async def test_workflow_controller_initialization(self):
        """Test workflow controller setup"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create orchestrator
        orchestrator = ValidationOrchestrator(
            ContentGenerator(agent_config, mock_client, app_config),
            [
                CustomerValidator(agent_config, mock_client, app_config),
                BusinessValidator(agent_config, mock_client, app_config),
                SocialMediaValidator(agent_config, mock_client, app_config)
            ],
            FeedbackAggregator(agent_config, mock_client, app_config),
            RevisionGenerator(agent_config, mock_client, app_config),
            app_config
        )
        
        # Create workflow controller
        controller = WorkflowController(orchestrator, config=app_config)
        
        assert controller is not None
        assert controller.orchestrator == orchestrator
        assert controller.config == app_config
        assert len(controller.processed_batches) == 0
        
        logger.info("✅ Workflow controller initialization working")
    
    @pytest.mark.asyncio
    async def test_run_single_batch(self):
        """Test running a single batch through workflow"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create full system
        orchestrator = ValidationOrchestrator(
            ContentGenerator(agent_config, mock_client, app_config),
            [
                CustomerValidator(agent_config, mock_client, app_config),
                BusinessValidator(agent_config, mock_client, app_config),
                SocialMediaValidator(agent_config, mock_client, app_config)
            ],
            FeedbackAggregator(agent_config, mock_client, app_config),
            RevisionGenerator(agent_config, mock_client, app_config),
            app_config
        )
        
        controller = WorkflowController(orchestrator, config=app_config)
        
        # Run single batch
        batch = await controller.run_single_batch(batch_size=2)
        
        assert isinstance(batch, Batch)
        assert batch.status == "completed"
        assert len(controller.processed_batches) == 1
        assert controller.processed_batches[0] == batch
        
        logger.info("✅ Single batch workflow working",
                   batch_id=batch.id,
                   approval_rate=batch.metrics.approval_rate)
    
    @pytest.mark.asyncio
    async def test_run_multiple_batches(self):
        """Test running multiple batches"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create system
        orchestrator = ValidationOrchestrator(
            ContentGenerator(agent_config, mock_client, app_config),
            [
                CustomerValidator(agent_config, mock_client, app_config),
                BusinessValidator(agent_config, mock_client, app_config),
                SocialMediaValidator(agent_config, mock_client, app_config)
            ],
            FeedbackAggregator(agent_config, mock_client, app_config),
            RevisionGenerator(agent_config, mock_client, app_config),
            app_config
        )
        
        controller = WorkflowController(orchestrator, config=app_config)
        
        # Run multiple batches
        batches = await controller.run_multiple_batches(
            num_batches=2,
            batch_size=2,
            delay_seconds=0
        )
        
        assert len(batches) == 2
        assert len(controller.processed_batches) == 2
        assert all(b.status == "completed" for b in batches)
        
        # Check performance metrics
        metrics = controller.get_performance_metrics()
        assert metrics["batches_processed"] == 2
        assert "summary" in metrics
        
        logger.info("✅ Multiple batch workflow working",
                   num_batches=len(batches),
                   total_approved=metrics["summary"]["total_approved"])
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self):
        """Test performance metrics tracking"""
        app_config = AppConfig.from_yaml()
        agent_config = AgentConfig()
        mock_client = MockAIClientOrchestration()
        
        # Create system
        orchestrator = ValidationOrchestrator(
            ContentGenerator(agent_config, mock_client, app_config),
            [
                CustomerValidator(agent_config, mock_client, app_config),
                BusinessValidator(agent_config, mock_client, app_config),
                SocialMediaValidator(agent_config, mock_client, app_config)
            ],
            FeedbackAggregator(agent_config, mock_client, app_config),
            RevisionGenerator(agent_config, mock_client, app_config),
            app_config
        )
        
        controller = WorkflowController(orchestrator, config=app_config)
        
        # Process a batch
        await controller.run_single_batch(batch_size=3)
        
        # Get metrics
        metrics = controller.get_performance_metrics()
        orchestrator_stats = orchestrator.get_statistics()
        
        assert metrics["batches_processed"] == 1
        assert orchestrator_stats["total_posts_processed"] >= 3
        assert "overall_approval_rate" in orchestrator_stats
        
        logger.info("✅ Performance tracking working",
                   **orchestrator_stats)

def run_tests():
    """Run all Phase 3 tests"""
    print("\n" + "="*60)
    print("🧪 PHASE 3 ORCHESTRATION TESTS")
    print("="*60 + "\n")
    
    # Test Orchestrator
    print("Testing Validation Orchestrator...")
    orch_tests = TestValidationOrchestrator()
    asyncio.run(orch_tests.test_orchestrator_initialization())
    asyncio.run(orch_tests.test_batch_processing())
    asyncio.run(orch_tests.test_parallel_validation())
    asyncio.run(orch_tests.test_revision_flow())
    print("✅ Orchestrator tests passed!\n")
    
    # Test Workflow Controller
    print("Testing Workflow Controller...")
    workflow_tests = TestWorkflowController()
    asyncio.run(workflow_tests.test_workflow_controller_initialization())
    asyncio.run(workflow_tests.test_run_single_batch())
    asyncio.run(workflow_tests.test_run_multiple_batches())
    asyncio.run(workflow_tests.test_performance_tracking())
    print("✅ Workflow Controller tests passed!\n")
    
    print("="*60)
    print("🎉 PHASE 3 COMPLETE - ORCHESTRATION TESTS PASSED!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Test with real OpenAI API for full integration")
    print("2. Move on to Phase 4: Data Export & Analytics")
    print("3. Fine-tune approval thresholds and parameters")

if __name__ == "__main__":
    run_tests()
