-- Demo data. Every account's password is Password@123 (test data only).

do $$
declare
  u record; uid uuid;
begin
  insert into public.departments(code,name) values ('CSE','Computer Science & Engineering'),('ECE','Electronics & Communication'),('MAT','Mathematics');
  for u in select * from (values
    ('admin@smartuni.edu','Admin Office','admin',null,null),
    ('soumyajyoti@smartuni.edu','Dr. Soumyajyoti Dey','faculty',null,'CSE'),
    ('rmehta@smartuni.edu','Dr. Ritu Mehta','faculty',null,'ECE'),
    ('akumar@smartuni.edu','Prof. Arjun Kumar','faculty',null,'MAT'),
    ('anushqa@smartuni.edu','Anushqa Dey','student','25MID0030','CSE'),
    ('aishani@smartuni.edu','Aishani Dutta','student','25MID0037','CSE'),
    ('rahul@smartuni.edu','Rahul Sharma','student','25MID0041','CSE'),
    ('priya@smartuni.edu','Priya Nair','student','25MID0045','ECE'),
    ('vikram@smartuni.edu','Vikram Singh','student','25MID0052','ECE'),
    ('sneha@smartuni.edu','Sneha Iyer','student','25MID0058','MAT')) t(email,name,role,reg,dept)
  loop
    uid := gen_random_uuid();
    insert into auth.users (instance_id,id,aud,role,email,encrypted_password,email_confirmed_at,raw_app_meta_data,raw_user_meta_data,created_at,updated_at,confirmation_token,recovery_token,email_change,email_change_token_new)
    values ('00000000-0000-0000-0000-000000000000',uid,'authenticated','authenticated',u.email,
      extensions.crypt('Password@123', extensions.gen_salt('bf')), now(),
      '{"provider":"email","providers":["email"]}',
      jsonb_build_object('full_name',u.name,'role',u.role,'reg_no',coalesce(u.reg,''),
        'department_id',coalesce((select id::text from public.departments where code=u.dept),'')),
      now(),now(),'','','','');
    insert into auth.identities (id,user_id,provider_id,identity_data,provider,created_at,updated_at,last_sign_in_at)
    values (gen_random_uuid(),uid,uid::text,jsonb_build_object('sub',uid::text,'email',u.email,'email_verified',true),'email',now(),now(),now());
  end loop;

  insert into public.courses(code,title,credits,department_id,faculty_id)
  select c.code,c.title,c.cr,(select id from public.departments where code=c.d),(select id from public.profiles where email=c.f)
  from (values ('CSE2004','Database Management Systems',4,'CSE','soumyajyoti@smartuni.edu'),
               ('CSE2001','Data Structures & Algorithms',4,'CSE','soumyajyoti@smartuni.edu'),
               ('ECE2002','Digital Logic Design',3,'ECE','rmehta@smartuni.edu'),
               ('MAT2001','Linear Algebra',3,'MAT','akumar@smartuni.edu'),
               ('MAT2003','Probability & Statistics',3,'MAT','akumar@smartuni.edu')) c(code,title,cr,d,f);

  insert into public.enrollments(student_id,course_id)
  select p.id,c.id from public.profiles p cross join public.courses c
  where p.role='student' and (c.code like 'MAT%' or left(c.code,3)=(select code from public.departments where id=p.department_id));

  insert into public.timetable(course_id,day_of_week,start_time,end_time,room)
  select (select id from public.courses where code=t.c),t.d,t.s::time,t.e::time,t.r from (values
   ('CSE2004',1,'09:00','09:50','SJT-301'),('CSE2004',3,'09:00','09:50','SJT-301'),('CSE2004',5,'14:00','15:40','Lab-2'),
   ('CSE2001',2,'10:00','10:50','SJT-205'),('CSE2001',4,'10:00','10:50','SJT-205'),
   ('ECE2002',1,'11:00','11:50','TT-102'),('ECE2002',3,'11:00','11:50','TT-102'),
   ('MAT2001',2,'08:00','08:50','MB-110'),('MAT2001',4,'08:00','08:50','MB-110'),
   ('MAT2003',1,'14:00','14:50','MB-112'),('MAT2003',5,'09:00','09:50','MB-112')) t(c,d,s,e,r);

  insert into public.attendance(course_id,student_id,class_date,status,marked_by)
  select tt.course_id,e.student_id,d::date,
    (case when random()<0.12 then 'absent' when random()<0.06 then 'late' else 'present' end)::public.attendance_status,
    c.faculty_id
  from public.timetable tt join public.courses c on c.id=tt.course_id join public.enrollments e on e.course_id=tt.course_id
  cross join generate_series(current_date-28, current_date-1, '1 day') d
  where extract(isodow from d)=tt.day_of_week
  on conflict do nothing;
  -- one chronic absentee for the low-attendance report
  update public.attendance set status='absent' where student_id=(select id from public.profiles where email='rahul@smartuni.edu') and id%3<>0;

  insert into public.marks(course_id,student_id,assessment,max_marks,marks_obtained)
  select e.course_id,e.student_id,a.n,a.m,round((a.m*(0.5+random()*0.5))::numeric,1)
  from public.enrollments e cross join (values ('CAT-1',50),('Quiz-1',10),('Assignment',20)) a(n,m);

  insert into public.notices(title,body,audience,author_id) values
   ('Mid-semester exam schedule','CAT-2 exams start on 10 November. Check the timetable page for rooms.','all',(select id from public.profiles where email='admin@smartuni.edu')),
   ('Faculty meeting','Department heads meeting on Friday 4 PM in the Senate Hall.','faculty',(select id from public.profiles where email='admin@smartuni.edu')),
   ('DBMS lab submission','Submit lab record 5 (normalisation) by Monday.','student',(select id from public.profiles where email='soumyajyoti@smartuni.edu'));

  insert into public.events(title,description,location,starts_at,ends_at,created_by) values
   ('Tech Fest 2026','Annual technical festival with hackathon and project expo.','Main Auditorium',now()+interval '12 days',now()+interval '14 days',(select id from public.profiles where email='admin@smartuni.edu')),
   ('Guest Lecture: Smart Campuses','Talk on IoT and data platforms in higher education.','Seminar Hall 2',now()+interval '5 days',now()+interval '5 days 2 hours',(select id from public.profiles where email='admin@smartuni.edu'));

  insert into public.feedback(student_id,course_id,feedback_text,expectations,rating,status,hod_comments,faculty_response,action_taken,action_date)
  values
   ((select id from public.profiles where email='anushqa@smartuni.edu'),(select id from public.courses where code='CSE2004'),'Lectures are clear but lab sessions feel rushed.','More time for SQL practice in labs.',4,'Pending HOD Review',null,null,null,null),
   ((select id from public.profiles where email='aishani@smartuni.edu'),(select id from public.courses where code='CSE2004'),'Would like more real-world case studies.','Industry examples of schema design.',4,'Approved','Valid suggestion, forwarded.',null,null,null),
   ((select id from public.profiles where email='priya@smartuni.edu'),(select id from public.courses where code='MAT2001'),'Pace is too fast in the eigenvalues unit.','Extra tutorial session.',3,'Faculty Responded','Approved.','Agreed, will slow down.','Added a weekly Saturday tutorial.',now());
end $$;
