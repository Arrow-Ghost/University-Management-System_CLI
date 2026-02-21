"""
Validation utilities for input validation and business rules.
"""

import re
from typing import Optional


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_registration_number(reg_no: str) -> bool:
    """
    Validate student registration number format.
    
    Args:
        reg_no: Registration number to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If registration number is invalid
    """
    if not reg_no or not reg_no.strip():
        raise ValidationError("Registration number cannot be empty")
    
    if len(reg_no.strip()) < 3:
        raise ValidationError("Registration number must be at least 3 characters")
    
    return True


def validate_password(password: str) -> bool:
    """
    Validate password.
    
    Args:
        password: Password to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If password is invalid
    """
    if not password or not password.strip():
        raise ValidationError("Password cannot be empty")
    
    if len(password.strip()) < 4:
        raise ValidationError("Password must be at least 4 characters")
    
    return True


def validate_employee_id(employee_id: str) -> bool:
    """
    Validate faculty employee ID.
    
    Args:
        employee_id: Employee ID to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If employee ID is invalid
    """
    if not employee_id or not employee_id.strip():
        raise ValidationError("Employee ID cannot be empty")
    
    return True


def validate_feedback_text(feedback_text: str) -> bool:
    """
    Validate feedback text.
    
    Args:
        feedback_text: Feedback text to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If feedback text is invalid
    """
    if not feedback_text or not feedback_text.strip():
        raise ValidationError("Feedback text cannot be empty")
    
    if len(feedback_text.strip()) < 10:
        raise ValidationError("Feedback text must be at least 10 characters")
    
    return True


def validate_rating(rating: Optional[int]) -> bool:
    """
    Validate rating value.
    
    Args:
        rating: Rating value (1-5) or None
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If rating is invalid
    """
    if rating is None:
        return True  # Rating is optional
    
    if not isinstance(rating, int):
        raise ValidationError("Rating must be an integer")
    
    if rating < 1 or rating > 5:
        raise ValidationError("Rating must be between 1 and 5")
    
    return True


def validate_course_code(course_code: str) -> bool:
    """
    Validate course code format.
    
    Args:
        course_code: Course code to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If course code is invalid
    """
    if not course_code or not course_code.strip():
        raise ValidationError("Course code cannot be empty")
    
    return True


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validate status transition according to workflow rules.
    
    Args:
        current_status: Current feedback status
        new_status: New status to transition to
        
    Returns:
        True if transition is valid
        
    Raises:
        ValidationError: If transition is invalid
    """
    valid_transitions = {
        'Pending HOD Review': ['Approved', 'Rejected'],
        'Approved': ['Faculty Responded'],
        'Rejected': [],  # Cannot transition from rejected
        'Faculty Responded': []  # Final state
    }
    
    if current_status not in valid_transitions:
        raise ValidationError(f"Invalid current status: {current_status}")
    
    if new_status not in valid_transitions[current_status]:
        raise ValidationError(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Valid transitions: {valid_transitions[current_status]}"
        )
    
    return True
