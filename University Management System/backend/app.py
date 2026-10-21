"""
Smart University Management System - REST backend.

FastAPI service in front of Supabase. Users sign in through Supabase Auth and
every request is forwarded with the user's own JWT, so the Row Level Security
policies in supabase/schema.sql decide what each role (admin/faculty/student)
may read or change.
"""

import csv
import io
import os
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_ANON_KEY in .env")

app = FastAPI(title="Smart University Management System", version="2.0")
client = httpx.AsyncClient(timeout=20)


# ---------------------------------------------------------------- supabase

def _headers(token: Optional[str]) -> dict:
    h = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    h["Authorization"] = f"Bearer {token or SUPABASE_KEY}"
    return h


async def _call(method: str, url: str, token: Optional[str], **kw) -> Any:
    extra = kw.pop("headers", {})
    r = await client.request(method, url, headers={**_headers(token), **extra}, **kw)
    if not r.is_success:
        try:
            body = r.json()
            msg = body.get("message") or body.get("msg") or body.get("error_description") or str(body)
        except ValueError:
            msg = r.text
        code = r.status_code if r.status_code in (400, 401, 403, 404, 409) else 400
        raise HTTPException(code, msg)
    return r.json() if r.content else None


async def rest(method: str, path: str, token: str, params=None, json=None, prefer="return=representation"):
    return await _call(method, f"{SUPABASE_URL}/rest/v1/{path}", token,
                       params=params, json=json, headers={"Prefer": prefer})


async def rpc(fn: str, token: str, args: dict):
    return await _call("POST", f"{SUPABASE_URL}/rest/v1/rpc/{fn}", token, json=args)


def bearer(authorization: str = Header(default="")) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Not signed in")
    return authorization[7:]


async def current_user(token: str = Depends(bearer)) -> dict:
    user = await _call("GET", f"{SUPABASE_URL}/auth/v1/user", token)
    rows = await rest("GET", "profiles", token, {"id": f"eq.{user['id']}", "select": "*,department:departments(code,name)"})
    if not rows:
        raise HTTPException(403, "No profile for this account")
    return {**rows[0], "token": token}


def require(*roles):
    async def dep(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(403, f"Only {', '.join(roles)} can do this")
        return user
    return dep


# ---------------------------------------------------------------- auth

class Login(BaseModel):
    email: str
    password: str


class Refresh(BaseModel):
    refresh_token: str


@app.post("/api/auth/login")
async def login(body: Login):
    try:
        session = await _call("POST", f"{SUPABASE_URL}/auth/v1/token?grant_type=password", None,
                              json={"email": body.email.strip().lower(), "password": body.password})
    except HTTPException:
        raise HTTPException(401, "Invalid email or password")
    profile = await current_user(session["access_token"])
    profile.pop("token")
    return {"access_token": session["access_token"], "refresh_token": session["refresh_token"], "profile": profile}


@app.post("/api/auth/refresh")
async def refresh(body: Refresh):
    session = await _call("POST", f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token", None,
                          json={"refresh_token": body.refresh_token})
    return {"access_token": session["access_token"], "refresh_token": session["refresh_token"]}


@app.get("/api/me")
async def me(user: dict = Depends(current_user)):
    return {k: v for k, v in user.items() if k != "token"}


# ---------------------------------------------------------------- dashboard

@app.get("/api/dashboard")
async def dashboard(user: dict = Depends(current_user)):
    t = user["token"]
    data: dict = {
        "notices": await rest("GET", "notices", t, {"select": "*,author:profiles!notices_author_id_fkey(full_name)", "order": "created_at.desc", "limit": 5}),
        "events": await rest("GET", "events", t, {"select": "*", "starts_at": "gte.now()", "order": "starts_at", "limit": 5}),
    }
    if user["role"] == "admin":
        data["stats"] = await rpc("dashboard_stats", t, {})
    elif user["role"] == "student":
        data["attendance"] = await rest("GET", "attendance_summary", t, {"student_id": f"eq.{user['id']}"})
        data["marks"] = await rest("GET", "marks_summary", t, {"student_id": f"eq.{user['id']}"})
    else:
        data["courses"] = await rest("GET", "courses", t, {"faculty_id": f"eq.{user['id']}", "select": "*,enrollments(count)"})
        data["pending_responses"] = len(await rest("GET", "feedback", t, {"status": "eq.Approved", "select": "id"}))
    return data


# ---------------------------------------------------------------- users

class NewUser(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    role: str
    reg_no: Optional[str] = None
    department_id: Optional[int] = None
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    reg_no: Optional[str] = None
    department_id: Optional[int] = None
    phone: Optional[str] = None


@app.get("/api/users")
async def list_users(role: Optional[str] = None, user: dict = Depends(current_user)):
    params = {"select": "*,department:departments(code)", "order": "role,full_name"}
    if role:
        params["role"] = f"eq.{role}"
    return await rest("GET", "profiles", user["token"], params)


@app.post("/api/users", status_code=201)
async def create_user(body: NewUser, user: dict = Depends(require("admin"))):
    uid = await rpc("admin_create_user", user["token"], {
        "p_email": body.email, "p_password": body.password, "p_full_name": body.full_name,
        "p_role": body.role, "p_reg_no": body.reg_no or None, "p_department_id": body.department_id,
        "p_phone": body.phone or None})
    return {"id": uid}


@app.patch("/api/users/{uid}")
async def update_user(uid: str, body: UserUpdate, user: dict = Depends(require("admin"))):
    return await rest("PATCH", "profiles", user["token"], {"id": f"eq.{uid}"}, body.model_dump(exclude_unset=True))


@app.delete("/api/users/{uid}", status_code=204)
async def delete_user(uid: str, user: dict = Depends(require("admin"))):
    await rpc("admin_delete_user", user["token"], {"p_id": uid})


# ---------------------------------------------------------------- simple resources
# name -> (table, select for listing, default order, roles allowed to write)

RESOURCES = {
    "departments": ("departments", "*", "code", ("admin",)),
    "courses": ("courses", "*,department:departments(code),faculty:profiles!courses_faculty_id_fkey(id,full_name),enrollments(count)", "code", ("admin",)),
    "timetable": ("timetable", "*,course:courses(code,title,faculty:profiles!courses_faculty_id_fkey(full_name))", "day_of_week,start_time", ("admin",)),
    "notices": ("notices", "*,author:profiles!notices_author_id_fkey(full_name)", "created_at.desc", ("admin", "faculty")),
    "events": ("events", "*", "starts_at", ("admin",)),
    "enrollments": ("enrollments", "*,student:profiles(full_name,reg_no),course:courses(code,title)", "course_id", ("admin",)),
    "marks": ("marks", "*,student:profiles!marks_student_id_fkey(full_name,reg_no),course:courses(code,title)", "course_id,assessment", ("admin", "faculty")),
}
FILTERABLE = {"course_id", "student_id", "role", "class_date", "status", "faculty_id", "department_id"}


def _filters(request: Request) -> dict:
    return {k: f"eq.{v}" for k, v in request.query_params.items() if k in FILTERABLE}


# ---------------------------------------------------------------- attendance

class AttendanceEntry(BaseModel):
    student_id: str
    status: str


class AttendanceSheet(BaseModel):
    course_id: int
    class_date: str
    entries: list[AttendanceEntry]


@app.get("/api/attendance/sheet")
async def attendance_sheet(course_id: int, class_date: str, user: dict = Depends(require("admin", "faculty"))):
    t = user["token"]
    students = await rest("GET", "enrollments", t, {"course_id": f"eq.{course_id}", "select": "student:profiles(id,full_name,reg_no)"})
    marked = await rest("GET", "attendance", t, {"course_id": f"eq.{course_id}", "class_date": f"eq.{class_date}", "select": "student_id,status"})
    status = {m["student_id"]: m["status"] for m in marked}
    rows = [{**s["student"], "status": status.get(s["student"]["id"])} for s in students]
    return sorted(rows, key=lambda r: r["reg_no"] or "")


@app.post("/api/attendance/sheet")
async def save_attendance(body: AttendanceSheet, user: dict = Depends(require("admin", "faculty"))):
    payload = [{"course_id": body.course_id, "class_date": body.class_date, "student_id": e.student_id,
                "status": e.status, "marked_by": user["id"]} for e in body.entries]
    await _call("POST", f"{SUPABASE_URL}/rest/v1/attendance?on_conflict=course_id,student_id,class_date", user["token"],
                json=payload, headers={"Prefer": "resolution=merge-duplicates,return=minimal"})
    return {"saved": len(payload)}


@app.get("/api/attendance")
async def list_attendance(request: Request, user: dict = Depends(current_user)):
    return await rest("GET", "attendance", user["token"],
                      {"select": "*,course:courses(code,title)", "order": "class_date.desc", **_filters(request)})


# ---------------------------------------------------------------- feedback / ATR

class FeedbackIn(BaseModel):
    course_id: int
    feedback_text: str = Field(min_length=10)
    expectations: Optional[str] = None
    rating: int = Field(ge=1, le=5)


class Review(BaseModel):
    approve: bool
    comments: Optional[str] = None


class Response(BaseModel):
    response: str = Field(min_length=3)
    action_taken: str = Field(min_length=3)


FEEDBACK_SELECT = "*,student:profiles!feedback_student_id_fkey(full_name,reg_no),course:courses(code,title,faculty:profiles!courses_faculty_id_fkey(full_name))"


@app.get("/api/feedback")
async def list_feedback(request: Request, user: dict = Depends(current_user)):
    return await rest("GET", "feedback", user["token"],
                      {"select": FEEDBACK_SELECT, "order": "submitted_at.desc", **_filters(request)})


@app.post("/api/feedback", status_code=201)
async def submit_feedback(body: FeedbackIn, user: dict = Depends(require("student"))):
    try:
        return await rest("POST", "feedback", user["token"], json={**body.model_dump(), "student_id": user["id"]})
    except HTTPException as e:
        if "duplicate" in str(e.detail):
            raise HTTPException(409, "You have already submitted feedback for this course")
        raise


@app.post("/api/feedback/{fid}/review")
async def review_feedback(fid: int, body: Review, user: dict = Depends(require("admin"))):
    await rpc("review_feedback", user["token"], {"p_id": fid, "p_approve": body.approve, "p_comments": body.comments})
    return {"ok": True}


@app.post("/api/feedback/{fid}/respond")
async def respond_feedback(fid: int, body: Response, user: dict = Depends(require("faculty"))):
    await rpc("respond_feedback", user["token"], {"p_id": fid, "p_response": body.response, "p_action": body.action_taken})
    return {"ok": True}


# ---------------------------------------------------------------- reports

REPORTS = {
    "attendance": ("attendance_summary", "course_code,reg_no",
                   ["reg_no", "full_name", "course_code", "course_title", "total_classes", "attended", "percentage"]),
    "marks": ("marks_summary", "course_code,reg_no",
              ["reg_no", "full_name", "course_code", "course_title", "obtained", "maximum", "percentage"]),
    "atr": ("feedback", "submitted_at.desc", None),
}


async def _report(kind: str, request: Request, token: str) -> list:
    if kind not in REPORTS:
        raise HTTPException(404, "Unknown report")
    view, order, _ = REPORTS[kind]
    params = {"order": order, **_filters(request)}
    if kind == "atr":
        params["select"] = FEEDBACK_SELECT
        params["status"] = "eq.Faculty Responded"
    return await rest("GET", view, token, params)


@app.get("/api/reports/{kind}.csv")
async def report_csv(kind: str, request: Request, user: dict = Depends(current_user)):
    rows = await _report(kind, request, user["token"])
    buf = io.StringIO()
    w = csv.writer(buf)
    if kind == "atr":
        w.writerow(["Student", "Reg No", "Course", "Faculty", "Rating", "Feedback", "HOD Comments", "Response", "Action Taken", "Action Date"])
        for r in rows:
            w.writerow([r["student"]["full_name"], r["student"]["reg_no"], r["course"]["code"],
                        (r["course"].get("faculty") or {}).get("full_name"), r["rating"], r["feedback_text"],
                        r["hod_comments"], r["faculty_response"], r["action_taken"], (r["action_date"] or "")[:10]])
    else:
        cols = REPORTS[kind][2]
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] for c in cols])
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="{kind}_report.csv"'})


@app.get("/api/reports/{kind}")
async def report(kind: str, request: Request, user: dict = Depends(current_user)):
    return await _report(kind, request, user["token"])


# generic CRUD routes go last so they never shadow the specific ones above

@app.get("/api/{name}")
async def list_resource(name: str, request: Request, user: dict = Depends(current_user)):
    if name not in RESOURCES:
        raise HTTPException(404, "Unknown resource")
    table, select, order, _ = RESOURCES[name]
    return await rest("GET", table, user["token"], {"select": select, "order": order, **_filters(request)})


@app.post("/api/{name}", status_code=201)
async def create_resource(name: str, body: dict, user: dict = Depends(current_user)):
    if name not in RESOURCES:
        raise HTTPException(404, "Unknown resource")
    table, _, _, roles = RESOURCES[name]
    if user["role"] not in roles:
        raise HTTPException(403, "Not allowed")
    if name == "notices":
        body["author_id"] = user["id"]
    return await rest("POST", table, user["token"], json=body)


@app.patch("/api/{name}/{rid}")
async def update_resource(name: str, rid: int, body: dict, user: dict = Depends(current_user)):
    if name not in RESOURCES or name == "enrollments":
        raise HTTPException(404, "Unknown resource")
    table, _, _, roles = RESOURCES[name]
    if user["role"] not in roles:
        raise HTTPException(403, "Not allowed")
    rows = await rest("PATCH", table, user["token"], {"id": f"eq.{rid}"}, body)
    if not rows:
        raise HTTPException(404, "Not found or not permitted")
    return rows[0]


@app.delete("/api/{name}/{rid}", status_code=204)
async def delete_resource(name: str, rid: str, user: dict = Depends(current_user)):
    if name not in RESOURCES:
        raise HTTPException(404, "Unknown resource")
    table, _, _, roles = RESOURCES[name]
    if user["role"] not in roles:
        raise HTTPException(403, "Not allowed")
    if name == "enrollments":  # composite key: "<student_id>:<course_id>"
        sid, cid = rid.split(":")
        params = {"student_id": f"eq.{sid}", "course_id": f"eq.{cid}"}
    else:
        params = {"id": f"eq.{rid}"}
    rows = await rest("DELETE", table, user["token"], params)
    if not rows:
        raise HTTPException(404, "Not found or not permitted")


# ---------------------------------------------------------------- frontend

FRONTEND = ROOT / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
async def index():
    return FileResponse(FRONTEND / "index.html")
