"""
Report service for generating Action Taken Reports (ATR).
"""

from typing import List, Optional
from database.db_connection import DatabaseConnection
from repositories.database_operations import FeedbackRepository
from models.feedback import Feedback


class ReportService:
    """Service for generating reports."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize report service.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.feedback_repo = FeedbackRepository(db)
    
    def get_atr_data(self, filters: Optional[dict] = None) -> List[dict]:
        """
        Get Action Taken Report data with complete information.
        
        Args:
            filters: Optional filters (course_code, employee_id, etc.)
            
        Returns:
            List of dictionaries containing ATR data
        """
        # Get feedbacks that have been responded to by faculty
        feedbacks = self.feedback_repo.get_all_feedbacks(filters)
        
        # Filter only those with faculty responses
        responded_feedbacks = [f for f in feedbacks if f.status == 'Faculty Responded']
        
        atr_data = []
        
        for feedback in responded_feedbacks:
            # Get course and faculty information
            course_query = """
                SELECT c.course_code, c.course_title, c.faculty_employee_id,
                       f.faculty_name
                FROM Courses c
                JOIN Faculty f ON c.faculty_employee_id = f.employee_id
                WHERE c.course_code = ?
            """
            course_row = self.db.fetch_one(course_query, (feedback.course_code,))
            
            # Get student information
            student_query = "SELECT name FROM Students WHERE reg_no = ?"
            student_row = self.db.fetch_one(student_query, (feedback.reg_no,))
            
            if course_row and student_row:
                atr_data.append({
                    'feedback_id': feedback.feedback_id,
                    'course_code': feedback.course_code,
                    'course_title': course_row['course_title'],
                    'faculty_name': course_row['faculty_name'],
                    'student_name': student_row['name'],
                    'student_reg_no': feedback.reg_no,
                    'feedback_text': feedback.feedback_text,
                    'expectations': feedback.expectations,
                    'rating': feedback.rating,
                    'hod_comments': feedback.hod_comments,
                    'faculty_response': feedback.faculty_response,
                    'action_taken': feedback.action_taken,
                    'submission_date': feedback.submission_date,
                    'action_date': feedback.action_date
                })
        
        return atr_data
    
    def get_all_atr_data(self) -> List[dict]:
        """
        Get all ATR data (no filters).
        
        Returns:
            List of dictionaries containing ATR data
        """
        return self.get_atr_data()
    
    def get_atr_by_course(self, course_code: str) -> List[dict]:
        """
        Get ATR data filtered by course.
        
        Args:
            course_code: Course code
            
        Returns:
            List of dictionaries containing ATR data
        """
        return self.get_atr_data({'course_code': course_code})
    
    def get_atr_by_faculty(self, employee_id: str) -> List[dict]:
        """
        Get ATR data filtered by faculty.
        
        Args:
            employee_id: Faculty employee ID
            
        Returns:
            List of dictionaries containing ATR data
        """
        return self.get_atr_data({'employee_id': employee_id})
