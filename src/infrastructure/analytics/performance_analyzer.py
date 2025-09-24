"""
Performance Analyzer - Analyzes system performance and content effectiveness
"""

import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from src.domain.models.post import LinkedInPost, PostStatus
from src.domain.models.batch import Batch

logger = structlog.get_logger()

class PerformanceAnalyzer:
    """Analyzes performance metrics and provides insights"""
    
    def __init__(self):
        self.logger = logger.bind(component="performance_analyzer")
        
    def analyze_batch_performance(self, batch: Batch) -> Dict[str, Any]:
        """Comprehensive analysis of a single batch"""
        analysis = {
            "batch_id": batch.id,
            "performance_metrics": self._calculate_performance_metrics(batch),
            "content_analysis": self._analyze_content_effectiveness(batch.posts),
            "validator_analysis": self._analyze_validator_behavior(batch.posts),
            "cost_analysis": self._calculate_cost_metrics(batch),
            "recommendations": self._generate_recommendations(batch)
        }
        
        return analysis
    
    def analyze_multiple_batches(self, batches: List[Batch]) -> Dict[str, Any]:
        """Analyze trends across multiple batches"""
        if not batches:
            return {}
        
        trend_analysis = {
            "total_batches": len(batches),
            "time_period": {
                "start": min(b.created_at for b in batches).isoformat(),
                "end": max(b.completed_at or b.created_at for b in batches).isoformat()
            },
            "overall_metrics": self._calculate_overall_metrics(batches),
            "trends": self._identify_trends(batches),
            "best_performing_elements": self._identify_best_performers(batches),
            "improvement_areas": self._identify_improvement_areas(batches)
        }
        
        return trend_analysis
    
    def _calculate_performance_metrics(self, batch: Batch) -> Dict[str, Any]:
        """Calculate key performance metrics for a batch"""
        posts = batch.posts
        approved = [p for p in posts if p.status == PostStatus.APPROVED]
        
        return {
            "approval_rate": batch.metrics.approval_rate,
            "first_attempt_approval_rate": len([p for p in approved if p.revision_count == 0]) / len(posts) if posts else 0,
            "revision_success_rate": batch.metrics.revision_success_rate,
            "average_score": batch.metrics.average_score,
            "score_distribution": self._get_score_distribution(posts),
            "processing_efficiency": {
                "avg_time_per_post": batch.metrics.average_processing_time,
                "total_processing_time": sum(p.processing_time_seconds or 0 for p in posts),
                "tokens_per_post": batch.metrics.total_tokens_used / len(posts) if posts else 0
            }
        }
    
    def _analyze_content_effectiveness(self, posts: List[LinkedInPost]) -> Dict[str, Any]:
        """Analyze what content elements are most effective"""
        approved = [p for p in posts if p.status == PostStatus.APPROVED]
        rejected = [p for p in posts if p.status == PostStatus.REJECTED]
        
        # Cultural reference effectiveness
        cultural_effectiveness = {}
        for post in posts:
            if post.cultural_reference:
                category = post.cultural_reference.category
                if category not in cultural_effectiveness:
                    cultural_effectiveness[category] = {"approved": 0, "rejected": 0, "avg_score": []}
                
                if post.status == PostStatus.APPROVED:
                    cultural_effectiveness[category]["approved"] += 1
                else:
                    cultural_effectiveness[category]["rejected"] += 1
                
                cultural_effectiveness[category]["avg_score"].append(post.average_score)
        
        # Calculate averages
        for category in cultural_effectiveness:
            scores = cultural_effectiveness[category]["avg_score"]
            cultural_effectiveness[category]["avg_score"] = sum(scores) / len(scores) if scores else 0
        
        return {
            "cultural_reference_effectiveness": cultural_effectiveness,
            "average_content_length": statistics.mean(len(p.content) for p in posts) if posts else 0,
            "hashtag_usage": self._analyze_hashtag_usage(posts),
            "target_audience_performance": self._analyze_audience_performance(posts)
        }
    
    def _analyze_validator_behavior(self, posts: List[LinkedInPost]) -> Dict[str, Any]:
        """Analyze validator scoring patterns"""
        validator_stats = {}
        
        for post in posts:
            for score in post.validation_scores:
                agent = score.agent_name
                if agent not in validator_stats:
                    validator_stats[agent] = {
                        "scores": [],
                        "approvals": 0,
                        "rejections": 0
                    }
                
                validator_stats[agent]["scores"].append(score.score)
                if score.approved:
                    validator_stats[agent]["approvals"] += 1
                else:
                    validator_stats[agent]["rejections"] += 1
        
        # Calculate statistics
        for agent in validator_stats:
            scores = validator_stats[agent]["scores"]
            validator_stats[agent]["average_score"] = statistics.mean(scores) if scores else 0
            validator_stats[agent]["score_std_dev"] = statistics.stdev(scores) if len(scores) > 1 else 0
            validator_stats[agent]["approval_rate"] = (
                validator_stats[agent]["approvals"] / 
                (validator_stats[agent]["approvals"] + validator_stats[agent]["rejections"])
            ) if (validator_stats[agent]["approvals"] + validator_stats[agent]["rejections"]) > 0 else 0
        
        return validator_stats
    
    def _calculate_cost_metrics(self, batch: Batch) -> Dict[str, Any]:
        """Calculate cost-related metrics"""
        approved_posts = [p for p in batch.posts if p.status == PostStatus.APPROVED]
        
        return {
            "total_cost": batch.metrics.total_cost,
            "cost_per_post": batch.metrics.total_cost / len(batch.posts) if batch.posts else 0,
            "cost_per_approved_post": batch.metrics.total_cost / len(approved_posts) if approved_posts else 0,
            "tokens_used": batch.metrics.total_tokens_used,
            "cost_breakdown": {
                "generation": batch.metrics.total_cost * 0.2,  # Estimate
                "validation": batch.metrics.total_cost * 0.5,  # Estimate
                "revision": batch.metrics.total_cost * 0.3   # Estimate
            }
        }
    
    def _generate_recommendations(self, batch: Batch) -> List[str]:
        """Generate recommendations based on batch performance"""
        recommendations = []
        
        # Check approval rate
        if batch.metrics.approval_rate < 0.2:
            recommendations.append("Consider adjusting content generation prompts - approval rate is very low")
        
        # Check revision effectiveness
        if batch.metrics.revision_success_rate < 0.3:
            recommendations.append("Revision process needs improvement - most revisions still fail")
        
        # Check processing time
        if batch.metrics.average_processing_time > 10:
            recommendations.append("Processing time is high - consider optimizing validation pipeline")
        
        # Check cost efficiency
        approved_posts = [p for p in batch.posts if p.status == PostStatus.APPROVED]
        if approved_posts and batch.metrics.total_cost / len(approved_posts) > 1.0:
            recommendations.append("Cost per approved post is high - optimize generation strategy")
        
        return recommendations
    
    def _get_score_distribution(self, posts: List[LinkedInPost]) -> Dict[str, int]:
        """Get distribution of scores"""
        distribution = {
            "0-3": 0,
            "3-5": 0,
            "5-7": 0,
            "7-9": 0,
            "9-10": 0
        }
        
        for post in posts:
            score = post.average_score
            if score <= 3:
                distribution["0-3"] += 1
            elif score <= 5:
                distribution["3-5"] += 1
            elif score <= 7:
                distribution["5-7"] += 1
            elif score <= 9:
                distribution["7-9"] += 1
            else:
                distribution["9-10"] += 1
        
        return distribution
    
    def _analyze_hashtag_usage(self, posts: List[LinkedInPost]) -> Dict[str, Any]:
        """Analyze hashtag effectiveness"""
        hashtag_stats = {}
        
        for post in posts:
            for hashtag in post.hashtags:
                if hashtag not in hashtag_stats:
                    hashtag_stats[hashtag] = {"count": 0, "approved": 0}
                
                hashtag_stats[hashtag]["count"] += 1
                if post.status == PostStatus.APPROVED:
                    hashtag_stats[hashtag]["approved"] += 1
        
        return hashtag_stats
    
    def _analyze_audience_performance(self, posts: List[LinkedInPost]) -> Dict[str, Any]:
        """Analyze performance by target audience"""
        audience_stats = {}
        
        for post in posts:
            audience = post.target_audience
            if audience not in audience_stats:
                audience_stats[audience] = {"count": 0, "approved": 0, "avg_score": []}
            
            audience_stats[audience]["count"] += 1
            if post.status == PostStatus.APPROVED:
                audience_stats[audience]["approved"] += 1
            audience_stats[audience]["avg_score"].append(post.average_score)
        
        # Calculate averages
        for audience in audience_stats:
            scores = audience_stats[audience]["avg_score"]
            audience_stats[audience]["avg_score"] = sum(scores) / len(scores) if scores else 0
            audience_stats[audience]["approval_rate"] = (
                audience_stats[audience]["approved"] / audience_stats[audience]["count"]
            )
        
        return audience_stats
    
    def _calculate_overall_metrics(self, batches: List[Batch]) -> Dict[str, Any]:
        """Calculate metrics across all batches"""
        total_posts = sum(b.metrics.total_posts for b in batches)
        total_approved = sum(b.metrics.approved_posts for b in batches)
        total_cost = sum(b.metrics.total_cost for b in batches)
        
        return {
            "total_posts_processed": total_posts,
            "total_approved": total_approved,
            "overall_approval_rate": total_approved / total_posts if total_posts else 0,
            "total_cost": total_cost,
            "average_cost_per_approved": total_cost / total_approved if total_approved else 0
        }
    
    def _identify_trends(self, batches: List[Batch]) -> Dict[str, Any]:
        """Identify trends over time"""
        sorted_batches = sorted(batches, key=lambda b: b.created_at)
        
        approval_rates = [b.metrics.approval_rate for b in sorted_batches]
        avg_scores = [b.metrics.average_score for b in sorted_batches]
        
        return {
            "approval_rate_trend": "improving" if approval_rates[-1] > approval_rates[0] else "declining",
            "score_trend": "improving" if avg_scores[-1] > avg_scores[0] else "declining",
            "latest_approval_rate": approval_rates[-1] if approval_rates else 0,
            "first_approval_rate": approval_rates[0] if approval_rates else 0
        }
    
    def _identify_best_performers(self, batches: List[Batch]) -> Dict[str, Any]:
        """Identify best performing elements across batches"""
        all_posts = []
        for batch in batches:
            all_posts.extend(batch.posts)
        
        approved = [p for p in all_posts if p.status == PostStatus.APPROVED]
        
        # Best cultural references
        cultural_scores = {}
        for post in approved:
            if post.cultural_reference:
                ref = post.cultural_reference.reference
                if ref not in cultural_scores:
                    cultural_scores[ref] = []
                cultural_scores[ref].append(post.average_score)
        
        best_cultural = {}
        for ref, scores in cultural_scores.items():
            best_cultural[ref] = statistics.mean(scores)
        
        return {
            "top_cultural_references": sorted(best_cultural.items(), key=lambda x: x[1], reverse=True)[:5],
            "best_batch": max(batches, key=lambda b: b.metrics.approval_rate).id if batches else None
        }
    
    def _identify_improvement_areas(self, batches: List[Batch]) -> List[str]:
        """Identify areas needing improvement"""
        areas = []
        
        avg_approval = statistics.mean(b.metrics.approval_rate for b in batches)
        if avg_approval < 0.3:
            areas.append("Overall approval rate needs improvement")
        
        avg_revision_success = statistics.mean(b.metrics.revision_success_rate for b in batches)
        if avg_revision_success < 0.5:
            areas.append("Revision success rate is low - feedback loop needs adjustment")
        
        return areas