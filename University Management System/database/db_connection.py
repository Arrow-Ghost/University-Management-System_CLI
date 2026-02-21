"""
Database connection module for SQLite database.
Handles database initialization and connection management.
"""

import sqlite3
import os
from typing import Optional


class DatabaseConnection:
    """Manages SQLite database connections and initialization."""
    
    def __init__(self, db_path: str = "university_management.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection.
        
        Returns:
            SQLite connection object
        """
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
        return self.connection
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Cursor object with results
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor
    
    def execute_many(self, query: str, params_list: list) -> None:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Fetch a single row from database.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Single row or None if not found
        """
        cursor = self.execute_query(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = ()) -> list:
        """
        Fetch all rows from database.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            List of rows
        """
        cursor = self.execute_query(query, params)
        return cursor.fetchall()
    
    def __enter__(self):
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def initialize_database() -> None:
    """
    Initialize database schema with all required tables.
    Creates tables if they don't exist.
    """
    db = DatabaseConnection()
    
    # Create Students table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS Students (
            reg_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Create Faculty table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS Faculty (
            employee_id TEXT PRIMARY KEY,
            faculty_name TEXT NOT NULL
        )
    """)
    
    # Create Courses table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS Courses (
            course_code TEXT PRIMARY KEY,
            course_title TEXT NOT NULL,
            faculty_employee_id TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            class_slot_duration INTEGER DEFAULT 50,
            FOREIGN KEY (faculty_employee_id) REFERENCES Faculty(employee_id)
        )
    """)
    
    # Create Feedback table
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS Feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT NOT NULL,
            course_code TEXT NOT NULL,
            feedback_text TEXT NOT NULL,
            expectations TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            status TEXT NOT NULL DEFAULT 'Pending HOD Review',
            hod_comments TEXT,
            faculty_response TEXT,
            action_taken TEXT,
            submission_date TEXT NOT NULL,
            action_date TEXT,
            FOREIGN KEY (reg_no) REFERENCES Students(reg_no),
            FOREIGN KEY (course_code) REFERENCES Courses(course_code),
            CHECK(status IN ('Pending HOD Review', 'Approved', 'Rejected', 'Faculty Responded'))
        )
    """)
    
    # Create index for faster lookups
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_feedback_reg_no 
        ON Feedback(reg_no)
    """)
    
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_feedback_course_code 
        ON Feedback(course_code)
    """)
    
    db.execute_query("""
        CREATE INDEX IF NOT EXISTS idx_feedback_status 
        ON Feedback(status)
    """)
    
    db.close()
    print("Database initialized successfully!")
