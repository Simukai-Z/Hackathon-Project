import os
import json
import dotenv
import datetime
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from openai import AzureOpenAI

dotenv.load_dotenv()
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_NAME = "gpt-35-turbo"

app = Flask(__name__)
app.secret_key = 'studycoach_secret_key'

# --- API: Reset AI Chat History ---
@app.route('/reset_history', methods=['POST'])
def reset_history():
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False})
    user_type = session['user_type']
    email = session['email']
    history_key = f"ai_history_{user_type}_{email}"
    if history_key in session:
        session.pop(history_key)
        session.modified = True
    return jsonify({'success': True})


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


openai_client = AzureOpenAI(
    api_key=AOAI_KEY,
    azure_endpoint=AOAI_ENDPOINT,
    api_version="2024-05-01-preview"
)

# --- API: Get AI Personality ---
@app.route('/get_personality', methods=['GET'])
def get_personality():
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'personality': ''})
    users = load_users()
    email = session['email']
    user_type = session['user_type']
    if user_type == 'student':
        user = next((u for u in users['students'] if u['email'] == email), None)
    else:
        user = next((u for u in users['teachers'] if u['email'] == email), None)
    personality = user.get('ai_personality', '') if user else ''
    return jsonify({'personality': personality})

# --- API: Save AI Personality ---
@app.route('/save_personality', methods=['POST'])
def save_personality():
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False})
    users = load_users()
    email = session['email']
    user_type = session['user_type']
    data = request.get_json()
    personality = data.get('personality', '')
    if user_type == 'student':
        user = next((u for u in users['students'] if u['email'] == email), None)
    else:
        user = next((u for u in users['teachers'] if u['email'] == email), None)
    if user is not None:
        user['ai_personality'] = personality
        save_users(users)
        return jsonify({'success': True})
    return jsonify({'success': False})
# --- AI Assistant Page ---
@app.route('/ai')
def ai_page():
    return render_template('ai_assistant.html')

# --- AI Chat Endpoint ---
@app.route('/chat', methods=['POST'])
def chat():
    # Get user info from session
    from flask import session
    users = load_users()
    classrooms_data = load_classrooms()
    user_type = session.get('user_type')
    email = session.get('email')
    assignments = []
    rubrics = []
    class_name = None
    data = request.get_json()
    ai_personality = data.get('personality', 'You are a helpful tutor that follows rubrics and teaches through guidance.')
    user_prompt = data.get('prompt', '')
    file_content = data.get('fileContent', '')

    # If there's file content, add it to the context
    if file_content:
        user_prompt = f"{user_prompt}\n[Student's Uploaded Content]:\n{file_content}"

    # Get all accessible assignments and rubrics
    accessible_classes = []
    if user_type == 'student':
        student = next((s for s in users['students'] if s['email'] == email), None)
        if student and student.get('classrooms'):
            accessible_classes = [c for c in classrooms_data['classrooms'] if c['code'] in student['classrooms']]
            # Get currently selected class for context
            selected_class = data.get('class_code') or (student['classrooms'][0] if student['classrooms'] else None)
            class_obj = next((c for c in accessible_classes if c['code'] == selected_class), None)
            if class_obj:
                class_name = class_obj.get('class_name')
    elif user_type == 'teacher':
        teacher = next((t for t in users['teachers'] if t['email'] == email), None)
        if teacher:
            accessible_classes = [c for c in classrooms_data['classrooms'] if c['teacher_email'] == email]
            selected_class = data.get('class_code')
            class_obj = next((c for c in accessible_classes if c['code'] == selected_class), None) if selected_class else (accessible_classes[0] if accessible_classes else None)
            if class_obj:
                class_name = class_obj.get('class_name')
    
    # Collect all assignments and rubrics from accessible classes
    all_assignments = []
    all_rubrics = []
    for c in accessible_classes:
        # Add class name to assignments and rubrics for context
        for assignment in c.get('assignments', []):
            assignment_copy = assignment.copy()
            assignment_copy['class_name'] = c.get('class_name', '')
            all_assignments.append(assignment_copy)
        for rubric in c.get('rubrics', []):
            rubric_copy = rubric.copy()
            rubric_copy['class_name'] = c.get('class_name', '')
            all_rubrics.append(rubric_copy)
    
    assignments = all_assignments
    rubrics = all_rubrics

    # Compose rubric summary for AI
    rubric_summary = '\n'.join([f"[{r.get('class_name', '')}] {r.get('title', '')}: {r.get('content', '')}" for r in rubrics])
    assignment_summary = '\n'.join([f"[{a.get('class_name', '')}] {a.get('title', '')}: {a.get('description', '') or a.get('content', '')}" for a in assignments])
    
    current_class_info = f"Current Class: {class_name or 'None selected'}" if class_name else "No specific class selected"
    
    # Organize assignments and rubrics by class
    assignments_by_class = {}
    rubrics_by_class = {}
    
    for a in assignments:
        class_name = a.get('class_name', 'Unspecified Class')
        if class_name not in assignments_by_class:
            assignments_by_class[class_name] = []
        assignments_by_class[class_name].append(a)
    
    for r in rubrics:
        class_name = r.get('class_name', 'Unspecified Class')
        if class_name not in rubrics_by_class:
            rubrics_by_class[class_name] = []
        rubrics_by_class[class_name].append(r)
    
    # Create organized context with clear class separation
    assignments_by_class_text = []
    for class_name, class_assignments in assignments_by_class.items():
        assignments_text = '\n'.join([f"  - {a.get('title', '')}: {a.get('description', '') or a.get('content', '')}" for a in class_assignments])
        assignments_by_class_text.append(f"{class_name}:\n{assignments_text}")
    
    rubrics_by_class_text = []
    for class_name, class_rubrics in rubrics_by_class.items():
        rubrics_text = '\n'.join([f"  - {r.get('title', '')}: {r.get('content', '')}" for r in class_rubrics])
        rubrics_by_class_text.append(f"{class_name}:\n{rubrics_text}")

    context = f"""{current_class_info}

Available Assignments By Class:
{'='*40}
{'\n\n'.join(assignments_by_class_text)}

Available Grading Rubrics By Class:
{'='*40}
{'\n\n'.join(rubrics_by_class_text)}"""

    system_prompt = f"""{ai_personality}

You are assisting in a classroom environment. Here's your context and instructions:

CURRENT CONTEXT:
{context}

CORE INSTRUCTIONS:
1. Always consider which class an assignment or rubric belongs to when providing assistance
2. When a student asks about an assignment:
   - First identify which class it belongs to
   - Use the rubrics specific to that class
   - If multiple classes have similar assignments, ask for clarification
3. Guide students through hints and questions, never give direct solutions
4. For uploaded work:
   - Match it to the correct class and assignment
   - Review against the appropriate class rubrics
   - Provide specific, constructive feedback
   - Reference the correct class context in your responses

INTERACTION GUIDELINES:
- Be encouraging and supportive while maintaining academic integrity
- If a student doesn't specify which class they're asking about, ask for clarification
- Always frame your responses in the context of the specific class and its requirements
- Help students understand concepts within their specific class context

Remember: Each class may have different requirements and rubrics, so always ensure you're using the correct context."""

    # --- Message History Logic ---
    history_key = f"ai_history_{user_type}_{email}"
    if history_key not in session:
        session[history_key] = []
    # Add user message
    session[history_key].append({"role": "user", "content": user_prompt})
    # Build message list: system prompt + history
    messages = [{"role": "system", "content": system_prompt}] + session[history_key]

    # If history exceeds 10, summarize and restart
    if len(session[history_key]) > 50:
        # Summarize history
        summary_prompt = "Summarize the following conversation between a student/teacher and an AI tutor in 1-2 paragraphs, focusing on the main topics and guidance given.\n" + \
            "\n".join([f"{m['role']}: {m['content']}" for m in session[history_key]])
        summary_response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes conversations for context retention."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=200,
            temperature=0.5
        )
        summary = summary_response.choices[0].message.content
        # Restart history with summary
        session[history_key] = [
            {"role": "system", "content": f"Conversation so far (summary): {summary}"}
        ]
        # Add the latest user message again
        session[history_key].append({"role": "user", "content": user_prompt})
        messages = [{"role": "system", "content": system_prompt}] + session[history_key]

    # Get AI response
    response = openai_client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=500,
        temperature=0.6
    )
    ai_reply = response.choices[0].message.content
    # Add AI reply to history
    session[history_key].append({"role": "assistant", "content": ai_reply})
    session.modified = True

    return jsonify({'response': ai_reply})

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