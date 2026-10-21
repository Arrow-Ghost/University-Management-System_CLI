// Smart University Management System - single page frontend.
// Talks only to the FastAPI backend (/api/*); the backend forwards the
// user's Supabase token so database RLS enforces each role's access.

const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const DAYS = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const fmtDate = (d) => (d ? new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "");
const fmtDateTime = (d) => (d ? new Date(d).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "");
const today = () => new Date().toISOString().slice(0, 10);

let session = JSON.parse(localStorage.getItem("su_session") || "null");
let me = null;

// ------------------------------------------------------------------ api
async function api(path, opts = {}, retry = true) {
  const headers = { "Content-Type": "application/json" };
  if (session) headers.Authorization = `Bearer ${session.access_token}`;
  const res = await fetch(`/api${path}`, { ...opts, headers, body: opts.body && JSON.stringify(opts.body) });
  if (res.status === 401 && session && retry) {
    const r = await fetch("/api/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: session.refresh_token }) });
    if (r.ok) { session = { ...session, ...(await r.json()) }; saveSession(); return api(path, opts, false); }
    logout(); throw new Error("Session expired");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(Array.isArray(data?.detail) ? data.detail.map((d) => d.msg).join(", ") : data?.detail || res.statusText);
  return data;
}
const get = (p) => api(p);
const post = (p, body) => api(p, { method: "POST", body });
const patch = (p, body) => api(p, { method: "PATCH", body });
const del = (p) => api(p, { method: "DELETE" });

function saveSession() { localStorage.setItem("su_session", JSON.stringify(session)); }

async function download(path, filename) {
  const res = await fetch(`/api${path}`, { headers: { Authorization: `Bearer ${session.access_token}` } });
  if (!res.ok) return toast("Download failed", true);
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(await res.blob()), download: filename });
  a.click(); URL.revokeObjectURL(a.href);
}

// ------------------------------------------------------------------ ui helpers
function toast(msg, bad = false) {
  const t = $("#toast"); t.textContent = msg; t.className = `toast show${bad ? " bad" : ""}`;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.className = "toast"), 2600);
}

function table(cols, rows, empty = "Nothing here yet.") {
  if (!rows.length) return `<p class="muted">${empty}</p>`;
  return `<div class="table-wrap"><table><thead><tr>${cols.map((c) => `<th>${c[0]}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((r) => `<tr>${cols.map((c) => `<td>${c[1](r)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

const pctBar = (p) => `<div style="display:flex;gap:8px;align-items:center"><div class="bar ${p < 75 ? "low" : ""}"><i style="width:${Math.min(p, 100)}%"></i></div>${p}%</div>`;
const statusBadge = (s) => `<span class="badge ${{ Approved: "ok", "Faculty Responded": "ok", Rejected: "bad", present: "ok", absent: "bad", late: "warn" }[s] || "warn"}">${esc(s)}</span>`;
const stars = (n) => `<span class="stars">${"★".repeat(n)}${"☆".repeat(5 - n)}</span>`;
const options = (rows, val, label, sel) => rows.map((r) => `<option value="${esc(val(r))}" ${String(val(r)) === String(sel) ? "selected" : ""}>${esc(label(r))}</option>`).join("");

// Opens a modal form. fields: [{name,label,type,options,required,value}]
function form(title, fields, onSubmit) {
  const f = $("#modal-form");
  f.innerHTML = `<h3>${esc(title)}</h3>${fields.map((x) => {
    const req = x.required === false ? "" : "required";
    const v = esc(x.value ?? "");
    if (x.type === "select") return `<label>${x.label}<select name="${x.name}" ${req}>${x.options}</select></label>`;
    if (x.type === "textarea") return `<label>${x.label}<textarea name="${x.name}" ${req}>${v}</textarea></label>`;
    return `<label>${x.label}<input name="${x.name}" type="${x.type || "text"}" value="${v}" ${req} ${x.attrs || ""}></label>`;
  }).join("")}<p class="error" id="modal-error"></p>
  <div class="actions"><button class="btn" value="cancel" formnovalidate>Cancel</button><button class="btn primary" value="ok">Save</button></div>`;
  const dlg = $("#modal");
  f.onsubmit = async (e) => {
    if (e.submitter?.value !== "ok") return;
    e.preventDefault();
    const data = Object.fromEntries(new FormData(f));
    for (const k in data) if (data[k] === "") data[k] = null;
    try { await onSubmit(data); dlg.close(); } catch (err) { $("#modal-error").textContent = err.message; }
  };
  dlg.showModal();
}

async function confirmDo(msg, fn) { if (confirm(msg)) { try { await fn(); toast("Done"); render(); } catch (e) { toast(e.message, true); } } }

// ------------------------------------------------------------------ pages
const PAGES = {
  dashboard: { title: "Dashboard", roles: ["admin", "faculty", "student"], render: dashboardPage },
  users: { title: "Users", roles: ["admin"], render: usersPage },
  departments: { title: "Departments", roles: ["admin"], render: departmentsPage },
  courses: { title: "Courses", roles: ["admin", "faculty", "student"], render: coursesPage },
  timetable: { title: "Timetable", roles: ["admin", "faculty", "student"], render: timetablePage },
  attendance: { title: "Attendance", roles: ["admin", "faculty", "student"], render: attendancePage },
  marks: { title: "Marks", roles: ["admin", "faculty", "student"], render: marksPage },
  notices: { title: "Notices", roles: ["admin", "faculty", "student"], render: noticesPage },
  events: { title: "Events", roles: ["admin", "faculty", "student"], render: eventsPage },
  feedback: { title: "Feedback & ATR", roles: ["admin", "faculty", "student"], render: feedbackPage },
  reports: { title: "Reports", roles: ["admin", "faculty"], render: reportsPage },
};

async function dashboardPage(v) {
  const d = await get("/dashboard");
  let top = "";
  if (me.role === "admin") {
    const s = d.stats;
    top = `<div class="stats">${[["Students", s.students], ["Faculty", s.faculty], ["Courses", s.courses], ["Departments", s.departments],
      ["Avg attendance", (s.avg_attendance ?? 0) + "%"], ["Feedback to review", s.pending_feedback]]
      .map(([l, n]) => `<div class="stat"><div class="n">${esc(n)}</div><div class="l">${l}</div></div>`).join("")}</div>
      <div class="card"><h3>Students below 75% attendance</h3>${table([["Reg no", (r) => esc(r.reg_no)], ["Name", (r) => esc(r.full_name)], ["Course", (r) => esc(r.code)], ["Attendance", (r) => pctBar(r.pct)]], s.low_attendance, "Everyone is above 75%.")}</div>`;
  } else if (me.role === "student") {
    top = `<div class="grid2"><div class="card"><h3>My attendance</h3>${table([["Course", (r) => `${esc(r.course_code)} <span class="muted">${esc(r.course_title)}</span>`], ["Classes", (r) => `${r.attended}/${r.total_classes}`], ["%", (r) => pctBar(r.percentage)]], d.attendance)}</div>
      <div class="card"><h3>My marks</h3>${table([["Course", (r) => esc(r.course_code)], ["Score", (r) => `${r.obtained}/${r.maximum}`], ["%", (r) => pctBar(r.percentage)]], d.marks)}</div></div>`;
  } else {
    top = `<div class="stats"><div class="stat"><div class="n">${d.courses.length}</div><div class="l">Courses I teach</div></div>
      <div class="stat"><div class="n">${d.courses.reduce((a, c) => a + (c.enrollments[0]?.count || 0), 0)}</div><div class="l">Students enrolled</div></div>
      <div class="stat"><div class="n">${d.pending_responses}</div><div class="l">Feedback awaiting my response</div></div></div>
      <div class="card"><h3>My courses</h3>${table([["Code", (r) => esc(r.code)], ["Title", (r) => esc(r.title)], ["Students", (r) => r.enrollments[0]?.count || 0]], d.courses)}</div>`;
  }
  v.innerHTML = `${top}<div class="grid2">
    <div class="card"><h3>Latest notices</h3><div class="list">${d.notices.map(noticeItem).join("") || '<p class="muted">No notices.</p>'}</div></div>
    <div class="card"><h3>Upcoming events</h3><div class="list">${d.events.map(eventItem).join("") || '<p class="muted">No upcoming events.</p>'}</div></div></div>`;
}

const noticeItem = (n) => `<div class="item"><b>${esc(n.title)}</b> <span class="badge">${esc(n.audience)}</span><div>${esc(n.body)}</div><div class="meta">${esc(n.author?.full_name)} · ${fmtDateTime(n.created_at)}</div></div>`;
const eventItem = (e) => `<div class="item"><b>${esc(e.title)}</b><div>${esc(e.description)}</div><div class="meta">${fmtDateTime(e.starts_at)} · ${esc(e.location)}</div></div>`;

async function usersPage(v) {
  const role = usersPage.role || "";
  const [users, depts] = await Promise.all([get(`/users${role ? `?role=${role}` : ""}`), get("/departments")]);
  v.innerHTML = `<div class="toolbar"><label>Role<select id="f-role"><option value="">All</option>${["admin", "faculty", "student"].map((r) => `<option ${r === role ? "selected" : ""}>${r}</option>`).join("")}</select></label>
    <button class="btn primary" id="add">+ Add user</button></div>
    <div class="card">${table([["Name", (u) => esc(u.full_name)], ["Email", (u) => esc(u.email)], ["Role", (u) => `<span class="badge">${u.role}</span>`],
      ["Reg no", (u) => esc(u.reg_no)], ["Dept", (u) => esc(u.department?.code)], ["", (u) => u.id === me.id ? "" : `<button class="btn small" data-edit="${u.id}">Edit</button> <button class="btn small danger" data-del="${u.id}">Delete</button>`]], users)}</div>`;
  $("#f-role").onchange = (e) => { usersPage.role = e.target.value; render(); };
  const deptOpts = (sel) => `<option value="">—</option>${options(depts, (d) => d.id, (d) => `${d.code} — ${d.name}`, sel)}`;
  $("#add").onclick = () => form("Add user", [
    { name: "full_name", label: "Full name" }, { name: "email", label: "Email", type: "email" },
    { name: "password", label: "Initial password", type: "password", attrs: 'minlength="6"' },
    { name: "role", label: "Role", type: "select", options: options(["student", "faculty", "admin"], (r) => r, (r) => r) },
    { name: "reg_no", label: "Registration no (students)", required: false },
    { name: "department_id", label: "Department", type: "select", options: deptOpts(), required: false },
    { name: "phone", label: "Phone", required: false }], async (d) => { await post("/users", d); toast("User created"); render(); });
  v.querySelectorAll("[data-edit]").forEach((b) => (b.onclick = () => {
    const u = users.find((x) => x.id === b.dataset.edit);
    form(`Edit ${u.full_name}`, [{ name: "full_name", label: "Full name", value: u.full_name },
      { name: "role", label: "Role", type: "select", options: options(["student", "faculty", "admin"], (r) => r, (r) => r, u.role) },
      { name: "reg_no", label: "Registration no", value: u.reg_no, required: false },
      { name: "department_id", label: "Department", type: "select", options: deptOpts(u.department_id), required: false },
      { name: "phone", label: "Phone", value: u.phone, required: false }], async (d) => { await patch(`/users/${u.id}`, d); toast("Saved"); render(); });
  }));
  v.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => confirmDo("Delete this user's profile and all their records?", () => del(`/users/${b.dataset.del}`))));
}

async function departmentsPage(v) {
  const depts = await get("/departments");
  v.innerHTML = `<div class="toolbar"><button class="btn primary" id="add">+ Add department</button></div>
    <div class="card">${table([["Code", (d) => esc(d.code)], ["Name", (d) => esc(d.name)], ["", (d) => `<button class="btn small danger" data-del="${d.id}">Delete</button>`]], depts)}</div>`;
  $("#add").onclick = () => form("Add department", [{ name: "code", label: "Code" }, { name: "name", label: "Name" }], async (d) => { await post("/departments", d); render(); });
  v.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => confirmDo("Delete department?", () => del(`/departments/${b.dataset.del}`))));
}

async function coursesPage(v) {
  const courses = await get("/courses");
  const mine = me.role === "student" ? new Set((await get(`/enrollments?student_id=${me.id}`)).map((e) => e.course_id)) : null;
  const list = mine ? courses.filter((c) => mine.has(c.id)) : courses;
  const admin = me.role === "admin";
  v.innerHTML = `${admin ? '<div class="toolbar"><button class="btn primary" id="add">+ Add course</button></div>' : ""}
    <div class="card">${mine ? "<h3>My registered courses</h3>" : ""}${table([["Code", (c) => esc(c.code)], ["Title", (c) => esc(c.title)], ["Credits", (c) => c.credits],
      ["Dept", (c) => esc(c.department?.code)], ["Faculty", (c) => esc(c.faculty?.full_name)], ["Students", (c) => c.enrollments[0]?.count ?? ""],
      ...(admin ? [["", (c) => `<button class="btn small" data-enr="${c.id}">Students</button> <button class="btn small" data-edit="${c.id}">Edit</button> <button class="btn small danger" data-del="${c.id}">Delete</button>`]] : [])], list)}</div>
    <div id="enr"></div>`;
  if (!admin) return;
  const [faculty, depts] = await Promise.all([get("/users?role=faculty"), get("/departments")]);
  const courseForm = (c = {}) => form(c.id ? "Edit course" : "Add course", [
    { name: "code", label: "Code", value: c.code }, { name: "title", label: "Title", value: c.title },
    { name: "credits", label: "Credits", type: "number", value: c.credits ?? 3 },
    { name: "department_id", label: "Department", type: "select", options: options(depts, (d) => d.id, (d) => d.code, c.department_id) },
    { name: "faculty_id", label: "Faculty", type: "select", options: `<option value="">—</option>` + options(faculty, (f) => f.id, (f) => f.full_name, c.faculty_id), required: false }],
    async (d) => { c.id ? await patch(`/courses/${c.id}`, d) : await post("/courses", d); toast("Saved"); render(); });
  $("#add").onclick = () => courseForm();
  v.querySelectorAll("[data-edit]").forEach((b) => (b.onclick = () => courseForm(courses.find((c) => c.id == b.dataset.edit))));
  v.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => confirmDo("Delete course and all its attendance/marks?", () => del(`/courses/${b.dataset.del}`))));
  v.querySelectorAll("[data-enr]").forEach((b) => (b.onclick = () => enrollmentPanel(courses.find((c) => c.id == b.dataset.enr))));
}

async function enrollmentPanel(course) {
  const [enr, students] = await Promise.all([get(`/enrollments?course_id=${course.id}`), get("/users?role=student")]);
  const ids = new Set(enr.map((e) => e.student_id));
  const box = $("#enr");
  box.innerHTML = `<div class="card"><h3>${esc(course.code)} — enrolled students</h3>
    <div class="toolbar"><label>Add student<select id="enr-s">${options(students.filter((s) => !ids.has(s.id)), (s) => s.id, (s) => `${s.reg_no || ""} ${s.full_name}`)}</select></label><button class="btn primary" id="enr-add">Enroll</button></div>
    ${table([["Reg no", (e) => esc(e.student.reg_no)], ["Name", (e) => esc(e.student.full_name)], ["", (e) => `<button class="btn small danger" data-un="${e.student_id}">Remove</button>`]], enr)}</div>`;
  $("#enr-add").onclick = async () => { try { await post("/enrollments", { student_id: $("#enr-s").value, course_id: course.id }); enrollmentPanel(course); } catch (e) { toast(e.message, true); } };
  box.querySelectorAll("[data-un]").forEach((b) => (b.onclick = async () => { await del(`/enrollments/${b.dataset.un}:${course.id}`); enrollmentPanel(course); }));
  box.scrollIntoView({ behavior: "smooth" });
}

async function timetablePage(v) {
  let slots = await get("/timetable");
  if (me.role !== "admin") {
    const allowed = me.role === "student"
      ? new Set((await get(`/enrollments?student_id=${me.id}`)).map((e) => e.course_id))
      : new Set((await get(`/courses?faculty_id=${me.id}`)).map((c) => c.id));
    slots = slots.filter((s) => allowed.has(s.course_id));
  }
  const admin = me.role === "admin";
  v.innerHTML = `${admin ? '<div class="toolbar"><button class="btn primary" id="add">+ Add class slot</button></div>' : ""}
    <div class="card"><div class="tt">${[1, 2, 3, 4, 5, 6].map((d) => `<div class="day"><h4>${DAYS[d]}</h4>${slots.filter((s) => s.day_of_week === d).map((s) => `
      <div class="slot"><b>${esc(s.course.code)}</b>${esc(s.course.title)}<div class="muted">${s.start_time.slice(0, 5)}–${s.end_time.slice(0, 5)} · ${esc(s.room)}</div>
      ${admin ? `<button class="btn small danger" data-del="${s.id}">Remove</button>` : ""}</div>`).join("") || '<p class="muted">—</p>'}</div>`).join("")}</div></div>`;
  if (!admin) return;
  const courses = await get("/courses");
  $("#add").onclick = () => form("Add class slot", [
    { name: "course_id", label: "Course", type: "select", options: options(courses, (c) => c.id, (c) => `${c.code} ${c.title}`) },
    { name: "day_of_week", label: "Day", type: "select", options: [1, 2, 3, 4, 5, 6].map((d) => `<option value="${d}">${DAYS[d]}</option>`).join("") },
    { name: "start_time", label: "Start", type: "time" }, { name: "end_time", label: "End", type: "time" }, { name: "room", label: "Room", required: false }],
    async (d) => { await post("/timetable", d); render(); });
  v.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => confirmDo("Remove this slot?", () => del(`/timetable/${b.dataset.del}`))));
}

async function teachableCourses() {
  return me.role === "admin" ? get("/courses") : get(`/courses?faculty_id=${me.id}`);
}

async function attendancePage(v) {
  if (me.role === "student") {
    const [summary, recent] = await Promise.all([get(`/reports/attendance?student_id=${me.id}`), get(`/attendance?student_id=${me.id}`)]);
    v.innerHTML = `<div class="card"><h3>Summary</h3>${table([["Course", (r) => `${esc(r.course_code)} <span class="muted">${esc(r.course_title)}</span>`], ["Attended", (r) => `${r.attended}/${r.total_classes}`], ["%", (r) => pctBar(r.percentage)]], summary)}</div>
      <div class="card"><h3>Class log</h3>${table([["Date", (r) => fmtDate(r.class_date)], ["Course", (r) => esc(r.course.code)], ["Status", (r) => statusBadge(r.status)]], recent)}</div>`;
    return;
  }
  const courses = await teachableCourses();
  const st = (attendancePage.state ||= { course: courses[0]?.id, date: today() });
  v.innerHTML = `<div class="toolbar"><label>Course<select id="a-course">${options(courses, (c) => c.id, (c) => `${c.code} ${c.title}`, st.course)}</select></label>
    <label>Date<input type="date" id="a-date" value="${st.date}" max="${today()}"></label>
    <button class="btn" id="all-p">Mark all present</button></div><div class="card" id="sheet">Loading…</div>`;
  $("#a-course").onchange = (e) => { st.course = e.target.value; render(); };
  $("#a-date").onchange = (e) => { st.date = e.target.value; render(); };
  if (!st.course) return ($("#sheet").innerHTML = '<p class="muted">No courses assigned.</p>');
  const rows = await get(`/attendance/sheet?course_id=${st.course}&class_date=${st.date}`);
  $("#sheet").innerHTML = rows.length ? `${table([["Reg no", (r) => esc(r.reg_no)], ["Name", (r) => esc(r.full_name)],
    ["Status", (r) => `<div class="att-choices">${["present", "absent", "late"].map((s) => `<label><input type="radio" name="s-${r.id}" value="${s}" ${(r.status || "present") === s ? "checked" : ""}>${s}</label>`).join("")}</div>`]], rows)}
    <div class="actions"><span class="muted">${rows.some((r) => r.status) ? "Already marked — saving will update it." : "Not yet marked."}</span><button class="btn primary" id="save">Save attendance</button></div>` : '<p class="muted">No students enrolled.</p>';
  $("#all-p").onclick = () => v.querySelectorAll('input[value="present"]').forEach((i) => (i.checked = true));
  const save = $("#save");
  if (save) save.onclick = async () => {
    const entries = rows.map((r) => ({ student_id: r.id, status: $(`input[name="s-${r.id}"]:checked`).value }));
    try { await post("/attendance/sheet", { course_id: +st.course, class_date: st.date, entries }); toast("Attendance saved"); render(); } catch (e) { toast(e.message, true); }
  };
}

async function marksPage(v) {
  if (me.role === "student") {
    const marks = await get(`/marks?student_id=${me.id}`);
    v.innerHTML = `<div class="card">${table([["Course", (m) => `${esc(m.course.code)} <span class="muted">${esc(m.course.title)}</span>`], ["Assessment", (m) => esc(m.assessment)], ["Marks", (m) => `${m.marks_obtained} / ${m.max_marks}`]], marks)}</div>`;
    return;
  }
  const courses = await teachableCourses();
  const st = (marksPage.state ||= { course: courses[0]?.id });
  const marks = st.course ? await get(`/marks?course_id=${st.course}`) : [];
  v.innerHTML = `<div class="toolbar"><label>Course<select id="m-course">${options(courses, (c) => c.id, (c) => `${c.code} ${c.title}`, st.course)}</select></label>
    <button class="btn primary" id="add">+ Enter marks</button></div>
    <div class="card">${table([["Reg no", (m) => esc(m.student.reg_no)], ["Name", (m) => esc(m.student.full_name)], ["Assessment", (m) => esc(m.assessment)],
      ["Marks", (m) => `${m.marks_obtained} / ${m.max_marks}`], ["", (m) => `<button class="btn small" data-edit="${m.id}">Edit</button> <button class="btn small danger" data-del="${m.id}">Delete</button>`]], marks)}</div>`;
  $("#m-course").onchange = (e) => { st.course = e.target.value; render(); };
  $("#add").onclick = async () => {
    const enr = await get(`/enrollments?course_id=${st.course}`);
    form("Enter marks", [{ name: "student_id", label: "Student", type: "select", options: options(enr, (e) => e.student_id, (e) => `${e.student.reg_no} ${e.student.full_name}`) },
      { name: "assessment", label: "Assessment (e.g. CAT-2)" }, { name: "max_marks", label: "Max marks", type: "number", attrs: 'step="0.5" min="1"' },
      { name: "marks_obtained", label: "Marks obtained", type: "number", attrs: 'step="0.5" min="0"' }],
      async (d) => { await post("/marks", { ...d, course_id: +st.course }); toast("Saved"); render(); });
  };
  v.querySelectorAll("[data-edit]").forEach((b) => (b.onclick = () => {
    const m = marks.find((x) => x.id == b.dataset.edit);
    form(`${m.student.full_name} — ${m.assessment}`, [{ name: "marks_obtained", label: `Marks obtained (max ${m.max_marks})`, type: "number", value: m.marks_obtained, attrs: 'step="0.5" min="0"' }],
      async (d) => { await patch(`/marks/${m.id}`, d); render(); });
  }));
  v.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => confirmDo("Delete this mark entry?", () => del(`/marks/${b.dataset.del}`))));
}

async function noticesPage(v) {
  const notices = await get("/notices");
  const canPost = me.role !== "student";
  v.innerHTML = `${canPost ? '<div class="toolbar"><button class="btn primary" id="add">+ Post notice</button></div>' : ""}
    <div class="card"><div class="list">${notices.map((n) => noticeItem(n) + (me.role === "admin" || n.author_id === me.id ? `<button class="btn small danger" data-del="${n.id}">Delete</button>` : "")).join("") || '<p class="muted">No notices.</p>'}</div></div>`;
  if (canPost) $("#add").onclick = () => form("Post notice", [{ name: "title", label: "Title" }, { name: "body", label: "Message", type: "textarea" },
    { name: "audience", label: "Audience", type: "select", options: options(["all", "student", "faculty"], (a) => a, (a) => a) }], async (d) => { await post("/notices", d); toast("Notice posted"); render(); });
  v.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => confirmDo("Delete notice?", () => del(`/notices/${b.dataset.del}`))));
}

async function eventsPage(v) {
  const events = await get("/events");
  const admin = me.role === "admin";
  v.innerHTML = `${admin ? '<div class="toolbar"><button class="btn primary" id="add">+ Add event</button></div>' : ""}
    <div class="card">${table([["When", (e) => fmtDateTime(e.starts_at)], ["Event", (e) => `<b>${esc(e.title)}</b><div class="muted">${esc(e.description)}</div>`], ["Where", (e) => esc(e.location)],
      ...(admin ? [["", (e) => `<button class="btn small danger" data-del="${e.id}">Delete</button>`]] : [])], events)}</div>`;
  if (!admin) return;
  $("#add").onclick = () => form("Add event", [{ name: "title", label: "Title" }, { name: "description", label: "Description", type: "textarea", required: false },
    { name: "location", label: "Location", required: false }, { name: "starts_at", label: "Starts", type: "datetime-local" }, { name: "ends_at", label: "Ends", type: "datetime-local", required: false }],
    async (d) => {
      d.starts_at = new Date(d.starts_at).toISOString(); if (d.ends_at) d.ends_at = new Date(d.ends_at).toISOString();
      await post("/events", d); render();
    });
  v.querySelectorAll("[data-del]").forEach((b) => (b.onclick = () => confirmDo("Delete event?", () => del(`/events/${b.dataset.del}`))));
}

async function feedbackPage(v) {
  const fb = await get("/feedback");
  const detail = (f) => `<div>${esc(f.feedback_text)}</div>${f.expectations ? `<div class="muted">Expects: ${esc(f.expectations)}</div>` : ""}
    ${f.hod_comments ? `<div><b>HOD:</b> ${esc(f.hod_comments)}</div>` : ""}${f.faculty_response ? `<div><b>Faculty:</b> ${esc(f.faculty_response)}</div><div><b>Action:</b> ${esc(f.action_taken)}</div>` : ""}`;
  const cols = [["Course", (f) => `${esc(f.course.code)}<div class="muted">${esc(f.course.faculty?.full_name)}</div>`], ["Rating", (f) => stars(f.rating)], ["Feedback", detail], ["Status", (f) => statusBadge(f.status)], ["Date", (f) => fmtDate(f.submitted_at)]];
  if (me.role === "student") {
    v.innerHTML = `<div class="toolbar"><button class="btn primary" id="add">+ Give feedback</button></div><div class="card"><h3>My feedback</h3>${table(cols, fb)}</div>`;
    const enr = await get(`/enrollments?student_id=${me.id}`);
    const done = new Set(fb.map((f) => f.course_id));
    $("#add").onclick = () => {
      const open = enr.filter((e) => !done.has(e.course_id));
      if (!open.length) return toast("You've given feedback for all your courses");
      form("Course feedback", [{ name: "course_id", label: "Course", type: "select", options: options(open, (e) => e.course_id, (e) => `${e.course.code} ${e.course.title}`) },
        { name: "rating", label: "Rating", type: "select", options: [5, 4, 3, 2, 1].map((n) => `<option value="${n}">${"★".repeat(n)}</option>`).join("") },
        { name: "feedback_text", label: "Feedback", type: "textarea", attrs: 'minlength="10"' }, { name: "expectations", label: "What would you like improved?", type: "textarea", required: false }],
        async (d) => { await post("/feedback", { ...d, course_id: +d.course_id, rating: +d.rating }); toast("Submitted for HOD review"); render(); });
    };
    return;
  }
  const isAdmin = me.role === "admin";
  const act = (f) => isAdmin && f.status === "Pending HOD Review" ? `<button class="btn small" data-rev="${f.id}">Review</button>`
    : !isAdmin && f.status === "Approved" ? `<button class="btn small primary" data-resp="${f.id}">Respond</button>` : "";
  v.innerHTML = `<div class="card"><p class="muted">${isAdmin ? "As HOD, approve feedback to forward it to the course faculty, or reject it." : "Approved feedback for your courses. Respond with the corrective action taken (ATR)."}</p>
    ${table([["Student", (f) => `${esc(f.student.full_name)}<div class="muted">${esc(f.student.reg_no)}</div>`], ...cols, ["", act]], fb)}</div>`;
  v.querySelectorAll("[data-rev]").forEach((b) => (b.onclick = () => form("Review feedback", [
    { name: "approve", label: "Decision", type: "select", options: '<option value="1">Approve — forward to faculty</option><option value="0">Reject</option>' },
    { name: "comments", label: "HOD comments", type: "textarea", required: false }], async (d) => { await post(`/feedback/${b.dataset.rev}/review`, { approve: d.approve === "1", comments: d.comments }); toast("Reviewed"); render(); })));
  v.querySelectorAll("[data-resp]").forEach((b) => (b.onclick = () => form("Action taken report", [
    { name: "response", label: "Response to student", type: "textarea" }, { name: "action_taken", label: "Corrective action taken", type: "textarea" }],
    async (d) => { await post(`/feedback/${b.dataset.resp}/respond`, { response: d.response, action_taken: d.action_taken }); toast("Response recorded"); render(); })));
}

async function reportsPage(v) {
  const kind = reportsPage.kind || "attendance";
  const courses = await teachableCourses();
  const course = reportsPage.course || "";
  const rows = await get(`/reports/${kind}${course ? `?course_id=${course}` : ""}`);
  const cols = kind === "atr"
    ? [["Course", (f) => esc(f.course.code)], ["Student", (f) => esc(f.student.full_name)], ["Rating", (f) => stars(f.rating)], ["Feedback", (f) => esc(f.feedback_text)], ["Action taken", (f) => esc(f.action_taken)], ["Date", (f) => fmtDate(f.action_date)]]
    : [["Reg no", (r) => esc(r.reg_no)], ["Name", (r) => esc(r.full_name)], ["Course", (r) => esc(r.course_code)],
      kind === "attendance" ? ["Classes", (r) => `${r.attended}/${r.total_classes}`] : ["Score", (r) => `${r.obtained}/${r.maximum}`], ["%", (r) => pctBar(r.percentage)]];
  v.innerHTML = `<div class="toolbar">
    <label>Report<select id="r-kind">${options([["attendance", "Attendance summary"], ["marks", "Marks summary"], ["atr", "Action Taken Report (ATR)"]], (k) => k[0], (k) => k[1], kind)}</select></label>
    <label>Course<select id="r-course"><option value="">All my courses</option>${options(courses, (c) => c.id, (c) => c.code, course)}</select></label>
    <button class="btn" id="csv">⬇ Download CSV</button></div><div class="card">${table(cols, rows)}</div>`;
  $("#r-kind").onchange = (e) => { reportsPage.kind = e.target.value; render(); };
  $("#r-course").onchange = (e) => { reportsPage.course = e.target.value; render(); };
  $("#csv").onclick = () => download(`/reports/${kind}.csv${course ? `?course_id=${course}` : ""}`, `${kind}_report.csv`);
}

// ------------------------------------------------------------------ shell
function currentPage() {
  const p = location.hash.slice(1);
  return PAGES[p] && PAGES[p].roles.includes(me.role) ? p : "dashboard";
}

async function render() {
  const key = currentPage();
  $("#nav").innerHTML = Object.entries(PAGES).filter(([, p]) => p.roles.includes(me.role))
    .map(([k, p]) => `<a href="#${k}" class="${k === key ? "active" : ""}">${p.title}</a>`).join("");
  $("#page-title").textContent = PAGES[key].title;
  const v = $("#view");
  v.innerHTML = '<p class="muted">Loading…</p>';
  try { await PAGES[key].render(v); } catch (e) { v.innerHTML = `<p class="error">${esc(e.message)}</p>`; }
}

function logout() {
  session = me = null; localStorage.removeItem("su_session");
  $("#shell").classList.add("hidden"); $("#login").classList.remove("hidden");
}

async function start() {
  if (!session) return logout();
  try { me = await get("/me"); } catch { return logout(); }
  $("#who-name").textContent = me.full_name;
  $("#who-role").textContent = me.role;
  $("#login").classList.add("hidden"); $("#shell").classList.remove("hidden");
  render();
}

$("#login-form").onsubmit = async (e) => {
  e.preventDefault();
  $("#login-error").textContent = "";
  try {
    const r = await post("/auth/login", Object.fromEntries(new FormData(e.target)));
    session = { access_token: r.access_token, refresh_token: r.refresh_token }; saveSession();
    location.hash = ""; start();
  } catch (err) { $("#login-error").textContent = err.message; }
};
$("#logout").onclick = logout;
$("#menu").onclick = () => $(".sidebar").classList.toggle("open");
window.addEventListener("hashchange", () => { $(".sidebar").classList.remove("open"); if (me) render(); });
start();
