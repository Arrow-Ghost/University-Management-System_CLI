# Student Feedback & Action Taken Report (ATR) Management System

A comprehensive Python backend system for managing the complete academic feedback workflow between Students, HOD (Head of Department), and Faculty.

## 🏗️ System Architecture

The system follows a clean layered architecture:

```
project/
│
├── main.py                    # Main entry point with CLI interface
├── seed_data.py               # Data seeder script
├── requirements.txt           # Python dependencies
│
├── database/
│   └── db_connection.py       # Database connection and initialization
│
├── models/
│   ├── student.py            # Student data model
│   ├── faculty.py            # Faculty data model
│   ├── hod.py                # HOD data structures
│   ├── course.py             # Course data model
│   └── feedback.py           # Feedback data model
│
├── services/
│   ├── auth_service.py       # Authentication service
│   ├── feedback_service.py   # Feedback management service
│   ├── hod_service.py        # HOD operations service
│   ├── faculty_service.py    # Faculty operations service
│   └── report_service.py     # Report generation service
│
├── repositories/
│   └── database_operations.py # Database abstraction layer
│
├── reports/
│   └── export_utils.py       # PDF and Excel export utilities
│
└── utils/
    └── validations.py        # Input validation utilities
```

## 📋 Features

### Student Module
- ✅ Student login with registration number and password
- ✅ View registered courses and class details
- ✅ Submit feedback (one per course)
- ✅ View feedback submission history
- ✅ Prevent duplicate submissions

### HOD Module
- ✅ View all feedbacks with filtering options
- ✅ Approve/Reject feedbacks
- ✅ Add HOD comments
- ✅ View pending feedbacks
- ✅ View detailed feedback information

### Faculty Module
- ✅ View only approved feedbacks
- ✅ Respond to approved feedbacks
- ✅ Submit corrective actions
- ✅ View feedback details

### Report Module (ATR)
- ✅ Generate Action Taken Reports
- ✅ View reports on screen (formatted console output)
- ✅ Export to PDF
- ✅ Export to Excel

## 🔄 Workflow Pipeline

```
Student Submission
        ↓
Pending HOD Review
        ↓
HOD Approval/Rejection
        ↓
Approved → Visible to Faculty
Rejected → Not visible to Faculty
        ↓
Faculty Response
        ↓
ATR Generated
```

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone or download the project**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Initialize database with sample data:**
```bash
python seed_data.py
```

This will create the database and populate it with sample students, faculty, courses, and feedbacks.

### Running the Application

```bash
python main.py
```

## 📝 Sample Login Credentials

After running `seed_data.py`, you can use these credentials:

### Students
- **Registration Number:** STU001, **Password:** password123
- **Registration Number:** STU002, **Password:** password123
- **Registration Number:** STU003, **Password:** password123

### Faculty
- **Employee ID:** FAC001
- **Employee ID:** FAC002

### HOD
- No password required (select option 2 from main menu)

## 🎯 Usage Guide

### Main Menu Options

1. **Student Login** - Access student dashboard
2. **HOD Login** - Access HOD dashboard
3. **Faculty Login** - Access faculty dashboard
4. **Generate Reports** - Generate and export ATR reports
5. **Exit** - Exit the application

### Student Workflow

1. Login with registration number and password
2. View your courses
3. Select a course to submit feedback
4. Enter feedback text, expectations, and optional rating
5. Submit feedback (one submission per course)
6. View your submission history

### HOD Workflow

1. Login as HOD
2. View all feedbacks or pending feedbacks
3. Review feedback details
4. Approve or reject feedbacks
5. Add comments if needed
6. Approved feedbacks become visible to faculty

### Faculty Workflow

1. Login with employee ID
2. View approved feedbacks for your courses
3. Select a feedback to respond
4. Enter your response and corrective actions
5. Submit response (updates status to "Faculty Responded")

### Report Generation

1. Select "Generate Reports" from main menu
2. Choose to view on screen, export to PDF, or export to Excel
3. ATR includes all feedbacks that have been responded to by faculty

## 🗄️ Database Schema

### Tables

1. **Students**
   - `reg_no` (PK) - Registration number
   - `name` - Student name
   - `password` - Password

2. **Faculty**
   - `employee_id` (PK) - Employee ID
   - `faculty_name` - Faculty name

3. **Courses**
   - `course_code` (PK) - Course code
   - `course_title` - Course title
   - `faculty_employee_id` (FK) - Faculty teaching the course
   - `time_slot` - Class time slot
   - `class_slot_duration` - Duration in minutes (default: 50)

4. **Feedback**
   - `feedback_id` (PK) - Auto-increment ID
   - `reg_no` (FK) - Student registration number
   - `course_code` (FK) - Course code
   - `feedback_text` - Feedback content
   - `expectations` - Student expectations
   - `rating` - Rating (1-5)
   - `status` - Status enum: 'Pending HOD Review', 'Approved', 'Rejected', 'Faculty Responded'
   - `hod_comments` - HOD comments
   - `faculty_response` - Faculty response
   - `action_taken` - Corrective actions taken
   - `submission_date` - Submission timestamp
   - `action_date` - Action taken timestamp

## ✅ Validation Rules

- Feedback text must be at least 10 characters
- Rating must be between 1-5 (if provided)
- Students can submit only once per course
- Faculty can only respond to approved feedbacks
- HOD cannot modify feedbacks that have been responded to
- Status transitions follow strict workflow rules

## 🔮 Future Expansion

The system is designed to be easily extensible for:

- **Frontend Integration:** Clean service layer ready for Flask/FastAPI APIs
- **AI Integration:** Services can be extended with:
  - Sentiment analysis of feedback
  - AI summarization
  - Auto-suggestions for corrective actions
- **Web UI:** React or other frontend frameworks
- **Additional Features:** Email notifications, advanced reporting, etc.

## 🛠️ Technical Details

### Design Principles

- **OOP:** All components use classes and object-oriented design
- **Separation of Concerns:** Clear separation between models, repositories, services, and UI
- **Database Abstraction:** Repository pattern for database operations
- **Exception Handling:** Comprehensive error handling throughout
- **Documentation:** Docstrings for all functions and classes
- **Logging Ready:** Structure supports easy logging integration

### Dependencies

- **reportlab:** PDF generation
- **pandas:** Data manipulation for Excel export
- **openpyxl:** Excel file creation

## 📄 License

This project is created for educational purposes.

## 🤝 Contributing

This is a modular system designed for easy extension. When adding new features:

1. Follow the existing architecture patterns
2. Add validation in `utils/validations.py`
3. Create services in `services/` directory
4. Update repository layer if new database operations are needed
5. Maintain docstrings and comments

## 📞 Support

For issues or questions, please refer to the code documentation and comments throughout the codebase.
