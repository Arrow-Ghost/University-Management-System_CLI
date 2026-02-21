"""
Feedback model representing feedback entity.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Feedback:
    """Feedback data model."""
    
    feedback_id: Optional[int] = None
    reg_no: str = ""
    course_code: str = ""
    feedback_text: str = ""
    expectations: Optional[str] = None
    rating: Optional[int] = None
    status: str = "Pending HOD Review"
    hod_comments: Optional[str] = None
    faculty_response: Optional[str] = None
    action_taken: Optional[str] = None
    submission_date: Optional[str] = None
    action_date: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Feedback(id={self.feedback_id}, status={self.status}, course={self.course_code})"
    
    def to_dict(self) -> dict:
        """Convert feedback to dictionary."""
        return {
            'feedback_id': self.feedback_id,
            'reg_no': self.reg_no,
            'course_code': self.course_code,
            'feedback_text': self.feedback_text,
            'expectations': self.expectations,
            'rating': self.rating,
            'status': self.status,
            'hod_comments': self.hod_comments,
            'faculty_response': self.faculty_response,
            'action_taken': self.action_taken,
            'submission_date': self.submission_date,
            'action_date': self.action_date
        }
    
    @staticmethod
    def get_current_datetime() -> str:
        """Get current datetime as string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
