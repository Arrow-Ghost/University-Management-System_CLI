"""
Repository layer for database operations.
Provides abstraction for all database queries.
"""

from typing import Optional, List
from database.db_connection import DatabaseConnection
from models.student import Student
from models.faculty import Faculty
from models.course import Course
from models.feedback import Feedback


class StudentRepository:
    """Repository for student-related database operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize student repository.
        
        Args:
            db: Database connection instance
        """
        self.db = db
    
    def get_student_by_reg_no(self, reg_no: str) -> Optional[Student]:
        """
        Get student by registration number.
        
        Args:
            reg_no: Registration number
            
        Returns:
            Student object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT reg_no, name, password FROM Students WHERE reg_no = ?",
            (reg_no,)
        )
        
        if row:
            return Student(
                reg_no=row['reg_no'],
                name=row['name'],
                password=row['password']
            )
        return None
    
    def authenticate_student(self, reg_no: str, password: str) -> Optional[Student]:
        """
        Authenticate student login.
        
        Args:
            reg_no: Registration number
            password: Password
            
        Returns:
            Student object if authenticated, None otherwise
        """
        student = self.get_student_by_reg_no(reg_no)
        if student and student.password == password:
            return student
        return None
    
    def get_student_courses(self, reg_no: str) -> List[dict]:
        """
        Get all courses for a student.
        
        Args:
            reg_no: Registration number
            
        Returns:
            List of course dictionaries with faculty information
        """
        query = """
            SELECT 
                c.course_code,
                c.course_title,
                c.faculty_employee_id,
                f.faculty_name,
                c.time_slot,
                c.class_slot_duration
            FROM Courses c
            JOIN Faculty f ON c.faculty_employee_id = f.employee_id
            ORDER BY c.course_code
        """
        rows = self.db.fetch_all(query)
        return [dict(row) for row in rows]


class FacultyRepository:
    """Repository for faculty-related database operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize faculty repository.
        
        Args:
            db: Database connection instance
        """
        self.db = db
    
    def get_faculty_by_employee_id(self, employee_id: str) -> Optional[Faculty]:
        """
        Get faculty by employee ID.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Faculty object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT employee_id, faculty_name FROM Faculty WHERE employee_id = ?",
            (employee_id,)
        )
        
        if row:
            return Faculty(
                employee_id=row['employee_id'],
                faculty_name=row['faculty_name']
            )
        return None
    
    def authenticate_faculty(self, employee_id: str) -> Optional[Faculty]:
        """
        Authenticate faculty login (simplified - no password for now).
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Faculty object if found, None otherwise
        """
        return self.get_faculty_by_employee_id(employee_id)
    
    def get_faculty_courses(self, employee_id: str) -> List[dict]:
        """
        Get all courses taught by a faculty.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            List of course dictionaries
        """
        query = """
            SELECT 
                course_code,
                course_title,
                faculty_employee_id,
                time_slot,
                class_slot_duration
            FROM Courses
            WHERE faculty_employee_id = ?
            ORDER BY course_code
        """
        rows = self.db.fetch_all(query, (employee_id,))
        return [dict(row) for row in rows]


class CourseRepository:
    """Repository for course-related database operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize course repository.
        
        Args:
            db: Database connection instance
        """
        self.db = db
    
    def get_course_by_code(self, course_code: str) -> Optional[Course]:
        """
        Get course by course code.
        
        Args:
            course_code: Course code
            
        Returns:
            Course object or None if not found
        """
        row = self.db.fetch_one(
            """SELECT course_code, course_title, faculty_employee_id, 
               time_slot, class_slot_duration 
               FROM Courses WHERE course_code = ?""",
            (course_code,)
        )
        
        if row:
            return Course(
                course_code=row['course_code'],
                course_title=row['course_title'],
                faculty_employee_id=row['faculty_employee_id'],
                time_slot=row['time_slot'],
                class_slot_duration=row['class_slot_duration']
            )
        return None
    
    def get_all_courses(self) -> List[Course]:
        """
        Get all courses.
        
        Returns:
            List of Course objects
        """
        rows = self.db.fetch_all("SELECT * FROM Courses ORDER BY course_code")
        return [
            Course(
                course_code=row['course_code'],
                course_title=row['course_title'],
                faculty_employee_id=row['faculty_employee_id'],
                time_slot=row['time_slot'],
                class_slot_duration=row['class_slot_duration']
            )
            for row in rows
        ]


class FeedbackRepository:
    """Repository for feedback-related database operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize feedback repository.
        
        Args:
            db: Database connection instance
        """
        self.db = db
    
    def create_feedback(self, feedback: Feedback) -> int:
        """
        Create new feedback entry.
        
        Args:
            feedback: Feedback object
            
        Returns:
            Feedback ID of created entry
        """
        query = """
            INSERT INTO Feedback 
            (reg_no, course_code, feedback_text, expectations, rating, 
             status, submission_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute_query(
            query,
            (
                feedback.reg_no,
                feedback.course_code,
                feedback.feedback_text,
                feedback.expectations,
                feedback.rating,
                feedback.status,
                feedback.submission_date
            )
        )
        return cursor.lastrowid
    
    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """
        Get feedback by ID.
        
        Args:
            feedback_id: Feedback ID
            
        Returns:
            Feedback object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM Feedback WHERE feedback_id = ?",
            (feedback_id,)
        )
        
        if row:
            return self._row_to_feedback(row)
        return None
    
    def get_feedback_by_student_and_course(self, reg_no: str, course_code: str) -> Optional[Feedback]:
        """
        Get feedback by student and course (for duplicate check).
        
        Args:
            reg_no: Registration number
            course_code: Course code
            
        Returns:
            Feedback object or None if not found
        """
        row = self.db.fetch_one(
            "SELECT * FROM Feedback WHERE reg_no = ? AND course_code = ?",
            (reg_no, course_code)
        )
        
        if row:
            return self._row_to_feedback(row)
        return None
    
    def get_student_feedbacks(self, reg_no: str) -> List[Feedback]:
        """
        Get all feedbacks submitted by a student.
        
        Args:
            reg_no: Registration number
            
        Returns:
            List of Feedback objects
        """
        rows = self.db.fetch_all(
            "SELECT * FROM Feedback WHERE reg_no = ? ORDER BY submission_date DESC",
            (reg_no,)
        )
        return [self._row_to_feedback(row) for row in rows]
    
    def get_all_feedbacks(self, filters: Optional[dict] = None) -> List[Feedback]:
        """
        Get all feedbacks with optional filters.
        
        Args:
            filters: Dictionary with filter criteria (course_code, employee_id, status, etc.)
            
        Returns:
            List of Feedback objects
        """
        query = "SELECT * FROM Feedback WHERE 1=1"
        params = []
        
        if filters:
            if 'course_code' in filters:
                query += " AND course_code = ?"
                params.append(filters['course_code'])
            
            if 'status' in filters:
                query += " AND status = ?"
                params.append(filters['status'])
            
            if 'employee_id' in filters:
                query += """ AND course_code IN 
                    (SELECT course_code FROM Courses WHERE faculty_employee_id = ?)"""
                params.append(filters['employee_id'])
            
            if 'reg_no' in filters:
                query += " AND reg_no = ?"
                params.append(filters['reg_no'])
        
        query += " ORDER BY submission_date DESC"
        
        rows = self.db.fetch_all(query, tuple(params))
        return [self._row_to_feedback(row) for row in rows]
    
    def get_approved_feedbacks_for_faculty(self, employee_id: str) -> List[Feedback]:
        """
        Get approved feedbacks for a faculty member.
        
        Args:
            employee_id: Faculty employee ID
            
        Returns:
            List of approved Feedback objects
        """
        query = """
            SELECT f.* FROM Feedback f
            JOIN Courses c ON f.course_code = c.course_code
            WHERE c.faculty_employee_id = ? AND f.status = 'Approved'
            ORDER BY f.submission_date DESC
        """
        rows = self.db.fetch_all(query, (employee_id,))
        return [self._row_to_feedback(row) for row in rows]
    
    def update_feedback_status(self, feedback_id: int, status: str, 
                               hod_comments: Optional[str] = None) -> bool:
        """
        Update feedback status (for HOD approval/rejection).
        
        Args:
            feedback_id: Feedback ID
            status: New status
            hod_comments: HOD comments (optional)
            
        Returns:
            True if updated successfully
        """
        query = """
            UPDATE Feedback 
            SET status = ?, hod_comments = ?
            WHERE feedback_id = ?
        """
        self.db.execute_query(query, (status, hod_comments, feedback_id))
        return True
    
    def update_faculty_response(self, feedback_id: int, faculty_response: str, 
                                action_taken: str) -> bool:
        """
        Update feedback with faculty response.
        
        Args:
            feedback_id: Feedback ID
            faculty_response: Faculty response text
            action_taken: Action taken description
            
        Returns:
            True if updated successfully
        """
        query = """
            UPDATE Feedback 
            SET faculty_response = ?, action_taken = ?, 
                action_date = ?, status = 'Faculty Responded'
            WHERE feedback_id = ?
        """
        from models.feedback import Feedback as FeedbackModel
        action_date = FeedbackModel.get_current_datetime()
        
        self.db.execute_query(
            query,
            (faculty_response, action_taken, action_date, feedback_id)
        )
        return True
    
    def _row_to_feedback(self, row) -> Feedback:
        """Convert database row to Feedback object."""
        return Feedback(
            feedback_id=row['feedback_id'],
            reg_no=row['reg_no'],
            course_code=row['course_code'],
            feedback_text=row['feedback_text'],
            expectations=row['expectations'],
            rating=row['rating'],
            status=row['status'],
            hod_comments=row['hod_comments'],
            faculty_response=row['faculty_response'],
            action_taken=row['action_taken'],
            submission_date=row['submission_date'],
            action_date=row['action_date']
        )
