"""
Faculty model representing faculty entity.
"""

from dataclasses import dataclass


@dataclass
class Faculty:
    """Faculty data model."""
    
    employee_id: str
    faculty_name: str
    
    def __str__(self) -> str:
        return f"Faculty(employee_id={self.employee_id}, name={self.faculty_name})"
    
    def to_dict(self) -> dict:
        """Convert faculty to dictionary."""
        return {
            'employee_id': self.employee_id,
            'faculty_name': self.faculty_name
        }
