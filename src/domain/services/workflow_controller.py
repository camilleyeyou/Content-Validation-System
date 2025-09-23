"""
Workflow Controller - High-level control of the content generation system
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from src.domain.services.validation_orchestrator import ValidationOrchestrator
from src.domain.models.batch import Batch
from src.domain.models.post import LinkedInPost  # Added this import
from src.infrastructure.persistence.export_manager import ExportManager
from src.infrastructure.config.config_manager import AppConfig

logger = structlog.get_logger()

class WorkflowController:
    """Controls the overall workflow and batch processing"""
    
    def __init__(self, 
                 orchestrator: ValidationOrchestrator,
                 export_manager: Optional['ExportManager'] = None,
                 config: Optional[AppConfig] = None):
        self.orchestrator = orchestrator
        self.export_manager = export_manager
        self.config = config or AppConfig.from_yaml()
        self.logger = logger.bind(component="workflow_controller")
        
        # Track all processed batches
        self.processed_batches: List[Batch] = []
    
    async def run_single_batch(self, batch_size: Optional[int] = None) -> Batch:
        """Run a single batch through the system"""
        self.logger.info("workflow_batch_started", batch_size=batch_size)
        
        try:
            # Process the batch
            batch = await self.orchestrator.process_batch(batch_size)
            
            # Store the batch
            self.processed_batches.append(batch)
            
            # Export if export manager is available
            if self.export_manager:
                await self._export_batch_results(batch)
            
            self.logger.info("workflow_batch_completed",
                           batch_id=batch.id,
                           approval_rate=batch.metrics.approval_rate)
            
            return batch
            
        except Exception as e:
            self.logger.error("workflow_batch_failed", error=str(e))
            raise
    
    async def run_multiple_batches(self, 
                                  num_batches: int,
                                  batch_size: Optional[int] = None,
                                  delay_seconds: float = 0) -> List[Batch]:
        """Run multiple batches with optional delay between them"""
        self.logger.info("workflow_multiple_batches_started",
                        num_batches=num_batches,
                        batch_size=batch_size)
        
        results = []
        
        for i in range(num_batches):
            self.logger.info("processing_batch_number",
                           batch_number=i+1,
                           total_batches=num_batches)
            
            batch = await self.run_single_batch(batch_size)
            results.append(batch)
            
            # Delay between batches if specified
            if delay_seconds > 0 and i < num_batches - 1:
                await asyncio.sleep(delay_seconds)
        
        # Generate summary report
        summary = self._generate_summary_report(results)
        self.logger.info("workflow_multiple_batches_completed", **summary)
        
        return results
    
    async def run_until_target(self,
                              target_approved_posts: int,
                              max_batches: int = 10,
                              batch_size: Optional[int] = None) -> List[Batch]:
        """Run batches until target number of approved posts is reached"""
        self.logger.info("workflow_target_mode_started",
                        target=target_approved_posts,
                        max_batches=max_batches)
        
        results = []
        total_approved = 0
        
        for i in range(max_batches):
            batch = await self.run_single_batch(batch_size)
            results.append(batch)
            
            total_approved += batch.metrics.approved_posts
            
            self.logger.info("workflow_target_progress",
                           current_approved=total_approved,
                           target=target_approved_posts,
                           batches_processed=i+1)
            
            if total_approved >= target_approved_posts:
                self.logger.info("workflow_target_reached",
                               total_approved=total_approved,
                               batches_used=i+1)
                break
        
        if total_approved < target_approved_posts:
            self.logger.warning("workflow_target_not_reached",
                              total_approved=total_approved,
                              target=target_approved_posts,
                              max_batches_reached=True)
        
        return results
    
    async def _export_batch_results(self, batch: Batch) -> None:
        """Export batch results to files"""
        try:
            # Export approved posts
            if batch.get_approved_posts():
                await self.export_manager.export_approved_posts(
                    batch.get_approved_posts(),
                    batch.id
                )
            
            # Export rejected posts for analysis
            if batch.get_rejected_posts():
                await self.export_manager.export_rejected_posts(
                    batch.get_rejected_posts(),
                    batch.id
                )
            
            # Export batch metrics
            await self.export_manager.export_batch_metrics(batch)
            
            self.logger.info("batch_exported",
                           batch_id=batch.id,
                           approved_count=len(batch.get_approved_posts()),
                           rejected_count=len(batch.get_rejected_posts()))
            
        except Exception as e:
            self.logger.error("batch_export_failed",
                            batch_id=batch.id,
                            error=str(e))
    
    def _generate_summary_report(self, batches: List[Batch]) -> Dict[str, Any]:
        """Generate a summary report for multiple batches"""
        total_posts = sum(b.metrics.total_posts for b in batches)
        total_approved = sum(b.metrics.approved_posts for b in batches)
        total_rejected = sum(b.metrics.rejected_posts for b in batches)
        total_revised = sum(b.metrics.revised_posts for b in batches)
        
        avg_approval_rate = total_approved / total_posts if total_posts > 0 else 0
        avg_revision_success = sum(b.metrics.revision_success_rate for b in batches) / len(batches) if batches else 0
        
        total_cost = sum(b.metrics.total_cost for b in batches)
        total_tokens = sum(b.metrics.total_tokens_used for b in batches)
        
        return {
            "num_batches": len(batches),
            "total_posts": total_posts,
            "total_approved": total_approved,
            "total_rejected": total_rejected,
            "total_revised": total_revised,
            "average_approval_rate": round(avg_approval_rate, 3),
            "average_revision_success_rate": round(avg_revision_success, 3),
            "total_cost": round(total_cost, 4),
            "total_tokens_used": total_tokens,
            "cost_per_approved_post": round(total_cost / total_approved, 4) if total_approved > 0 else 0
        }
    
    def get_all_approved_posts(self) -> List[LinkedInPost]:
        """Get all approved posts from all processed batches"""
        approved_posts = []
        for batch in self.processed_batches:
            approved_posts.extend(batch.get_approved_posts())
        return approved_posts
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics"""
        orchestrator_stats = self.orchestrator.get_statistics()
        
        if not self.processed_batches:
            return {
                "batches_processed": 0,
                "orchestrator_stats": orchestrator_stats
            }
        
        summary = self._generate_summary_report(self.processed_batches)
        
        return {
            "batches_processed": len(self.processed_batches),
            "summary": summary,
            "orchestrator_stats": orchestrator_stats,
            "average_processing_time": sum(
                b.metrics.average_processing_time for b in self.processed_batches
            ) / len(self.processed_batches)
        }
