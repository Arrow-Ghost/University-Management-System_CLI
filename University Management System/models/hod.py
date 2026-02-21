"""
HOD (Head of Department) model.
Note: HOD is a special role, not a separate entity in the database.
This module provides HOD-related data structures.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HODReview:
    """HOD review decision data model."""
    
    feedback_id: int
    decision: str  # 'Approved' or 'Rejected'
    comments: Optional[str] = None
    
    def __str__(self) -> str:
        return f"HODReview(feedback_id={self.feedback_id}, decision={self.decision})"
