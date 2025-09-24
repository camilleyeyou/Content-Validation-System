"""
Phase 4 Test Suite - Test Data Export and Analytics
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pytest
import json
import csv
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Import configurations
from src.infrastructure.config.config_manager import AppConfig
from src.infrastructure.logging.logger_config import configure_logging, get_logger

# Import export and analytics
from src.infrastructure.persistence.export_manager import ExportManager
from src.infrastructure.analytics.performance_analyzer import PerformanceAnalyzer

# Import models
from src.domain.models.post import LinkedInPost, PostStatus, ValidationScore, CulturalReference
from src.domain.models.batch import Batch, BatchMetrics

# Configure logging
configure_logging(level="DEBUG")
logger = get_logger("test_phase4")

class TestExportManager:
    """Test the export manager functionality"""
    
    @pytest.mark.asyncio
    async def test_export_manager_initialization(self):
        """Test export manager setup"""
        export_manager = ExportManager(output_dir="data/test_output")
        
        assert export_manager.output_dir.exists()
        assert export_manager.approved_dir.exists()
        assert export_manager.rejected_dir.exists()
        assert export_manager.metrics_dir.exists()
        
        logger.info("✅ Export manager initialization working")
        
        # Cleanup test directories
        import shutil
        if export_manager.output_dir.exists():
            shutil.rmtree(export_manager.output_dir)
    
    @pytest.mark.asyncio
    async def test_export_approved_posts_csv(self):
        """Test exporting approved posts to CSV"""
        export_manager = ExportManager(output_dir="data/test_output")
        
        # Create test posts
        posts = [
            LinkedInPost(
                batch_id="test-batch-001",
                post_number=1,
                content="This is an approved post about Jesse A. Eisenbalm lip balm that helps professionals stay human.",
                target_audience="Tech professionals",
                status=PostStatus.APPROVED,
                cultural_reference=CulturalReference(
                    category="tv_show",
                    reference="The Office",
                    context="Jim's humanity"
                )
            ),
            LinkedInPost(
                batch_id="test-batch-001",
                post_number=2,
                content="Another approved post showcasing the Stop. Breathe. Apply. ritual for modern professionals.",
                target_audience="Marketing professionals",
                status=PostStatus.APPROVED,
                hashtags=["HumanFirst", "LipCare"]
            )
        ]
        
        # Add validation scores
        for post in posts:
            post.add_validation(ValidationScore(
                agent_name="CustomerValidator",
                score=7.5,
                approved=True,
                feedback="Good"
            ))
        
        # Export posts
        filepath = await export_manager.export_approved_posts(posts, "test-batch-001", format="csv")
        
        assert Path(filepath).exists()
        assert ".csv" in filepath
        
        # Read and verify CSV content
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['status'] == 'approved'
        
        logger.info("✅ CSV export for approved posts working", filepath=filepath)
        
        # Cleanup
        import shutil
        shutil.rmtree(export_manager.output_dir)
    
    @pytest.mark.asyncio
    async def test_export_rejected_posts(self):
        """Test exporting rejected posts with failure analysis"""
        export_manager = ExportManager(output_dir="data/test_output")
        
        # Create rejected posts
        posts = [
            LinkedInPost(
                batch_id="test-batch-002",
                post_number=1,
                content="This post was rejected for being too promotional and not authentic enough for our brand voice.",
                target_audience="Everyone",
                status=PostStatus.REJECTED
            )
        ]
        
        # Add validation scores with feedback
        posts[0].add_validation(ValidationScore(
            agent_name="CustomerValidator",
            score=4.5,
            approved=False,
            feedback="Too salesy, lacks authenticity"
        ))
        posts[0].add_validation(ValidationScore(
            agent_name="BusinessValidator",
            score=5.0,
            approved=False,
            feedback="Weak brand differentiation"
        ))
        
        # Export rejected posts
        filepath = await export_manager.export_rejected_posts(posts, "test-batch-002", format="csv")
        
        assert Path(filepath).exists()
        assert "rejected" in filepath
        
        logger.info("✅ Rejected posts export working", filepath=filepath)
        
        # Cleanup
        import shutil
        shutil.rmtree(export_manager.output_dir)
    
    @pytest.mark.asyncio
    async def test_export_batch_metrics(self):
        """Test exporting batch metrics"""
        export_manager = ExportManager(output_dir="data/test_output")
        
        # Create a batch with metrics
        batch = Batch()
        batch.id = "test-batch-003"
        batch.status = "completed"
        batch.completed_at = datetime.now()
        
        # Set metrics
        batch.metrics.total_posts = 5
        batch.metrics.approved_posts = 3
        batch.metrics.rejected_posts = 2
        batch.metrics.approval_rate = 0.6
        batch.metrics.average_score = 7.2
        batch.metrics.total_tokens_used = 1500
        batch.metrics.total_cost = 0.15
        
        # Export metrics
        filepath = await export_manager.export_batch_metrics(batch)
        
        assert Path(filepath).exists()
        assert ".json" in filepath
        
        # Verify JSON content
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert data['batch_id'] == "test-batch-003"
            assert data['metrics']['approval_rate'] == 0.6
            assert data['metrics']['total_cost'] == 0.15
        
        logger.info("✅ Batch metrics export working", filepath=filepath)
        
        # Cleanup
        import shutil
        shutil.rmtree(export_manager.output_dir)
    
    @pytest.mark.asyncio
    async def test_export_to_excel(self):
        """Test Excel export functionality"""
        export_manager = ExportManager(output_dir="data/test_output")
        
        # Create test posts
        posts = [
            LinkedInPost(
                batch_id="test-batch-004",
                post_number=1,
                content="Excel export test post about Jesse A. Eisenbalm keeping professionals human in an AI world.",
                target_audience="Tech professionals",
                status=PostStatus.APPROVED,
                hashtags=["HumanFirst", "ExcelTest"]
            )
        ]
        
        posts[0].add_validation(ValidationScore(
            agent_name="SocialMediaValidator",
            score=8.0,
            approved=True
        ))
        
        # Export to Excel
        filepath = await export_manager.export_approved_posts(posts, "test-batch-004", format="excel")
        
        assert Path(filepath).exists()
        assert ".xlsx" in filepath
        
        # Verify Excel can be read
        import pandas as pd
        df = pd.read_excel(filepath, sheet_name='Posts')
        assert len(df) == 1
        assert df.iloc[0]['Status'] == 'approved'
        
        logger.info("✅ Excel export working", filepath=filepath)
        
        # Cleanup
        import shutil
        shutil.rmtree(export_manager.output_dir)

class TestPerformanceAnalyzer:
    """Test performance analysis functionality"""
    
    def test_analyzer_initialization(self):
        """Test performance analyzer setup"""
        analyzer = PerformanceAnalyzer()
        assert analyzer is not None
        logger.info("✅ Performance analyzer initialization working")
    
    def test_batch_performance_analysis(self):
        """Test analyzing single batch performance"""
        analyzer = PerformanceAnalyzer()
        
        # Create test batch with posts
        batch = Batch()
        batch.id = "test-batch-005"
        
        # Create diverse posts for analysis
        for i in range(5):
            post = LinkedInPost(
                batch_id=batch.id,
                post_number=i+1,
                content=f"Post {i+1} content about Jesse A. Eisenbalm lip balm for staying human in an AI world.",
                target_audience="Tech professionals" if i % 2 == 0 else "Marketing professionals",
                status=PostStatus.APPROVED if i < 3 else PostStatus.REJECTED
            )
            
            # Add validation scores
            post.add_validation(ValidationScore(
                agent_name="CustomerValidator",
                score=7.5 if i < 3 else 5.5,
                approved=i < 3
            ))
            post.add_validation(ValidationScore(
                agent_name="BusinessValidator",
                score=7.0 if i < 3 else 5.0,
                approved=i < 3
            ))
            
            post.processing_time_seconds = 2.5 + i * 0.5
            batch.posts.append(post)
        
        # Complete batch and calculate metrics
        batch.complete()
        
        # Analyze performance
        analysis = analyzer.analyze_batch_performance(batch)
        
        assert analysis['batch_id'] == "test-batch-005"
        assert 'performance_metrics' in analysis
        assert 'content_analysis' in analysis
        assert 'validator_analysis' in analysis
        assert 'cost_analysis' in analysis
        assert 'recommendations' in analysis
        
        # Check specific metrics
        perf_metrics = analysis['performance_metrics']
        assert perf_metrics['approval_rate'] == 0.6  # 3 out of 5 approved
        
        logger.info("✅ Batch performance analysis working",
                   approval_rate=perf_metrics['approval_rate'])
    
    def test_validator_behavior_analysis(self):
        """Test analyzing validator scoring patterns"""
        analyzer = PerformanceAnalyzer()
        
        # Create posts with varied validator scores
        posts = []
        for i in range(4):
            post = LinkedInPost(
                batch_id="test-batch",
                post_number=i+1,
                content=f"Test post {i+1} for validator analysis of Jesse A. Eisenbalm premium lip balm product.",
                target_audience="Professionals"
            )
            
            # Customer validator tends to be lenient
            post.add_validation(ValidationScore(
                agent_name="CustomerValidator",
                score=6.5 + i,
                approved=i >= 1
            ))
            
            # Business validator is strict
            post.add_validation(ValidationScore(
                agent_name="BusinessValidator",
                score=5.0 + i * 0.5,
                approved=i >= 2
            ))
            
            # Social validator is moderate
            post.add_validation(ValidationScore(
                agent_name="SocialMediaValidator",
                score=6.0 + i * 0.75,
                approved=i >= 1
            ))
            
            posts.append(post)
        
        # Analyze validator behavior
        validator_stats = analyzer._analyze_validator_behavior(posts)
        
        assert "CustomerValidator" in validator_stats
        assert "BusinessValidator" in validator_stats
        assert "SocialMediaValidator" in validator_stats
        
        # Business validator should have lowest approval rate
        assert validator_stats["BusinessValidator"]["approval_rate"] < validator_stats["CustomerValidator"]["approval_rate"]
        
        logger.info("✅ Validator behavior analysis working",
                   validators=list(validator_stats.keys()))
    
    def test_multiple_batch_analysis(self):
        """Test analyzing trends across multiple batches"""
        analyzer = PerformanceAnalyzer()
        
        batches = []
        
        # Create 3 batches with improving performance
        for batch_num in range(3):
            batch = Batch()
            batch.id = f"test-batch-{batch_num:03d}"
            batch.created_at = datetime.now()
            
            # Simulate improving approval rates
            approval_rate = 0.3 + (batch_num * 0.2)  # 0.3, 0.5, 0.7
            
            batch.metrics.total_posts = 5
            batch.metrics.approved_posts = int(5 * approval_rate)
            batch.metrics.rejected_posts = 5 - batch.metrics.approved_posts
            batch.metrics.approval_rate = approval_rate
            batch.metrics.average_score = 6.0 + batch_num
            batch.metrics.total_cost = 0.5
            batch.metrics.total_tokens_used = 1000
            
            batch.completed_at = datetime.now()
            batches.append(batch)
        
        # Analyze trends
        trend_analysis = analyzer.analyze_multiple_batches(batches)
        
        assert trend_analysis['total_batches'] == 3
        assert 'overall_metrics' in trend_analysis
        assert 'trends' in trend_analysis
        
        # Check that approval rate trend is improving
        assert trend_analysis['trends']['approval_rate_trend'] == 'improving'
        
        logger.info("✅ Multiple batch trend analysis working",
                   trend=trend_analysis['trends']['approval_rate_trend'])
    
    def test_cost_analysis(self):
        """Test cost metric calculations"""
        analyzer = PerformanceAnalyzer()
        
        batch = Batch()
        batch.id = "test-cost-batch"
        
        # Add posts
        for i in range(3):
            post = LinkedInPost(
                batch_id=batch.id,
                post_number=i+1,
                content=f"Post {i+1} for cost analysis testing of Jesse A. Eisenbalm lip balm marketing content.",
                target_audience="Professionals",
                status=PostStatus.APPROVED if i < 2 else PostStatus.REJECTED
            )
            batch.posts.append(post)
        
        batch.metrics.total_cost = 0.45
        batch.metrics.total_tokens_used = 1500
        batch.metrics.approved_posts = 2
        batch.metrics.total_posts = 3
        
        # Analyze costs
        cost_metrics = analyzer._calculate_cost_metrics(batch)
        
        assert cost_metrics['total_cost'] == 0.45
        assert cost_metrics['cost_per_post'] == 0.15  # 0.45 / 3
        assert cost_metrics['cost_per_approved_post'] == 0.225  # 0.45 / 2
        assert 'cost_breakdown' in cost_metrics
        
        logger.info("✅ Cost analysis working",
                   cost_per_approved=cost_metrics['cost_per_approved_post'])
    
    def test_recommendations_generation(self):
        """Test generation of performance recommendations"""
        analyzer = PerformanceAnalyzer()
        
        # Create batch with poor performance
        batch = Batch()
        batch.id = "test-recommendations"
        batch.metrics.approval_rate = 0.1  # Very low
        batch.metrics.revision_success_rate = 0.2  # Poor revision success
        batch.metrics.average_processing_time = 15  # High processing time
        batch.metrics.total_cost = 5.0
        batch.metrics.approved_posts = 1
        batch.metrics.total_posts = 10
        
        # Generate recommendations
        recommendations = analyzer._generate_recommendations(batch)
        
        assert len(recommendations) > 0
        assert any("approval rate" in r.lower() for r in recommendations)
        assert any("revision" in r.lower() for r in recommendations)
        
        logger.info("✅ Recommendations generation working",
                   num_recommendations=len(recommendations))

def run_tests():
    """Run all Phase 4 tests"""
    print("\n" + "="*60)
    print("🧪 PHASE 4 DATA EXPORT & ANALYTICS TESTS")
    print("="*60 + "\n")
    
    # Test Export Manager
    print("Testing Export Manager...")
    export_tests = TestExportManager()
    asyncio.run(export_tests.test_export_manager_initialization())
    asyncio.run(export_tests.test_export_approved_posts_csv())
    asyncio.run(export_tests.test_export_rejected_posts())
    asyncio.run(export_tests.test_export_batch_metrics())
    asyncio.run(export_tests.test_export_to_excel())
    print("✅ Export Manager tests passed!\n")
    
    # Test Performance Analyzer
    print("Testing Performance Analyzer...")
    analyzer_tests = TestPerformanceAnalyzer()
    analyzer_tests.test_analyzer_initialization()
    analyzer_tests.test_batch_performance_analysis()
    analyzer_tests.test_validator_behavior_analysis()
    analyzer_tests.test_multiple_batch_analysis()
    analyzer_tests.test_cost_analysis()
    analyzer_tests.test_recommendations_generation()
    print("✅ Performance Analyzer tests passed!\n")
    
    print("="*60)
    print("🎉 PHASE 4 COMPLETE - DATA EXPORT & ANALYTICS TESTS PASSED!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Move on to Phase 5: Integration & Production Testing")
    print("2. Test with real data exports")
    print("3. Set up automated reporting")

if __name__ == "__main__":
    run_tests()