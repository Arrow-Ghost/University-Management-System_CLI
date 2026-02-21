"""
Course model representing course entity.
"""

from dataclasses import dataclass


@dataclass
class Course:
    """Course data model."""
    
    course_code: str
    course_title: str
    faculty_employee_id: str
    time_slot: str
    class_slot_duration: int = 50
    
    def __str__(self) -> str:
        return f"Course(code={self.course_code}, title={self.course_title})"
    
    def to_dict(self) -> dict:
        """Convert course to dictionary."""
        return {
            'course_code': self.course_code,
            'course_title': self.course_title,
            'faculty_employee_id': self.faculty_employee_id,
            'time_slot': self.time_slot,
            'class_slot_duration': self.class_slot_duration
        }
