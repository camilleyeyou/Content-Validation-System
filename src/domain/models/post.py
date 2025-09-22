from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, validator, ConfigDict

class PostStatus(Enum):
    """Post lifecycle states"""
    GENERATED = "generated"
    VALIDATING = "validating"
    APPROVED = "approved"
    REVISION_NEEDED = "revision_needed"
    REVISED = "revised"
    REJECTED = "rejected"

class ValidationScore(BaseModel):
    """Validation result from an agent"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    agent_name: str
    score: float = Field(ge=0, le=10)
    approved: bool
    feedback: Optional[str] = None
    criteria_breakdown: Dict[str, Any] = Field(default_factory=dict)  # Changed from Dict[str, float] to Dict[str, Any]
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('approved')
    def validate_approval(cls, v, values):
        """Ensure approval aligns with score threshold"""
        if 'score' in values:
            return values['score'] >= 7.0
        return False

class CulturalReference(BaseModel):
    """Track cultural references used in posts"""
    category: str  # 'tv_show', 'workplace', 'seasonal', 'quote'
    reference: str  # 'The Office', 'Zoom fatigue', etc.
    context: str  # How it was used

class LinkedInPost(BaseModel):
    """Core post model with full lifecycle tracking"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid4()))
    batch_id: str
    post_number: int
    
    # Content
    content: str = Field(min_length=50, max_length=3000)
    hook: Optional[str] = None  # Opening line
    hashtags: List[str] = Field(default_factory=list, max_items=10)
    
    # Targeting
    target_audience: str
    cultural_reference: Optional[CulturalReference] = None
    
    # Status tracking
    status: PostStatus = PostStatus.GENERATED
    validation_scores: List[ValidationScore] = Field(default_factory=list)
    revision_count: int = 0
    max_revisions: int = 2
    
    # History
    original_content: Optional[str] = None
    revision_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: Optional[float] = None
    total_tokens_used: int = 0
    estimated_cost: float = 0.0
    
    @property
    def average_score(self) -> float:
        """Calculate average validation score"""
        if not self.validation_scores:
            return 0.0
        return sum(s.score for s in self.validation_scores) / len(self.validation_scores)
    
    @property
    def approval_count(self) -> int:
        """Count number of approvals"""
        return sum(1 for s in self.validation_scores if s.approved)
    
    def is_approved(self, min_approvals: int = 2) -> bool:
        """Check if post meets approval threshold"""
        return self.approval_count >= min_approvals
    
    def can_revise(self) -> bool:
        """Check if post can still be revised"""
        return self.revision_count < self.max_revisions
    
    def add_validation(self, score: ValidationScore) -> None:
        """Add a validation score and update status"""
        self.validation_scores.append(score)
        self.updated_at = datetime.utcnow()
    
    def create_revision(self, new_content: str) -> None:
        """Create a revision of the post"""
        if self.original_content is None:
            self.original_content = self.content
        
        self.revision_history.append({
            "revision_number": self.revision_count,
            "previous_content": self.content,
            "timestamp": datetime.utcnow().isoformat(),
            "average_score_before": self.average_score
        })
        
        self.content = new_content
        self.revision_count += 1
        self.status = PostStatus.REVISED
        self.validation_scores = []  # Clear for re-validation
        self.updated_at = datetime.utcnow()
