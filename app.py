import os
import json
import re
import dotenv
import datetime
import hashlib
import uuid
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from openai import AzureOpenAI
import markdown


# Import study tools blueprint
from routes.study_tools import study_tools_bp
# Import API blueprint
from routes.api import api_bp

dotenv.load_dotenv()
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_NAME = "gpt-35-turbo"

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


# Register blueprints
app.register_blueprint(study_tools_bp, url_prefix='/study-tools')
app.register_blueprint(api_bp, url_prefix='/api')

# Add markdown filter for templates
@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown text to HTML"""
    if not text:
        return ''
    return markdown.markdown(text, extensions=['nl2br', 'fenced_code', 'tables'])

# Add escapejs filter for templates
@app.template_filter('escapejs')
def escapejs_filter(text):
    """Escape JavaScript strings safely"""
    if not text:
        return ''
    # Escape quotes, backslashes, and newlines for JavaScript
    return (text.replace('\\', '\\\\')
                .replace("'", "\\'")
                .replace('"', '\\"')
                .replace('\n', '\\n')
                .replace('\r', '\\r')
                .replace('\t', '\\t'))

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
    current_time = datetime.datetime.now(datetime.UTC).isoformat()
    
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
        now = datetime.datetime.now(datetime.UTC)
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
        now = datetime.datetime.now(datetime.UTC)
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
    # Require authentication to access AI assistant
    if 'email' not in session:
        return redirect(url_for('login'))
    
    # Track student activity if they're logged in as a student
    if 'user_type' in session and session['user_type'] == 'student':
        update_student_activity(session['email'])
    
    # Check if game results are passed in the URL
    game_results = request.args.get('game_results')
    initial_message = None
    game_results_context = None
    
    if game_results:
        try:
            import urllib.parse
            results_data = json.loads(urllib.parse.unquote(game_results))
            
            # Extract comprehensive game results for AI context
            game_results_context = {
                'set_name': results_data.get('set_name', 'Unknown'),
                'score': results_data.get('score', 0),
                'accuracy': results_data.get('accuracy', 0),
                'total_questions': results_data.get('total_questions', 0),
                'correct_answers': results_data.get('correct_answers', 0),
                'performance_level': results_data.get('performance_level', 'unknown'),
                'is_win': results_data.get('is_win', False),
                'average_time': results_data.get('average_time', 0),
                'lives_remaining': results_data.get('lives_remaining', 0)
            }
            
            # Create an enhanced initial message that includes performance context
            performance_emoji = "🎉" if game_results_context['is_win'] else "💪"
            performance_text = "excellent" if game_results_context['accuracy'] >= 90 else "great" if game_results_context['accuracy'] >= 75 else "good progress"
            
            initial_message = f"""I just completed the {game_results_context['set_name']} study game! Here are my results:

{performance_emoji} **Game Performance Summary:**
• Score: {game_results_context['score']} points
• Accuracy: {game_results_context['accuracy']}% ({game_results_context['correct_answers']}/{game_results_context['total_questions']} correct)
• Performance Level: {game_results_context['performance_level'].title()}
• Result: {"Won! 🏆" if game_results_context['is_win'] else "Still learning 📚"}
• Average Response Time: {game_results_context['average_time']}s
• Lives Remaining: {game_results_context['lives_remaining']}/3

I'd like to discuss my performance and get some personalized study advice. What areas should I focus on based on these results?"""
            
        except Exception as e:
            print(f"Error parsing game results: {e}")
            # Fallback to basic message if parsing fails
            try:
                results_data = json.loads(urllib.parse.unquote(game_results))
                initial_message = results_data.get('message', '')
            except:
                pass
    
    # Pre-load resources for hyperlink processing as fallback
    user_email = session['email']
    resources = {
        'flashcards': [],
        'study_guides': [],
        'assignments': [],
        'rubrics': []
    }
    
    try:
        # Load flashcard sets
        try:
            with open('flashcards.json', 'r') as f:
                flashcards_data = json.load(f)
                if user_email in flashcards_data:
                    for set_name in flashcards_data[user_email]:
                        resources['flashcards'].append({
                            'name': set_name,
                            'title': set_name
                        })
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Load study guides
        try:
            with open('study_guides.json', 'r') as f:
                guides_data = json.load(f)
                if user_email in guides_data:
                    for guide_title in guides_data[user_email]:
                        resources['study_guides'].append({
                            'name': guide_title,
                            'title': guide_title
                        })
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Load assignments and rubrics from classrooms
        try:
            classrooms_data = load_classrooms()
            user_classrooms = []
            
            # Find classrooms where user is enrolled
            for classroom in classrooms_data.get('classrooms', []):
                if user_email in classroom.get('students', []):
                    user_classrooms.append((classroom.get('code'), classroom))
            
            # Extract assignments and rubrics
            for class_code, classroom in user_classrooms:
                # Add assignments
                for assignment in classroom.get('assignments', []):
                    resources['assignments'].append({
                        'id': assignment.get('id'),
                        'title': assignment.get('title'),
                        'class_code': class_code
                    })
                
                # Add rubrics
                for rubric in classroom.get('rubrics', []):
                    resources['rubrics'].append({
                        'id': rubric.get('id'),
                        'title': rubric.get('title'),
                        'class_code': class_code
                    })
        except Exception as e:
            print(f"Error loading classroom resources: {e}")
    except Exception as e:
        print(f"Error loading resources for AI page: {e}")
    
    print(f"DEBUG: Resources loaded for user {user_email}:")
    print(f"  Flashcards: {len(resources['flashcards'])}")
    print(f"  Study guides: {len(resources['study_guides'])}")
    print(f"  Assignments: {len(resources['assignments'])}")
    print(f"  Rubrics: {len(resources['rubrics'])}")
    
    return render_template('ai_assistant.html', initial_message=initial_message, resources=resources)

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

    # Get the user's name based on their type
    user_name = "User"
    user_role = "User"
    
    if user_type == 'student' and email:
        student = next((s for s in users['students'] if s['email'] == email), None)
        if student:
            user_name = student.get('name', 'Student')
            user_role = "Student"
    elif user_type == 'teacher' and email:
        teacher = next((t for t in users['teachers'] if t['email'] == email), None)
        if teacher:
            user_name = teacher.get('name', 'Teacher')
            user_role = "Teacher"

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
            accessible_classes = [c for c in classrooms_data['classrooms'] if (('teacher_emails' in c and email in c['teacher_emails']) or (c.get('teacher_email') == email))]
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
    submissions_context = ""
    
    if user_type == 'student' and email:
        performance = calculate_student_performance(email)
        recent_grades = performance.get('recent_grades', [])
        
        # Get detailed student submissions for AI analysis
        student_submissions = get_student_submissions(email)
        if student_submissions:
            submissions_info = []
            for submission in student_submissions[-5:]:  # Last 5 submissions
                sub_info = {
                    'assignment': submission.get('assignment_title', 'Unknown'),
                    'class': submission.get('class_name', 'Unknown'),
                    'grade': submission.get('grade'),
                    'feedback': submission.get('feedback', ''),
                    'submission_text': submission.get('submission_text', ''),
                    'submission_link': submission.get('submission_link', ''),
                    'timestamp': submission.get('timestamp', '')
                }
                
                sub_text = f"""
Assignment: {sub_info['assignment']} (Class: {sub_info['class']})
Submission Content: {sub_info['submission_text'][:300]}{'...' if len(sub_info['submission_text']) > 300 else ''}
{f"Link: {sub_info['submission_link']}" if sub_info['submission_link'] else ""}
Grade: {sub_info['grade'] if sub_info['grade'] is not None else 'Not graded yet'}
Teacher Feedback: {sub_info['feedback'][:200] if sub_info['feedback'] else 'No feedback yet'}{'...' if sub_info['feedback'] and len(sub_info['feedback']) > 200 else ''} 
Submitted: {sub_info['timestamp']}"""
                submissions_info.append(sub_text)
            
            submissions_context = f"""
STUDENT SUBMISSION HISTORY:
{'='*35}
{chr(10).join(submissions_info)}

AI ANALYSIS INSTRUCTIONS:
- Review the student's previous submissions to understand their writing style and common areas for improvement
- Reference specific past work when providing feedback (e.g., "Like in your recent assignment on...")
- Note patterns in teacher feedback to reinforce consistent improvement areas
- Compare current questions to past submission quality to provide targeted advice
- Help student connect feedback from previous assignments to current work"""
        
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
    
    elif user_type == 'teacher' and email:
        # Get teacher's feedback history for easy reference
        teacher_feedback_history = []
        for classroom in accessible_classes:
            for assignment in classroom.get('assignments', []):
                for submission in assignment.get('submissions', []):
                    if submission.get('graded_by') == email and submission.get('feedback'):
                        feedback_info = {
                            'student': submission.get('student_email', 'Unknown'),
                            'assignment': assignment.get('title', 'Unknown'),
                            'class': classroom.get('class_name', 'Unknown'),
                            'grade': submission.get('grade'),
                            'feedback': submission.get('feedback', ''),
                            'timestamp': submission.get('graded_timestamp', '')
                        }
                        teacher_feedback_history.append(feedback_info)
        
        if teacher_feedback_history:
            recent_feedback = teacher_feedback_history[-10:]  # Last 10 pieces of feedback
            feedback_summary = []
            for feedback in recent_feedback:
                feedback_text = f"""
Student: {feedback['student']} | Assignment: {feedback['assignment']} (Class: {feedback['class']})
Grade: {feedback['grade']} | Feedback: {feedback['feedback'][:150]}{'...' if len(feedback['feedback']) > 150 else ''}
Date: {feedback['timestamp']}"""
                feedback_summary.append(feedback_text)
            
            submissions_context = f"""
YOUR RECENT FEEDBACK HISTORY:
{'='*35}
{chr(10).join(feedback_summary)}

TEACHER ASSISTANCE INSTRUCTIONS:
- Reference your previous feedback patterns to maintain consistency
- Help you recall what you've told students about similar assignments
- Suggest improvements based on recurring issues you've noted
- Help you develop more effective feedback strategies
- Assist with identifying common student challenges from your grading history"""

    context = f"""{current_class_info}

Available Assignments By Class:
{'='*40}
{'\n\n'.join(assignments_by_class_text)}

Available Grading Rubrics By Class:
{'='*40}
{'\n\n'.join(rubrics_by_class_text)}

{performance_context}

{submissions_context}"""

    # Load study tools data (flashcards, study guides, and game results)
    study_tools_context = ""
    if user_type == 'student' and email:
        try:
            # Load user's flashcard sets from flashcards.json
            flashcard_sets = []
            try:
                with open('flashcards.json', 'r') as f:
                    flashcards_data = json.load(f)
                    if email in flashcards_data:
                        for set_name, set_data in flashcards_data[email].items():
                            flashcard_sets.append({
                                'name': set_name,
                                'cards_count': len(set_data.get('cards', [])),
                                'created_date': set_data.get('created_date', ''),
                                'subject': set_data.get('subject', 'General')
                            })
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading flashcards from flashcards.json: {e}")
            
            # Also check data directory for any additional flashcard sets (legacy support)
            flashcard_sets_dir = os.path.join('data', 'flashcard_sets')
            if os.path.exists(flashcard_sets_dir):
                for filename in os.listdir(flashcard_sets_dir):
                    if filename.endswith('.json'):
                        try:
                            with open(os.path.join(flashcard_sets_dir, filename), 'r') as f:
                                flashcard_data = json.load(f)
                                if flashcard_data.get('created_by') == email:
                                    flashcard_sets.append({
                                        'name': flashcard_data.get('name', 'Untitled'),
                                        'cards_count': len(flashcard_data.get('cards', [])),
                                        'created_date': flashcard_data.get('created_date', ''),
                                        'subject': flashcard_data.get('subject', 'General')
                                    })
                        except:
                            continue
            
            # Load user's study guides from study_guides.json
            study_guides = []
            try:
                with open('study_guides.json', 'r') as f:
                    study_guides_data = json.load(f)
                    if email in study_guides_data:
                        for guide_name, guide_data in study_guides_data[email].items():
                            study_guides.append({
                                'name': guide_name,
                                'title': guide_data.get('title', guide_name),
                                'content_length': len(str(guide_data.get('sections', []))),
                                'created_date': guide_data.get('created_date', ''),
                                'subject': guide_data.get('subject', 'General'),
                                'complexity_level': guide_data.get('complexity_level', 'intermediate')
                            })
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading study guides from study_guides.json: {e}")
            
            # Also check data directory for any additional study guides (legacy support)
            study_guides_dir = os.path.join('data', 'study_guides')
            if os.path.exists(study_guides_dir):
                for filename in os.listdir(study_guides_dir):
                    if filename.endswith('.json'):
                        try:
                            with open(os.path.join(study_guides_dir, filename), 'r') as f:
                                guide_data = json.load(f)
                                if guide_data.get('created_by') == email:
                                    study_guides.append({
                                        'name': guide_data.get('name', 'Untitled'),
                                        'content_length': len(guide_data.get('content', '')),
                                        'created_date': guide_data.get('created_date', ''),
                                        'subject': guide_data.get('subject', 'General')
                                    })
                        except:
                            continue
            
            # Load user's game results
            user_results_file = os.path.join('data', 'user_game_results', f"{email.replace('@', '_').replace('.', '_')}.json")
            game_results = []
            if os.path.exists(user_results_file):
                try:
                    with open(user_results_file, 'r') as f:
                        game_results = json.load(f)
                        # Keep only the last 10 results for context
                        game_results = game_results[-10:]
                except:
                    pass
            
            # Build study tools context
            flashcard_context = []
            for fc in flashcard_sets:
                fc_text = f"📚 '{fc['name']}' ({fc['subject']}) - {fc['cards_count']} cards"
                flashcard_context.append(fc_text)
            
            study_guide_context = []
            for sg in study_guides:
                sg_text = f"📖 '{sg['name']}' ({sg['subject']}) - {sg['content_length']} characters"
                study_guide_context.append(sg_text)
            
            game_results_context = []
            for gr in game_results[-5:]:  # Last 5 games
                accuracy = gr.get('accuracy', 0)
                game_text = f"🎮 {gr.get('flashcard_set_name', 'Unknown Set')} - Score: {gr.get('total_score', 0)}, Accuracy: {accuracy}% ({'Win' if gr.get('is_win', False) else 'Loss'})"
                game_results_context.append(game_text)
            
            study_tools_parts = []
            
            if flashcard_context:
                study_tools_parts.append(f"FLASHCARD SETS:\n" + '\n'.join(flashcard_context))
            
            if study_guide_context:
                study_tools_parts.append(f"STUDY GUIDES:\n" + '\n'.join(study_guide_context))
            
            if game_results_context:
                study_tools_parts.append(f"RECENT STUDY GAME RESULTS:\n" + '\n'.join(game_results_context))
            
            if study_tools_parts:
                study_tools_context = f"""
STUDENT'S STUDY TOOLS:
{'='*25}
{chr(10).join(study_tools_parts)}

STUDY TOOLS INSTRUCTIONS:
- When discussing study materials, reference the student's existing flashcards and study guides by name
- Provide clickable links to their study materials: 
  * Flashcards: <a href="/study-tools/flashcards/view/[SET_NAME]" target="_blank">View [SET_NAME] Flashcards</a>
  * Study Mode: <a href="/study-tools/flashcards/study/[SET_NAME]" target="_blank">Study [SET_NAME] (Game Mode Available)</a>
  * Study Guides: <a href="/study-tools/study-guides/view/[GUIDE_NAME]" target="_blank">View [GUIDE_NAME] Study Guide</a>
- Reference their game performance to encourage improvement or celebrate success
- Suggest creating new study materials when appropriate: <a href="/study-tools/create-flashcards" target="_blank">Create New Flashcards</a> or <a href="/study-tools/create-study-guide" target="_blank">Create Study Guide</a>
- If they performed poorly in recent games, offer encouragement and study tips
- If they performed well, congratulate them and suggest advancing to more challenging material
- Always use HTML links in your responses so students can easily access their study materials
"""
            
        except Exception as e:
            print(f"Error loading study tools context: {e}")
            study_tools_context = ""

    system_prompt = f"""{ai_personality}

You are assisting in a classroom environment. Here's your context and instructions:

USER INFORMATION:
Name: {user_name}
Role: {user_role}
Email: {email}

CURRENT CONTEXT:
{context}

{study_tools_context}

CORE INSTRUCTIONS:
1. Always address the user by their name ({user_name}) and acknowledge their role as a {user_role}
2. Adapt your responses based on their role:
   - If they are a Student: Guide them through learning with hints and questions, never give direct solutions
   - If they are a Teacher: Provide more direct assistance with curriculum, grading, and classroom management
3. Always consider which class an assignment or rubric belongs to when providing assistance
4. When someone asks about an assignment:
   - First identify which class it belongs to
   - Use the rubrics specific to that class
   - If multiple classes have similar assignments, ask for clarification
5. For uploaded work:
   - Match it to the correct class and assignment
   - Review against the appropriate class rubrics
   - Provide specific, constructive feedback
   - Reference the correct class context in your responses

ENHANCED PERSONALIZATION INSTRUCTIONS:
6. For Students - Use their submission history to provide targeted advice:
   - Reference specific past assignments when relevant ("In your recent essay on..., you showed strength in...")
   - Identify patterns in teacher feedback and help reinforce those lessons
   - Connect current questions to previous work to show growth opportunities
   - Provide improvement suggestions based on their actual submission style and common areas for growth
   - Be encouraging about progress while addressing consistent feedback themes

7. For Teachers - Help with feedback consistency and effectiveness:
   - Reference your previous feedback patterns to maintain consistency across students
   - Help recall what you've previously told students about similar work
   - Suggest improvements based on recurring issues you've identified in student work
   - Assist with developing more effective feedback strategies
   - Help identify common challenges students face based on your grading history

INTERACTION GUIDELINES:
- Be encouraging and supportive while maintaining academic integrity
- Always greet users by name and acknowledge if they are a student or teacher
- If someone doesn't specify which class they're asking about, ask for clarification
- Always frame your responses in the context of the specific class and its requirements
- For students: Help them understand concepts through guided discovery, referencing their actual work
- For teachers: Provide direct, practical assistance with educational tasks, drawing from their feedback history
- Use specific examples from submission history when appropriate to make advice more relevant and actionable

IMPORTANT: NEVER ask students to upload assignments they've already submitted. If a student asks about an assignment they've submitted, their submission content and teacher feedback will be automatically provided to you in the conversation. Use this information directly to provide feedback and analysis.

{performance_context}

{submissions_context}

Remember: Each class may have different requirements and rubrics, so always ensure you're using the correct context. 
Use the submission history data to provide more personalized, relevant guidance that connects to the user's actual academic experience."""

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

    # Enhanced AI response with automatic submission retrieval
    enhanced_prompt = user_prompt
    
    # If student is asking about a specific assignment, automatically provide submission content
    if user_type == 'student' and email:
        print(f"DEBUG: Student {email} asking: {user_prompt}")
        
        # Check if the user is asking about a specific assignment
        student_submissions = get_student_submissions(email)
        print(f"DEBUG: Found {len(student_submissions)} submissions for student")
        
        matching_submissions = []
        
        # More flexible assignment matching
        user_prompt_lower = user_prompt.lower()
        
        for submission in student_submissions:
            assignment_title = submission.get('assignment_title', '').lower()
            print(f"DEBUG: Checking assignment '{assignment_title}' against prompt '{user_prompt_lower}'")
            
            # Multiple matching strategies
            matches = False
            
            # Strategy 1: Exact assignment title match
            if assignment_title and assignment_title in user_prompt_lower:
                matches = True
                print(f"DEBUG: Exact match found for '{assignment_title}'")
            
            # Strategy 2: Individual words from assignment title
            elif assignment_title:
                title_words = [word for word in assignment_title.split() if len(word) > 2]  # Skip short words
                if title_words and any(word in user_prompt_lower for word in title_words):
                    matches = True
                    print(f"DEBUG: Word match found for '{assignment_title}' with words {title_words}")
            
            # Strategy 3: Check if user mentions assignment-related keywords
            assignment_keywords = ['assignment', 'homework', 'essay', 'reflection', 'paper', 'submission']
            if any(keyword in user_prompt_lower for keyword in assignment_keywords):
                # If they mention assignment keywords, look for partial title matches
                if assignment_title:
                    title_parts = assignment_title.replace(':', ' ').replace('-', ' ').split()
                    if any(part in user_prompt_lower for part in title_parts if len(part) > 2):
                        matches = True
                        print(f"DEBUG: Keyword + partial match found for '{assignment_title}' with parts {title_parts}")
            
            if matches:
                matching_submissions.append(submission)
                print(f"DEBUG: Added matching submission for '{assignment_title}'")
        
        print(f"DEBUG: Total matching submissions: {len(matching_submissions)}")
        
        # If we found matching assignments, add submission content to the prompt
        if matching_submissions:
            submission_content = []
            for submission in matching_submissions:
                content = f"""
--- YOUR SUBMISSION FOR "{submission.get('assignment_title', 'Unknown')}" ---
Submitted Content: {submission.get('submission_text', 'No text submission')}
{f"Submitted Link: {submission.get('submission_link', '')}" if submission.get('submission_link') else ""}
Grade: {submission.get('grade', 'Not graded yet')}
Teacher Feedback: {submission.get('feedback') if submission.get('feedback') else 'No written feedback provided' if submission.get('grade') is not None else 'Not graded yet'}
Graded by: {submission.get('graded_by', 'Not graded')}
Submitted on: {submission.get('timestamp', 'Unknown date')}
---"""
                submission_content.append(content)
            
            enhanced_prompt = f"{user_prompt}\n\n[AUTOMATIC SUBMISSION RETRIEVAL - The student is asking about an assignment they've already submitted. Here's their submission content:]\n{''.join(submission_content)}"
            print(f"DEBUG: Enhanced prompt created with {len(submission_content)} submissions")

    # Get AI response with enhanced prompt
    messages_enhanced = messages[:-1] + [{"role": "user", "content": enhanced_prompt}]
    
    # Check if user is requesting to create study materials
    user_prompt_lower = user_prompt.lower()
    study_creation_requests = {
        'flashcards': ['create flashcard', 'make flashcard', 'generate flashcard', 'flashcard for', 'flashcard about'],
        'study_guide': ['create study guide', 'make study guide', 'generate study guide', 'study guide for', 'study guide about']
    }
    
    # Detect study materials creation requests
    creation_type = None
    for material_type, keywords in study_creation_requests.items():
        if any(keyword in user_prompt_lower for keyword in keywords):
            creation_type = material_type
            break
    
    # Handle study materials creation
    if creation_type and user_type == 'student' and email:
        try:
            from services.ai_service import AIService
            ai_service = AIService()
            
            # Extract topic and details from user prompt
            topic_extractors = ['about', 'for', 'on', 'regarding', 'covering']
            topic = "General Topic"
            details = user_prompt
            
            # Try to extract a more specific topic
            for extractor in topic_extractors:
                if extractor in user_prompt_lower:
                    parts = user_prompt_lower.split(extractor, 1)
                    if len(parts) > 1:
                        topic = parts[1].strip()[:50]  # Limit topic length
                        break
            
            if creation_type == 'flashcards':
                # Create flashcards
                result = ai_service.create_flashcards_from_chat(topic, details, num_cards=10)
                
                if result['success']:
                    # Save the flashcards
                    try:
                        flashcards_data = json.loads(result['flashcards'])
                        
                        # Create flashcard set
                        flashcard_set = {
                            'id': str(uuid.uuid4()),
                            'name': f"AI Generated: {topic}",
                            'description': f"Created from chat request: {user_prompt[:100]}...",
                            'created_date': datetime.now().strftime('%Y-%m-%d'),
                            'flashcards': flashcards_data
                        }
                        
                        # Save to user's directory
                        user_dir = f"study_tools/flashcards/{email.replace('@', '_').replace('.', '_')}"
                        os.makedirs(user_dir, exist_ok=True)
                        
                        filename = f"{flashcard_set['name'].replace(' ', '_').replace(':', '')}.json"
                        filepath = f"{user_dir}/{filename}"
                        
                        with open(filepath, 'w') as f:
                            json.dump(flashcard_set, f, indent=2)
                        
                        ai_reply = f"""I've successfully created a flashcard set for you about "{topic}"! 🎯

**Flashcard Set Created**: {flashcard_set['name']}
**Number of Cards**: {len(flashcards_data)}

You can access your new flashcards here:
- <a href="/study-tools/flashcards/view/{flashcard_set['name']}" target="_blank">📚 View Flashcards</a>
- <a href="/study-tools/flashcards/study/{flashcard_set['name']}" target="_blank">🎮 Study Mode (with Game)</a>

The flashcards cover key concepts and include questions that test understanding, not just memorization. Ready to start studying?"""
                        
                    except json.JSONDecodeError:
                        ai_reply = "I created some flashcards for you, but there was an issue saving them. Let me help you create them manually through the <a href='/study-tools/create-flashcards' target='_blank'>flashcard creation page</a>."
                else:
                    ai_reply = f"I'd be happy to help you create flashcards about {topic}! Let me guide you to the <a href='/study-tools/create-flashcards' target='_blank'>flashcard creation page</a> where you can provide more details and I'll generate them for you."
            
            elif creation_type == 'study_guide':
                # Create study guide
                result = ai_service.create_study_guide_from_chat(topic, details)
                
                if result['success']:
                    # Save the study guide
                    study_guide = {
                        'id': str(uuid.uuid4()),
                        'title': f"AI Generated: {topic}",
                        'content': result['content'],
                        'created_date': datetime.now().strftime('%Y-%m-%d'),
                        'description': f"Created from chat request: {user_prompt[:100]}..."
                    }
                    
                    # Save to user's directory
                    user_dir = f"study_tools/study_guides/{email.replace('@', '_').replace('.', '_')}"
                    os.makedirs(user_dir, exist_ok=True)
                    
                    filename = f"{study_guide['title'].replace(' ', '_').replace(':', '')}.json"
                    filepath = f"{user_dir}/{filename}"
                    
                    with open(filepath, 'w') as f:
                        json.dump(study_guide, f, indent=2)
                    
                    ai_reply = f"""I've created a comprehensive study guide for you about "{topic}"! 📖

**Study Guide Created**: {study_guide['title']}

You can access your new study guide here:
- <a href="/study-tools/study-guides/view/{study_guide['title']}" target="_blank">📄 View Study Guide</a>

The study guide includes key concepts, definitions, examples, and practice questions to help you master the material. Ready to dive in?"""
                    
                else:
                    ai_reply = f"I'd be happy to help you create a study guide about {topic}! Let me guide you to the <a href='/study-tools/create-study-guide' target='_blank'>study guide creation page</a> where you can provide more details and I'll generate it for you."
            
        except Exception as e:
            print(f"Error creating study materials: {e}")
            ai_reply = f"I'd love to help you create study materials! Please visit the <a href='/study-tools/study-tools' target='_blank'>Study Tools</a> section where you can create flashcards and study guides with my assistance."
    
    else:
        # Normal AI response generation
        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages_enhanced,
            max_tokens=500,
            temperature=0.6
        )
        ai_reply = response.choices[0].message.content
    
    # Add original user message and AI reply to history (not the enhanced prompt)
    session[history_key].append({"role": "assistant", "content": ai_reply})
    session.modified = True

    # Enhance AI response with clickable links
    enhanced_ai_reply = enhance_response_with_links(ai_reply, user_type, email)

    return jsonify({'response': enhanced_ai_reply})

def enhance_response_with_links(ai_response, user_type, email):
    """Enhance AI response with clickable links to study materials and assignments"""
    if user_type != 'student' or not email:
        return ai_response
    
    enhanced_response = ai_response
    
    try:
        # Get user's study materials for link generation
        flashcard_sets = []
        study_guides = []
        
        # Load flashcard sets
        user_flashcards_dir = f"study_tools/flashcards/{email.replace('@', '_').replace('.', '_')}"
        if os.path.exists(user_flashcards_dir):
            for filename in os.listdir(user_flashcards_dir):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(user_flashcards_dir, filename), 'r') as f:
                            flashcard_data = json.load(f)
                            flashcard_sets.append({
                                'name': flashcard_data.get('name', filename.replace('.json', '')),
                                'filename': filename.replace('.json', '')
                            })
                    except:
                        continue
        
        # Load study guides
        user_guides_dir = f"study_tools/study_guides/{email.replace('@', '_').replace('.', '_')}"
        if os.path.exists(user_guides_dir):
            for filename in os.listdir(user_guides_dir):
                if filename.endswith('.json'):
                    try:
                        with open(os.path.join(user_guides_dir, filename), 'r') as f:
                            guide_data = json.load(f)
                            study_guides.append({
                                'name': guide_data.get('title', filename.replace('.json', '')),
                                'filename': filename.replace('.json', '')
                            })
                    except:
                        continue
        
        # Create clickable links for mentioned study materials
        import re
        
        # Find mentions of flashcard sets and create links
        for flashcard in flashcard_sets:
            name = flashcard['name']
            patterns = [
                name,
                name.lower(),
                name.replace(' ', ''),
                name.replace(' ', '_'),
                flashcard['filename']
            ]
            
            for pattern in patterns:
                if pattern and len(pattern) > 3:  # Avoid short matches
                    # Create a case-insensitive regex pattern
                    regex_pattern = re.escape(pattern)
                    regex = re.compile(regex_pattern, re.IGNORECASE)
                    
                    # Replace first occurrence with clickable link
                    def replace_func(match):
                        matched_text = match.group(0)
                        return f'<a href="/study-tools/flashcards/view/{name}" target="_blank" class="study-link">📚 {matched_text}</a>'
                    
                    enhanced_response = regex.sub(replace_func, enhanced_response, count=1)
        
        # Find mentions of study guides and create links
        for guide in study_guides:
            name = guide['name']
            patterns = [
                name,
                name.lower(),
                name.replace(' ', ''),
                name.replace(' ', '_'),
                guide['filename']
            ]
            
            for pattern in patterns:
                if pattern and len(pattern) > 3:  # Avoid short matches
                    # Create a case-insensitive regex pattern
                    regex_pattern = re.escape(pattern)
                    regex = re.compile(regex_pattern, re.IGNORECASE)
                    
                    # Replace first occurrence with clickable link
                    def replace_func(match):
                        matched_text = match.group(0)
                        return f'<a href="/study-tools/study-guides/view/{name}" target="_blank" class="study-link">📖 {matched_text}</a>'
                    
                    enhanced_response = regex.sub(replace_func, enhanced_response, count=1)
        
        # Add general study tools links for common phrases
        common_phrases = {
            r'\bflashcards?\b': '<a href="/study-tools/flashcards" target="_blank" class="study-link">flashcards</a>',
            r'\bstudy guides?\b': '<a href="/study-tools/study-guides" target="_blank" class="study-link">study guides</a>',
            r'\bcreate flashcards?\b': '<a href="/study-tools/create-flashcards" target="_blank" class="study-link">create flashcards</a>',
            r'\bcreate study guide\b': '<a href="/study-tools/create-study-guide" target="_blank" class="study-link">create study guide</a>',
            r'\bstudy tools?\b': '<a href="/study-tools/study-tools" target="_blank" class="study-link">study tools</a>'
        }
        
        for pattern, replacement in common_phrases.items():
            enhanced_response = re.sub(pattern, replacement, enhanced_response, flags=re.IGNORECASE)
    
    except Exception as e:
        print(f"Error enhancing response with links: {e}")
        return ai_response
    
    return enhanced_response

@app.route('/')
def home():
    if 'user_type' in session:
        if session['user_type'] == 'student':
            return redirect(url_for('student_main'))
        elif session['user_type'] == 'teacher':
            return redirect(url_for('teacher_main'))
    return render_template('home.html')

@app.route('/logo_test')
def logo_test():
    return render_template('logo_test.html')

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
    now = datetime.datetime.now(datetime.UTC)
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
        'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
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

@app.route('/unsubmit_assignment', methods=['POST'])
def unsubmit_assignment():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    
    # Track student activity
    update_student_activity(session['email'])
    
    assignment_id = request.form.get('assignment_id')
    
    if not assignment_id:
        flash('Invalid assignment ID')
        return redirect(url_for('student_main'))
    
    # Find the assignment and classroom
    classrooms = load_classrooms()
    assignment = None
    classroom = None
    submission = None
    
    for c in classrooms.get('classrooms', []):
        if session['email'] in c.get('students', []):
            for a in c.get('assignments', []):
                if a['id'] == assignment_id:
                    assignment = a
                    classroom = c
                    # Find the student's submission
                    for s in a.get('submissions', []):
                        if s.get('student_email') == session['email']:
                            submission = s
                            break
                    break
            if assignment:
                break
    
    if not assignment:
        flash('Assignment not found')
        return redirect(url_for('student_main'))
        
    if not submission:
        flash('No submission found to remove')
        return redirect(url_for('student_main'))
    
    # Check if the submission has been graded - if so, don't allow unsubmission
    if submission.get('grade') is not None:
        flash('Cannot unsubmit assignment that has already been graded')
        return redirect(url_for('student_main'))
    
    # Remove the submission
    assignment['submissions'] = [s for s in assignment['submissions'] if s.get('student_email') != session['email']]
    
    # If there was a file, we should remove it from the filesystem
    if submission.get('filename'):
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], submission['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing file: {e}")
            # Don't fail the unsubmit if file removal fails
    
    save_classrooms(classrooms)
    flash('Assignment unsubmitted successfully! You can now resubmit if needed.')
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
        grade = int(grade_num)  # Keep as integer for consistency
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
    submission['graded_timestamp'] = datetime.datetime.now(datetime.UTC).isoformat()
    
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
        
        # Determine what content was actually provided
        has_text = submission.get('submission_text', '').strip()
        has_link = submission.get('submission_link', '').strip()
        has_file = submission.get('filename', '') and file_content and not file_content.startswith('[')
        
        print(f"DEBUG: Content detection - has_text: {bool(has_text)}, has_link: {bool(has_link)}, has_file: {bool(has_file)}", flush=True)
        print(f"DEBUG: File content starts with: '{file_content[:50] if file_content else 'EMPTY'}...'", flush=True)
        
        # Create a list of provided submission types
        provided_content = []
        if has_text:
            provided_content.append(f"Text: {submission.get('submission_text', '')}")
        if has_link:
            provided_content.append(f"Link: {submission.get('submission_link', '')}")
        if has_file:
            provided_content.append(f"File ({submission.get('filename', 'Unknown')}): {file_content}")
        
        if not provided_content:
            provided_content.append("No substantial content provided")
        
        submission_content = "\n\n".join(provided_content)
        print(f"DEBUG: Final submission content structure: {[type.split(':')[0] for type in provided_content]}", flush=True)
        
        # For consistency, remove re-grading context that might bias the AI toward higher grades
        # Instead, focus on objective grading criteria
        
        # Build content description without mentioning what's missing
        content_types_used = []
        if has_text:
            content_types_used.append("written text")
        if has_link:
            content_types_used.append("external link")  
        if has_file:
            content_types_used.append("uploaded file")
        
        submission_method_desc = f"The student submitted their work via {' and '.join(content_types_used) if content_types_used else 'direct input'}."
        
        grading_prompt = f"""
        You are grading an assignment submission. Grade this work objectively based on the content provided.
        
        GRADING CRITERIA:
        - Content Quality and Completeness (40%)
        - Understanding and Analysis (30%) 
        - Organization and Clarity (20%)
        - Following Instructions (10%)
        
        ASSIGNMENT DETAILS:
        Student Name: {student_name}
        Assignment Title: {assignment.get('title', 'Assignment')}
        Assignment Description: {assignment.get('description', 'No description provided')}
        
        SUBMISSION DETAILS:
        {submission_method_desc}
        
        STUDENT WORK TO EVALUATE:
        {submission_content}
        
        GRADING INSTRUCTIONS:
        - Evaluate ONLY the content provided above
        - The student chose an appropriate submission method - do not comment on format choices
        - Focus on content quality, understanding, organization, and instruction compliance
        - Use grades: 90-100 (Excellent), 80-89 (Good), 70-79 (Satisfactory), 60-69 (Needs Improvement), <60 (Inadequate)
        - Be consistent and fair
        
        Provide your response as:
        GRADE: [number]
        FEEDBACK: [constructive feedback addressing {student_name} directly about their work quality]
        """
        print(f"DEBUG: About to call OpenAI with prompt length: {len(grading_prompt)}", flush=True)
        print(f"DEBUG: Submission method description: {submission_method_desc}", flush=True)
        
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
        submission['graded_timestamp'] = datetime.datetime.now(datetime.UTC).isoformat()
        
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
        if (('teacher_emails' in classroom and session['email'] in classroom['teacher_emails']) or (classroom.get('teacher_email') == session['email'])):
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
        if (('teacher_emails' in c and session['email'] in c['teacher_emails']) or (c.get('teacher_email') == session['email'])):
            if c['school'] not in schools:
                schools[c['school']] = []
            schools[c['school']].append(c)
    selected_class = flask_request.args.get('class')
    class_obj = None
    if selected_class:
        for c in classrooms_data['classrooms']:
            if c['code'] == selected_class and (('teacher_emails' in c and session['email'] in c['teacher_emails']) or (c.get('teacher_email') == session['email'])):
                class_obj = c
                break
    now = datetime.datetime.now(datetime.UTC)
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
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
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
            'timestamp': datetime.datetime.now(datetime.UTC).isoformat(),
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
    # If not logged in as student, show modern join page
    return render_template('join_classroom.html', join_code=code)

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
                
                # Convert grade to integer if it exists, to ensure consistent type
                grade = submission.get('grade')
                if grade is not None:
                    try:
                        grade = int(grade) if isinstance(grade, str) else grade
                    except (ValueError, TypeError):
                        grade = None
                
                submission_info = {
                    'classroom_name': classroom['class_name'],
                    'classroom_id': classroom['code'],
                    'assignment_title': assignment['title'],
                    'assignment_id': assignment['id'],
                    'submission': submission,
                    'student_name': student_name,
                    'submitted_at': submission.get('timestamp', 'Unknown'),
                    'grade': grade,
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
        # Convert grades to integers before summing to handle mixed int/string grades
        grades = []
        for s in all_submissions:
            if s['grade'] is not None:
                try:
                    # Convert grade to int, handling both string and int inputs
                    grade_value = int(s['grade']) if isinstance(s['grade'], str) else s['grade']
                    grades.append(grade_value)
                except (ValueError, TypeError):
                    # Skip invalid grades
                    continue
        
        if grades:
            average_grade = sum(grades) / len(grades)
        else:
            average_grade = 0
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

@app.route('/teacher/feedback_history')
def teacher_feedback_history():
    """View teacher's feedback history for easy reference"""
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    classrooms = load_classrooms()
    users = load_users()
    teacher_email = session['email']
    
    # Collect all feedback given by this teacher
    feedback_history = []
    
    for classroom in classrooms.get('classrooms', []):
        if classroom.get('teacher_email') == teacher_email:
            for assignment in classroom.get('assignments', []):
                for submission in assignment.get('submissions', []):
                    if submission.get('graded_by') == teacher_email and submission.get('feedback'):
                        # Get student name
                        student_info = next((s for s in users.get('students', []) if s['email'] == submission.get('student_email')), {})
                        student_name = student_info.get('name', submission.get('student_email', 'Unknown'))
                        
                        feedback_entry = {
                            'student_name': student_name,
                            'student_email': submission.get('student_email'),
                            'assignment_title': assignment.get('title', 'Unknown Assignment'),
                            'class_name': classroom.get('class_name', 'Unknown Class'),
                            'class_code': classroom.get('code'),
                            'assignment_id': assignment.get('id'),
                            'grade': submission.get('grade'),
                            'feedback': submission.get('feedback', ''),
                            'graded_timestamp': submission.get('graded_timestamp', ''),
                            'submission_preview': submission.get('submission_text', '')[:200] + '...' if submission.get('submission_text') else 'No text submission'
                        }
                        feedback_history.append(feedback_entry)
    
    # Sort by most recent first
    feedback_history.sort(key=lambda x: x.get('graded_timestamp', ''), reverse=True)
    
    # Get teacher info
    teacher = next((t for t in users.get('teachers', []) if t['email'] == teacher_email), {})
    
    return render_template('teacher_feedback_history.html', 
                         feedback_history=feedback_history,
                         teacher=teacher)

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
        'grade': submission.get('grade'),
        'feedback': submission.get('feedback', ''),
        'graded_by': submission.get('graded_by', ''),
        'graded_timestamp': submission.get('graded_timestamp', ''),
        'google_docs_info': google_docs_info
    }
    
    return jsonify(submission_data)

if __name__ == '__main__':
    # Note: URL regeneration would happen during request handling
    # when dynamic_url_for is available in the context
    print("Starting Flask application with dynamic URL generation...")
    
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)