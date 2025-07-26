import os
import json
import re
import dotenv
import datetime
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from openai import AzureOpenAI

dotenv.load_dotenv()
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_NAME = "gpt-35-turbo"

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configure file upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_google_docs_url(url):
    """Check if a URL is a Google Docs URL"""
    if not url:
        return False
    google_domains = ['docs.google.com', 'drive.google.com']
    return any(domain in url.lower() for domain in google_domains)

def get_google_docs_instructions(url):
    """Get instructions for handling Google Docs submissions"""
    if not is_google_docs_url(url):
        return None
    
    return {
        'is_google_docs': True,
        'sharing_instructions': 'Please ensure this Google Docs link is shared with viewing permissions for anyone with the link, or specifically shared with the teacher.',
        'grading_note': 'To grade this Google Docs submission, you may need to open the link directly and verify sharing permissions are properly set.',
        'export_hint': 'For better integration, students can export their Google Docs as PDF and upload the file instead.'
    }

def extract_google_docs_id(url):
    """Extract document ID from Google Docs URL for potential API usage"""
    if not is_google_docs_url(url):
        return None
    
    # Pattern to extract document ID from various Google Docs URL formats
    import re
    patterns = [
        r'/document/d/([a-zA-Z0-9-_]+)',
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

# Configuration for URL generation
# This allows Flask to generate proper external URLs regardless of the domain
app.config['PREFERRED_URL_SCHEME'] = 'https'  # Use HTTPS by default for external URLs

# Set SERVER_NAME from environment if provided, otherwise let Flask auto-detect
if os.getenv('SERVER_NAME'):
    app.config['SERVER_NAME'] = os.getenv('SERVER_NAME')

# Helper function to get the current request's host URL
def get_current_host():
    """Get the current request's host URL, including protocol and port if needed"""
    from flask import request
    if request:
        return request.host_url.rstrip('/')
    else:
        # Fallback when outside request context
        scheme = app.config.get('PREFERRED_URL_SCHEME', 'http')
        server_name = app.config.get('SERVER_NAME', 'localhost:5000')
        return f"{scheme}://{server_name}"

# Helper function for generating dynamic URLs
def generate_url(endpoint, **kwargs):
    """Generate a URL using the current request context or app context"""
    from flask import request
    if request:
        # Use the current request's host for URL generation
        return request.host_url.rstrip('/') + url_for(endpoint, **kwargs)
    else:
        # Fallback to app context when outside request
        with app.app_context():
            return url_for(endpoint, _external=True, **kwargs)

# Utility function to regenerate classroom join URLs
def regenerate_classroom_urls():
    """Utility function to regenerate all classroom join URLs if needed"""
    from flask import request
    classrooms = load_classrooms()
    updated = False
    
    for classroom in classrooms.get('classrooms', []):
        if 'code' in classroom:
            # Generate the proper join URL using the actual request host
            from flask import request
            if request:
                # Use the same logic as dynamic_url_for
                host = request.headers.get('X-Forwarded-Host') or request.headers.get('Host') or request.host
                scheme = request.headers.get('X-Forwarded-Proto') or request.scheme
                url_path = url_for('join_classroom_link', code=classroom['code'])
                join_url = f"{scheme}://{host}{url_path}"
            else:
                # Fallback when outside request context
                join_url = url_for('join_classroom_link', code=classroom['code'], _external=True)
                
            # Update if the URL has changed or doesn't exist
            if classroom.get('join_url') != join_url:
                classroom['join_url'] = join_url
                updated = True
    
    if updated:
        save_classrooms(classrooms)
        return True
    return False

# Context processor to provide dynamic URL functions to all templates
@app.context_processor
def utility_processor():
    """Make utility functions available in all templates"""
    def dynamic_url_for(endpoint, **kwargs):
        """Generate URL using the actual request host and scheme"""
        from flask import request
        
        # Get the actual host from request headers (handles GitHub Codespaces/proxies)
        if request:
            # Check for forwarded host header first (used by reverse proxies)
            host = request.headers.get('X-Forwarded-Host') or request.headers.get('Host') or request.host
            
            # Check for forwarded protocol (HTTPS from reverse proxy)
            scheme = request.headers.get('X-Forwarded-Proto') or request.scheme
            
            # Build the full URL manually with the correct host
            url_path = url_for(endpoint, **kwargs)
            return f"{scheme}://{host}{url_path}"
        else:
            # Fallback when outside request context
            return url_for(endpoint, _external=True, **kwargs)
    
    def get_host_url():
        """Get the current host URL"""
        from flask import request
        if request:
            return request.host_url.rstrip('/')
        else:
            return get_current_host()
    
    return dict(
        dynamic_url_for=dynamic_url_for,
        get_host_url=get_host_url
    )

# Context processor to make url generation available in templates
@app.context_processor
def inject_url_helpers():
    return {
        'generate_url': generate_url
    }

# Add datetime filter for Jinja2 templates
@app.template_filter('datetime')
def datetime_filter(value):
    if not value:
        return ''
    try:
        if isinstance(value, str):
            dt = datetime.datetime.fromisoformat(value)
        else:
            dt = value
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return str(value)

# Add current year filter for templates
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.datetime.now().year}

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

def save_users(users):
    """Save users data to JSON file"""
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)

def update_student_activity(student_email):
    """Update the last activity timestamp for a student"""
    users = load_users()
    current_time = datetime.datetime.utcnow().isoformat()
    
    # Find and update the student
    for student in users['students']:
        if student['email'] == student_email:
            student['last_activity'] = current_time
            break
    
    save_users(users)

def format_last_activity(last_activity):
    """Format the last activity timestamp into a human-readable string"""
    if not last_activity:
        return "Never"
    
    try:
        last_active = datetime.datetime.fromisoformat(last_activity)
        now = datetime.datetime.utcnow()
        diff = now - last_active
        
        seconds = diff.total_seconds()
        
        if seconds < 60:  # Less than 1 minute
            return "Just now"
        elif seconds < 3600:  # Less than 1 hour
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:  # Less than 1 day
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:  # Less than 1 week
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:  # More than 1 week, show the actual date
            return last_active.strftime("%b %d, %Y")
    except:
        return "Unknown"

def calculate_activity_score(last_activity):
    """Calculate activity score based on last activity time (0-100)"""
    if not last_activity:
        return 0
    
    try:
        last_active = datetime.datetime.fromisoformat(last_activity)
        now = datetime.datetime.utcnow()
        hours_since = (now - last_active).total_seconds() / 3600
        
        # Activity score decreases over time
        if hours_since <= 1:      # Within 1 hour: 90-100%
            return min(100, 90 + (1 - hours_since) * 10)
        elif hours_since <= 6:    # Within 6 hours: 70-90%
            return min(90, 70 + (6 - hours_since) * 4)
        elif hours_since <= 24:   # Within 24 hours: 40-70%
            return min(70, 40 + (24 - hours_since) * 1.67)
        elif hours_since <= 72:   # Within 3 days: 20-40%
            return min(40, 20 + (72 - hours_since) * 0.42)
        elif hours_since <= 168:  # Within 1 week: 10-20%
            return min(20, 10 + (168 - hours_since) * 0.1)
        else:                     # More than 1 week: 0-10%
            return max(0, 10 - min(hours_since - 168, 168) * 0.06)
    except:
        return 0

def load_classrooms():
    if not os.path.exists(CLASSROOMS_FILE):
        return {"classrooms": []}
    with open(CLASSROOMS_FILE, 'r') as f:
        return json.load(f)

def save_classrooms(classrooms):
    with open(CLASSROOMS_FILE, 'w') as f:
        json.dump(classrooms, f, indent=2)

def get_student_submissions(student_email, assignment_id=None):
    """Get submissions for a student, optionally filtered by assignment"""
    classrooms = load_classrooms()
    submissions = []
    
    for classroom in classrooms.get('classrooms', []):
        if student_email in classroom.get('students', []):
            for assignment in classroom.get('assignments', []):
                if assignment_id is None or assignment['id'] == assignment_id:
                    for submission in assignment.get('submissions', []):
                        if submission.get('student_email') == student_email:
                            submission['assignment_title'] = assignment.get('title', '')
                            submission['class_name'] = classroom.get('class_name', '')
                            submissions.append(submission)
    
    return submissions

def get_student_grades(student_email):
    """Get all grades for a student"""
    submissions = get_student_submissions(student_email)
    return [s for s in submissions if s.get('grade') is not None]

def calculate_student_performance(student_email):
    """Calculate overall performance metrics for a student"""
    grades = get_student_grades(student_email)
    
    if not grades:
        return {
            'average_grade': None,
            'total_assignments': 0,
            'completed_assignments': 0,
            'recent_performance': 'no_data'
        }
    
    # Calculate average grade
    numeric_grades = []
    for grade in grades:
        grade_value = grade.get('grade')
        if isinstance(grade_value, (int, float)):
            numeric_grades.append(grade_value)
        elif isinstance(grade_value, str) and grade_value.replace('.', '').isdigit():
            numeric_grades.append(float(grade_value))
    
    avg_grade = sum(numeric_grades) / len(numeric_grades) if numeric_grades else 0
    
    # Determine recent performance trend
    recent_performance = 'good' if avg_grade >= 80 else 'needs_improvement' if avg_grade >= 60 else 'struggling'
    
    return {
        'average_grade': round(avg_grade, 1) if numeric_grades else None,
        'total_assignments': len(grades),
        'completed_assignments': len([g for g in grades if g.get('grade') is not None]),
        'recent_performance': recent_performance,
        'recent_grades': grades[-3:] if grades else []  # Last 3 grades
    }


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
    # Track student activity if they're logged in as a student
    if 'user_type' in session and session['user_type'] == 'student':
        update_student_activity(session['email'])
    return render_template('ai_assistant.html')

# --- AI Chat Endpoint ---
@app.route('/chat', methods=['POST'])
def chat():
    # Get user info from session
    from flask import session
    
    # Track student activity when they use the AI chat
    if session.get('user_type') == 'student' and session.get('email'):
        update_student_activity(session['email'])
    
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

    # Add student performance context for personalized feedback
    performance_context = ""
    if user_type == 'student' and email:
        performance = calculate_student_performance(email)
        recent_grades = performance.get('recent_grades', [])
        
        if recent_grades:
            grades_text = []
            for grade_info in recent_grades:
                grade_text = f"Assignment: {grade_info.get('assignment_title', 'Unknown')} - Grade: {grade_info.get('grade', 'N/A')}"
                if grade_info.get('feedback'):
                    grade_text += f" (Feedback: {grade_info.get('feedback', '')[:100]}...)"
                grades_text.append(grade_text)
            
            performance_context = f"""
STUDENT PERFORMANCE CONTEXT:
{'='*30}
Average Grade: {performance.get('average_grade', 'N/A')}
Performance Level: {performance.get('recent_performance', 'no_data')}
Recent Grades: 
{chr(10).join([f"  - {g}" for g in grades_text])}

PERSONALIZATION INSTRUCTIONS:
- If student has good grades (80+): Congratulate them and encourage continued excellence
- If student needs improvement (60-79): Provide supportive guidance and specific improvement tips  
- If student is struggling (<60): Be extra encouraging, break down concepts, offer additional help
- Reference their recent assignment performance when relevant to build connection
"""

    context = f"""{current_class_info}

Available Assignments By Class:
{'='*40}
{'\n\n'.join(assignments_by_class_text)}

Available Grading Rubrics By Class:
{'='*40}
{'\n\n'.join(rubrics_by_class_text)}

{performance_context}"""

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

    # Track student activity
    update_student_activity(session['email'])

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

@app.route('/submit_assignment', methods=['POST'])
def submit_assignment():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    
    # Track student activity
    update_student_activity(session['email'])
    
    assignment_id = request.form.get('assignment_id')
    submission_text = request.form.get('submission_text', '')
    submission_link = request.form.get('submission_link', '')
    submitted_file = request.files.get('submission_file')
    
    if not assignment_id:
        flash('Invalid assignment submission')
        return redirect(url_for('student_main'))
    
    # Find the assignment and classroom
    classrooms = load_classrooms()
    assignment = None
    classroom = None
    
    for c in classrooms.get('classrooms', []):
        if session['email'] in c.get('students', []):
            for a in c.get('assignments', []):
                if a['id'] == assignment_id:
                    assignment = a
                    classroom = c
                    break
            if assignment:
                break
    
    if not assignment:
        flash('Assignment not found')
        return redirect(url_for('student_main'))
    
    # Handle file upload
    filename = None
    if submitted_file and submitted_file.filename and allowed_file(submitted_file.filename):
        filename = secure_filename(f"{session['email']}_{assignment_id}_{submitted_file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        submitted_file.save(file_path)
    
    # Create submission
    submission = {
        'id': str(uuid4()),
        'student_email': session['email'],
        'assignment_id': assignment_id,
        'submission_text': submission_text,
        'submission_link': submission_link,
        'filename': filename,
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'grade': None,
        'feedback': None,
        'graded_by': None,
        'graded_timestamp': None
    }
    
    # Add submission to assignment
    if 'submissions' not in assignment:
        assignment['submissions'] = []
    
    # Remove any existing submission from this student for this assignment
    assignment['submissions'] = [s for s in assignment['submissions'] if s.get('student_email') != session['email']]
    assignment['submissions'].append(submission)
    
    save_classrooms(classrooms)
    flash('Assignment submitted successfully!')
    return redirect(url_for('student_main'))

@app.route('/grade_assignment', methods=['POST'])
def grade_assignment():
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    # Handle both old format (submission_id) and new format (classroom_id, assignment_id, student_email)
    submission_id = request.form.get('submission_id')
    classroom_id = request.form.get('classroom_id')
    assignment_id = request.form.get('assignment_id')  
    student_email = request.form.get('student_email')
    grade = request.form.get('grade')
    feedback = request.form.get('feedback', '')
    use_ai = request.form.get('use_ai') == 'true'
    
    if not grade:
        flash('Missing grade')
        return redirect(url_for('teacher_main'))
    
    # Validate grade is a number and within valid range
    try:
        grade_num = float(grade)
        if grade_num < 0 or grade_num > 100:
            flash('Grade must be between 0 and 100')
            return redirect(url_for('teacher_main'))
        grade = str(int(grade_num))  # Convert to integer string for consistency
    except ValueError:
        flash('Grade must be a valid number')
        return redirect(url_for('teacher_main'))
    
    # Find the submission
    classrooms = load_classrooms()
    submission = None
    assignment = None
    
    if submission_id:
        # Old format - find by submission_id
        for classroom in classrooms.get('classrooms', []):
            if classroom.get('teacher_email') == session['email']:
                for a in classroom.get('assignments', []):
                    for s in a.get('submissions', []):
                        if s.get('id') == submission_id:
                            submission = s
                            assignment = a
                            break
                    if submission:
                        break
            if submission:
                break
    elif classroom_id and assignment_id and student_email:
        # New format - find by classroom_id, assignment_id, student_email
        for classroom in classrooms.get('classrooms', []):
            if classroom.get('code') == classroom_id and classroom.get('teacher_email') == session['email']:
                for a in classroom.get('assignments', []):
                    if a.get('id') == assignment_id:
                        for s in a.get('submissions', []):
                            if s.get('student_email') == student_email:
                                submission = s
                                assignment = a
                                break
                        if submission:
                            break
                if submission:
                    break
    else:
        flash('Missing required parameters')
        return redirect(url_for('teacher_main'))
    
    if not submission:
        flash('Submission not found')
        return redirect(url_for('teacher_main'))
    
    # If using AI assistance, enhance the feedback
    if use_ai and feedback:
        try:
            ai_prompt = f"""
            As a supportive teacher, please enhance this feedback for a student assignment:
            
            Assignment: {assignment.get('title', 'Assignment')}
            Grade: {grade}
            Teacher's Initial Feedback: {feedback}
            
            Please provide constructive, encouraging feedback that:
            1. Acknowledges what the student did well
            2. Provides specific suggestions for improvement
            3. Maintains a positive, supportive tone
            4. Is appropriate for the grade level
            
            Keep the response under 200 words and make it personal and encouraging.
            """
            
            ai_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": ai_prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            enhanced_feedback = ai_response.choices[0].message.content.strip()
            feedback = enhanced_feedback
            
        except Exception as e:
            print(f"AI feedback enhancement failed: {e}")
            # Continue with original feedback if AI fails
    
    # Update the submission
    submission['grade'] = grade
    submission['feedback'] = feedback
    submission['graded_by'] = session['email']
    submission['graded_timestamp'] = datetime.datetime.utcnow().isoformat()
    
    save_classrooms(classrooms)
    flash('Assignment graded successfully!')
    return redirect(url_for('teacher_main'))

@app.route('/ai_grade_assignment', methods=['POST'])
def ai_grade_assignment():
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    # Handle both old format (submission_id) and new format (classroom_id, assignment_id, student_email)
    submission_id = request.form.get('submission_id')
    classroom_id = request.form.get('classroom_id')
    assignment_id = request.form.get('assignment_id')
    student_email = request.form.get('student_email')
    
    if not submission_id and not (classroom_id and assignment_id and student_email):
        flash('Missing required parameters')
        return redirect(url_for('teacher_main'))
    
    # Find the submission
    classrooms = load_classrooms()
    submission = None
    assignment = None
    classroom = None
    
    if submission_id:
        # Old format - find by submission_id
        for c in classrooms.get('classrooms', []):
            if c.get('teacher_email') == session['email']:
                for a in c.get('assignments', []):
                    for s in a.get('submissions', []):
                        if s.get('id') == submission_id:
                            submission = s
                            assignment = a
                            classroom = c
                            break
                    if submission:
                        break
            if submission:
                break
    else:
        # New format - find by classroom_id, assignment_id, student_email
        for c in classrooms.get('classrooms', []):
            if c.get('code') == classroom_id and c.get('teacher_email') == session['email']:
                for a in c.get('assignments', []):
                    if a.get('id') == assignment_id:
                        for s in a.get('submissions', []):
                            if s.get('student_email') == student_email:
                                submission = s
                                assignment = a
                                classroom = c
                                break
                        if submission:
                            break
                if submission:
                    break
    
    if not submission:
        flash('Submission not found')
        return redirect(url_for('teacher_main'))
    
    # Use AI to grade the assignment
    try:
        print("DEBUG: Starting AI grading process", flush=True)
        # Check if this is a re-grade
        is_regrade = submission.get('grade') is not None
        previous_grade = submission.get('grade') if is_regrade else None
        previous_feedback = submission.get('feedback') if is_regrade else None
        print(f"DEBUG: Is regrade: {is_regrade}, Previous grade: {previous_grade}", flush=True)
        
        # Create a content hash for consistency
        import hashlib
        
        # Get student name for personalized feedback
        users = load_users()
        student_name = "Student"
        for student in users.get('students', []):
            if student['email'] == submission['student_email']:
                student_name = student.get('name', 'Student')
                break
        
        # Initialize file_content at the beginning
        file_content = ""
        print(f"DEBUG: Initialized file_content: '{file_content}'", flush=True)
        
        # Read file content if available
        try:
            print(f"DEBUG: Initial file_content value: '{file_content}'", flush=True)
            if submission.get('filename'):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], submission['filename'])
                print(f"DEBUG: Attempting to read file: {file_path}", flush=True)
                print(f"DEBUG: File exists: {os.path.exists(file_path)}", flush=True)
                if os.path.exists(file_path):
                    try:
                        # Try to read as text file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        print(f"DEBUG: File content read successfully: '{file_content}' (length: {len(file_content)})", flush=True)
                        # Limit content length to avoid token limits
                        if len(file_content) > 3000:
                            file_content = file_content[:3000] + "... [Content truncated]"
                    except Exception as e:
                        print(f"DEBUG: Error reading with UTF-8: {e}", flush=True)
                        try:
                            # Fallback: try with different encoding
                            with open(file_path, 'r', encoding='latin-1') as f:
                                file_content = f.read()
                            print(f"DEBUG: File content read with latin-1: '{file_content}' (length: {len(file_content)})", flush=True)
                            if len(file_content) > 3000:
                                file_content = file_content[:3000] + "... [Content truncated]"
                        except Exception as e2:
                            print(f"DEBUG: Error reading with latin-1: {e2}", flush=True)
                            file_content = f"[Unable to read file content: {str(e2)}]"
                else:
                    print(f"DEBUG: File not found at path: {file_path}", flush=True)
                    file_content = "[File not found on server]"
            else:
                print("DEBUG: No filename in submission", flush=True)
                file_content = "[No file attached]"
            
            print(f"DEBUG: Final file_content value: '{file_content[:100] if file_content else 'EMPTY'}...'", flush=True)
        except Exception as e:
            print(f"DEBUG: Exception in file reading section: {e}", flush=True)
            file_content = "[Error reading file]"
        
        # Create content hash after we have the file content
        content_for_hash = f"{submission.get('submission_text', '')}{submission.get('submission_link', '')}{submission.get('filename', '')}{file_content}{assignment.get('title', '')}{assignment.get('description', '')}"
        content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
        print(f"DEBUG: Content hash created: {content_hash[:8]}", flush=True)
        
        # For consistency, remove re-grading context that might bias the AI toward higher grades
        # Instead, focus on objective grading criteria
        grading_prompt = f"""
        You are a fair and consistent grading system. Grade this assignment objectively based ONLY on the content provided.
        
        GRADING CRITERIA:
        - Content Quality and Completeness (40%)
        - Understanding and Analysis (30%) 
        - Organization and Clarity (20%)
        - Following Instructions (10%)
        
        ASSIGNMENT DETAILS:
        Student Name: {student_name}
        Assignment Title: {assignment.get('title', 'Assignment')}
        Assignment Description: {assignment.get('description', 'No description provided')}
        Content Hash: {content_hash[:8]} (for grading consistency)
        
        STUDENT SUBMISSION:
        Text Submission: {submission.get('submission_text', 'No text submission')}
        Link Submission: {submission.get('submission_link', 'No link submission')}
        File Name: {submission.get('filename', 'No file attached')}
        File Content: {file_content if file_content else 'No file content available'}
        
        IMPORTANT GRADING INSTRUCTIONS:
        1. Grade based on ALL the submitted content above (text, link, and file content)
        2. If a Google Docs link is provided, note that you cannot access external links
        3. Be consistent - the same submission should always receive the same grade
        4. Use the full 0-100 scale appropriately: 90-100 (Excellent), 80-89 (Good), 70-79 (Satisfactory), 60-69 (Needs Improvement), Below 60 (Inadequate)
        5. Provide specific feedback based on the grading criteria above
        6. If there is no actual content to grade (empty text, no accessible link, no file content), assign a low grade with appropriate feedback
        
        Please provide:
        1. A numerical grade (0-100)
        2. Constructive feedback addressing strengths and specific areas for improvement
        3. Reference the grading criteria in your feedback
        
        Format your response as:
        GRADE: [number]
        FEEDBACK: [detailed feedback addressing the student by name, referencing specific aspects of their submission]
        
        Be objective, fair, and consistent in your assessment.
        """
        print(f"DEBUG: About to call OpenAI with prompt length: {len(grading_prompt)}", flush=True)
        print(f"DEBUG: File content in prompt: {file_content[:100] if file_content else 'No file content'}...", flush=True)
        
        ai_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": grading_prompt}],
            max_tokens=500,
            temperature=0.3,  # Lower temperature for more consistent results
            seed=int(content_hash[:8], 16) % 2147483647  # Use content hash as seed for consistency
        )
        
        ai_content = ai_response.choices[0].message.content.strip()
        print(f"DEBUG: AI response: '{ai_content}'", flush=True)
        
        # Parse the AI response
        grade = None
        feedback = ai_content
        
        if "GRADE:" in ai_content and "FEEDBACK:" in ai_content:
            parts = ai_content.split("FEEDBACK:")
            grade_part = parts[0].replace("GRADE:", "").strip()
            feedback = parts[1].strip()
            
            # Extract numerical grade from grade part only
            import re
            grade_match = re.search(r'\b(\d{1,3})\b', grade_part)
            if grade_match:
                potential_grade = int(grade_match.group())
                # Validate grade is in valid range
                if 0 <= potential_grade <= 100:
                    grade = potential_grade
        
        # If still no valid grade, try alternative parsing
        if grade is None:
            # Look for "GRADE: XX" pattern more specifically
            import re
            grade_pattern = re.search(r'GRADE:\s*(\d{1,3})', ai_content, re.IGNORECASE)
            if grade_pattern:
                potential_grade = int(grade_pattern.group(1))
                if 0 <= potential_grade <= 100:
                    grade = potential_grade
        
        # Final fallback: look for standalone numbers that could be grades
        if grade is None:
            import re
            # Look for numbers that are likely grades (0-100 range)
            potential_grades = re.findall(r'\b(\d{1,2}|100)\b', ai_content)
            for pg in potential_grades:
                pg_int = int(pg)
                if 0 <= pg_int <= 100:
                    grade = pg_int
                    break
        
        # Absolute fallback with validation
        if grade is None or grade < 0 or grade > 100:
            print(f"Warning: Invalid or missing grade from AI response. Using default grade 75.")
            print(f"AI Response: {ai_content[:200]}...")
            grade = 75  # Default grade if parsing fails
        
        # Ensure grade is within valid range
        grade = max(0, min(100, grade))
        
        # Update the submission
        submission['grade'] = grade
        submission['feedback'] = feedback
        submission['graded_by'] = f"AI (via {session['email']})"
        submission['graded_timestamp'] = datetime.datetime.utcnow().isoformat()
        
        save_classrooms(classrooms)
        
        if is_regrade:
            flash(f'Assignment graded by AI! Grade: {grade}% (previous: {previous_grade}%)')
        else:
            flash(f'Assignment graded by AI! Grade: {grade}%')
        return redirect(url_for('teacher_main'))
        
    except Exception as e:
        print(f"AI grading failed: {e}")
        flash('AI grading failed. Please grade manually.')
        return redirect(url_for('teacher_main'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    # Security check: ensure file exists and user has permission
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    
    # Additional security: check if teacher has access to this submission
    classrooms = load_classrooms()
    has_access = False
    
    for classroom in classrooms.get('classrooms', []):
        if classroom.get('teacher_email') == session['email']:
            for assignment in classroom.get('assignments', []):
                for submission in assignment.get('submissions', []):
                    if submission.get('filename') == filename:
                        has_access = True
                        break
                if has_access:
                    break
        if has_access:
            break
    
    if not has_access:
        return "Access denied", 403
    
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/my_uploads/<filename>')
def student_uploaded_file(filename):
    """Serve uploaded files for students (their own files only)"""
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    
    # Security check: ensure file exists and belongs to this student
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    
    # Check if filename starts with student's email (our naming convention)
    if not filename.startswith(session['email']):
        return "Access denied", 403
    
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
        
        # Add activity scores to each student
        for student in class_obj['student_objs']:
            last_activity = student.get('last_activity')
            student['activity_score'] = calculate_activity_score(last_activity)
            student['last_activity_formatted'] = format_last_activity(last_activity)
            
        # Add student names to submissions for better display
        if class_obj.get('assignments'):
            for assignment in class_obj['assignments']:
                if assignment.get('submissions'):
                    for submission in assignment['submissions']:
                        student_email = submission.get('student_email')
                        student_obj = next((s for s in class_obj['student_objs'] if s['email'] == student_email), None)
                        submission['student_name'] = student_obj['name'] if student_obj else student_email
            
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

# Debug route to test URL generation (remove in production)
@app.route('/debug/urls')
def debug_urls():
    """Debug endpoint to show how URLs are generated dynamically"""
    if not app.debug:
        return "Debug mode only", 404
    
    sample_urls = {
        'home': url_for('home', _external=True),
        'login': url_for('login', _external=True),
        'join_classroom_sample': url_for('join_classroom_link', code='ABC123', _external=True),
        'ai_assistant': url_for('ai_page', _external=True),
        'chat_api': url_for('chat', _external=True),
    }
    
    html_content = "<h2>Dynamic URL Generation Test</h2>"
    html_content += "<p>All URLs are generated dynamically using Flask url_for():</p>"
    html_content += "<ul>"
    for k, v in sample_urls.items():
        html_content += f"<li><strong>{k}:</strong> {v}</li>"
    html_content += "</ul>"
    html_content += "<p>These URLs will automatically adapt to your domain.</p>"
    
    return html_content

def regenerate_classroom_urls():
    """Utility to regenerate all classroom join URLs with current domain"""
    classrooms_data = load_classrooms()
    classrooms = classrooms_data.get('classrooms', [])
    updated = False
    
    for classroom in classrooms:
        # Update join URLs that might be hardcoded
        old_url = classroom.get('join_url', '')
        if 'localhost' in old_url or not old_url:
            # Generate new URL with current domain using proper external URL generation
            new_url = url_for('join_classroom_link', code=classroom['code'], _external=True)
            classroom['join_url'] = new_url
            updated = True
    
    if updated:
        save_classrooms(classrooms_data)
        return True
    return False

@app.route('/test-urls')
def test_urls():
    """Debug route to show how URLs are being generated"""
    from flask import request
    
    # Show all relevant headers for debugging
    headers_info = {
        'Host': request.headers.get('Host'),
        'X-Forwarded-Host': request.headers.get('X-Forwarded-Host'),
        'X-Forwarded-Proto': request.headers.get('X-Forwarded-Proto'),
        'X-Forwarded-For': request.headers.get('X-Forwarded-For'),
        'request.host': request.host,
        'request.host_url': request.host_url,
        'request.scheme': request.scheme,
        'request.url': request.url,
    }
    
    sample_urls = {
        'current_host': request.host_url,
        'home_url': url_for('home'),
        'login_url': url_for('login'),
        'student_main_url': url_for('student_main'),
        'teacher_main_url': url_for('teacher_main'),
        'join_sample': url_for('join_classroom_link', code='SAMPLE'),
        'join_sample_external': url_for('join_classroom_link', code='SAMPLE', _external=True),
        'join_sample_dynamic': dynamic_url_for('join_classroom_link', code='SAMPLE'),
    }
    
    return f"""
    <h2>URL Generation Test</h2>
    <h3>Request Headers & Info:</h3>
    <ul>
        {''.join([f'<li><strong>{k}:</strong> {v}</li>' for k, v in headers_info.items()])}
    </ul>
    
    <h3>Generated URLs:</h3>
    <ul>
        {''.join([f'<li><strong>{k}:</strong> {v}</li>' for k, v in sample_urls.items()])}
    </ul>
    <p>The 'join_sample_dynamic' should use your actual domain, not localhost.</p>
    """

@app.route('/grading')
def grading_page():
    if 'user_type' not in session or session['user_type'] != 'teacher':
        flash('Access denied. Teachers only.')
        return redirect(url_for('login'))
    
    classrooms = load_classrooms()
    users = load_users()
    
    # Get teacher's classrooms
    teacher_classrooms = [c for c in classrooms.get('classrooms', []) if c['teacher_email'] == session['email']]
    
    # Collect all submissions with student info
    all_submissions = []
    for classroom in teacher_classrooms:
        for assignment in classroom.get('assignments', []):
            for submission in assignment.get('submissions', []):
                # Get student info
                student_info = next((u for u in users.get('students', []) if u['email'] == submission['student_email']), {})
                student_name = student_info.get('name', submission['student_email'])
                
                submission_info = {
                    'classroom_name': classroom['class_name'],
                    'classroom_id': classroom['code'],
                    'assignment_title': assignment['title'],
                    'assignment_id': assignment['id'],
                    'submission': submission,
                    'student_name': student_name,
                    'submitted_at': submission.get('timestamp', 'Unknown'),
                    'grade': submission.get('grade'),
                    'feedback': submission.get('feedback', ''),
                    'graded_by': submission.get('graded_by', ''),
                    'graded_timestamp': submission.get('graded_timestamp', '')
                }
                all_submissions.append(submission_info)
    
    # Sort by submission date (newest first)
    all_submissions.sort(key=lambda x: x['submitted_at'] or '', reverse=True)
    
    # Calculate grading statistics
    total_submissions = len(all_submissions)
    graded_submissions = len([s for s in all_submissions if s['grade'] is not None])
    pending_submissions = total_submissions - graded_submissions
    
    if graded_submissions > 0:
        average_grade = sum(s['grade'] for s in all_submissions if s['grade'] is not None) / graded_submissions
    else:
        average_grade = 0
    
    stats = {
        'total': total_submissions,
        'graded': graded_submissions,
        'pending': pending_submissions,
        'average_grade': round(average_grade, 1)
    }
    
    return render_template('grading.html', 
                         submissions=all_submissions,
                         stats=stats,
                         classrooms=teacher_classrooms)

@app.route('/view_submission/<classroom_id>/<assignment_id>/<student_email>')
def view_submission(classroom_id, assignment_id, student_email):
    """View detailed submission content"""
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return jsonify({'error': 'Access denied'}), 403
    
    classrooms = load_classrooms()
    users = load_users()
    
    # Find the submission
    submission = None
    assignment = None
    classroom = None
    
    for c in classrooms.get('classrooms', []):
        if c.get('code') == classroom_id and c.get('teacher_email') == session['email']:
            for a in c.get('assignments', []):
                if a.get('id') == assignment_id:
                    for s in a.get('submissions', []):
                        if s.get('student_email') == student_email:
                            submission = s
                            assignment = a
                            classroom = c
                            break
                    if submission:
                        break
            if submission:
                break
    
    if not submission:
        return jsonify({'error': 'Submission not found'}), 404
    
    # Get student info
    student_info = next((u for u in users.get('students', []) if u['email'] == student_email), {})
    student_name = student_info.get('name', student_email)
    
    # Check if it's a Google Docs link
    google_docs_info = get_google_docs_instructions(submission.get('submission_link', ''))
    
    submission_data = {
        'student_name': student_name,
        'assignment_title': assignment.get('title', 'Assignment'),
        'assignment_description': assignment.get('description', 'No description provided'),
        'submission_text': submission.get('submission_text', ''),
        'submission_link': submission.get('submission_link', ''),
        'filename': submission.get('filename', ''),
        'timestamp': submission.get('timestamp', ''),
        'google_docs_info': google_docs_info
    }
    
    return jsonify(submission_data)

if __name__ == '__main__':
    # Note: URL regeneration would happen during request handling
    # when dynamic_url_for is available in the context
    print("Starting Flask application with dynamic URL generation...")
    
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)