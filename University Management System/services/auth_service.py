"""
Authentication service for user login and session management.
"""

from typing import Optional, Tuple
from database.db_connection import DatabaseConnection
from repositories.database_operations import StudentRepository, FacultyRepository
from models.student import Student
from models.faculty import Faculty
from utils.validations import ValidationError, validate_registration_number, validate_password, validate_employee_id


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize authentication service.
        
        Args:
            db: Database connection instance
        """
        self.db = db
        self.student_repo = StudentRepository(db)
        self.faculty_repo = FacultyRepository(db)
        self.current_user: Optional[dict] = None
    
    def login_student(self, reg_no: str, password: str) -> Tuple[bool, Optional[Student], str]:
        """
        Authenticate student login.
        
        Args:
            reg_no: Registration number
            password: Password
            
        Returns:
            Tuple of (success, student_object, message)
        """
        try:
            validate_registration_number(reg_no)
            validate_password(password)
            
            student = self.student_repo.authenticate_student(reg_no.strip(), password.strip())
            
            if student:
                self.current_user = {
                    'type': 'student',
                    'reg_no': student.reg_no,
                    'name': student.name
                }
                return True, student, f"Welcome, {student.name}!"
            else:
                return False, None, "Invalid registration number or password."
        
        except ValidationError as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, f"Login error: {str(e)}"
    
    def login_faculty(self, employee_id: str) -> Tuple[bool, Optional[Faculty], str]:
        """
        Authenticate faculty login.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Tuple of (success, faculty_object, message)
        """
        try:
            validate_employee_id(employee_id)
            
            faculty = self.faculty_repo.authenticate_faculty(employee_id.strip())
            
            if faculty:
                self.current_user = {
                    'type': 'faculty',
                    'employee_id': faculty.employee_id,
                    'name': faculty.faculty_name
                }
                return True, faculty, f"Welcome, {faculty.faculty_name}!"
            else:
                return False, None, "Invalid employee ID."
        
        except ValidationError as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, f"Login error: {str(e)}"
    
    def login_hod(self) -> Tuple[bool, dict, str]:
        """
        Authenticate HOD login (simplified - no password for now).
        HOD is a special role with full access.
        
        Returns:
            Tuple of (success, hod_info, message)
        """
        self.current_user = {
            'type': 'hod',
            'name': 'Head of Department'
        }
        return True, self.current_user, "Welcome, HOD!"
    
    def logout(self) -> None:
        """Logout current user."""
        self.current_user = None
    
    def get_current_user(self) -> Optional[dict]:
        """
        Get current logged-in user information.
        
        Returns:
            Dictionary with user info or None
        """
        return self.current_user
