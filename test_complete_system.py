
"""
Complete System Test - Run the entire LinkedIn content validation pipeline
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Load environment variables
load_dotenv()

from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.logging.logger_config import configure_logging, get_logger
from src.infrastructure.persistence.export_manager import ExportManager
from src.infrastructure.analytics.performance_analyzer import PerformanceAnalyzer

from src.domain.agents.base_agent import AgentConfig
from src.domain.agents.advanced_content_generator import AdvancedContentGenerator
from src.domain.agents.validators.sarah_chen_validator import SarahChenValidator
from src.domain.agents.validators.marcus_williams_validator import MarcusWilliamsValidator
from src.domain.agents.validators.jordan_park_validator import JordanParkValidator
from src.domain.agents.feedback_aggregator import FeedbackAggregator
from src.domain.agents.revision_generator import RevisionGenerator

from src.domain.services.validation_orchestrator import ValidationOrchestrator
from src.domain.services.workflow_controller import WorkflowController

# Configure logging
configure_logging(level="INFO")
logger = get_logger("system_test")

# Check if we should use real API
USE_REAL_API = os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your-openai-api-key-here"

class MockAIClient:
    """Mock AI client for testing without API key"""
    
    def __init__(self):
        self.call_count = 0
        
    async def generate(self, prompt: str, system_prompt: str = None, **kwargs):
        """Mock responses for testing"""
        self.call_count += 1
        
        if "Generate" in prompt and "LinkedIn posts" in prompt:
            return self._mock_generation()
        elif "skeptical 28-year-old" in prompt:
            return self._mock_customer_validation()
        elif "Marketing Executive" in prompt:
            return self._mock_business_validation()
        elif "engagement potential" in prompt:
            return self._mock_social_validation()
        elif "Analyze why this LinkedIn post failed" in prompt:
            return self._mock_feedback()
        elif "Revise this LinkedIn post" in prompt:
            return self._mock_revision()
        
        return {"content": "Mock response", "usage": {"total_tokens": 100}}
    
    def _mock_generation(self):
        return {
            "content": {
                "posts": [
                    {
                        "content": "Remember when Jim from The Office taught us that small moments matter? In our AI-obsessed workplace, Jesse A. Eisenbalm ($8.99) is that small moment. Stop. Breathe. Apply. A premium ritual that keeps you grounded when every meeting is 'pivotal' and every email is 'urgent'. Because your humanity isn't a KPI, but your lips deserve premium care.",
                        "hook": "Remember when Jim from The Office taught us that small moments matter?",
                        "target_audience": "Tech professionals",
                        "cultural_reference": {
                            "category": "tv_show",
                            "reference": "The Office",
                            "context": "Jim's humanity in corporate chaos"
                        },
                        "hashtags": ["HumanFirst", "LinkedInLife", "PremiumSelfCare", "OfficeLife"]
                    },
                    {
                        "content": "That Zoom fatigue hitting different at 3pm? Your fifth back-to-back video call doesn't care about your chapped lips, but you should. Jesse A. Eisenbalm - because for $8.99, you can own one thing that AI can't optimize: your moment to Stop. Breathe. Apply. Stay human, stay smooth.",
                        "hook": "That Zoom fatigue hitting different at 3pm?",
                        "target_audience": "Remote workers",
                        "cultural_reference": {
                            "category": "workplace",
                            "reference": "Zoom fatigue",
                            "context": "Modern remote work struggle"
                        },
                        "hashtags": ["RemoteWork", "ZoomFatigue", "SelfCare", "StayHuman"]
                    },
                    {
                        "content": "Performance review season got you questioning your humanity? While AI writes your self-assessment, take a moment for an actual self-assessment. Stop. Breathe. Apply. Jesse A. Eisenbalm - $8.99 for the only metric that matters: staying human when everything else is automated.",
                        "hook": "Performance review season got you questioning your humanity?",
                        "target_audience": "Corporate professionals",
                        "cultural_reference": {
                            "category": "seasonal",
                            "reference": "Performance reviews",
                            "context": "Annual corporate ritual"
                        },
                        "hashtags": ["CorporateLife", "PerformanceReview", "HumanTouch", "LipCare"]
                    }
                ]
            },
            "usage": {"total_tokens": 300}
        }
    
    def _mock_customer_validation(self):
        import random
        score = random.choice([7.5, 6.8, 8.0, 5.5])
        return {
            "content": {
                "score": score,
                "approved": score >= 7,
                "workplace_relevance": score + 0.5,
                "authenticity": score - 0.5,
                "value_perception": score,
                "feedback": "Good authenticity" if score >= 7 else "Too promotional"
            },
            "usage": {"total_tokens": 80}
        }
    
    def _mock_business_validation(self):
        import random
        score = random.choice([7.0, 6.2, 7.8, 5.8])
        return {
            "content": {
                "score": score,
                "approved": score >= 7,
                "brand_differentiation": score,
                "premium_positioning": score + 0.3,
                "linkedin_fit": score - 0.2,
                "feedback": "Strong positioning" if score >= 7 else "Needs differentiation"
            },
            "usage": {"total_tokens": 90}
        }
    
    def _mock_social_validation(self):
        import random
        score = random.choice([8.0, 7.2, 8.5, 6.5])
        return {
            "content": {
                "score": score,
                "approved": score >= 7,
                "hook_effectiveness": score + 0.5,
                "engagement_potential": score,
                "shareability": score - 0.3,
                "feedback": "Strong hook" if score >= 7 else "Won't stop scroll"
            },
            "usage": {"total_tokens": 85}
        }
    
    def _mock_feedback(self):
        return {
            "content": {
                "main_issues": ["Needs stronger hook", "Value proposition unclear"],
                "specific_improvements": {
                    "hook": "Make it more attention-grabbing",
                    "value_proposition": "Emphasize the ritual aspect"
                },
                "priority_fix": "Strengthen the opening line"
            },
            "usage": {"total_tokens": 100}
        }
    
    def _mock_revision(self):
        return {
            "content": {
                "revised_content": "Ever notice how your lips are the only part of you that hasn't been automated yet? Jesse A. Eisenbalm gets it. Stop. Breathe. Apply. For $8.99, own the one daily ritual that AI can't optimize. Premium botanicals for professionals who refuse to become machines.",
                "changes_made": ["Stronger hook", "Clearer value prop", "Better flow"]
            },
            "usage": {"total_tokens": 120}
        }

async def test_complete_system():
    """Test the complete content validation system"""
    
    print("\n" + "="*60)
    print("🚀 COMPLETE SYSTEM TEST")
    print("="*60)
    
    # Load configuration
    app_config = AppConfig.from_yaml()
    agent_config = AgentConfig()
    
    # Create AI client
    if USE_REAL_API:
        print("✅ Using REAL OpenAI API")
        from src.infrastructure.ai.openai_client import OpenAIClient
        ai_client = OpenAIClient(app_config)
    else:
        print("⚠️  Using MOCK AI client (no API key found)")
        ai_client = MockAIClient()
    
    print("\n" + "-"*60)
    print("INITIALIZING SYSTEM COMPONENTS")
    print("-"*60)
    
    # Create all agents
    print("Creating agents...")
    content_generator = AdvancedContentGenerator(agent_config, ai_client, app_config)
    validators = [
        SarahChenValidator(agent_config, ai_client, app_config),
        MarcusWilliamsValidator(agent_config, ai_client, app_config),
        JordanParkValidator(agent_config, ai_client, app_config)
    ]
    feedback_aggregator = FeedbackAggregator(agent_config, ai_client, app_config)
    revision_generator = RevisionGenerator(agent_config, ai_client, app_config)
    
    # Create orchestrator
    print("Creating orchestrator...")
    orchestrator = ValidationOrchestrator(
        content_generator,
        validators,
        feedback_aggregator,
        revision_generator,
        app_config
    )
    
    # Create export manager and analyzer
    print("Creating export manager and analyzer...")
    export_manager = ExportManager(output_dir="data/test_output")
    analyzer = PerformanceAnalyzer()
    
    # Create workflow controller
    print("Creating workflow controller...")
    controller = WorkflowController(orchestrator, export_manager, app_config)
    
    print("\n" + "-"*60)
    print("RUNNING BATCH PROCESSING")
    print("-"*60)
    
    # Process a batch
    print(f"Processing batch of {app_config.batch.posts_per_batch} posts...")
    batch = await controller.run_single_batch(batch_size=3)
    
    print(f"\nBatch {batch.id[:8]} completed!")
    print(f"Status: {batch.status}")
    print(f"Total posts: {batch.metrics.total_posts}")
    print(f"Approved: {batch.metrics.approved_posts}")
    print(f"Rejected: {batch.metrics.rejected_posts}")
    print(f"Approval rate: {batch.metrics.approval_rate:.1%}")
    
    # Show approved posts
    if batch.get_approved_posts():
        print("\n" + "-"*60)
        print("APPROVED POSTS")
        print("-"*60)
        for i, post in enumerate(batch.get_approved_posts(), 1):
            print(f"\n📝 Post {i}:")
            print(f"Content: {post.content[:150]}...")
            print(f"Score: {post.average_score:.1f}")
            print(f"Revisions: {post.revision_count}")
            if post.cultural_reference:
                print(f"Cultural Ref: {post.cultural_reference.reference}")
    
    # Show rejected posts
    if batch.get_rejected_posts():
        print("\n" + "-"*60)
        print("REJECTED POSTS")
        print("-"*60)
        for post in batch.get_rejected_posts():
            print(f"\n❌ Post {post.post_number}:")
            print(f"Score: {post.average_score:.1f}")
            for score in post.validation_scores:
                if not score.approved:
                    print(f"  - {score.agent_name}: {score.feedback}")
    
    # Performance analysis
    print("\n" + "-"*60)
    print("PERFORMANCE ANALYSIS")
    print("-"*60)
    
    analysis = analyzer.analyze_batch_performance(batch)
    perf_metrics = analysis['performance_metrics']
    
    print(f"First attempt approval rate: {perf_metrics.get('first_attempt_approval_rate', 0):.1%}")
    print(f"Revision success rate: {batch.metrics.revision_success_rate:.1%}")
    print(f"Average processing time: {batch.metrics.average_processing_time:.2f}s")
    print(f"Total cost: ${batch.metrics.total_cost:.4f}")
    print(f"Cost per approved post: ${batch.metrics.total_cost / max(batch.metrics.approved_posts, 1):.4f}")
    
    # Recommendations
    if analysis.get('recommendations'):
        print("\n📊 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")
    
    # Export results
    print("\n" + "-"*60)
    print("EXPORTING RESULTS")
    print("-"*60)
    
    if batch.get_approved_posts():
        csv_path = await export_manager.export_approved_posts(
            batch.get_approved_posts(),
            batch.id,
            format="csv"
        )
        print(f"✅ Approved posts exported to: {csv_path}")
    
    if batch.get_rejected_posts():
        csv_path = await export_manager.export_rejected_posts(
            batch.get_rejected_posts(),
            batch.id,
            format="csv"
        )
        print(f"✅ Rejected posts exported to: {csv_path}")
    
    metrics_path = await export_manager.export_batch_metrics(batch)
    print(f"✅ Batch metrics exported to: {metrics_path}")
    
    # Get overall stats
    print("\n" + "-"*60)
    print("SYSTEM STATISTICS")
    print("-"*60)
    
    stats = orchestrator.get_statistics()
    print(f"Total posts processed: {stats['total_posts_processed']}")
    print(f"Total approvals: {stats['total_approvals']}")
    print(f"Overall approval rate: {stats['overall_approval_rate']:.1%}")
    
    # Token usage (if using mock)
    if isinstance(ai_client, MockAIClient):
        print(f"\nMock API calls made: {ai_client.call_count}")
    
    print("\n" + "="*60)
    print("✅ SYSTEM TEST COMPLETE!")
    print("="*60)
    
    return batch

async def test_multiple_batches():
    """Test running multiple batches"""
    
    print("\n" + "="*60)
    print("🚀 MULTIPLE BATCH TEST")
    print("="*60)
    
    # Load configuration
    app_config = AppConfig.from_yaml()
    agent_config = AgentConfig()
    
    # Create AI client
    ai_client = MockAIClient() if not USE_REAL_API else OpenAIClient(app_config)
    
    # Create system
    content_generator = AdvancedContentGenerator(agent_config, ai_client, app_config)
    validators = [
        SarahChenValidator(agent_config, ai_client, app_config),
        MarcusWilliamsValidator(agent_config, ai_client, app_config),
        JordanParkValidator(agent_config, ai_client, app_config)
    ]
    
    orchestrator = ValidationOrchestrator(
        content_generator,
        validators,
        FeedbackAggregator(agent_config, ai_client, app_config),
        RevisionGenerator(agent_config, ai_client, app_config),
        app_config
    )
    
    controller = WorkflowController(
        orchestrator,
        ExportManager(output_dir="data/test_output"),
        app_config
    )
    
    # Run multiple batches
    print("Running 3 batches...")
    batches = await controller.run_multiple_batches(
        num_batches=3,
        batch_size=2,
        delay_seconds=0.5
    )
    
    # Show summary
    metrics = controller.get_performance_metrics()
    summary = metrics['summary']
    
    print("\n" + "-"*60)
    print("MULTI-BATCH SUMMARY")
    print("-"*60)
    print(f"Total posts: {summary['total_posts']}")
    print(f"Total approved: {summary['total_approved']}")
    print(f"Average approval rate: {summary['average_approval_rate']:.1%}")
    print(f"Total cost: ${summary['total_cost']:.4f}")
    print(f"Cost per approved: ${summary['cost_per_approved_post']:.4f}")
    
    # Analyze trends
    analyzer = PerformanceAnalyzer()
    trend_analysis = analyzer.analyze_multiple_batches(batches)
    
    print(f"\nTrend: {trend_analysis['trends']['approval_rate_trend']}")
    print(f"Best performers: {trend_analysis.get('best_performing_elements', {}).get('top_cultural_references', [])[:3]}")
    
    print("\n✅ Multiple batch test complete!")
    
    return batches

def main():
    """Main test runner"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║  Jesse A. Eisenbalm LinkedIn Content Validation System║
    ║                    SYSTEM TEST                        ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    if USE_REAL_API:
        print("🔑 OpenAI API key detected - will use real API")
        response = input("⚠️  This will make real API calls and incur costs. Continue? (y/n): ")
        if response.lower() != 'y':
            print("Test cancelled.")
            return
    else:
        print("🎭 No API key found - using mock responses")
    
    print("\nSelect test mode:")
    print("1. Single batch test")
    print("2. Multiple batch test")
    print("3. Both tests")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        asyncio.run(test_complete_system())
    elif choice == "2":
        asyncio.run(test_multiple_batches())
    elif choice == "3":
        asyncio.run(test_complete_system())
        asyncio.run(test_multiple_batches())
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()