"""
Data seeder script to populate database with sample data.
Run this script to initialize the database with test data.
"""

from database.db_connection import DatabaseConnection, initialize_database


def seed_database():
    """Seed database with sample data."""
    # Initialize database schema
    initialize_database()
    
    db = DatabaseConnection()
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        db.execute_query("DELETE FROM Feedback")
        db.execute_query("DELETE FROM Courses")
        db.execute_query("DELETE FROM Students")
        db.execute_query("DELETE FROM Faculty")
        
        # Insert Sample Students
        print("Inserting sample students...")
        students_data = [
            ("STU001", "John Doe", "password123"),
            ("STU002", "Jane Smith", "password123"),
            ("STU003", "Bob Johnson", "password123"),
            ("STU004", "Alice Williams", "password123"),
            ("STU005", "Charlie Brown", "password123"),
        ]
        db.execute_many(
            "INSERT INTO Students (reg_no, name, password) VALUES (?, ?, ?)",
            students_data
        )
        
        # Insert Sample Faculty
        print("Inserting sample faculty...")
        faculty_data = [
            ("FAC001", "Dr. Sarah Anderson"),
            ("FAC002", "Prof. Michael Chen"),
            ("FAC003", "Dr. Emily Davis"),
            ("FAC004", "Prof. Robert Wilson"),
        ]
        db.execute_many(
            "INSERT INTO Faculty (employee_id, faculty_name) VALUES (?, ?)",
            faculty_data
        )
        
        # Insert Sample Courses
        print("Inserting sample courses...")
        courses_data = [
            ("CS101", "Introduction to Computer Science", "FAC001", "Mon 09:00-09:50", 50),
            ("CS201", "Data Structures", "FAC001", "Wed 10:00-10:50", 50),
            ("CS301", "Database Systems", "FAC002", "Tue 11:00-11:50", 50),
            ("CS302", "Software Engineering", "FAC002", "Thu 14:00-14:50", 50),
            ("MATH101", "Calculus I", "FAC003", "Mon 13:00-13:50", 50),
            ("MATH201", "Linear Algebra", "FAC003", "Wed 15:00-15:50", 50),
            ("PHYS101", "Physics Fundamentals", "FAC004", "Tue 09:00-09:50", 50),
        ]
        db.execute_many(
            """INSERT INTO Courses 
               (course_code, course_title, faculty_employee_id, time_slot, class_slot_duration) 
               VALUES (?, ?, ?, ?, ?)""",
            courses_data
        )
        
        # Insert Sample Feedback (some already approved for testing)
        print("Inserting sample feedback...")
        from models.feedback import Feedback
        
        feedbacks_data = [
            (
                "STU001", "CS101", 
                "The course content is well-structured and the professor explains concepts clearly. However, I would appreciate more practical examples.",
                "I expect more hands-on coding exercises and assignments.",
                4,
                "Approved",
                "Good feedback. Will discuss with faculty.",
                "Thank you for your feedback. We will add more practical examples in the next session.",
                "Added 3 new coding exercises to the course material.",
                Feedback.get_current_datetime(),
                Feedback.get_current_datetime()
            ),
            (
                "STU002", "CS201",
                "Data Structures course is challenging but interesting. The assignments help in understanding the concepts better.",
                "More practice problems would be helpful.",
                5,
                "Faculty Responded",
                "Approved. Faculty will add more problems.",
                "We have added 10 additional practice problems to the course portal.",
                "Updated course portal with new practice problems and solutions.",
                Feedback.get_current_datetime(),
                Feedback.get_current_datetime()
            ),
            (
                "STU003", "CS301",
                "Database Systems course covers important topics. The SQL practice sessions are very useful.",
                "Would like more real-world database design examples.",
                4,
                "Pending HOD Review",
                None,
                None,
                None,
                Feedback.get_current_datetime(),
                None
            ),
            (
                "STU004", "MATH101",
                "Calculus course is well-taught. The professor is very patient and explains step-by-step.",
                "More solved examples in class would be beneficial.",
                5,
                "Approved",
                "Approved. Faculty will incorporate more examples.",
                None,
                None,
                Feedback.get_current_datetime(),
                None
            ),
            (
                "STU005", "PHYS101",
                "Physics fundamentals course is interesting. The lab sessions complement the theory well.",
                "Would appreciate more visual demonstrations.",
                4,
                "Rejected",
                "Feedback does not meet the minimum requirements.",
                None,
                None,
                Feedback.get_current_datetime(),
                None
            ),
        ]
        
        db.execute_many(
            """INSERT INTO Feedback 
               (reg_no, course_code, feedback_text, expectations, rating, status,
                hod_comments, faculty_response, action_taken, submission_date, action_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            feedbacks_data
        )
        
        print("\n" + "=" * 60)
        print("Database seeded successfully!")
        print("=" * 60)
        print("\nSample Login Credentials:")
        print("-" * 60)
        print("Students:")
        print("  Registration Number: STU001, Password: password123")
        print("  Registration Number: STU002, Password: password123")
        print("  Registration Number: STU003, Password: password123")
        print("\nFaculty:")
        print("  Employee ID: FAC001")
        print("  Employee ID: FAC002")
        print("\nHOD:")
        print("  (No password required - select option 2 from main menu)")
        print("=" * 60)
    
    except Exception as e:
        print(f"\nError seeding database: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
