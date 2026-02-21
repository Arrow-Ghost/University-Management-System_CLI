"""
HOD service for managing feedback reviews and approvals.
"""

from typing import List, Optional, Tuple
from database.db_connection import DatabaseConnection
from repositories.database_operations import FeedbackRepository
from models.feedback import Feedback
from utils.validations import ValidationError, validate_status_transition


class HODService:
    """Service for handling HOD operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize HOD service.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.feedback_repo = FeedbackRepository(db)
    
    def get_all_feedbacks(self, filters: Optional[dict] = None) -> List[Feedback]:
        """
        Get all feedbacks with optional filters.
        
        Args:
            filters: Dictionary with filter criteria
            
        Returns:
            List of Feedback objects
        """
        return self.feedback_repo.get_all_feedbacks(filters)
    
    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """
        Get feedback by ID.
        
        Args:
            feedback_id: Feedback ID
            
        Returns:
            Feedback object or None
        """
        return self.feedback_repo.get_feedback_by_id(feedback_id)
    
    def approve_feedback(self, feedback_id: int, hod_comments: Optional[str] = None) -> Tuple[bool, str]:
        """
        Approve feedback by HOD.
        
        Args:
            feedback_id: Feedback ID
            hod_comments: HOD comments (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            feedback = self.feedback_repo.get_feedback_by_id(feedback_id)
            
            if not feedback:
                return False, "Feedback not found."
            
            # Validate status transition
            validate_status_transition(feedback.status, 'Approved')
            
            # Update feedback status
            self.feedback_repo.update_feedback_status(
                feedback_id,
                'Approved',
                hod_comments.strip() if hod_comments else None
            )
            
            return True, f"Feedback {feedback_id} approved successfully. It is now visible to faculty."
        
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error approving feedback: {str(e)}"
    
    def reject_feedback(self, feedback_id: int, hod_comments: Optional[str] = None) -> Tuple[bool, str]:
        """
        Reject feedback by HOD.
        
        Args:
            feedback_id: Feedback ID
            hod_comments: HOD comments explaining rejection (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            feedback = self.feedback_repo.get_feedback_by_id(feedback_id)
            
            if not feedback:
                return False, "Feedback not found."
            
            # Validate status transition
            validate_status_transition(feedback.status, 'Rejected')
            
            # Update feedback status
            self.feedback_repo.update_feedback_status(
                feedback_id,
                'Rejected',
                hod_comments.strip() if hod_comments else None
            )
            
            return True, f"Feedback {feedback_id} rejected. It will not be visible to faculty."
        
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error rejecting feedback: {str(e)}"
    
    def get_pending_feedbacks(self) -> List[Feedback]:
        """
        Get all feedbacks pending HOD review.
        
        Returns:
            List of pending Feedback objects
        """
        return self.feedback_repo.get_all_feedbacks({'status': 'Pending HOD Review'})
