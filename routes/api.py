from flask import Blueprint, request, jsonify, session
import uuid
import datetime
import json
import os
from openai import AzureOpenAI

from config import load_classrooms, save_classrooms, load_users, save_users

# Initialize Azure OpenAI client
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_NAME = "gpt-35-turbo"

if AOAI_ENDPOINT and AOAI_KEY:
    client = AzureOpenAI(
        azure_endpoint=AOAI_ENDPOINT,
        api_key=AOAI_KEY,
        api_version="2024-02-15-preview"
    )
else:
    client = None

api_bp = Blueprint('api', __name__)

def get_current_teacher_email():
    return session.get('email')

def get_current_teacher():
    users = load_users()
    email = get_current_teacher_email()
    return next((t for t in users['teachers'] if t['email'] == email), None)

# --- Create a new class (teacher only) ---
@api_bp.route('/create_class', methods=['POST'])
def create_class():
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    data = request.get_json()
    class_name = data.get('class_name')
    school = data.get('school', '')
    if not class_name:
        return jsonify({'success': False, 'error': 'Class name required'}), 400
    classrooms = load_classrooms()
    code = str(uuid.uuid4())[:8]
    teacher_email = get_current_teacher_email()
    new_class = {
        'code': code,
        'teacher_emails': [teacher_email],
        'class_name': class_name,
        'school': school,
        'students': [],
        'assignments': [],
        'rubrics': [],
        'created_at': datetime.datetime.now().isoformat()
    }
    classrooms['classrooms'].append(new_class)
    save_classrooms(classrooms)
    # Add class to teacher's profile
    users = load_users()
    for t in users['teachers']:
        if t['email'] == teacher_email:
            t.setdefault('classrooms', []).append(code)
            break
    save_users(users)
    return jsonify({'success': True, 'classroom': new_class})

# --- Join an existing class as a teacher ---
@api_bp.route('/join_class_as_teacher', methods=['POST'])
def join_class_as_teacher():
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    data = request.get_json()
    code = data.get('class_code')
    if not code:
        return jsonify({'success': False, 'error': 'Class code required'}), 400
    classrooms = load_classrooms()
    found = False
    for classroom in classrooms['classrooms']:
        if classroom['code'] == code:
            teacher_email = get_current_teacher_email()
            if 'teacher_emails' not in classroom:
                classroom['teacher_emails'] = [classroom.get('teacher_email')] if classroom.get('teacher_email') else []
            if teacher_email not in classroom['teacher_emails']:
                classroom['teacher_emails'].append(teacher_email)
            found = True
            break
    if not found:
        return jsonify({'success': False, 'error': 'Class not found'}), 404
    save_classrooms(classrooms)
    # Add class to teacher's profile
    users = load_users()
    for t in users['teachers']:
        if t['email'] == teacher_email:
            t.setdefault('classrooms', []).append(code)
            break
    save_users(users)
    return jsonify({'success': True})

# --- List classes managed or joined by the current teacher ---
@api_bp.route('/my_classes', methods=['GET'])
def my_classes():
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    teacher_email = get_current_teacher_email()
    classrooms = load_classrooms()
    my_classes = [c for c in classrooms['classrooms'] if teacher_email in c.get('teacher_emails', [])]
    return jsonify({'success': True, 'classrooms': my_classes})

# --- AI Grade Submission ---
@api_bp.route('/ai_grade_submission', methods=['POST'])
def ai_grade_submission():
    if session.get('user_type') != 'teacher':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if not client:
        return jsonify({'success': False, 'error': 'AI service not available'}), 503
    
    data = request.get_json()
    submission_id = data.get('submission_id')
    
    if not submission_id:
        return jsonify({'success': False, 'error': 'Submission ID required'}), 400
    
    # Find the submission
    classrooms = load_classrooms()
    submission = None
    assignment = None
    classroom = None
    
    teacher_email = get_current_teacher_email()
    
    for c in classrooms.get('classrooms', []):
        if teacher_email in c.get('teacher_emails', []):
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
    
    if not submission or not assignment:
        return jsonify({'success': False, 'error': 'Submission not found'}), 404
    
    try:
        # Get submission content
        submission_text = submission.get('submission_text', '')
        if not submission_text and submission.get('filename'):
            submission_text = f"File submitted: {submission.get('filename')}"
        
        # Find associated rubric
        rubric_content = ""
        if assignment.get('rubric_id'):
            rubric = next((r for r in classroom.get('rubrics', []) if r.get('id') == assignment.get('rubric_id')), None)
            if rubric:
                rubric_content = f"\n\nGrading Rubric:\n{rubric.get('content', '')}"
        
        # Create AI prompt
        prompt = f"""You are an experienced teacher grading a student assignment. Please provide a fair and constructive grade.

Assignment: {assignment.get('title', 'N/A')}
Instructions: {assignment.get('content', 'N/A')}

Student Submission:
{submission_text}
{rubric_content}

Please provide:
1. A numerical grade from 0-100
2. Constructive feedback explaining the grade

Format your response as JSON:
{{"grade": <number>, "feedback": "<feedback text>"}}"""

        # Call Azure OpenAI
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            result = json.loads(ai_response)
            grade = result.get('grade')
            feedback = result.get('feedback', '')
            
            # Validate grade
            if not isinstance(grade, (int, float)) or grade < 0 or grade > 100:
                grade = 75  # Default fallback
                
        except json.JSONDecodeError:
            # Fallback parsing if JSON fails
            grade = 75
            feedback = ai_response[:500] if ai_response else "AI grading completed."
        
        return jsonify({
            'success': True,
            'grade': int(grade),
            'feedback': feedback
        })
        
    except Exception as e:
        print(f"AI grading error: {e}")
        return jsonify({'success': False, 'error': 'AI grading failed'}), 500
