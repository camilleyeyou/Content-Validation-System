"""
Export Manager - Handles exporting posts and metrics to various formats
"""

import json
import csv
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import structlog

from src.domain.models.post import LinkedInPost, PostStatus
from src.domain.models.batch import Batch

logger = structlog.get_logger()

class ExportManager:
    """Manages export of posts and metrics to CSV, Excel, and JSON formats"""
    
    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(component="export_manager")
        
        # Create subdirectories for different export types
        self.approved_dir = self.output_dir / "approved"
        self.rejected_dir = self.output_dir / "rejected"
        self.metrics_dir = self.output_dir / "metrics"
        
        for dir_path in [self.approved_dir, self.rejected_dir, self.metrics_dir]:
            dir_path.mkdir(exist_ok=True)
    
    async def export_approved_posts(self, 
                                   posts: List[LinkedInPost], 
                                   batch_id: str,
                                   format: str = "csv") -> str:
        """Export approved posts to specified format"""
        if not posts:
            self.logger.warning("No approved posts to export", batch_id=batch_id)
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"approved_posts_{batch_id[:8]}_{timestamp}"
        
        if format == "csv":
            filepath = await self._export_posts_to_csv(
                posts, self.approved_dir / f"{filename_base}.csv", "approved"
            )
        elif format == "excel":
            filepath = await self._export_posts_to_excel(
                posts, self.approved_dir / f"{filename_base}.xlsx", "approved"
            )
        elif format == "json":
            filepath = await self._export_posts_to_json(
                posts, self.approved_dir / f"{filename_base}.json"
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        self.logger.info("approved_posts_exported",
                        batch_id=batch_id,
                        count=len(posts),
                        filepath=str(filepath))
        
        return str(filepath)
    
    async def export_rejected_posts(self,
                                   posts: List[LinkedInPost],
                                   batch_id: str,
                                   format: str = "csv") -> str:
        """Export rejected posts with failure analysis"""
        if not posts:
            self.logger.warning("No rejected posts to export", batch_id=batch_id)
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"rejected_posts_{batch_id[:8]}_{timestamp}"
        
        if format == "csv":
            filepath = await self._export_posts_to_csv(
                posts, self.rejected_dir / f"{filename_base}.csv", "rejected"
            )
        elif format == "excel":
            filepath = await self._export_posts_to_excel(
                posts, self.rejected_dir / f"{filename_base}.xlsx", "rejected"
            )
        else:
            filepath = await self._export_posts_to_json(
                posts, self.rejected_dir / f"{filename_base}.json"
            )
        
        self.logger.info("rejected_posts_exported",
                        batch_id=batch_id,
                        count=len(posts),
                        filepath=str(filepath))
        
        return str(filepath)
    
    async def export_batch_metrics(self, batch: Batch, format: str = "json") -> str:
        """Export batch metrics and performance data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_metrics_{batch.id[:8]}_{timestamp}.json"
        filepath = self.metrics_dir / filename
        
        metrics_data = {
            "batch_id": batch.id,
            "created_at": batch.created_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "status": batch.status,
            "metrics": {
                "total_posts": batch.metrics.total_posts,
                "approved_posts": batch.metrics.approved_posts,
                "rejected_posts": batch.metrics.rejected_posts,
                "revised_posts": batch.metrics.revised_posts,
                "approval_rate": batch.metrics.approval_rate,
                "revision_success_rate": batch.metrics.revision_success_rate,
                "average_score": batch.metrics.average_score,
                "average_processing_time": batch.metrics.average_processing_time,
                "total_tokens_used": batch.metrics.total_tokens_used,
                "total_cost": batch.metrics.total_cost
            },
            "cultural_reference_performance": batch.metrics.cultural_reference_performance,
            "posts_summary": self._generate_posts_summary(batch.posts)
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)
        
        self.logger.info("batch_metrics_exported",
                        batch_id=batch.id,
                        filepath=str(filepath))
        
        return str(filepath)
    
    async def _export_posts_to_csv(self, 
                                  posts: List[LinkedInPost], 
                                  filepath: Path,
                                  export_type: str) -> Path:
        """Export posts to CSV format"""
        rows = []
        
        for post in posts:
            row = {
                "post_id": post.id,
                "batch_id": post.batch_id,
                "post_number": post.post_number,
                "status": post.status.value,
                "content": post.content,
                "target_audience": post.target_audience,
                "cultural_reference": post.cultural_reference.reference if post.cultural_reference else "",
                "cultural_category": post.cultural_reference.category if post.cultural_reference else "",
                "hashtags": ", ".join(post.hashtags) if post.hashtags else "",
                "average_score": round(post.average_score, 2),
                "approval_count": post.approval_count,
                "revision_count": post.revision_count,
                "created_at": post.created_at.isoformat(),
                "processing_time": post.processing_time_seconds or 0
            }
            
            # Add validation scores
            for score in post.validation_scores:
                row[f"{score.agent_name}_score"] = round(score.score, 2)
                row[f"{score.agent_name}_approved"] = score.approved
                if export_type == "rejected" and score.feedback:
                    row[f"{score.agent_name}_feedback"] = score.feedback
            
            rows.append(row)
        
        # Write to CSV
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(filepath, index=False)
        
        return filepath
    
    async def _export_posts_to_excel(self,
                                    posts: List[LinkedInPost],
                                    filepath: Path,
                                    export_type: str) -> Path:
        """Export posts to Excel format with multiple sheets"""
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Main posts sheet
            main_data = []
            for post in posts:
                main_data.append({
                    "Post ID": post.id[:8],
                    "Content": post.content,
                    "Target Audience": post.target_audience,
                    "Cultural Reference": post.cultural_reference.reference if post.cultural_reference else "",
                    "Hashtags": ", ".join(post.hashtags) if post.hashtags else "",
                    "Average Score": round(post.average_score, 2),
                    "Status": post.status.value,
                    "Revisions": post.revision_count
                })
            
            df_main = pd.DataFrame(main_data)
            df_main.to_excel(writer, sheet_name='Posts', index=False)
            
            # Validation scores sheet
            scores_data = []
            for post in posts:
                for score in post.validation_scores:
                    scores_data.append({
                        "Post ID": post.id[:8],
                        "Validator": score.agent_name,
                        "Score": round(score.score, 2),
                        "Approved": score.approved,
                        "Feedback": score.feedback or ""
                    })
            
            if scores_data:
                df_scores = pd.DataFrame(scores_data)
                df_scores.to_excel(writer, sheet_name='Validation Scores', index=False)
            
            # Summary statistics sheet
            if export_type == "approved":
                summary_data = {
                    "Metric": ["Total Posts", "Average Score", "Average Revisions", "Most Common Audience"],
                    "Value": [
                        len(posts),
                        round(sum(p.average_score for p in posts) / len(posts), 2),
                        round(sum(p.revision_count for p in posts) / len(posts), 2),
                        max(set(p.target_audience for p in posts), 
                            key=lambda x: sum(1 for p in posts if p.target_audience == x))
                    ]
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        return filepath
    
    async def _export_posts_to_json(self,
                                   posts: List[LinkedInPost],
                                   filepath: Path) -> Path:
        """Export posts to JSON format"""
        posts_data = []
        
        for post in posts:
            post_dict = {
                "id": post.id,
                "batch_id": post.batch_id,
                "post_number": post.post_number,
                "status": post.status.value,
                "content": post.content,
                "target_audience": post.target_audience,
                "hashtags": post.hashtags,
                "cultural_reference": None,
                "validation_scores": [],
                "metrics": {
                    "average_score": round(post.average_score, 2),
                    "approval_count": post.approval_count,
                    "revision_count": post.revision_count,
                    "processing_time": post.processing_time_seconds
                },
                "timestamps": {
                    "created": post.created_at.isoformat(),
                    "updated": post.updated_at.isoformat()
                }
            }
            
            if post.cultural_reference:
                post_dict["cultural_reference"] = {
                    "category": post.cultural_reference.category,
                    "reference": post.cultural_reference.reference,
                    "context": post.cultural_reference.context
                }
            
            for score in post.validation_scores:
                post_dict["validation_scores"].append({
                    "agent": score.agent_name,
                    "score": round(score.score, 2),
                    "approved": score.approved,
                    "feedback": score.feedback,
                    "criteria": score.criteria_breakdown
                })
            
            posts_data.append(post_dict)
        
        with open(filepath, 'w') as f:
            json.dump(posts_data, f, indent=2, default=str)
        
        return filepath
    
    def _generate_posts_summary(self, posts: List[LinkedInPost]) -> Dict[str, Any]:
        """Generate summary statistics for posts"""
        if not posts:
            return {}
        
        approved = [p for p in posts if p.status == PostStatus.APPROVED]
        rejected = [p for p in posts if p.status == PostStatus.REJECTED]
        
        # Cultural reference analysis
        cultural_refs = {}
        for post in posts:
            if post.cultural_reference:
                ref = post.cultural_reference.reference
                cultural_refs[ref] = cultural_refs.get(ref, {"count": 0, "avg_score": 0})
                cultural_refs[ref]["count"] += 1
                cultural_refs[ref]["avg_score"] += post.average_score
        
        for ref in cultural_refs:
            cultural_refs[ref]["avg_score"] /= cultural_refs[ref]["count"]
        
        return {
            "total": len(posts),
            "approved": len(approved),
            "rejected": len(rejected),
            "approval_rate": len(approved) / len(posts) if posts else 0,
            "average_score_approved": sum(p.average_score for p in approved) / len(approved) if approved else 0,
            "average_revisions": sum(p.revision_count for p in posts) / len(posts),
            "cultural_reference_performance": cultural_refs,
            "target_audience_breakdown": self._get_audience_breakdown(posts)
        }
    
    def _get_audience_breakdown(self, posts: List[LinkedInPost]) -> Dict[str, int]:
        """Get breakdown of target audiences"""
        audience_counts = {}
        for post in posts:
            audience = post.target_audience
            audience_counts[audience] = audience_counts.get(audience, 0) + 1
        return audience_counts