-- Smart University Management System - Supabase schema
-- Run once in the Supabase SQL editor on a fresh project.

create extension if not exists pgcrypto with schema extensions;

create type public.user_role as enum ('admin','faculty','student');
create type public.attendance_status as enum ('present','absent','late');
create type public.feedback_status as enum ('Pending HOD Review','Approved','Rejected','Faculty Responded');
create type public.notice_audience as enum ('all','student','faculty');

create table public.departments (
  id bigint generated always as identity primary key,
  code text not null unique,
  name text not null
);

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  full_name text not null,
  role public.user_role not null default 'student',
  reg_no text unique,
  department_id bigint references public.departments(id) on delete set null,
  phone text,
  created_at timestamptz not null default now()
);

create table public.courses (
  id bigint generated always as identity primary key,
  code text not null unique,
  title text not null,
  credits int not null default 3 check (credits between 0 and 10),
  department_id bigint references public.departments(id) on delete set null,
  faculty_id uuid references public.profiles(id) on delete set null
);

create table public.enrollments (
  student_id uuid not null references public.profiles(id) on delete cascade,
  course_id bigint not null references public.courses(id) on delete cascade,
  enrolled_at timestamptz not null default now(),
  primary key (student_id, course_id)
);

create table public.timetable (
  id bigint generated always as identity primary key,
  course_id bigint not null references public.courses(id) on delete cascade,
  day_of_week int not null check (day_of_week between 1 and 7),
  start_time time not null,
  end_time time not null,
  room text,
  check (end_time > start_time)
);

create table public.attendance (
  id bigint generated always as identity primary key,
  course_id bigint not null references public.courses(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  class_date date not null,
  status public.attendance_status not null,
  marked_by uuid references public.profiles(id) on delete set null,
  unique (course_id, student_id, class_date)
);

create table public.marks (
  id bigint generated always as identity primary key,
  course_id bigint not null references public.courses(id) on delete cascade,
  student_id uuid not null references public.profiles(id) on delete cascade,
  assessment text not null,
  max_marks numeric(6,2) not null check (max_marks > 0),
  marks_obtained numeric(6,2) not null check (marks_obtained >= 0),
  check (marks_obtained <= max_marks),
  unique (course_id, student_id, assessment)
);

create table public.notices (
  id bigint generated always as identity primary key,
  title text not null,
  body text not null,
  audience public.notice_audience not null default 'all',
  author_id uuid references public.profiles(id) on delete set null default auth.uid(),
  created_at timestamptz not null default now()
);

create table public.events (
  id bigint generated always as identity primary key,
  title text not null,
  description text,
  location text,
  starts_at timestamptz not null,
  ends_at timestamptz,
  created_by uuid references public.profiles(id) on delete set null default auth.uid()
);

create table public.feedback (
  id bigint generated always as identity primary key,
  student_id uuid not null references public.profiles(id) on delete cascade default auth.uid(),
  course_id bigint not null references public.courses(id) on delete cascade,
  feedback_text text not null,
  expectations text,
  rating int not null check (rating between 1 and 5),
  status public.feedback_status not null default 'Pending HOD Review',
  hod_comments text,
  faculty_response text,
  action_taken text,
  submitted_at timestamptz not null default now(),
  action_date timestamptz,
  unique (student_id, course_id)
);

create index on public.courses(faculty_id);
create index on public.courses(department_id);
create index on public.profiles(department_id);
create index on public.enrollments(course_id);
create index on public.timetable(course_id);
create index on public.attendance(student_id);
create index on public.marks(student_id);
create index on public.feedback(course_id);
create index on public.feedback(status);
create index on public.notices(author_id);
create index on public.events(created_by);
create index on public.attendance(marked_by);

-- helpers
create or replace function public.my_role() returns public.user_role
language sql stable security definer set search_path = '' as
$$ select role from public.profiles where id = (select auth.uid()) $$;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = '' as
$$ select coalesce((select role = 'admin' from public.profiles where id = (select auth.uid())), false) $$;

create or replace function public.teaches(p_course bigint) returns boolean
language sql stable security definer set search_path = '' as
$$ select exists(select 1 from public.courses where id = p_course and faculty_id = (select auth.uid())) $$;

create or replace function public.teaches_student(p_student uuid) returns boolean
language sql stable security definer set search_path = '' as
$$ select exists(select 1 from public.enrollments e join public.courses c on c.id = e.course_id
                 where e.student_id = p_student and c.faculty_id = (select auth.uid())) $$;

-- new auth user -> profile
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, email, full_name, role, reg_no, department_id, phone)
  values (new.id, new.email,
          coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email,'@',1)),
          coalesce((new.raw_user_meta_data->>'role')::public.user_role, 'student'),
          nullif(new.raw_user_meta_data->>'reg_no',''),
          nullif(new.raw_user_meta_data->>'department_id','')::bigint,
          nullif(new.raw_user_meta_data->>'phone',''));
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- admin creates an account (no service key needed)
create or replace function public.admin_create_user(
  p_email text, p_password text, p_full_name text, p_role public.user_role,
  p_reg_no text default null, p_department_id bigint default null, p_phone text default null)
returns uuid language plpgsql security definer set search_path = '' as $$
declare uid uuid := gen_random_uuid();
begin
  if not public.is_admin() then raise exception 'Only admins can create users' using errcode = '42501'; end if;
  if length(coalesce(p_password,'')) < 6 then raise exception 'Password must be at least 6 characters'; end if;
  insert into auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
    raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
    confirmation_token, recovery_token, email_change, email_change_token_new)
  values ('00000000-0000-0000-0000-000000000000', uid, 'authenticated', 'authenticated', lower(p_email),
    extensions.crypt(p_password, extensions.gen_salt('bf')), now(),
    '{"provider":"email","providers":["email"]}',
    jsonb_build_object('full_name', p_full_name, 'role', p_role, 'reg_no', coalesce(p_reg_no,''),
                       'department_id', coalesce(p_department_id::text,''), 'phone', coalesce(p_phone,'')),
    now(), now(), '', '', '', '');
  insert into auth.identities (id, user_id, provider_id, identity_data, provider, created_at, updated_at, last_sign_in_at)
  values (gen_random_uuid(), uid, uid::text,
    jsonb_build_object('sub', uid::text, 'email', lower(p_email), 'email_verified', true),
    'email', now(), now(), now());
  return uid;
end $$;

-- feedback workflow (ATR)
create or replace function public.review_feedback(p_id bigint, p_approve boolean, p_comments text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_admin() then raise exception 'Only admin/HOD can review feedback' using errcode='42501'; end if;
  update public.feedback set status = case when p_approve then 'Approved' else 'Rejected' end::public.feedback_status,
         hod_comments = p_comments
   where id = p_id and status = 'Pending HOD Review';
  if not found then raise exception 'Feedback not found or already reviewed'; end if;
end $$;

create or replace function public.respond_feedback(p_id bigint, p_response text, p_action text)
returns void language plpgsql security definer set search_path = '' as $$
begin
  update public.feedback f set faculty_response = p_response, action_taken = p_action,
         status = 'Faculty Responded', action_date = now()
   where f.id = p_id and f.status = 'Approved' and public.teaches(f.course_id);
  if not found then raise exception 'Feedback not found, not approved, or not your course'; end if;
end $$;

-- reports (invoker => RLS applies)
create or replace view public.attendance_summary with (security_invoker = true) as
select a.student_id, p.full_name, p.reg_no, a.course_id, c.code as course_code, c.title as course_title,
       count(*) as total_classes,
       count(*) filter (where a.status in ('present','late')) as attended,
       round(100.0 * count(*) filter (where a.status in ('present','late')) / count(*), 1) as percentage
from public.attendance a join public.profiles p on p.id = a.student_id join public.courses c on c.id = a.course_id
group by a.student_id, p.full_name, p.reg_no, a.course_id, c.code, c.title;

create or replace view public.marks_summary with (security_invoker = true) as
select m.student_id, p.full_name, p.reg_no, m.course_id, c.code as course_code, c.title as course_title,
       sum(m.marks_obtained) as obtained, sum(m.max_marks) as maximum,
       round(100.0 * sum(m.marks_obtained) / sum(m.max_marks), 1) as percentage
from public.marks m join public.profiles p on p.id = m.student_id join public.courses c on c.id = m.course_id
group by m.student_id, p.full_name, p.reg_no, m.course_id, c.code, c.title;

create or replace function public.dashboard_stats() returns json
language sql stable security definer set search_path = '' as $$
  select case when public.is_admin() then json_build_object(
    'students', (select count(*) from public.profiles where role='student'),
    'faculty', (select count(*) from public.profiles where role='faculty'),
    'courses', (select count(*) from public.courses),
    'departments', (select count(*) from public.departments),
    'pending_feedback', (select count(*) from public.feedback where status='Pending HOD Review'),
    'avg_attendance', (select round(100.0*count(*) filter (where status in ('present','late'))/nullif(count(*),0),1) from public.attendance),
    'low_attendance', (select coalesce(json_agg(x),'[]') from (
        select p.full_name, p.reg_no, c.code, round(100.0*count(*) filter (where a.status in ('present','late'))/count(*),1) pct
        from public.attendance a join public.profiles p on p.id=a.student_id join public.courses c on c.id=a.course_id
        group by p.full_name,p.reg_no,c.code having 100.0*count(*) filter (where a.status in ('present','late'))/count(*) < 75
        order by pct limit 10) x),
    'feedback_by_status', (select coalesce(json_object_agg(status, n),'{}') from (select status, count(*) n from public.feedback group by status) s)
  ) else null end
$$;

-- RLS
alter table public.departments enable row level security;
alter table public.profiles enable row level security;
alter table public.courses enable row level security;
alter table public.enrollments enable row level security;
alter table public.timetable enable row level security;
alter table public.attendance enable row level security;
alter table public.marks enable row level security;
alter table public.notices enable row level security;
alter table public.events enable row level security;
alter table public.feedback enable row level security;

create policy "read departments" on public.departments for select to authenticated using (true);
create policy "admin departments" on public.departments for all to authenticated using (public.is_admin()) with check (public.is_admin());

create policy "read profiles" on public.profiles for select to authenticated
  using (id = (select auth.uid()) or public.is_admin() or role <> 'student' or public.teaches_student(id));
create policy "admin update profiles" on public.profiles for update to authenticated using (public.is_admin()) with check (public.is_admin());
create policy "admin delete profiles" on public.profiles for delete to authenticated using (public.is_admin());

create policy "read courses" on public.courses for select to authenticated using (true);
create policy "admin courses" on public.courses for all to authenticated using (public.is_admin()) with check (public.is_admin());

create policy "read enrollments" on public.enrollments for select to authenticated
  using (student_id = (select auth.uid()) or public.is_admin() or public.teaches(course_id));
create policy "admin enrollments" on public.enrollments for all to authenticated using (public.is_admin()) with check (public.is_admin());

create policy "read timetable" on public.timetable for select to authenticated using (true);
create policy "admin timetable" on public.timetable for all to authenticated using (public.is_admin()) with check (public.is_admin());

create policy "read attendance" on public.attendance for select to authenticated
  using (student_id = (select auth.uid()) or public.is_admin() or public.teaches(course_id));
create policy "write attendance" on public.attendance for all to authenticated
  using (public.is_admin() or public.teaches(course_id)) with check (public.is_admin() or public.teaches(course_id));

create policy "read marks" on public.marks for select to authenticated
  using (student_id = (select auth.uid()) or public.is_admin() or public.teaches(course_id));
create policy "write marks" on public.marks for all to authenticated
  using (public.is_admin() or public.teaches(course_id)) with check (public.is_admin() or public.teaches(course_id));

create policy "read notices" on public.notices for select to authenticated
  using (audience = 'all' or public.is_admin() or audience::text = public.my_role()::text or author_id = (select auth.uid()));
create policy "post notices" on public.notices for insert to authenticated
  with check (public.my_role() in ('admin','faculty') and author_id = (select auth.uid()));
create policy "delete notices" on public.notices for delete to authenticated
  using (public.is_admin() or author_id = (select auth.uid()));

create policy "read events" on public.events for select to authenticated using (true);
create policy "admin events" on public.events for all to authenticated using (public.is_admin()) with check (public.is_admin());

create policy "read feedback" on public.feedback for select to authenticated
  using (student_id = (select auth.uid()) or public.is_admin()
         or (public.teaches(course_id) and status in ('Approved','Faculty Responded')));
create policy "submit feedback" on public.feedback for insert to authenticated
  with check (student_id = (select auth.uid()) and status = 'Pending HOD Review'
              and exists(select 1 from public.enrollments e where e.student_id = (select auth.uid()) and e.course_id = feedback.course_id));

revoke execute on function public.admin_create_user, public.review_feedback, public.respond_feedback, public.dashboard_stats from anon, public;
grant execute on function public.admin_create_user, public.review_feedback, public.respond_feedback, public.dashboard_stats to authenticated;


create or replace function public.admin_delete_user(p_id uuid) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.is_admin() then raise exception 'Only admins can delete users' using errcode = '42501'; end if;
  if p_id = (select auth.uid()) then raise exception 'You cannot delete your own account'; end if;
  delete from auth.users where id = p_id;  -- cascades to profiles and their records
  if not found then raise exception 'User not found'; end if;
end $$;
revoke execute on function public.admin_delete_user from anon, public;
grant execute on function public.admin_delete_user to authenticated;

revoke execute on function public.handle_new_user() from anon, authenticated, public;
revoke execute on function public.is_admin(), public.my_role(), public.teaches(bigint), public.teaches_student(uuid) from anon, public;
grant execute on function public.is_admin(), public.my_role(), public.teaches(bigint), public.teaches_student(uuid) to authenticated;
