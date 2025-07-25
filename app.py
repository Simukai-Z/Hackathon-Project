import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from uuid import uuid4
import datetime

app = Flask(__name__)
app.secret_key = 'studycoach_secret_key'

USERS_FILE = 'users.json'
CLASSROOMS_FILE = 'classrooms.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {"students": [], "teachers": []}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_classrooms():
    if not os.path.exists(CLASSROOMS_FILE):
        return {"classrooms": []}
    with open(CLASSROOMS_FILE, 'r') as f:
        return json.load(f)

def save_classrooms(classrooms):
    with open(CLASSROOMS_FILE, 'w') as f:
        json.dump(classrooms, f, indent=2)

@app.route('/')
def home():
    if 'user_type' in session:
        if session['user_type'] == 'student':
            return redirect(url_for('student_main'))
        elif session['user_type'] == 'teacher':
            return redirect(url_for('teacher_main'))
    return render_template('home.html')

@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        join_code = request.form.get('join_code')
        users = load_users()
        if any(s['email'] == email for s in users['students']):
            flash('Email already registered as student.')
            return redirect(url_for('student_signup'))
        student = {
            'id': str(uuid4()),
            'name': name,
            'email': email,
            'classrooms': []
        }
        if join_code:
            classrooms = load_classrooms()
            classroom = next((c for c in classrooms['classrooms'] if c['code'] == join_code), None)
            if classroom:
                if join_code not in student['classrooms']:
                    student['classrooms'].append(join_code)
                if email not in classroom['students']:
                    classroom['students'].append(email)
                save_classrooms(classrooms)
            else:
                flash('Invalid classroom join code.')
                return redirect(url_for('student_signup'))
        users['students'].append(student)
        save_users(users)
        session['user_type'] = 'student'
        session['email'] = email
        return redirect(url_for('student_main'))
    return render_template('student_signup.html')

@app.route('/teacher_signup', methods=['GET', 'POST'])
def teacher_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        school = request.form['school']
        class_name = request.form['class_name']
        users = load_users()
        if any(t['email'] == email for t in users['teachers']):
            flash('Email already registered as teacher.')
            return redirect(url_for('teacher_signup'))
        code = uuid4().hex[:8]
        teacher = {
            'id': str(uuid4()),
            'name': name,
            'email': email,
            'school': school,
            'class_name': class_name,
            'classroom_code': code
        }
        users['teachers'].append(teacher)
        save_users(users)
        classrooms = load_classrooms()
        classrooms['classrooms'].append({
            'code': code,
            'teacher_email': email,
            'class_name': class_name,
            'school': school,
            'students': [],
            'rubrics': [],
            'assignments': []
        })
        save_classrooms(classrooms)
        session['user_type'] = 'teacher'
        session['email'] = email
        return redirect(url_for('teacher_main'))
    return render_template('teacher_signup.html')

@app.route('/student_main', methods=['GET', 'POST'])
def student_main():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))

    users = load_users()
    student = next((s for s in users['students'] if s['email'] == session['email']), None)
    classrooms_data = load_classrooms()
    joined_classrooms = []
    schools = {}

    if student and student.get('classrooms'):
        for code in student['classrooms']:
            classroom = next((c for c in classrooms_data['classrooms'] if c['code'] == code), None)
            if classroom:
                joined_classrooms.append(classroom)
                if classroom['school'] not in schools:
                    schools[classroom['school']] = []
                schools[classroom['school']].append(classroom)

    # Handle join classroom form
    if request.method == 'POST':
        join_code = request.form.get('join_code')
        classroom = next((c for c in classrooms_data['classrooms'] if c['code'] == join_code), None)
        if classroom:
            if join_code not in student['classrooms']:
                student['classrooms'].append(join_code)
            if session['email'] not in classroom['students']:
                classroom['students'].append(session['email'])
            save_classrooms(classrooms_data)
            save_users(users)
            users = load_users()
            student = next((s for s in users['students'] if s['email'] == session['email']), None)
            flash('Joined classroom!')
            return redirect(url_for('student_main'))
        else:
            flash('Invalid classroom code.')

    # Stream logic
    selected_class = request.args.get('class')
    class_obj = None
    if selected_class and student and student.get('classrooms'):
        for code in student['classrooms']:
            if str(code).strip() == str(selected_class).strip():
                class_obj = next((c for c in classrooms_data['classrooms'] if str(c['code']).strip() == str(selected_class).strip()), None)
                break

    # Sort rubrics/assignments by timestamp desc, add 'new' badge if <24h
    now = datetime.datetime.utcnow()
    def is_new(ts):
        try:
            dt = datetime.datetime.fromisoformat(ts)
            return (now - dt).total_seconds() < 86400
        except:
            return False

    if class_obj:
        class_obj['rubrics'] = sorted(class_obj.get('rubrics', []), key=lambda r: r.get('timestamp', ''), reverse=True)
        class_obj['assignments'] = sorted(class_obj.get('assignments', []), key=lambda a: a.get('timestamp', ''), reverse=True)
        for r in class_obj['rubrics']:
            r['is_new'] = is_new(r.get('timestamp', ''))
        for a in class_obj['assignments']:
            a['is_new'] = is_new(a.get('timestamp', ''))
        # Attach teacher's name for UI header
        teacher_obj = next((t for t in users['teachers'] if t['email'] == class_obj['teacher_email']), None)
        class_obj['teacher_name'] = teacher_obj['name'] if teacher_obj else None

    all_students = users['students']

    return render_template(
        'student_main.html',
        student=student,
        schools=schools,
        class_obj=class_obj,
        request=request,
        students=all_students
    )

@app.route('/teacher_main')
def teacher_main():
    from flask import request as flask_request
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    users = load_users()
    teacher = next((t for t in users['teachers'] if t['email'] == session['email']), None)
    classrooms_data = load_classrooms()
    schools = {}
    for c in classrooms_data['classrooms']:
        if c['teacher_email'] == session['email']:
            if c['school'] not in schools:
                schools[c['school']] = []
            schools[c['school']].append(c)
    selected_class = flask_request.args.get('class')
    class_obj = None
    if selected_class:
        for c in classrooms_data['classrooms']:
            if c['code'] == selected_class and c['teacher_email'] == session['email']:
                class_obj = c
                break
    now = datetime.datetime.utcnow()
    def is_new(ts):
        try:
            dt = datetime.datetime.fromisoformat(ts)
            return (now - dt).total_seconds() < 86400
        except:
            return False
    if class_obj:
        class_obj['rubrics'] = sorted(class_obj.get('rubrics', []), key=lambda r: r.get('timestamp', ''), reverse=True)
        class_obj['assignments'] = sorted(class_obj.get('assignments', []), key=lambda a: a.get('timestamp', ''), reverse=True)
        for r in class_obj['rubrics']:
            r['is_new'] = is_new(r.get('timestamp', ''))
        for a in class_obj['assignments']:
            a['is_new'] = is_new(a.get('timestamp', ''))
        class_obj['student_objs'] = [s for s in users['students'] if s['email'] in class_obj['students']]
    return render_template('teacher_main.html', teacher=teacher, schools=schools, class_obj=class_obj, request=flask_request, student=None, students=users['students'])

@app.route('/teacher/add_rubric', methods=['POST'])
def add_rubric():
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    code = request.form['class_code']
    title = request.form['title']
    content = request.form.get('content', '')
    rubric_file = request.files.get('rubric_file')
    if rubric_file and rubric_file.filename.endswith('.txt'):
        content = rubric_file.read().decode('utf-8')
    import datetime
    classrooms = load_classrooms()
    classroom = next((c for c in classrooms['classrooms'] if c['code'] == code and c['teacher_email'] == session['email']), None)
    if classroom:
        rubric_id = str(uuid4())
        classroom.setdefault('rubrics', []).append({
            'id': rubric_id,
            'title': title,
            'content': content,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'teacher_email': session['email']
        })
        save_classrooms(classrooms)
    return redirect(url_for('teacher_main', **{'class': code}))

@app.route('/teacher/add_assignment', methods=['POST'])
def add_assignment():
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    code = request.form['class_code']
    title = request.form['title']
    content = request.form.get('content', '')
    description = request.form.get('description', '')
    rubric_id = request.form.get('rubric_id')
    content_file = request.files.get('content_file')
    if content_file and content_file.filename.endswith('.txt'):
        content = content_file.read().decode('utf-8')
    desc_file = request.files.get('desc_file')
    if desc_file and desc_file.filename.endswith('.txt'):
        description = desc_file.read().decode('utf-8')
    import datetime
    classrooms = load_classrooms()
    classroom = next((c for c in classrooms['classrooms'] if c['code'] == code and c['teacher_email'] == session['email']), None)
    if classroom:
        assignment_id = str(uuid4())
        classroom.setdefault('assignments', []).append({
            'id': assignment_id,
            'title': title,
            'content': content,
            'description': description,
            'rubric_id': rubric_id,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'teacher_email': session['email']
        })
        save_classrooms(classrooms)
    return redirect(url_for('teacher_main', **{'class': code}))

# Edit assignment route
@app.route('/teacher/edit_assignment/<class_code>/<assignment_id>', methods=['GET', 'POST'])
def edit_assignment(class_code, assignment_id):
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    classrooms = load_classrooms()
    classroom = next((c for c in classrooms['classrooms'] if c['code'] == class_code and c['teacher_email'] == session['email']), None)
    if not classroom:
        flash('Classroom not found.')
        return redirect(url_for('teacher_main'))
    assignment = next((a for a in classroom.get('assignments', []) if a['id'] == assignment_id), None)
    if not assignment:
        flash('Assignment not found.')
        return redirect(url_for('teacher_main', **{'class': class_code}))
    if request.method == 'POST':
        assignment['title'] = request.form['title']
        assignment['content'] = request.form.get('content', '')
        assignment['description'] = request.form.get('description', '')
        assignment['rubric_id'] = request.form.get('rubric_id')
        content_file = request.files.get('content_file')
        if content_file and content_file.filename.endswith('.txt'):
            assignment['content'] = content_file.read().decode('utf-8')
        desc_file = request.files.get('desc_file')
        if desc_file and desc_file.filename.endswith('.txt'):
            assignment['description'] = desc_file.read().decode('utf-8')
        save_classrooms(classrooms)
        flash('Assignment updated!')
        return redirect(url_for('teacher_main', **{'class': class_code}))
    # GET: show edit form
    rubrics = classroom.get('rubrics', [])
    return render_template('edit_assignment.html', assignment=assignment, class_code=class_code, rubrics=rubrics)

@app.route('/classroom/join/<code>', methods=['GET'])
def join_classroom_link(code):
    if 'user_type' in session and session['user_type'] == 'student':
        users = load_users()
        student = next((s for s in users['students'] if s['email'] == session['email']), None)
        if student:
            classrooms = load_classrooms()
            classroom = next((c for c in classrooms['classrooms'] if c['code'] == code), None)
            if classroom:
                if 'classrooms' not in student:
                    student['classrooms'] = []
                if code not in student['classrooms']:
                    student['classrooms'].append(code)
                if session['email'] not in classroom['students']:
                    classroom['students'].append(session['email'])
                save_classrooms(classrooms)
                save_users(users)
                return render_template('join_confirmation.html', classroom=classroom)
            else:
                flash('Classroom not found.')
                return redirect(url_for('student_main'))
    session['pending_join_code'] = code
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user_type = request.form['user_type']
        users = load_users()
        if user_type == 'student':
            user = next((s for s in users['students'] if s['email'] == email), None)
            if user:
                session['user_type'] = 'student'
                session['email'] = email
                join_code = session.pop('pending_join_code', None)
                if join_code:
                    classrooms = load_classrooms()
                    classroom = next((c for c in classrooms['classrooms'] if c['code'] == join_code), None)
                    if classroom:
                        if 'classrooms' not in user:
                            user['classrooms'] = []
                        if join_code not in user['classrooms']:
                            user['classrooms'].append(join_code)
                        if email not in classroom['students']:
                            classroom['students'].append(email)
                        save_classrooms(classrooms)
                        save_users(users)
                        return render_template('join_confirmation.html', classroom=classroom)
                    else:
                        return render_template('join_confirmation.html', classroom=classroom)
                return redirect(url_for('student_main'))
        elif user_type == 'teacher':
            user = next((t for t in users['teachers'] if t['email'] == email), None)
            if user:
                session['user_type'] = 'teacher'
                session['email'] = email
                return redirect(url_for('teacher_main'))
        flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
# app.py - Flask application for StudyCoach