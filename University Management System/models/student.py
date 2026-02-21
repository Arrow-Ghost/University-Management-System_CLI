"""
Student model representing student entity.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Student:
    """Student data model."""
    
    reg_no: str
    name: str
    password: str
    
    def __str__(self) -> str:
        return f"Student(reg_no={self.reg_no}, name={self.name})"
    
    def to_dict(self) -> dict:
        """Convert student to dictionary."""
        return {
            'reg_no': self.reg_no,
            'name': self.name
        }
