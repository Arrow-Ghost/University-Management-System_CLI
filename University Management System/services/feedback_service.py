"""
Feedback service for managing feedback submissions and operations.
"""

from typing import List, Optional, Tuple
from database.db_connection import DatabaseConnection
from repositories.database_operations import FeedbackRepository, StudentRepository
from models.feedback import Feedback
from utils.validations import (
    ValidationError, validate_feedback_text, validate_rating, 
    validate_course_code
)


class FeedbackService:
    """Service for handling feedback operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize feedback service.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.feedback_repo = FeedbackRepository(db)
        self.student_repo = StudentRepository(db)
    
    def submit_feedback(self, reg_no: str, course_code: str, feedback_text: str,
                       expectations: Optional[str] = None, rating: Optional[int] = None) -> Tuple[bool, str]:
        """
        Submit new feedback from student.
        
        Args:
            reg_no: Registration number
            course_code: Course code
            feedback_text: Feedback text
            expectations: Student expectations (optional)
            rating: Rating 1-5 (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate inputs
            validate_feedback_text(feedback_text)
            validate_course_code(course_code)
            if rating is not None:
                validate_rating(rating)
            
            # Check for duplicate submission
            existing = self.feedback_repo.get_feedback_by_student_and_course(reg_no, course_code)
            if existing:
                return False, "You have already submitted feedback for this course. Only one submission per course is allowed."
            
            # Create feedback object
            feedback = Feedback(
                reg_no=reg_no.strip(),
                course_code=course_code.strip(),
                feedback_text=feedback_text.strip(),
                expectations=expectations.strip() if expectations else None,
                rating=rating,
                status="Pending HOD Review",
                submission_date=Feedback.get_current_datetime()
            )
            
            # Save to database
            feedback_id = self.feedback_repo.create_feedback(feedback)
            
            return True, f"Feedback submitted successfully! Feedback ID: {feedback_id}"
        
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error submitting feedback: {str(e)}"
    
    def get_student_feedbacks(self, reg_no: str) -> List[Feedback]:
        """
        Get all feedbacks submitted by a student.
        
        Args:
            reg_no: Registration number
            
        Returns:
            List of Feedback objects
        """
        return self.feedback_repo.get_student_feedbacks(reg_no)
    
    def get_feedback_details(self, feedback_id: int) -> Optional[Feedback]:
        """
        Get detailed feedback information.
        
        Args:
            feedback_id: Feedback ID
            
        Returns:
            Feedback object or None
        """
        return self.feedback_repo.get_feedback_by_id(feedback_id)
    
    def can_student_submit_feedback(self, reg_no: str, course_code: str) -> Tuple[bool, str]:
        """
        Check if student can submit feedback for a course.
        
        Args:
            reg_no: Registration number
            course_code: Course code
            
        Returns:
            Tuple of (can_submit, message)
        """
        existing = self.feedback_repo.get_feedback_by_student_and_course(reg_no, course_code)
        if existing:
            return False, f"You have already submitted feedback for {course_code}. Status: {existing.status}"
        return True, "You can submit feedback for this course."
