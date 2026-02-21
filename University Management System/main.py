"""
Main entry point for Student Feedback & Action Taken Report (ATR) Management System.
Provides menu-driven CLI interface for all user roles.
"""

import os
import sys
from database.db_connection import DatabaseConnection, initialize_database
from services.auth_service import AuthService
from services.feedback_service import FeedbackService
from services.hod_service import HODService
from services.faculty_service import FacultyService
from services.report_service import ReportService
from repositories.database_operations import StudentRepository
from reports.export_utils import display_atr_console, export_to_pdf, export_to_excel, ExportError


class CLIMenu:
    """CLI menu interface for the system."""
    
    def __init__(self):
        """Initialize CLI menu with database and services."""
        # Initialize database
        initialize_database()
        
        # Create database connection
        self.db = DatabaseConnection()
        
        # Initialize services
        self.auth_service = AuthService(self.db)
        self.feedback_service = FeedbackService(self.db)
        self.hod_service = HODService(self.db)
        self.faculty_service = FacultyService(self.db)
        self.report_service = ReportService(self.db)
        self.student_repo = StudentRepository(self.db)
    
    def clear_screen(self):
        """Clear console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_main_menu(self):
        """Display main menu options."""
        print("\n" + "=" * 60)
        print("STUDENT FEEDBACK & ACTION TAKEN REPORT (ATR) MANAGEMENT SYSTEM")
        print("=" * 60)
        print("\nMain Menu:")
        print("1. Student Login")
        print("2. HOD Login")
        print("3. Faculty Login")
        print("4. Generate Reports")
        print("5. Exit")
        print("=" * 60)
    
    def student_dashboard(self, student):
        """Student dashboard menu."""
        while True:
            print("\n" + "=" * 60)
            print(f"STUDENT DASHBOARD - Welcome, {student.name}!")
            print("=" * 60)
            print("\nOptions:")
            print("1. View My Courses")
            print("2. Submit Feedback")
            print("3. View My Feedback Submissions")
            print("4. Logout")
            print("=" * 60)
            
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '1':
                self.view_student_courses(student.reg_no)
            elif choice == '2':
                self.submit_feedback(student.reg_no)
            elif choice == '3':
                self.view_student_feedbacks(student.reg_no)
            elif choice == '4':
                self.auth_service.logout()
                print("\nLogged out successfully!")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def view_student_courses(self, reg_no: str):
        """Display student's registered courses."""
        print("\n" + "-" * 60)
        print("MY COURSES")
        print("-" * 60)
        
        courses = self.student_repo.get_student_courses(reg_no)
        
        if not courses:
            print("\nNo courses found.")
            return
        
        print(f"\n{'Course Code':<15} {'Course Title':<30} {'Faculty':<20} {'Time Slot':<15}")
        print("-" * 80)
        
        for course in courses:
            print(f"{course['course_code']:<15} {course['course_title']:<30} "
                  f"{course['faculty_name']:<20} {course['time_slot']:<15}")
        
        print("-" * 60)
    
    def submit_feedback(self, reg_no: str):
        """Handle student feedback submission."""
        print("\n" + "-" * 60)
        print("SUBMIT FEEDBACK")
        print("-" * 60)
        
        # Show courses
        courses = self.student_repo.get_student_courses(reg_no)
        if not courses:
            print("\nNo courses available.")
            return
        
        print("\nAvailable Courses:")
        for idx, course in enumerate(courses, 1):
            print(f"{idx}. {course['course_code']} - {course['course_title']}")
        
        try:
            course_idx = int(input("\nSelect course number: ").strip()) - 1
            if course_idx < 0 or course_idx >= len(courses):
                print("Invalid course selection.")
                return
            
            selected_course = courses[course_idx]
            course_code = selected_course['course_code']
            
            # Check if already submitted
            can_submit, message = self.feedback_service.can_student_submit_feedback(reg_no, course_code)
            if not can_submit:
                print(f"\n{message}")
                return
            
            # Get feedback details
            print(f"\nSubmitting feedback for: {selected_course['course_title']}")
            feedback_text = input("Enter your feedback (min 10 characters): ").strip()
            
            expectations = input("Enter your expectations (optional): ").strip()
            if not expectations:
                expectations = None
            
            rating_input = input("Enter rating (1-5, optional): ").strip()
            rating = None
            if rating_input:
                try:
                    rating = int(rating_input)
                except ValueError:
                    print("Invalid rating. Proceeding without rating.")
            
            # Submit feedback
            success, message = self.feedback_service.submit_feedback(
                reg_no, course_code, feedback_text, expectations, rating
            )
            
            print(f"\n{message}")
        
        except ValueError:
            print("\nInvalid input. Please enter a number.")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def view_student_feedbacks(self, reg_no: str):
        """Display student's submitted feedbacks."""
        print("\n" + "-" * 60)
        print("MY FEEDBACK SUBMISSIONS")
        print("-" * 60)
        
        feedbacks = self.feedback_service.get_student_feedbacks(reg_no)
        
        if not feedbacks:
            print("\nNo feedback submissions found.")
            return
        
        for idx, feedback in enumerate(feedbacks, 1):
            print(f"\n{idx}. Feedback ID: {feedback.feedback_id}")
            print(f"   Course Code: {feedback.course_code}")
            print(f"   Status: {feedback.status}")
            print(f"   Submission Date: {feedback.submission_date}")
            if feedback.rating:
                print(f"   Rating: {feedback.rating}/5")
            print(f"   Feedback: {feedback.feedback_text[:50]}...")
            print("-" * 60)
    
    def hod_dashboard(self):
        """HOD dashboard menu."""
        while True:
            print("\n" + "=" * 60)
            print("HOD DASHBOARD")
            print("=" * 60)
            print("\nOptions:")
            print("1. View All Feedbacks")
            print("2. View Pending Feedbacks")
            print("3. Approve Feedback")
            print("4. Reject Feedback")
            print("5. View Feedback Details")
            print("6. Logout")
            print("=" * 60)
            
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '1':
                self.view_all_feedbacks_hod()
            elif choice == '2':
                self.view_pending_feedbacks()
            elif choice == '3':
                self.approve_feedback_hod()
            elif choice == '4':
                self.reject_feedback_hod()
            elif choice == '5':
                self.view_feedback_details_hod()
            elif choice == '6':
                self.auth_service.logout()
                print("\nLogged out successfully!")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def view_all_feedbacks_hod(self):
        """Display all feedbacks for HOD."""
        print("\n" + "-" * 60)
        print("ALL FEEDBACKS")
        print("-" * 60)
        
        feedbacks = self.hod_service.get_all_feedbacks()
        
        if not feedbacks:
            print("\nNo feedbacks found.")
            return
        
        print(f"\n{'ID':<6} {'Course':<12} {'Student':<15} {'Status':<25} {'Date':<20}")
        print("-" * 80)
        
        for feedback in feedbacks:
            student = self.student_repo.get_student_by_reg_no(feedback.reg_no)
            student_name = student.name if student else feedback.reg_no
            
            print(f"{feedback.feedback_id:<6} {feedback.course_code:<12} "
                  f"{student_name[:14]:<15} {feedback.status:<25} "
                  f"{feedback.submission_date[:19]:<20}")
        
        print("-" * 60)
    
    def view_pending_feedbacks(self):
        """Display pending feedbacks for HOD."""
        print("\n" + "-" * 60)
        print("PENDING FEEDBACKS")
        print("-" * 60)
        
        feedbacks = self.hod_service.get_pending_feedbacks()
        
        if not feedbacks:
            print("\nNo pending feedbacks.")
            return
        
        for idx, feedback in enumerate(feedbacks, 1):
            student = self.student_repo.get_student_by_reg_no(feedback.reg_no)
            student_name = student.name if student else feedback.reg_no
            
            print(f"\n{idx}. Feedback ID: {feedback.feedback_id}")
            print(f"   Student: {student_name} ({feedback.reg_no})")
            print(f"   Course: {feedback.course_code}")
            print(f"   Feedback: {feedback.feedback_text[:100]}...")
            print(f"   Submission Date: {feedback.submission_date}")
            print("-" * 60)
    
    def approve_feedback_hod(self):
        """Handle HOD feedback approval."""
        print("\n" + "-" * 60)
        print("APPROVE FEEDBACK")
        print("-" * 60)
        
        try:
            feedback_id = int(input("Enter Feedback ID to approve: ").strip())
            
            feedback = self.hod_service.get_feedback_by_id(feedback_id)
            if not feedback:
                print("\nFeedback not found.")
                return
            
            print(f"\nFeedback Details:")
            print(f"Course Code: {feedback.course_code}")
            print(f"Feedback: {feedback.feedback_text}")
            print(f"Status: {feedback.status}")
            
            hod_comments = input("\nEnter HOD comments (optional): ").strip()
            if not hod_comments:
                hod_comments = None
            
            success, message = self.hod_service.approve_feedback(feedback_id, hod_comments)
            print(f"\n{message}")
        
        except ValueError:
            print("\nInvalid Feedback ID.")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def reject_feedback_hod(self):
        """Handle HOD feedback rejection."""
        print("\n" + "-" * 60)
        print("REJECT FEEDBACK")
        print("-" * 60)
        
        try:
            feedback_id = int(input("Enter Feedback ID to reject: ").strip())
            
            feedback = self.hod_service.get_feedback_by_id(feedback_id)
            if not feedback:
                print("\nFeedback not found.")
                return
            
            print(f"\nFeedback Details:")
            print(f"Course Code: {feedback.course_code}")
            print(f"Feedback: {feedback.feedback_text}")
            print(f"Status: {feedback.status}")
            
            hod_comments = input("\nEnter rejection reason (optional): ").strip()
            if not hod_comments:
                hod_comments = None
            
            success, message = self.hod_service.reject_feedback(feedback_id, hod_comments)
            print(f"\n{message}")
        
        except ValueError:
            print("\nInvalid Feedback ID.")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def view_feedback_details_hod(self):
        """Display detailed feedback information for HOD."""
        print("\n" + "-" * 60)
        print("FEEDBACK DETAILS")
        print("-" * 60)
        
        try:
            feedback_id = int(input("Enter Feedback ID: ").strip())
            
            feedback = self.hod_service.get_feedback_by_id(feedback_id)
            if not feedback:
                print("\nFeedback not found.")
                return
            
            student = self.student_repo.get_student_by_reg_no(feedback.reg_no)
            
            print(f"\nFeedback ID: {feedback.feedback_id}")
            print(f"Student: {student.name if student else 'N/A'} ({feedback.reg_no})")
            print(f"Course Code: {feedback.course_code}")
            print(f"Status: {feedback.status}")
            print(f"\nFeedback Text:")
            print(f"  {feedback.feedback_text}")
            print(f"\nExpectations:")
            print(f"  {feedback.expectations or 'N/A'}")
            print(f"\nRating: {feedback.rating if feedback.rating else 'N/A'}/5")
            print(f"\nHOD Comments:")
            print(f"  {feedback.hod_comments or 'N/A'}")
            print(f"\nFaculty Response:")
            print(f"  {feedback.faculty_response or 'N/A'}")
            print(f"\nAction Taken:")
            print(f"  {feedback.action_taken or 'N/A'}")
            print(f"\nSubmission Date: {feedback.submission_date}")
            print(f"Action Date: {feedback.action_date or 'N/A'}")
        
        except ValueError:
            print("\nInvalid Feedback ID.")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def faculty_dashboard(self, faculty):
        """Faculty dashboard menu."""
        while True:
            print("\n" + "=" * 60)
            print(f"FACULTY DASHBOARD - Welcome, {faculty.faculty_name}!")
            print("=" * 60)
            print("\nOptions:")
            print("1. View Approved Feedbacks")
            print("2. Respond to Feedback")
            print("3. View Feedback Details")
            print("4. Logout")
            print("=" * 60)
            
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '1':
                self.view_approved_feedbacks(faculty.employee_id)
            elif choice == '2':
                self.respond_to_feedback(faculty.employee_id)
            elif choice == '3':
                self.view_feedback_details_faculty()
            elif choice == '4':
                self.auth_service.logout()
                print("\nLogged out successfully!")
                break
            else:
                print("\nInvalid choice. Please try again.")
    
    def view_approved_feedbacks(self, employee_id: str):
        """Display approved feedbacks for faculty."""
        print("\n" + "-" * 60)
        print("APPROVED FEEDBACKS")
        print("-" * 60)
        
        feedbacks = self.faculty_service.get_approved_feedbacks(employee_id)
        
        if not feedbacks:
            print("\nNo approved feedbacks available.")
            return
        
        print(f"\n{'ID':<6} {'Course':<12} {'Student':<15} {'Status':<25} {'Date':<20}")
        print("-" * 80)
        
        for feedback in feedbacks:
            student = self.student_repo.get_student_by_reg_no(feedback.reg_no)
            student_name = student.name if student else feedback.reg_no
            
            print(f"{feedback.feedback_id:<6} {feedback.course_code:<12} "
                  f"{student_name[:14]:<15} {feedback.status:<25} "
                  f"{feedback.submission_date[:19]:<20}")
        
        print("-" * 60)
    
    def respond_to_feedback(self, employee_id: str):
        """Handle faculty response to feedback."""
        print("\n" + "-" * 60)
        print("RESPOND TO FEEDBACK")
        print("-" * 60)
        
        # Show approved feedbacks
        feedbacks = self.faculty_service.get_approved_feedbacks(employee_id)
        
        if not feedbacks:
            print("\nNo approved feedbacks available to respond to.")
            return
        
        print("\nApproved Feedbacks:")
        for idx, feedback in enumerate(feedbacks, 1):
            student = self.student_repo.get_student_by_reg_no(feedback.reg_no)
            student_name = student.name if student else feedback.reg_no
            print(f"{idx}. ID: {feedback.feedback_id} - {feedback.course_code} "
                  f"(Student: {student_name})")
        
        try:
            feedback_id = int(input("\nEnter Feedback ID to respond: ").strip())
            
            feedback = self.faculty_service.get_feedback_by_id(feedback_id)
            if not feedback:
                print("\nFeedback not found.")
                return
            
            if feedback.status != 'Approved':
                print(f"\nCannot respond to feedback with status '{feedback.status}'. "
                      "Only approved feedbacks can be responded to.")
                return
            
            # Show feedback details
            print(f"\nFeedback Details:")
            print(f"Course Code: {feedback.course_code}")
            print(f"Feedback: {feedback.feedback_text}")
            print(f"Expectations: {feedback.expectations or 'N/A'}")
            print(f"HOD Comments: {feedback.hod_comments or 'N/A'}")
            
            # Get faculty response
            faculty_response = input("\nEnter your response: ").strip()
            action_taken = input("Enter corrective action taken: ").strip()
            
            success, message = self.faculty_service.submit_response(
                feedback_id, faculty_response, action_taken
            )
            
            print(f"\n{message}")
        
        except ValueError:
            print("\nInvalid Feedback ID.")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def view_feedback_details_faculty(self):
        """Display detailed feedback information for faculty."""
        print("\n" + "-" * 60)
        print("FEEDBACK DETAILS")
        print("-" * 60)
        
        try:
            feedback_id = int(input("Enter Feedback ID: ").strip())
            
            feedback = self.faculty_service.get_feedback_by_id(feedback_id)
            if not feedback:
                print("\nFeedback not found.")
                return
            
            student = self.student_repo.get_student_by_reg_no(feedback.reg_no)
            
            print(f"\nFeedback ID: {feedback.feedback_id}")
            print(f"Student: {student.name if student else 'N/A'} ({feedback.reg_no})")
            print(f"Course Code: {feedback.course_code}")
            print(f"Status: {feedback.status}")
            print(f"\nFeedback Text:")
            print(f"  {feedback.feedback_text}")
            print(f"\nExpectations:")
            print(f"  {feedback.expectations or 'N/A'}")
            print(f"\nRating: {feedback.rating if feedback.rating else 'N/A'}/5")
            print(f"\nHOD Comments:")
            print(f"  {feedback.hod_comments or 'N/A'}")
            print(f"\nFaculty Response:")
            print(f"  {feedback.faculty_response or 'N/A'}")
            print(f"\nAction Taken:")
            print(f"  {feedback.action_taken or 'N/A'}")
            print(f"\nSubmission Date: {feedback.submission_date}")
            print(f"Action Date: {feedback.action_date or 'N/A'}")
        
        except ValueError:
            print("\nInvalid Feedback ID.")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def generate_reports_menu(self):
        """Report generation menu."""
        print("\n" + "=" * 60)
        print("GENERATE REPORTS")
        print("=" * 60)
        print("\nOptions:")
        print("1. View ATR on Screen")
        print("2. Export ATR to PDF")
        print("3. Export ATR to Excel")
        print("4. Back to Main Menu")
        print("=" * 60)
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == '1':
            self.view_atr_console()
        elif choice == '2':
            self.export_atr_pdf()
        elif choice == '3':
            self.export_atr_excel()
        elif choice == '4':
            return
        else:
            print("\nInvalid choice.")
    
    def view_atr_console(self):
        """Display ATR in console."""
        print("\n" + "-" * 60)
        print("ACTION TAKEN REPORT (ATR)")
        print("-" * 60)
        
        atr_data = self.report_service.get_all_atr_data()
        
        if not atr_data:
            print("\nNo ATR data available. Faculty responses are required to generate ATR.")
            return
        
        display_atr_console(atr_data)
    
    def export_atr_pdf(self):
        """Export ATR to PDF."""
        print("\n" + "-" * 60)
        print("EXPORT ATR TO PDF")
        print("-" * 60)
        
        atr_data = self.report_service.get_all_atr_data()
        
        if not atr_data:
            print("\nNo ATR data available. Faculty responses are required to generate ATR.")
            return
        
        try:
            output_path = input("Enter output file path (default: atr_report.pdf): ").strip()
            if not output_path:
                output_path = "atr_report.pdf"
            
            file_path = export_to_pdf(atr_data, output_path)
            print(f"\nPDF exported successfully to: {file_path}")
        
        except ExportError as e:
            print(f"\nExport Error: {str(e)}")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def export_atr_excel(self):
        """Export ATR to Excel."""
        print("\n" + "-" * 60)
        print("EXPORT ATR TO EXCEL")
        print("-" * 60)
        
        atr_data = self.report_service.get_all_atr_data()
        
        if not atr_data:
            print("\nNo ATR data available. Faculty responses are required to generate ATR.")
            return
        
        try:
            output_path = input("Enter output file path (default: atr_report.xlsx): ").strip()
            if not output_path:
                output_path = "atr_report.xlsx"
            
            file_path = export_to_excel(atr_data, output_path)
            print(f"\nExcel file exported successfully to: {file_path}")
        
        except ExportError as e:
            print(f"\nExport Error: {str(e)}")
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    def run(self):
        """Main application loop."""
        try:
            while True:
                self.display_main_menu()
                choice = input("\nEnter your choice: ").strip()
                
                if choice == '1':
                    # Student Login
                    print("\n" + "-" * 60)
                    print("STUDENT LOGIN")
                    print("-" * 60)
                    reg_no = input("Enter Registration Number: ").strip()
                    password = input("Enter Password: ").strip()
                    
                    success, student, message = self.auth_service.login_student(reg_no, password)
                    print(f"\n{message}")
                    
                    if success and student:
                        self.student_dashboard(student)
                
                elif choice == '2':
                    # HOD Login
                    print("\n" + "-" * 60)
                    print("HOD LOGIN")
                    print("-" * 60)
                    print("HOD access granted (no password required for demo)")
                    
                    success, hod_info, message = self.auth_service.login_hod()
                    print(f"\n{message}")
                    
                    if success:
                        self.hod_dashboard()
                
                elif choice == '3':
                    # Faculty Login
                    print("\n" + "-" * 60)
                    print("FACULTY LOGIN")
                    print("-" * 60)
                    employee_id = input("Enter Employee ID: ").strip()
                    
                    success, faculty, message = self.auth_service.login_faculty(employee_id)
                    print(f"\n{message}")
                    
                    if success and faculty:
                        self.faculty_dashboard(faculty)
                
                elif choice == '4':
                    # Generate Reports
                    self.generate_reports_menu()
                
                elif choice == '5':
                    # Exit
                    print("\nThank you for using the system. Goodbye!")
                    self.db.close()
                    break
                
                else:
                    print("\nInvalid choice. Please try again.")
        
        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user.")
            self.db.close()
            sys.exit(0)
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            self.db.close()
            sys.exit(1)


def main():
    """Main entry point."""
    menu = CLIMenu()
    menu.run()


if __name__ == "__main__":
    main()
