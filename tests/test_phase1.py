"""
Phase 1 Test Suite - Verify core architecture is working
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pytest
from datetime import datetime
from pathlib import Path

# Test imports
from src.domain.models.post import LinkedInPost, PostStatus, ValidationScore, CulturalReference
from src.domain.models.batch import Batch, BatchMetrics
from src.domain.agents.base_agent import BaseAgent, AgentConfig
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.logging.logger_config import configure_logging, get_logger

# Configure logging for tests
configure_logging(level="DEBUG")
logger = get_logger("test_phase1")

class TestDomainModels:
    """Test domain models are working correctly"""
    
    def test_linkedin_post_creation(self):
        """Test creating a LinkedIn post"""
        post = LinkedInPost(
            batch_id="test-batch-001",
            post_number=1,
            content="This is a test post about Jesse A. Eisenbalm lip balm for professionals.",
            target_audience="Tech professionals",
            cultural_reference=CulturalReference(
                category="tv_show",
                reference="The Office",
                context="Jim's pranks keep us human"
            )
        )
        
        assert post.id is not None
        assert post.status == PostStatus.GENERATED
        assert post.revision_count == 0
        assert post.average_score == 0.0
        logger.info("✅ LinkedIn post model working", post_id=post.id)
    
    def test_validation_score(self):
        """Test validation score logic"""
        # Score below 7 should not approve
        score1 = ValidationScore(
            agent_name="CustomerValidator",
            score=6.5,
            approved=True,  # Will be corrected by validator
            feedback="Needs more authenticity"
        )
        assert score1.approved == False
        
        # Score 7+ should approve
        score2 = ValidationScore(
            agent_name="BusinessValidator",
            score=7.5,
            approved=False,  # Will be corrected
            feedback="Good brand positioning"
        )
        assert score2.approved == True
        logger.info("✅ Validation score logic working")
    
    def test_post_approval_logic(self):
        """Test post approval counting"""
        post = LinkedInPost(
            batch_id="test-batch-002",
            post_number=1,
            content="Test content for approval logic testing in LinkedIn validation system",
            target_audience="LinkedIn professionals"  # Added required field
        )
        
        # Add validation scores
        post.add_validation(ValidationScore(
            agent_name="CustomerValidator",
            score=8.0,
            approved=True
        ))
        post.add_validation(ValidationScore(
            agent_name="BusinessValidator",
            score=7.5,
            approved=True
        ))
        post.add_validation(ValidationScore(
            agent_name="SocialValidator",
            score=6.0,
            approved=False
        ))
        
        assert post.approval_count == 2
        assert post.is_approved(min_approvals=2) == True
        assert round(post.average_score, 2) == 7.17
        logger.info("✅ Post approval logic working")
    
    def test_post_revision(self):
        """Test post revision functionality"""
        post = LinkedInPost(
            batch_id="test-batch-003",
            post_number=1,
            content="Original content about Jesse A. Eisenbalm lip balm for LinkedIn professionals",
            target_audience="Business professionals"  # Added required field
        )
        
        # Create revision
        assert post.can_revise() == True
        post.create_revision("Revised content version 1 with improved engagement hook")
        
        assert post.content == "Revised content version 1 with improved engagement hook"
        assert post.original_content == "Original content about Jesse A. Eisenbalm lip balm for LinkedIn professionals"
        assert post.revision_count == 1
        assert len(post.revision_history) == 1
        assert post.status == PostStatus.REVISED
        
        # Test max revision limit
        post.create_revision("Revised content version 2 with even better positioning")
        assert post.revision_count == 2
        assert post.can_revise() == False
        logger.info("✅ Post revision logic working")

class TestBatchModel:
    """Test batch model functionality"""
    
    def test_batch_creation(self):
        """Test batch creation and management"""
        batch = Batch()
        
        # Add posts
        for i in range(3):
            post = LinkedInPost(
                batch_id=batch.id,
                post_number=i+1,
                content=f"Test post {i+1} about Jesse A. Eisenbalm premium lip balm",
                target_audience="Tech professionals"  # Added required field
            )
            batch.add_post(post)
        
        assert len(batch.posts) == 3
        assert batch.status == "pending"
        logger.info("✅ Batch creation working", batch_id=batch.id)
    
    def test_batch_metrics(self):
        """Test batch metrics calculation"""
        batch = Batch()
        
        # Create posts with different statuses
        approved_post = LinkedInPost(
            batch_id=batch.id,
            post_number=1,
            content="Approved post about Jesse A. Eisenbalm keeping professionals human",
            target_audience="LinkedIn professionals",  # Added required field
            status=PostStatus.APPROVED
        )
        approved_post.add_validation(ValidationScore(
            agent_name="Test",
            score=8.0,
            approved=True
        ))
        
        rejected_post = LinkedInPost(
            batch_id=batch.id,
            post_number=2,
            content="Rejected post that didn't meet our brand standards for LinkedIn",
            target_audience="LinkedIn professionals",  # Added required field
            status=PostStatus.REJECTED
        )
        
        batch.posts = [approved_post, rejected_post]
        batch.complete()
        
        assert batch.metrics.total_posts == 2
        assert batch.metrics.approved_posts == 1
        assert batch.metrics.rejected_posts == 1
        assert batch.metrics.approval_rate == 0.5
        assert batch.status == "completed"
        logger.info("✅ Batch metrics calculation working")

class TestConfiguration:
    """Test configuration management"""
    
    def test_config_loading(self):
        """Test loading configuration"""
        # Check if config file exists, if not create it
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            from setup_project import create_default_config
            create_default_config()
        
        config = AppConfig.from_yaml()
        
        assert config.batch.posts_per_batch == 5
        assert config.batch.max_revisions == 2
        assert config.brand.product_name == "Jesse A. Eisenbalm"
        assert config.brand.price == "$8.99"
        assert len(config.cultural_references.tv_shows) > 0
        logger.info("✅ Configuration loading working")
    
    def test_agent_config(self):
        """Test agent configuration"""
        config = AgentConfig(
            model="gpt-4o-mini",
            temperature=0.8,
            max_tokens=500
        )
        
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.8
        assert config.retry_attempts == 3  # Default value
        logger.info("✅ Agent configuration working")

class TestBaseAgent:
    """Test base agent functionality"""
    
    @pytest.mark.asyncio
    async def test_agent_stats(self):
        """Test agent statistics tracking"""
        
        # Mock AI client for testing
        class MockAIClient:
            async def generate(self, **kwargs):
                return {
                    "content": "Test response",
                    "usage": {"total_tokens": 100}
                }
        
        # Create test agent
        class TestAgent(BaseAgent):
            async def process(self, input_data):
                response = await self._call_ai("Test prompt")
                return response
        
        agent = TestAgent(
            name="TestAgent",
            config=AgentConfig(),
            ai_client=MockAIClient()
        )
        
        # Process something
        await agent.process("test input")
        
        stats = agent.get_stats()
        assert stats["name"] == "TestAgent"
        assert stats["call_count"] == 1
        assert stats["total_tokens"] == 100
        assert stats["estimated_cost"] > 0
        logger.info("✅ Agent statistics tracking working", stats=stats)

def run_tests():
    """Run all Phase 1 tests"""
    print("\n" + "="*60)
    print("🧪 PHASE 1 CORE ARCHITECTURE TESTS")
    print("="*60 + "\n")
    
    # Test domain models
    print("Testing Domain Models...")
    model_tests = TestDomainModels()
    model_tests.test_linkedin_post_creation()
    model_tests.test_validation_score()
    model_tests.test_post_approval_logic()
    model_tests.test_post_revision()
    print("✅ All domain model tests passed!\n")
    
    # Test batch functionality
    print("Testing Batch Functionality...")
    batch_tests = TestBatchModel()
    batch_tests.test_batch_creation()
    batch_tests.test_batch_metrics()
    print("✅ All batch tests passed!\n")
    
    # Test configuration
    print("Testing Configuration...")
    config_tests = TestConfiguration()
    config_tests.test_config_loading()
    config_tests.test_agent_config()
    print("✅ All configuration tests passed!\n")
    
    # Test async agent functionality
    print("Testing Base Agent...")
    agent_tests = TestBaseAgent()
    asyncio.run(agent_tests.test_agent_stats())
    print("✅ All agent tests passed!\n")
    
    print("="*60)
    print("🎉 PHASE 1 COMPLETE - ALL TESTS PASSED!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Review the generated project structure")
    print("2. Add your OpenAI API key to .env file")
    print("3. Move on to Phase 2: Agent Implementation")

if __name__ == "__main__":
    run_tests()
