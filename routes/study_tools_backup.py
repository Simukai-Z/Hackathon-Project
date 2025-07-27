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
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from services.ai_service import AIService
from config import load_users, save_users, load_classrooms, UPLOAD_FOLDER

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
    
    # Recent activity
    recent_flashcards = []
    recent_study_guides = []
    
    for set_id, card_set in user_flashcards.items():
        recent_flashcards.append({
            'id': set_id,
            'title': card_set.get('title', 'Untitled'),
            'card_count': len(card_set.get('cards', [])),
            'created_at': card_set.get('created_at', ''),
            'last_studied': user_progress.get('flashcards', {}).get(set_id, {}).get('last_studied', 'Never')
        })
    
    for guide_id, guide in user_study_guides.items():
        recent_study_guides.append({
            'id': guide_id,
            'title': guide.get('title', 'Untitled'),
            'subject': guide.get('subject', 'General'),
            'created_at': guide.get('created_at', ''),
            'last_accessed': guide.get('last_accessed', 'Never')
        })
    
    # Sort by creation date (most recent first)
    recent_flashcards.sort(key=lambda x: x['created_at'], reverse=True)
    recent_study_guides.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('study_tools/dashboard.html',
                         total_flashcard_sets=total_flashcard_sets,
                         total_flashcards=total_flashcards,
                         total_study_guides=total_study_guides,
                         recent_flashcards=recent_flashcards[:5],
                         recent_study_guides=recent_study_guides[:5])

# ============ FLASH CARDS ROUTES ============

@study_tools_bp.route('/flashcards')
def flashcards_list():
    """List all flash card sets for the current user"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    flashcards_data = load_flashcards()
    progress_data = load_study_progress()
    
    user_flashcards = flashcards_data.get(user_email, {})
    user_progress = progress_data.get(user_email, {}).get('flashcards', {})
    
    # Prepare flash card sets with progress info
    flashcard_sets = []
    for set_id, card_set in user_flashcards.items():
        set_progress = user_progress.get(set_id, {})
        
        flashcard_sets.append({
            'id': set_id,
            'title': card_set.get('title', 'Untitled'),
            'description': card_set.get('description', ''),
            'subject': card_set.get('subject', 'General'),
            'card_count': len(card_set.get('cards', [])),
            'created_at': card_set.get('created_at', ''),
            'last_studied': set_progress.get('last_studied', 'Never'),
            'mastery_level': set_progress.get('mastery_level', 0),
            'total_reviews': set_progress.get('total_reviews', 0)
        })
    
    # Sort by last studied (most recent first)
    flashcard_sets.sort(key=lambda x: x['last_studied'] if x['last_studied'] != 'Never' else '', reverse=True)
    
    return render_template('study_tools/flashcards_list.html', flashcard_sets=flashcard_sets)

@study_tools_bp.route('/flashcards/create')
def create_flashcard_set():
    """Create a new flash card set"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    return render_template('study_tools/create_flashcards.html')

@study_tools_bp.route('/flashcards/save', methods=['POST'])
def save_flashcard_set():
    """Save a new or existing flash card set"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        user_email = session['email']
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'})
        
        if not data.get('cards') or len(data.get('cards', [])) == 0:
            return jsonify({'success': False, 'message': 'At least one card is required'})
        
        # Load existing data
        flashcards_data = load_flashcards()
        if user_email not in flashcards_data:
            flashcards_data[user_email] = {}
        
        # Generate new set ID or use existing
        set_id = data.get('set_id', str(uuid.uuid4()))
        
        # Prepare flash card set data
        card_set = {
            'title': data['title'],
            'description': data.get('description', ''),
            'subject': data.get('subject', 'General'),
            'cards': data['cards'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save the set
        flashcards_data[user_email][set_id] = card_set
        
        if save_flashcards(flashcards_data):
            return jsonify({
                'success': True, 
                'message': 'Flash card set saved successfully!',
                'set_id': set_id
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save flash card set'})
            
    except Exception as e:
        print(f"Error saving flash card set: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@study_tools_bp.route('/flashcards/<set_id>')
def view_flashcard_set(set_id):
    """View and study a flash card set"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    flashcards_data = load_flashcards()
    progress_data = load_study_progress()
    
    user_flashcards = flashcards_data.get(user_email, {})
    
    if set_id not in user_flashcards:
        return redirect(url_for('study_tools.flashcards_list'))
    
    card_set = user_flashcards[set_id]
    set_progress = progress_data.get(user_email, {}).get('flashcards', {}).get(set_id, {})
    
    # Calculate spaced repetition priorities
    cards_with_priority = []
    for i, card in enumerate(card_set.get('cards', [])):
        card_progress = set_progress.get('cards', {}).get(str(i), {})
        
        # Calculate priority based on performance and time since last review
        incorrect_count = card_progress.get('incorrect_count', 0)
        correct_count = card_progress.get('correct_count', 0)
        last_reviewed = card_progress.get('last_reviewed')
        
        # Higher priority for cards with more incorrect answers
        priority = incorrect_count + 1
        
        # Increase priority if card hasn't been reviewed recently
        if last_reviewed:
            days_since_review = (datetime.now() - datetime.fromisoformat(last_reviewed)).days
            if days_since_review > 7:  # Haven't seen in a week
                priority += 2
            elif days_since_review > 3:  # Haven't seen in 3 days
                priority += 1
        else:
            priority += 3  # Never reviewed
        
        cards_with_priority.append({
            'index': i,
            'card': card,
            'priority': priority,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'accuracy': correct_count / (correct_count + incorrect_count) * 100 if (correct_count + incorrect_count) > 0 else 0
        })
    
    # Sort by priority (highest first) for spaced repetition
    cards_with_priority.sort(key=lambda x: x['priority'], reverse=True)
    
    return render_template('study_tools/study_flashcards.html', 
                         card_set=card_set, 
                         set_id=set_id,
                         cards_with_priority=cards_with_priority,
                         set_progress=set_progress)

@study_tools_bp.route('/flashcards/<set_id>/quiz')
def quiz_flashcards(set_id):
    """Quiz mode for flash cards"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    flashcards_data = load_flashcards()
    
    user_flashcards = flashcards_data.get(user_email, {})
    
    if set_id not in user_flashcards:
        return redirect(url_for('study_tools.flashcards_list'))
    
    card_set = user_flashcards[set_id]
    
    return render_template('study_tools/quiz_flashcards.html', 
                         card_set=card_set, 
                         set_id=set_id)

@study_tools_bp.route('/flashcards/<set_id>/record-answer', methods=['POST'])
def record_flashcard_answer(set_id):
    """Record a flash card answer for spaced repetition"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        user_email = session['email']
        data = request.get_json()
        
        card_index = data.get('card_index')
        is_correct = data.get('is_correct', False)
        
        # Load progress data
        progress_data = load_study_progress()
        if user_email not in progress_data:
            progress_data[user_email] = {}
        if 'flashcards' not in progress_data[user_email]:
            progress_data[user_email]['flashcards'] = {}
        if set_id not in progress_data[user_email]['flashcards']:
            progress_data[user_email]['flashcards'][set_id] = {
                'cards': {},
                'total_reviews': 0,
                'last_studied': datetime.now().isoformat()
            }
        
        set_progress = progress_data[user_email]['flashcards'][set_id]
        
        # Initialize card progress if needed
        if str(card_index) not in set_progress['cards']:
            set_progress['cards'][str(card_index)] = {
                'correct_count': 0,
                'incorrect_count': 0,
                'last_reviewed': None
            }
        
        card_progress = set_progress['cards'][str(card_index)]
        
        # Update progress
        if is_correct:
            card_progress['correct_count'] += 1
        else:
            card_progress['incorrect_count'] += 1
        
        card_progress['last_reviewed'] = datetime.now().isoformat()
        set_progress['total_reviews'] += 1
        set_progress['last_studied'] = datetime.now().isoformat()
        
        # Calculate mastery level for the set
        total_correct = sum(card.get('correct_count', 0) for card in set_progress['cards'].values())
        total_attempts = sum(card.get('correct_count', 0) + card.get('incorrect_count', 0) 
                           for card in set_progress['cards'].values())
        
        if total_attempts > 0:
            set_progress['mastery_level'] = int((total_correct / total_attempts) * 100)
        
        # Save progress
        save_study_progress(progress_data)
        
        return jsonify({'success': True, 'message': 'Answer recorded'})
        
    except Exception as e:
        print(f"Error recording flash card answer: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@study_tools_bp.route('/flashcards/generate-ai', methods=['POST'])
def generate_ai_flashcards():
    """Generate flash cards using AI from uploaded content"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        subject = data.get('subject', 'General')
        card_count = min(int(data.get('card_count', 10)), 20)  # Limit to 20 cards
        
        if not content:
            return jsonify({'success': False, 'message': 'Content is required'})
        
        # Use AI service to generate flash cards
        ai_service = AIService()
        
        prompt = f"""
        Create {card_count} educational flash cards from the following content about {subject}.
        
        Content:
        {content}
        
        Requirements:
        - Create clear, concise questions and answers
        - Focus on key concepts, definitions, and important facts
        - Make questions challenging but fair for students
        - Vary question types (definitions, explanations, examples, etc.)
        - Return ONLY a JSON array of objects with 'question' and 'answer' fields
        - Keep questions and answers appropriately sized for flash cards
        
        Example format:
        [
            {{"question": "What is photosynthesis?", "answer": "The process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen."}},
            {{"question": "What are the main components needed for photosynthesis?", "answer": "Sunlight, carbon dioxide (CO2), water (H2O), and chlorophyll."}}
        ]
        """
        
        response = ai_service.get_ai_response(prompt, max_tokens=2000)
        
        # Try to parse the AI response as JSON
        try:
            # Clean the response to extract just the JSON part
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            flashcards = json.loads(response_clean)
            
            # Validate the structure
            if not isinstance(flashcards, list):
                raise ValueError("Response is not a list")
            
            for card in flashcards:
                if not isinstance(card, dict) or 'question' not in card or 'answer' not in card:
                    raise ValueError("Invalid card structure")
            
            return jsonify({'success': True, 'flashcards': flashcards})
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing AI response: {e}")
            print(f"AI Response: {response}")
            return jsonify({'success': False, 'message': 'Failed to generate valid flash cards. Please try again.'})
        
    except Exception as e:
        print(f"Error generating AI flash cards: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

# ============ STUDY GUIDES ROUTES ============

@study_tools_bp.route('/study-guides')
def study_guides_list():
    """List all study guides for the current user"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    study_guides_data = load_study_guides()
    
    user_study_guides = study_guides_data.get(user_email, {})
    
    # Prepare study guides list
    study_guides = []
    for guide_id, guide in user_study_guides.items():
        study_guides.append({
            'id': guide_id,
            'title': guide.get('title', 'Untitled'),
            'subject': guide.get('subject', 'General'),
            'description': guide.get('description', ''),
            'created_at': guide.get('created_at', ''),
            'last_accessed': guide.get('last_accessed', 'Never'),
            'content_length': len(guide.get('content', ''))
        })
    
    # Sort by creation date (most recent first)
    study_guides.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('study_tools/study_guides_list.html', study_guides=study_guides)

@study_tools_bp.route('/study-guides/create')
def create_study_guide():
    """Create a new study guide"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    return render_template('study_tools/create_study_guide.html')

@study_tools_bp.route('/study-guides/generate-ai', methods=['POST'])
def generate_ai_study_guide():
    """Generate a study guide using AI"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        subject = data.get('subject', 'General')
        topic = data.get('topic', '')
        
        if not content:
            return jsonify({'success': False, 'message': 'Content is required'})
        
        # Use AI service to generate study guide
        ai_service = AIService()
        
        prompt = f"""
        Create a comprehensive study guide for {subject} {f'focusing on {topic}' if topic else ''}.
        
        Source Material:
        {content}
        
        Requirements:
        - Create a well-structured study guide with clear sections
        - Include key concepts, definitions, important facts, and formulas
        - Add sample questions for practice
        - Highlight critical information that students should remember
        - Use markdown formatting for better readability
        - Include a summary section at the end
        - Make it suitable for high school or college level students
        
        Structure the guide with these sections:
        # Study Guide: [Topic]
        
        ## Key Concepts
        ## Important Definitions
        ## Critical Facts & Formulas
        ## Sample Questions
        ## Summary
        ## Study Tips
        """
        
        response = ai_service.get_ai_response(prompt, max_tokens=3000)
        
        return jsonify({'success': True, 'study_guide': response})
        
    except Exception as e:
        print(f"Error generating AI study guide: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@study_tools_bp.route('/study-guides/save', methods=['POST'])
def save_study_guide():
    """Save a study guide"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        user_email = session['email']
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'})
        
        if not data.get('content'):
            return jsonify({'success': False, 'message': 'Content is required'})
        
        # Load existing data
        study_guides_data = load_study_guides()
        if user_email not in study_guides_data:
            study_guides_data[user_email] = {}
        
        # Generate new guide ID or use existing
        guide_id = data.get('guide_id', str(uuid.uuid4()))
        
        # Prepare study guide data
        study_guide = {
            'title': data['title'],
            'subject': data.get('subject', 'General'),
            'description': data.get('description', ''),
            'content': data['content'],
            'notes': data.get('notes', ''),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat()
        }
        
        # Save the guide
        study_guides_data[user_email][guide_id] = study_guide
        
        if save_study_guides(study_guides_data):
            return jsonify({
                'success': True, 
                'message': 'Study guide saved successfully!',
                'guide_id': guide_id
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save study guide'})
            
    except Exception as e:
        print(f"Error saving study guide: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})

@study_tools_bp.route('/study-guides/<guide_id>')
def view_study_guide(guide_id):
    """View a study guide"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    study_guides_data = load_study_guides()
    
    user_study_guides = study_guides_data.get(user_email, {})
    
    if guide_id not in user_study_guides:
        return redirect(url_for('study_tools.study_guides_list'))
    
    study_guide = user_study_guides[guide_id]
    
    # Update last accessed time
    study_guide['last_accessed'] = datetime.now().isoformat()
    save_study_guides(study_guides_data)
    
    return render_template('study_tools/view_study_guide.html', 
                         study_guide=study_guide, 
                         guide_id=guide_id)

@study_tools_bp.route('/study-guides/<guide_id>/export-pdf')
def export_study_guide_pdf(guide_id):
    """Export study guide as PDF"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    study_guides_data = load_study_guides()
    
    user_study_guides = study_guides_data.get(user_email, {})
    
    if guide_id not in user_study_guides:
        return jsonify({'success': False, 'message': 'Study guide not found'})
    
    study_guide = user_study_guides[guide_id]
    
    try:
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        story.append(Paragraph(study_guide['title'], title_style))
        story.append(Spacer(1, 12))
        
        # Subject and description
        if study_guide.get('subject'):
            story.append(Paragraph(f"<b>Subject:</b> {study_guide['subject']}", styles['Normal']))
            story.append(Spacer(1, 6))
        
        if study_guide.get('description'):
            story.append(Paragraph(f"<b>Description:</b> {study_guide['description']}", styles['Normal']))
            story.append(Spacer(1, 12))
        
        # Content (convert markdown-like formatting to basic HTML)
        content = study_guide['content']
        content = content.replace('# ', '<font size=14><b>').replace('\n## ', '</b></font><br/><br/><font size=12><b>')
        content = content.replace('\n**', '<br/><b>').replace('**', '</b>')
        content = content.replace('\n*', '<br/>•').replace('\n-', '<br/>•')
        content = content.replace('\n', '<br/>')
        
        story.append(Paragraph(content, styles['Normal']))
        
        # Notes if available
        if study_guide.get('notes'):
            story.append(Spacer(1, 20))
            story.append(Paragraph("<b>Personal Notes:</b>", styles['Heading2']))
            story.append(Paragraph(study_guide['notes'].replace('\n', '<br/>'), styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{study_guide['title']}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        return jsonify({'success': False, 'message': 'Failed to export PDF'})

@study_tools_bp.route('/study-guides/<guide_id>/update-notes', methods=['POST'])
def update_study_guide_notes(guide_id):
    """Update personal notes in a study guide"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        user_email = session['email']
        data = request.get_json()
        notes = data.get('notes', '')
        
        # Load existing data
        study_guides_data = load_study_guides()
        user_study_guides = study_guides_data.get(user_email, {})
        
        if guide_id not in user_study_guides:
            return jsonify({'success': False, 'message': 'Study guide not found'})
        
        # Update notes
        user_study_guides[guide_id]['notes'] = notes
        user_study_guides[guide_id]['updated_at'] = datetime.now().isoformat()
        
        if save_study_guides(study_guides_data):
            return jsonify({'success': True, 'message': 'Notes updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update notes'})
            
    except Exception as e:
        print(f"Error updating notes: {e}")
        return jsonify({'success': False, 'message': 'Server error occurred'})
