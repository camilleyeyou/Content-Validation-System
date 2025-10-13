"""
Complete System Test - Run the entire LinkedIn content validation pipeline
Now includes:
- Optional LinkedIn OAuth (via linkedin_oauth_server.py) without hardcoding secrets
- Publishing approved posts to LinkedIn using LinkedInIntegrationService
- DALL-E image generation via dedicated ImageGenerationAgent
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Project path
sys.path.insert(0, os.path.abspath('.'))

# Load .env (do not hardcode any secret)
load_dotenv()

# --- App imports ---
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.logging.logger_config import configure_logging, get_logger
from src.infrastructure.persistence.export_manager import ExportManager
from src.infrastructure.analytics.performance_analyzer import PerformanceAnalyzer

from src.domain.agents.base_agent import AgentConfig
from src.domain.agents.advanced_content_generator import AdvancedContentGenerator
from src.domain.agents.image_generation_agent import ImageGenerationAgent
from src.domain.agents.validators.sarah_chen_validator import SarahChenValidator
from src.domain.agents.validators.marcus_williams_validator import MarcusWilliamsValidator
from src.domain.agents.validators.jordan_park_validator import JordanParkValidator
from src.domain.agents.feedback_aggregator import FeedbackAggregator
from src.domain.agents.revision_generator import RevisionGenerator

from src.domain.services.validation_orchestrator import ValidationOrchestrator
from src.domain.services.workflow_controller import WorkflowController

# --- LinkedIn pieces ---
from src.infrastructure.social.linkedin_publisher import LinkedInIntegrationService
try:
    from linkedin_oauth_server import LinkedInOAuthServer
except ImportError:
    LinkedInOAuthServer = None

# Logging
configure_logging(level="INFO")
logger = get_logger("system_test")

# Detect whether to use real OpenAI
USE_REAL_API = os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your-openai-api-key-here"


# ---------------------------
# Mock AI client with image generation
# ---------------------------
class MockAIClient:
    """Mock AI client for testing without API key - includes image generation"""

    def __init__(self):
        self.call_count = 0
        self.image_count = 0

    async def generate(self, prompt: str, system_prompt: str = None, **kwargs):
        self.call_count += 1
        response_format = kwargs.get('response_format', 'json')

        # Image prompt creation (for ImageGenerationAgent)
        if "Analyze this LinkedIn post and create a DETAILED image prompt" in prompt:
            return {
                "content": "Professional lifestyle photography of premium Jesse A. Eisenbalm lip balm on a modern office desk with laptop and coffee. Warm natural window lighting creating soft shadows, shallow depth of field with lip balm in sharp focus. Sophisticated navy blue and gold color palette, clean white surfaces. The scene conveys a moment of self-care pause during busy professional work. High-end product photography style, modern and elegant.",
                "usage": {"total_tokens": 100}
            }

        # Content generation
        if "Generate" in prompt and ("LinkedIn post" in prompt or "LinkedIn posts" in prompt):
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

    async def generate_image(self, prompt: str, size: str = "1024x1024", 
                           quality: str = "standard", style: str = "vivid"):
        """Mock DALL-E image generation"""
        self.image_count += 1
        
        # Return a placeholder image URL
        mock_images = [
            "https://via.placeholder.com/1024x1024/4A90E2/FFFFFF?text=Jesse+A.+Eisenbalm+Workspace",
            "https://via.placeholder.com/1024x1024/1E3A5F/FFD700?text=Premium+Lip+Balm+Ritual",
            "https://via.placeholder.com/1024x1024/2C5F7C/F5F5F5?text=Modern+Professional+Moment"
        ]
        
        return {
            "url": mock_images[self.image_count % len(mock_images)],
            "revised_prompt": f"Mock revised: {prompt[:100]}..."
        }

    def _mock_generation(self):
        """Mock content generation (no image_prompt field - ImageAgent handles that)"""
        import random
        
        posts = [
            {
                "content": "Remember when Jim from The Office taught us that small moments matter? In our AI-obsessed workplace, Jesse A. Eisenbalm ($8.99) is that small moment. Stop. Breathe. Apply. A premium ritual that keeps you grounded when every meeting is 'pivotal' and every email is 'urgent'. Because your humanity isn't a KPI, but your lips deserve premium care.\n\n#HumanFirst #LinkedInLife #PremiumSelfCare #OfficeLife",
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
                "content": "That Zoom fatigue hitting different at 3pm? Your fifth back-to-back video call doesn't care about your chapped lips, but you should. Jesse A. Eisenbalm - because for $8.99, you can own one thing that AI can't optimize: your moment to Stop. Breathe. Apply. Stay human, stay smooth.\n\n#RemoteWork #ZoomFatigue #SelfCare #StayHuman",
                "hook": "That Zoom fatigue hitting different at 3pm?",
                "target_audience": "Remote workers",
                "cultural_reference": {
                    "category": "workplace",
                    "reference": "Zoom fatigue",
                    "context": "Modern remote work struggle"
                },
                "hashtags": ["RemoteWork", "ZoomFatigue", "SelfCare", "StayHuman"]
            }
        ]
        
        selected = random.choice(posts)
        
        return {
            "content": selected,
            "usage": {"total_tokens": 350}
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
                "specific_improvements": {"hook": "Make it more attention-grabbing","value_proposition": "Emphasize the ritual aspect"},
                "priority_fix": "Strengthen the opening line"
            },
            "usage": {"total_tokens": 100}
        }

    def _mock_revision(self):
        return {
            "content": {
                "revised_content": "Ever notice how your lips are the only part of you that hasn't been automated yet? Jesse A. Eisenbalm gets it. Stop. Breathe. Apply. For $8.99, own the one daily ritual that AI can't optimize. Premium botanicals for professionals who refuse to become machines.",
                "changes_made": ["Stronger hook","Clearer value prop","Better flow"]
            },
            "usage": {"total_tokens": 120}
        }


# --------------------------------
# LinkedIn helpers (no secrets)
# --------------------------------
def _load_existing_token_from_file() -> str | None:
    """Loads token from config/linkedin_token.json if present."""
    token_file = Path("config/linkedin_token.json")
    if token_file.exists():
        try:
            data = json.loads(token_file.read_text(encoding="utf-8"))
            return data.get("access_token")
        except Exception:
            return None
    return None


def ensure_linkedin_token(interactive_auth: bool = True) -> bool:
    """
    Ensure we have a LinkedIn access token without hardcoding any secret.
    """
    # 1) Already in env?
    if os.getenv("LINKEDIN_ACCESS_TOKEN"):
        return True

    # 2) Try token file
    file_token = _load_existing_token_from_file()
    if file_token:
        os.environ["LINKEDIN_ACCESS_TOKEN"] = file_token
        return True

    # 3) Run OAuth if allowed and available
    if interactive_auth and LinkedInOAuthServer is not None:
        print("\nNo LinkedIn token detected. Launching OAuth flow...")
        oauth = LinkedInOAuthServer()
        token = oauth.authorize()
        if token:
            os.environ["LINKEDIN_ACCESS_TOKEN"] = token
            return True
        else:
            print("❌ LinkedIn OAuth failed.")
            return False

    print("ℹ️ Skipping LinkedIn auth (no token and OAuth helper unavailable or disabled).")
    return False


async def publish_approved_posts_to_linkedin(batch) -> dict | None:
    """
    Publishes approved posts using LinkedInIntegrationService if we have a token.
    """
    if not batch or not batch.get_approved_posts():
        print("No approved posts to publish.")
        return None

    if not ensure_linkedin_token(interactive_auth=False):
        print("🔒 LinkedIn token not available. Run auth first (menu option) or set LINKEDIN_ACCESS_TOKEN.")
        return None

    print("\n" + "-"*60)
    print("PUBLISHING APPROVED POSTS TO LINKEDIN")
    print("-"*60)

    service = LinkedInIntegrationService()
    results = await service.publish_batch_results(batch)

    # Summary
    print("\n" + "-"*60)
    print("LINKEDIN PUBLISH SUMMARY")
    print("-"*60)
    print(f"Successful: {results.get('successful', 0)}")
    print(f"Failed: {results.get('failed', 0)}")
    if results.get("errors"):
        for e in results["errors"]:
            print(f"  - Post {e.get('post_id')}: {e.get('error')}")

    return results


# ---------------------------
# Core test flows
# ---------------------------
async def test_complete_system(run_publish: bool = False):
    """Run your full generation/validation flow with images; optionally publish approved posts."""

    print("\n" + "="*60)
    print("🚀 COMPLETE SYSTEM TEST WITH IMAGE GENERATION AGENT")
    print("="*60)

    # Load configuration
    app_config = AppConfig.from_yaml()
    agent_config = AgentConfig()

    # Create AI client
    if USE_REAL_API:
        print("✅ Using REAL OpenAI API (with DALL-E 3)")
        from src.infrastructure.ai.openai_client import OpenAIClient
        ai_client = OpenAIClient(app_config)
    else:
        print("🎭 Using MOCK AI client (no OpenAI key found)")
        ai_client = MockAIClient()

    print("\n" + "-"*60)
    print("INITIALIZING SYSTEM COMPONENTS")
    print("-"*60)

    # Agents
    content_generator = AdvancedContentGenerator(agent_config, ai_client, app_config)
    
    # NEW: Image generation agent (dedicated)
    image_generator = ImageGenerationAgent(agent_config, ai_client, app_config)
    
    validators = [
        SarahChenValidator(agent_config, ai_client, app_config),
        MarcusWilliamsValidator(agent_config, ai_client, app_config),
        JordanParkValidator(agent_config, ai_client, app_config)
    ]
    feedback_aggregator = FeedbackAggregator(agent_config, ai_client, app_config)
    revision_generator = RevisionGenerator(agent_config, ai_client, app_config)

    # Orchestrator - NOW WITH IMAGE GENERATOR
    orchestrator = ValidationOrchestrator(
        content_generator,
        validators,
        feedback_aggregator,
        revision_generator,
        image_generator,  # NEW: Dedicated image generation agent
        app_config
    )

    # Export/analyze
    export_manager = ExportManager(output_dir="data/test_output")
    analyzer = PerformanceAnalyzer()

    # Controller
    controller = WorkflowController(orchestrator, export_manager, app_config)

    # ---- Run a batch
    print("\n" + "-"*60)
    print("RUNNING BATCH PROCESSING WITH IMAGE GENERATION")
    print("-"*60)
    print(f"Processing batch of {app_config.batch.posts_per_batch} post(s)...")
    batch = await controller.run_single_batch(batch_size=app_config.batch.posts_per_batch)

    print(f"\nBatch {batch.id[:8]} completed!")
    print(f"Status: {batch.status}")
    print(f"Total posts: {batch.metrics.total_posts}")
    print(f"Approved: {batch.metrics.approved_posts}")
    print(f"Rejected: {batch.metrics.rejected_posts}")
    print(f"Posts with images: {batch.metrics.posts_with_images}")
    print(f"Approval rate: {batch.metrics.approval_rate:.1%}")

    # Approved preview with images
    if batch.get_approved_posts():
        print("\n" + "-"*60)
        print("APPROVED POSTS WITH IMAGES")
        print("-"*60)
        for i, post in enumerate(batch.get_approved_posts(), 1):
            print(f"\n📝 Post {i}:")
            print(f"Content: {post.content[:150]}...")
            print(f"Score: {post.average_score:.1f}")
            print(f"Revisions: {post.revision_count}")
            if post.cultural_reference:
                print(f"Cultural Ref: {post.cultural_reference.reference}")
            # Image info
            if hasattr(post, 'image_url') and post.image_url:
                print(f"🖼️  Image URL: {post.image_url[:80]}...")
                if hasattr(post, 'image_description') and post.image_description:
                    print(f"   Description: {post.image_description[:80]}...")
            else:
                print(f"⚠️  No image generated")

    # Rejected summary
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

    # Performance
    print("\n" + "-"*60)
    print("PERFORMANCE ANALYSIS")
    print("-"*60)

    analysis = analyzer.analyze_batch_performance(batch)
    perf_metrics = analysis['performance_metrics']

    print(f"First attempt approval rate: {perf_metrics.get('first_attempt_approval_rate', 0):.1%}")
    print(f"Revision success rate: {batch.metrics.revision_success_rate:.1%}")
    print(f"Average processing time: {batch.metrics.average_processing_time:.2f}s")
    print(f"Total cost: ${batch.metrics.total_cost:.4f}")
    if batch.metrics.posts_with_images > 0:
        print(f"Image generation cost: ${batch.metrics.image_cost:.4f}")
        print(f"Text generation cost: ${batch.metrics.text_cost:.4f}")
    print(f"Cost per approved post: ${batch.metrics.total_cost / max(batch.metrics.approved_posts, 1):.4f}")

    if analysis.get('recommendations'):
        print("\n📊 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"  • {rec}")

    # Export
    print("\n" + "-"*60)
    print("EXPORTING RESULTS")
    print("-"*60)

    if batch.get_approved_posts():
        csv_path = await export_manager.export_approved_posts(
            batch.get_approved_posts(), batch.id, format="csv"
        )
        print(f"✅ Approved posts exported to: {csv_path}")

    if batch.get_rejected_posts():
        csv_path = await export_manager.export_rejected_posts(
            batch.get_rejected_posts(), batch.id, format="csv"
        )
        print(f"✅ Rejected posts exported to: {csv_path}")

    metrics_path = await export_manager.export_batch_metrics(batch)
    print(f"✅ Batch metrics exported to: {metrics_path}")

    # System stats
    print("\n" + "-"*60)
    print("SYSTEM STATISTICS")
    print("-"*60)

    stats = orchestrator.get_statistics()
    print(f"Total posts processed: {stats['total_posts_processed']}")
    print(f"Total approvals: {stats['total_approvals']}")
    print(f"Overall approval rate: {stats['overall_approval_rate']:.1%}")

    # Token/Image usage
    if isinstance(ai_client, MockAIClient):
        print(f"\nMock API calls made: {ai_client.call_count}")
        print(f"Mock images generated: {ai_client.image_count}")
    else:
        print(f"\n💰 Note: Real DALL-E images cost $0.04 each (standard quality)")

    # Optional: publish approved posts to LinkedIn
    if run_publish:
        await publish_approved_posts_to_linkedin(batch)

    print("\n" + "="*60)
    print("✅ SYSTEM TEST COMPLETE!")
    print("="*60)

    return batch


async def test_multiple_batches():
    """Run multiple batches (no publish in this helper)"""
    print("\n" + "="*60)
    print("🚀 MULTIPLE BATCH TEST")
    print("="*60)

    app_config = AppConfig.from_yaml()
    agent_config = AgentConfig()

    if USE_REAL_API:
        from src.infrastructure.ai.openai_client import OpenAIClient
        ai_client = OpenAIClient(app_config)
    else:
        ai_client = MockAIClient()

    content_generator = AdvancedContentGenerator(agent_config, ai_client, app_config)
    image_generator = ImageGenerationAgent(agent_config, ai_client, app_config)
    
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
        image_generator,
        app_config
    )

    controller = WorkflowController(
        orchestrator,
        ExportManager(output_dir="data/test_output"),
        app_config
    )

    print("Running 3 batches...")
    batches = await controller.run_multiple_batches(
        num_batches=3, batch_size=1, delay_seconds=0.5
    )

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

    analyzer = PerformanceAnalyzer()
    trend_analysis = analyzer.analyze_multiple_batches(batches)
    print(f"\nTrend: {trend_analysis['trends']['approval_rate_trend']}")
    print(f"Best performers: {trend_analysis.get('best_performing_elements', {}).get('top_cultural_references', [])[:3]}")

    print("\n✅ Multiple batch test complete!")
    return batches


def main():
    """Interactive runner with LinkedIn auth/publish options"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║  Jesse A. Eisenbalm LinkedIn Content Validation System║
    ║    WITH DEDICATED IMAGE GENERATION AGENT (DALL-E 3)    ║
    ╚════════════════════════════════════════════════════════╝
    """)

    if USE_REAL_API:
        print("🔑 OpenAI API key detected - will use real API")
        print("💰 DALL-E 3 costs: $0.04 per image (standard quality)")
        resp = input("⚠️  This will make real API calls and incur costs. Continue? (y/n): ")
        if resp.lower() != 'y':
            print("Test cancelled."); return
    else:
        print("🎭 No OpenAI key found - using mock responses with placeholder images")

    print("\nSelect mode:")
    print("1. Single batch only (1 post with image)")
    print("2. Single batch + publish to LinkedIn (uses existing token if available)")
    print("3. Multiple batch test (3 posts with images)")
    print("4. LinkedIn OAuth now (obtain token)")
    print("5. Exit")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        asyncio.run(test_complete_system(run_publish=False))
    elif choice == "2":
        if not ensure_linkedin_token(interactive_auth=False):
            print("\n🔐 No token found. Choose option 4 to authenticate first.")
            return
        asyncio.run(test_complete_system(run_publish=True))
    elif choice == "3":
        asyncio.run(test_multiple_batches())
    elif choice == "4":
        if LinkedInOAuthServer is None:
            print("⚠️ linkedin_oauth_server.py not found/importable. Place it at project root.")
            return
        print("\nLaunching LinkedIn OAuth flow...")
        oauth = LinkedInOAuthServer()
        token = oauth.authorize()
        if token:
            print("✅ Token saved. You can now choose option 2 to publish.")
        else:
            print("❌ OAuth failed.")
    elif choice == "5":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()