from flask import Blueprint, request, jsonify, session
import uuid
import datetime

from config import load_classrooms, save_classrooms, load_users, save_users

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
