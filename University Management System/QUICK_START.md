# Quick Start Guide

## 🚀 Setup in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Seed Database
```bash
python seed_data.py
```

This creates the database and adds sample data:
- 5 Students (STU001-STU005, password: password123)
- 4 Faculty members (FAC001-FAC004)
- 7 Courses
- 5 Sample feedbacks (various statuses)

### Step 3: Run Application
```bash
python main.py
```

## 🎮 Quick Test Workflow

### Test Student Flow:
1. Select option `1` (Student Login)
2. Login: `STU001` / `password123`
3. View courses (option 1)
4. Submit feedback (option 2) - try CS301
5. View submissions (option 3)

### Test HOD Flow:
1. Select option `2` (HOD Login)
2. View pending feedbacks (option 2)
3. Approve a feedback (option 3) - use Feedback ID from pending list
4. Add comments and approve

### Test Faculty Flow:
1. Select option `3` (Faculty Login)
2. Login: `FAC001`
3. View approved feedbacks (option 1)
4. Respond to feedback (option 2)
5. Enter response and action taken

### Test Report Generation:
1. Select option `4` (Generate Reports)
2. View ATR on screen (option 1)
3. Export to PDF (option 2)
4. Export to Excel (option 3)

## 📊 Database File

The database file `university_management.db` will be created automatically in the project root directory.

## 🔍 Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root directory:
```bash
cd "University Management System"
python main.py
```

### Missing Dependencies
If PDF/Excel export fails, install dependencies:
```bash
pip install reportlab pandas openpyxl
```

### Database Issues
If database errors occur, delete `university_management.db` and run `seed_data.py` again.

## 📝 Notes

- All passwords for students are: `password123`
- Faculty login only requires Employee ID (no password)
- HOD login requires no credentials
- Each student can submit feedback only once per course
- Only approved feedbacks are visible to faculty
- ATR reports only include feedbacks that have been responded to by faculty
