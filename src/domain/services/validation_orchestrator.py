"""
Validation Orchestrator - Manages the complete validation workflow
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from src.domain.models.post import LinkedInPost, PostStatus, ValidationScore
from src.domain.models.batch import Batch, BatchMetrics
from src.domain.agents.base_agent import BaseAgent
from src.domain.agents.content_generator import ContentGenerator
from src.domain.agents.validators.customer_validator import CustomerValidator
from src.domain.agents.validators.business_validator import BusinessValidator
from src.domain.agents.validators.social_validator import SocialMediaValidator
from src.domain.agents.feedback_aggregator import FeedbackAggregator
from src.domain.agents.revision_generator import RevisionGenerator
from src.infrastructure.config.config_manager import AppConfig

logger = structlog.get_logger()

class ValidationOrchestrator:
    """Orchestrates the validation workflow with parallel processing"""
    
    def __init__(self,
                 content_generator: ContentGenerator,
                 validators: List[BaseAgent],
                 feedback_aggregator: FeedbackAggregator,
                 revision_generator: RevisionGenerator,
                 config: AppConfig):
        self.content_generator = content_generator
        self.validators = validators
        self.feedback_aggregator = feedback_aggregator
        self.revision_generator = revision_generator
        self.config = config
        self.logger = logger.bind(component="orchestrator")
        
        # Performance tracking
        self._total_posts_processed = 0
        self._total_approvals = 0
        self._total_revisions = 0
        self._total_rejections = 0
    
    async def process_batch(self, batch_size: Optional[int] = None) -> Batch:
        """Process a batch of posts through the complete workflow"""
        batch_size = batch_size or self.config.batch.posts_per_batch
        batch = Batch()
        
        self.logger.info("batch_processing_started", 
                        batch_id=batch.id, 
                        size=batch_size)
        
        try:
            # Step 1: Generate initial posts
            posts = await self._generate_initial_posts(batch.id, batch_size)
            for post in posts:
                batch.add_post(post)
            
            # Step 2: Process each post through validation pipeline
            for post in batch.posts:
                await self._process_single_post(post)
            
            # Step 3: Check if we need regeneration
            approval_rate = self._calculate_approval_rate(batch.posts)
            
            if approval_rate < self.config.batch.target_approval_rate:
                self.logger.info("batch_regeneration_needed",
                               approval_rate=approval_rate,
                               target=self.config.batch.target_approval_rate)
                
                # Analyze failures and regenerate
                additional_posts = await self._handle_regeneration(
                    batch, 
                    batch_size
                )
                
                # Process regenerated posts
                for post in additional_posts:
                    batch.add_post(post)
                    await self._process_single_post(post)
            
            # Step 4: Complete batch and calculate metrics
            batch.complete()
            
            # Update orchestrator stats
            self._update_statistics(batch)
            
            self.logger.info("batch_processing_completed",
                           batch_id=batch.id,
                           approved=batch.metrics.approved_posts,
                           rejected=batch.metrics.rejected_posts,
                           approval_rate=batch.metrics.approval_rate)
            
            return batch
            
        except Exception as e:
            batch.status = "failed"
            batch.error = str(e)
            self.logger.error("batch_processing_failed", 
                            batch_id=batch.id, 
                            error=str(e))
            raise
    
    async def _process_single_post(self, post: LinkedInPost) -> LinkedInPost:
        """Process a single post through validation and potential revision"""
        start_time = time.time()
        post.status = PostStatus.VALIDATING
        
        self.logger.info("post_processing_started", 
                        post_id=post.id,
                        batch_id=post.batch_id)
        
        # Keep trying until approved or max revisions reached
        while True:
            # Step 1: Validate with all validators in parallel
            validation_scores = await self._validate_post_parallel(post)
            
            # Clear old scores and add new ones
            post.validation_scores = []
            for score in validation_scores:
                post.add_validation(score)
            
            # Step 2: Check approval status
            if post.is_approved(self.config.batch.min_approvals_required):
                post.status = PostStatus.APPROVED
                post.processing_time_seconds = time.time() - start_time
                
                self.logger.info("post_approved",
                               post_id=post.id,
                               approval_count=post.approval_count,
                               average_score=post.average_score)
                break
            
            # Step 3: Check if we can revise
            if post.can_revise():
                self.logger.info("post_revision_needed",
                               post_id=post.id,
                               revision_count=post.revision_count,
                               average_score=post.average_score)
                
                # Aggregate feedback and generate revision
                feedback = await self.feedback_aggregator.process(post)
                revised_post = await self.revision_generator.process((post, feedback))
                
                # The revision generator modifies the post in-place
                post = revised_post
                post.status = PostStatus.REVISION_NEEDED
                
                # Continue loop to re-validate
                continue
            else:
                # Max revisions reached, reject
                post.status = PostStatus.REJECTED
                post.processing_time_seconds = time.time() - start_time
                
                self.logger.info("post_rejected",
                               post_id=post.id,
                               revision_count=post.revision_count,
                               average_score=post.average_score)
                break
        
        return post
    
    async def _validate_post_parallel(self, post: LinkedInPost) -> List[ValidationScore]:
        """Validate a post with all validators in parallel"""
        validation_tasks = []
        
        for validator in self.validators:
            task = asyncio.create_task(validator.process(post))
            validation_tasks.append(task)
        
        # Wait for all validators to complete
        validation_scores = await asyncio.gather(*validation_tasks)
        
        self.logger.debug("parallel_validation_completed",
                         post_id=post.id,
                         validator_count=len(validation_scores))
        
        return validation_scores
    
    async def _generate_initial_posts(self, batch_id: str, count: int) -> List[LinkedInPost]:
        """Generate initial batch of posts"""
        input_data = {
            "batch_id": batch_id,
            "count": count,
            "brand_context": {
                "product": self.config.brand.product_name,
                "price": self.config.brand.price,
                "tagline": self.config.brand.tagline,
                "audience": self.config.brand.target_audience
            }
        }
        
        generated_data = await self.content_generator.process(input_data)
        
        # Convert to LinkedInPost objects
        posts = []
        for post_data in generated_data:
            post = LinkedInPost(
                batch_id=batch_id,
                post_number=post_data.get("post_number", len(posts) + 1),
                content=post_data["content"],
                target_audience=post_data.get("target_audience", "LinkedIn professionals"),
                cultural_reference=post_data.get("cultural_reference"),
                hashtags=post_data.get("hashtags", [])
            )
            posts.append(post)
        
        self.logger.info("initial_posts_generated",
                        batch_id=batch_id,
                        count=len(posts))
        
        return posts
    
    async def _handle_regeneration(self, batch: Batch, target_count: int) -> List[LinkedInPost]:
        """Handle regeneration of posts based on failure patterns"""
        rejected_posts = batch.get_rejected_posts()
        
        if not rejected_posts:
            return []
        
        # Analyze failure patterns
        failure_patterns = self._analyze_failure_patterns(rejected_posts)
        
        # Calculate how many more posts we need
        approved_count = len(batch.get_approved_posts())
        needed_count = max(1, target_count - approved_count)
        
        # Generate new posts avoiding failure patterns
        input_data = {
            "batch_id": batch.id,
            "count": needed_count,
            "brand_context": {
                "product": self.config.brand.product_name,
                "price": self.config.brand.price,
                "tagline": self.config.brand.tagline,
                "audience": self.config.brand.target_audience
            },
            "avoid_patterns": failure_patterns
        }
        
        generated_data = await self.content_generator.process(input_data)
        
        # Convert to LinkedInPost objects
        new_posts = []
        for post_data in generated_data:
            post = LinkedInPost(
                batch_id=batch.id,
                post_number=len(batch.posts) + len(new_posts) + 1,
                content=post_data["content"],
                target_audience=post_data.get("target_audience", "LinkedIn professionals"),
                cultural_reference=post_data.get("cultural_reference"),
                hashtags=post_data.get("hashtags", [])
            )
            new_posts.append(post)
        
        self.logger.info("regenerated_posts",
                        batch_id=batch.id,
                        count=len(new_posts),
                        avoiding_patterns=list(failure_patterns.keys()))
        
        return new_posts
    
    def _analyze_failure_patterns(self, rejected_posts: List[LinkedInPost]) -> Dict[str, Any]:
        """Analyze patterns in rejected posts"""
        patterns = {
            "common_issues": [],
            "low_scoring_criteria": {},
            "cultural_references_failed": [],
            "target_audiences_failed": []
        }
        
        for post in rejected_posts:
            # Collect feedback messages
            for score in post.validation_scores:
                if score.feedback and not score.approved:
                    patterns["common_issues"].append(score.feedback)
                
                # Track low-scoring criteria
                if hasattr(score, 'criteria_breakdown'):
                    for criterion, value in score.criteria_breakdown.items():
                        if isinstance(value, (int, float)) and value < 5:
                            patterns["low_scoring_criteria"][criterion] = \
                                patterns["low_scoring_criteria"].get(criterion, 0) + 1
            
            # Track failed cultural references
            if post.cultural_reference:
                patterns["cultural_references_failed"].append(
                    post.cultural_reference.reference
                )
            
            # Track failed target audiences
            patterns["target_audiences_failed"].append(post.target_audience)
        
        # Keep only unique values and most common issues
        patterns["common_issues"] = list(set(patterns["common_issues"]))[:5]
        patterns["cultural_references_failed"] = list(set(patterns["cultural_references_failed"]))
        patterns["target_audiences_failed"] = list(set(patterns["target_audiences_failed"]))
        
        return patterns
    
    def _calculate_approval_rate(self, posts: List[LinkedInPost]) -> float:
        """Calculate the approval rate for a list of posts"""
        if not posts:
            return 0.0
        
        approved = sum(1 for p in posts if p.status == PostStatus.APPROVED)
        return approved / len(posts)
    
    def _update_statistics(self, batch: Batch) -> None:
        """Update orchestrator statistics"""
        self._total_posts_processed += batch.metrics.total_posts
        self._total_approvals += batch.metrics.approved_posts
        self._total_rejections += batch.metrics.rejected_posts
        self._total_revisions += batch.metrics.revised_posts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            "total_posts_processed": self._total_posts_processed,
            "total_approvals": self._total_approvals,
            "total_rejections": self._total_rejections,
            "total_revisions": self._total_revisions,
            "overall_approval_rate": self._total_approvals / self._total_posts_processed 
                if self._total_posts_processed > 0 else 0,
            "revision_effectiveness": self._total_revisions / self._total_posts_processed
                if self._total_posts_processed > 0 else 0
        }