"""
Faculty service for managing faculty responses to feedback.
"""

from typing import List, Optional, Tuple
from database.db_connection import DatabaseConnection
from repositories.database_operations import FeedbackRepository, FacultyRepository
from models.feedback import Feedback


class FacultyService:
    """Service for handling faculty operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize faculty service.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.feedback_repo = FeedbackRepository(db)
        self.faculty_repo = FacultyRepository(db)
    
    def get_approved_feedbacks(self, employee_id: str) -> List[Feedback]:
        """
        Get all approved feedbacks for a faculty member.
        Faculty can only see approved feedbacks.
        
        Args:
            employee_id: Faculty employee ID
            
        Returns:
            List of approved Feedback objects
        """
        return self.feedback_repo.get_approved_feedbacks_for_faculty(employee_id)
    
    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """
        Get feedback by ID.
        
        Args:
            feedback_id: Feedback ID
            
        Returns:
            Feedback object or None
        """
        return self.feedback_repo.get_feedback_by_id(feedback_id)
    
    def submit_response(self, feedback_id: int, faculty_response: str, 
                       action_taken: str) -> Tuple[bool, str]:
        """
        Submit faculty response to approved feedback.
        
        Args:
            feedback_id: Feedback ID
            faculty_response: Faculty response text
            action_taken: Description of corrective action taken
            
        Returns:
            Tuple of (success, message)
        """
        try:
            feedback = self.feedback_repo.get_feedback_by_id(feedback_id)
            
            if not feedback:
                return False, "Feedback not found."
            
            if feedback.status != 'Approved':
                return False, f"Cannot respond to feedback with status '{feedback.status}'. Only approved feedbacks can be responded to."
            
            if not faculty_response or not faculty_response.strip():
                return False, "Faculty response cannot be empty."
            
            if not action_taken or not action_taken.strip():
                return False, "Action taken description cannot be empty."
            
            # Update feedback with faculty response
            self.feedback_repo.update_faculty_response(
                feedback_id,
                faculty_response.strip(),
                action_taken.strip()
            )
            
            return True, f"Response submitted successfully for feedback {feedback_id}. Status updated to 'Faculty Responded'."
        
        except Exception as e:
            return False, f"Error submitting response: {str(e)}"
    
    def get_faculty_courses(self, employee_id: str) -> List[dict]:
        """
        Get all courses taught by faculty.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            List of course dictionaries
        """
        return self.faculty_repo.get_faculty_courses(employee_id)
