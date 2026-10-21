# Smart University Management System

One role-based platform for **admin, faculty and students** that brings academics,
attendance, timetables, notices, events, student records, course feedback (ATR) and
reports together on a single shared **Supabase (PostgreSQL)** database — as proposed in
*Smart University Review 1* (Anushqa Dey, Aishani Dutta — guide Dr. Soumyajyoti Dey).

This grew out of the earlier Student Feedback & ATR CLI (still in `main.py`, SQLite).
The feedback → HOD review → faculty action-taken workflow is now one module of the web app.

## Architecture

```
frontend/  (HTML + CSS + vanilla JS SPA)
     │  fetch /api/*  (Bearer = user's Supabase JWT)
backend/app.py  (FastAPI REST API)
     │  forwards the user's JWT to Supabase REST / Auth
Supabase  (Postgres + Auth + Row Level Security)
     └─ supabase/schema.sql  tables, views, RLS policies, RPC functions
```

Access control lives in the database: every table has Row Level Security, so even if
someone bypassed the backend, a student can still only read their own attendance and
marks, faculty can only mark attendance/marks for courses they teach, and only admins
manage users, courses and timetables.

## Modules

| Module | Admin | Faculty | Student |
|---|---|---|---|
| Dashboard | campus stats, <75% attendance alerts | my courses, pending ATRs | my attendance & marks |
| Users / Departments | create, edit, delete | — | — |
| Courses & enrollment | CRUD, enroll students | view | my courses |
| Timetable | manage slots | my classes | my classes |
| Attendance | mark any course | mark own courses | view % and log |
| Marks | any course | own courses | view own |
| Notices | post to all / students / faculty | post | read |
| Events | manage | view | view |
| Feedback & ATR | approve / reject (HOD) | respond with action taken | submit (one per course) |
| Reports (CSV) | attendance, marks, ATR | for own courses | — |

## Database (Supabase)

Tables: `departments, profiles, courses, enrollments, timetable, attendance, marks,
notices, events, feedback`. Views: `attendance_summary, marks_summary`.
Functions: `admin_create_user`, `admin_delete_user`, `review_feedback`,
`respond_feedback`, `dashboard_stats`.

The live project is `smart-university` (ref `igrgruudtvlxqmsngaan`, Mumbai region).
To set up a fresh project: run `supabase/schema.sql` then `supabase/seed.sql` in the
Supabase SQL editor and put its URL and publishable key in `.env`.

## Run

```bash
pip install -r requirements.txt
python -m uvicorn backend.app:app --port 8000
```

Open http://localhost:8000. API docs: http://localhost:8000/docs

`.env` (see `.env.example`):

```
SUPABASE_URL=https://igrgruudtvlxqmsngaan.supabase.co
SUPABASE_ANON_KEY=<publishable key>
```

## Demo accounts

All seeded accounts use the password `Password@123` (demo data only — change for real use).

| Role | Email |
|---|---|
| Admin (HOD) | admin@smartuni.edu |
| Faculty | soumyajyoti@smartuni.edu, rmehta@smartuni.edu, akumar@smartuni.edu |
| Student | anushqa@smartuni.edu (25MID0030), aishani@smartuni.edu (25MID0037), rahul@smartuni.edu … |

## Legacy CLI

The original feedback CLI (`main.py`, SQLite, PDF/Excel export) still runs with
`python main.py` and is unchanged.
