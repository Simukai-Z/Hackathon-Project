"""
Study Tools Routes - Flash Cards and Study Guides
Handles all routes related to flash cards and study guides functionality
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
from datetime import datetime, timedelta
import json
import uuid
import os
from werkzeug.utils import secure_filename
import base64
from io import BytesIO

try:
    from services.ai_service import AIService
except ImportError:
    AIService = None

try:
    from config import load_users, save_users, load_classrooms, UPLOAD_FOLDER
except ImportError:
    def load_users():
        return {"students": [], "teachers": []}
    def save_users(users):
        pass
    def load_classrooms():
        return {"classrooms": []}
    UPLOAD_FOLDER = "uploads"

study_tools_bp = Blueprint('study_tools', __name__)

def get_current_user_email():
    """Get current user email from session"""
    return session.get('email')

def get_current_user_type():
    """Get current user type from session"""
    return session.get('user_type')

def is_user_logged_in():
    """Check if user is logged in"""
    return 'email' in session and 'user_type' in session

# Flash Cards Data Storage (In production, use a database)
FLASHCARDS_FILE = 'flashcards.json'
STUDY_GUIDES_FILE = 'study_guides.json'
STUDY_PROGRESS_FILE = 'study_progress.json'

def load_flashcards():
    """Load flash cards from JSON file"""
    try:
        if os.path.exists(FLASHCARDS_FILE):
            with open(FLASHCARDS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading flash cards: {e}")
    return {}

def save_flashcards(data):
    """Save flash cards to JSON file"""
    try:
        with open(FLASHCARDS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving flash cards: {e}")
        return False

def load_study_guides():
    """Load study guides from JSON file"""
    try:
        if os.path.exists(STUDY_GUIDES_FILE):
            with open(STUDY_GUIDES_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading study guides: {e}")
    return {}

def save_study_guides(data):
    """Save study guides to JSON file"""
    try:
        with open(STUDY_GUIDES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving study guides: {e}")
        return False

def load_study_progress():
    """Load study progress from JSON file"""
    try:
        if os.path.exists(STUDY_PROGRESS_FILE):
            with open(STUDY_PROGRESS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading study progress: {e}")
    return {}

def save_study_progress(data):
    """Save study progress to JSON file"""
    try:
        with open(STUDY_PROGRESS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving study progress: {e}")
        return False

@study_tools_bp.route('/study-tools')
def study_tools_dashboard():
    """Main study tools dashboard"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    flashcards_data = load_flashcards()
    study_guides_data = load_study_guides()
    progress_data = load_study_progress()
    
    # Get user's flash card sets
    user_flashcards = flashcards_data.get(user_email, {})
    user_study_guides = study_guides_data.get(user_email, {})
    user_progress = progress_data.get(user_email, {})
    
    # Calculate statistics
    total_flashcard_sets = len(user_flashcards)
    total_flashcards = sum(len(card_set.get('cards', [])) for card_set in user_flashcards.values())
    total_study_guides = len(user_study_guides)
    
    # Calculate average score
    scores = []
    for progress in user_progress.values():
        if 'correct_percentage' in progress:
            scores.append(progress['correct_percentage'])
    average_score = round(sum(scores) / len(scores)) if scores else 0
    
    # Recent activity (mock data for now)
    recent_activity = []
    
    print("DEBUG: About to render template with data:")
    print(f"  total_flashcard_sets: {total_flashcard_sets}")
    print(f"  total_flashcards: {total_flashcards}")
    print(f"  total_study_guides: {total_study_guides}")
    print(f"  average_score: {average_score}")
    print(f"  recent_activity: {recent_activity}")
    
    try:
        return render_template('study_tools_dashboard.html',
                             total_flashcard_sets=total_flashcard_sets,
                             total_flashcards=total_flashcards,
                             total_study_guides=total_study_guides,
                             average_score=average_score,
                             recent_activity=recent_activity)
    except Exception as e:
        print(f"DEBUG: Template rendering error: {e}")
        return f"Template Error: {e}", 500

@study_tools_bp.route('/flashcards')
def flashcards():
    """Flash cards management page"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    flashcards_data = load_flashcards()
    progress_data = load_study_progress()
    
    user_flashcards = flashcards_data.get(user_email, {})
    user_progress = progress_data.get(user_email, {})
    
    return render_template('flashcards.html',
                         flashcard_sets=user_flashcards,
                         user_progress=user_progress)

@study_tools_bp.route('/create-flashcards')
def create_flashcards():
    """Create flash cards page"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    return render_template('create_flashcards.html')

@study_tools_bp.route('/api/create-flashcards', methods=['POST'])
def api_create_flashcards():
    """API endpoint to create flash cards"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        user_email = session['email']
        set_name = request.form.get('set_name')
        content_source = request.form.get('content_source')
        card_count = int(request.form.get('card_count', 15))
        difficulty_level = request.form.get('difficulty_level', 'intermediate')
        
        if not set_name:
            return jsonify({'success': False, 'error': 'Set name is required'}), 400
        
        # Get content based on source
        content_text = ""
        if content_source == 'text':
            content_text = request.form.get('content_text', '')
        elif content_source == 'file':
            # Handle file upload
            uploaded_file = request.files.get('content_file')
            if uploaded_file:
                # For now, we'll just use the filename as content
                content_text = f"Content from file: {uploaded_file.filename}"
        elif content_source == 'assignment':
            assignment_id = request.form.get('assignment_id')
            content_text = f"Content from assignment ID: {assignment_id}"
        
        if not content_text:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        # Generate flash cards (mock implementation)
        cards = []
        for i in range(card_count):
            cards.append({
                'id': str(uuid.uuid4()),
                'front': f"Question {i+1} from {set_name}",
                'back': f"Answer {i+1} based on the provided content",
                'difficulty': difficulty_level,
                'created_at': datetime.now().isoformat()
            })
        
        # Save flash cards
        flashcards_data = load_flashcards()
        if user_email not in flashcards_data:
            flashcards_data[user_email] = {}
        
        flashcards_data[user_email][set_name] = {
            'cards': cards,
            'created_at': datetime.now().isoformat(),
            'difficulty': difficulty_level,
            'total_cards': len(cards)
        }
        
        if save_flashcards(flashcards_data):
            return jsonify({'success': True, 'message': f'Created {len(cards)} flash cards successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save flash cards'}), 500
            
    except Exception as e:
        print(f"Error creating flash cards: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while creating flash cards'}), 500

@study_tools_bp.route('/study-guides')
def study_guides():
    """Study guides management page"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    study_guides_data = load_study_guides()
    user_study_guides = study_guides_data.get(user_email, {})
    
    return render_template('study_guides.html',
                         study_guides=user_study_guides)

@study_tools_bp.route('/create-study-guide')
def create_study_guide():
    """Create study guide page"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    return render_template('create_study_guide.html')
