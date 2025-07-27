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

def create_fallback_flashcards(content, subject, num_cards, difficulty):
    """Create meaningful fallback flash cards when AI fails"""
    cards = []
    
    # Split content into sentences or meaningful chunks
    sentences = content.replace('\n', ' ').split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    # Create cards from content chunks
    for i in range(min(num_cards, len(sentences) + 3)):  # Ensure we have enough cards
        if i < len(sentences):
            sentence = sentences[i].strip()
            if sentence:
                # Create a question from the sentence
                if ',' in sentence:
                    parts = sentence.split(',', 1)
                    question = f"What can you tell me about {parts[0].strip()}?"
                    answer = sentence
                else:
                    question = f"Explain the concept: {sentence[:50]}..."
                    answer = sentence
            else:
                question = f"What is an important concept in {subject}?"
                answer = f"This relates to the study of {subject} and its key principles."
        else:
            # Generic questions when we run out of content
            generic_questions = [
                (f"What are the main principles of {subject}?", f"The main principles involve understanding the core concepts and their applications."),
                (f"How is {subject} applied in practice?", f"Practical applications of {subject} involve real-world implementations and problem-solving."),
                (f"What are the key terms in {subject}?", f"Key terminology helps in understanding the fundamental vocabulary and concepts.")
            ]
            question, answer = generic_questions[i % len(generic_questions)]
        
        cards.append({
            'id': str(uuid.uuid4()),
            'front': question,
            'back': answer,
            'difficulty': difficulty,
            'created_at': datetime.now().isoformat()
        })
    
    return cards

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

def calculate_progress_from_game_results(user_email):
    """Calculate user progress from game results data"""
    try:
        user_results_file = os.path.join('data', 'user_game_results', f"{user_email.replace('@', '_').replace('.', '_')}.json")
        
        if not os.path.exists(user_results_file):
            return {}
        
        with open(user_results_file, 'r') as f:
            user_results = json.load(f)
        
        # Group results by flashcard set
        set_progress = {}
        
        for result in user_results:
            set_name = result.get('flashcard_set_name')
            if not set_name:
                continue
                
            if set_name not in set_progress:
                set_progress[set_name] = {
                    'total_questions': 0,
                    'correct_answers': 0,
                    'games_played': 0,
                    'best_accuracy': 0,
                    'recent_accuracy': 0
                }
            
            # Update statistics
            progress = set_progress[set_name]
            progress['total_questions'] += result.get('total_questions', 0)
            progress['correct_answers'] += result.get('correct_answers', 0)
            progress['games_played'] += 1
            
            # Track accuracy
            current_accuracy = float(result.get('accuracy', 0))
            if current_accuracy > progress['best_accuracy']:
                progress['best_accuracy'] = current_accuracy
            progress['recent_accuracy'] = current_accuracy  # Most recent game
        
        # Calculate final percentages
        final_progress = {}
        for set_name, stats in set_progress.items():
            if stats['total_questions'] > 0:
                overall_accuracy = (stats['correct_answers'] / stats['total_questions']) * 100
                # Use a weighted average of overall accuracy and best single-game performance
                mastery_score = (overall_accuracy * 0.7) + (stats['best_accuracy'] * 0.3)
                
                final_progress[set_name] = {
                    'correct_percentage': round(mastery_score, 1),
                    'games_played': stats['games_played'],
                    'total_questions': stats['total_questions'],
                    'correct_answers': stats['correct_answers'],
                    'best_accuracy': stats['best_accuracy']
                }
        
        return final_progress
        
    except Exception as e:
        print(f"Error calculating progress from game results: {e}")
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
    
    # Calculate progress from game results instead of using static progress file
    user_progress = calculate_progress_from_game_results(user_email)
    
    # Get user's flash card sets
    user_flashcards = flashcards_data.get(user_email, {})
    user_study_guides = study_guides_data.get(user_email, {})
    
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
    
    # Calculate progress from game results instead of using static progress file
    user_progress = calculate_progress_from_game_results(user_email)
    
    user_flashcards = flashcards_data.get(user_email, {})
    
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
        
        # Generate flash cards using AI service
        cards = []
        ai_generated = False
        
        # Use AI service if available, otherwise fall back to sample content
        if AIService:
            try:
                ai_service = AIService()
                
                # Get actual assignment content if source is assignment
                if content_source == 'assignment' and request.form.get('assignment_id'):
                    assignment_id = request.form.get('assignment_id')
                    # Load assignment content from classrooms data
                    classrooms_data = load_classrooms()
                    assignment_content = None
                    
                    for classroom in classrooms_data.get('classrooms', []):
                        for assignment in classroom.get('assignments', []):
                            if assignment.get('id') == assignment_id or assignment.get('title') == assignment_id:
                                assignment_content = assignment.get('description', '') or assignment.get('content', '')
                                break
                        if assignment_content:
                            break
                    
                    if assignment_content:
                        content_text = assignment_content
                
                # Generate flash cards using AI
                result = ai_service.generate_flashcards(
                    content=content_text,
                    subject=set_name,
                    num_cards=card_count,
                    difficulty=difficulty_level
                )
                
                if result['success']:
                    # Parse AI response (expecting JSON format)
                    import json as json_module
                    import re
                    
                    ai_text = result['flashcards']
                    ai_cards = []
                    
                    try:
                        # First try to parse as direct JSON
                        ai_cards = json_module.loads(ai_text)
                    except json.JSONDecodeError:
                        # Try to extract JSON from markdown code blocks
                        json_match = re.search(r'```json\s*(.*?)\s*```', ai_text, re.DOTALL)
                        if json_match:
                            try:
                                ai_cards = json_module.loads(json_match.group(1))
                            except json.JSONDecodeError:
                                pass
                        
                        # If still no valid JSON, try to find JSON array patterns
                        if not ai_cards:
                            json_array_match = re.search(r'\[\s*\{.*?\}\s*\]', ai_text, re.DOTALL)
                            if json_array_match:
                                try:
                                    ai_cards = json_module.loads(json_array_match.group(0))
                                except json.JSONDecodeError:
                                    pass
                    
                    if ai_cards and isinstance(ai_cards, list):
                        # Successfully parsed AI cards
                        for i, ai_card in enumerate(ai_cards):
                            if isinstance(ai_card, dict):
                                cards.append({
                                    'id': str(uuid.uuid4()),
                                    'front': ai_card.get('question', f"Question {i+1}"),
                                    'back': ai_card.get('answer', f"Answer {i+1}"),
                                    'difficulty': ai_card.get('difficulty', difficulty_level),
                                    'category': ai_card.get('category', set_name),
                                    'created_at': datetime.now().isoformat()
                                })
                        ai_generated = True
                        print(f"Successfully parsed {len(cards)} AI flash cards")
                    else:
                        print(f"Could not parse AI flash cards, creating fallback cards. Raw response: {ai_text[:200]}")
                        # Create meaningful fallback cards based on content
                        fallback_cards = create_fallback_flashcards(content_text, set_name, card_count, difficulty_level)
                        cards.extend(fallback_cards)
                        ai_generated = True
                else:
                    print(f"AI service error: {result.get('error')}")
                    
            except Exception as e:
                print(f"AI generation failed: {e}, falling back to template cards")
        
        # Fallback to template cards if AI is not available or failed
        if not ai_generated:
            # Create meaningful questions based on content analysis
            if content_source == 'text' and len(content_text) > 50:
                # Try to extract key phrases for better questions
                words = content_text.split()
                key_terms = [word.strip('.,!?') for word in words if len(word) > 6][:10]
                
                base_questions = [
                    f"What is the significance of {', '.join(key_terms[:3])} in {set_name}?",
                    f"How do the concepts in {set_name} apply to real-world scenarios?",
                    f"What are the main principles underlying {set_name}?",
                    f"Explain the relationship between different elements in {set_name}.",
                    f"What practical applications can be derived from {set_name}?"
                ]
                
                base_answers = [
                    f"These key terms represent fundamental concepts that form the core understanding of {set_name}. They interconnect to create a comprehensive framework for learning.",
                    f"The concepts can be applied through practical exercises, problem-solving scenarios, and real-world implementations as outlined in the study material.",
                    f"The main principles include systematic understanding, practical application, and critical analysis of the subject matter.",
                    f"The elements work together synergistically, with each component building upon others to create a complete understanding of the topic.",
                    f"Practical applications include hands-on projects, analytical exercises, and real-world problem solving that demonstrate mastery of the concepts."
                ]
            else:
                # Default meaningful questions
                base_questions = [
                    f"What are the core concepts in {set_name}?",
                    f"How would you explain {set_name} to a peer?",
                    f"What makes {set_name} important to understand?",
                    f"What are common applications of {set_name}?",
                    f"How does {set_name} relate to broader topics in this field?"
                ]
                
                base_answers = [
                    f"The core concepts include fundamental principles, key terminology, and practical applications that form the foundation of understanding {set_name}.",
                    f"I would explain {set_name} by breaking down the main ideas, providing relevant examples, and connecting it to concepts they already understand.",
                    f"{set_name} is important because it provides essential knowledge and skills that are applicable in academic and professional contexts.",
                    f"Common applications include problem-solving scenarios, analytical tasks, and practical implementations relevant to the field.",
                    f"{set_name} connects to broader topics by sharing fundamental principles and serving as a building block for more advanced concepts."
                ]
            
            # Generate cards using the template
            for i in range(card_count):
                q_index = i % len(base_questions)
                cards.append({
                    'id': str(uuid.uuid4()),
                    'front': base_questions[q_index],
                    'back': base_answers[q_index],
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
    flashcards_data = load_flashcards()
    
    user_study_guides = study_guides_data.get(user_email, {})
    user_flashcards = flashcards_data.get(user_email, {})
    
    # Add flashcard information to each study guide
    for guide_title, guide_data in user_study_guides.items():
        # Look for flashcard sets that were generated from this study guide
        related_flashcard_sets = []
        for fc_set_name, fc_data in user_flashcards.items():
            # Check if this flashcard set was generated from this study guide
            if (fc_set_name.startswith(guide_title) or 
                guide_title.lower() in fc_set_name.lower() or
                fc_set_name.endswith('- Flash Cards') and fc_set_name.replace('- Flash Cards', '').strip() == guide_title):
                related_flashcard_sets.append(fc_set_name)
        
        guide_data['related_flashcards'] = related_flashcard_sets
    
    return render_template('study_guides.html',
                         study_guides=user_study_guides)

@study_tools_bp.route('/create-study-guide')
def create_study_guide():
    """Create study guide page"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    return render_template('create_study_guide.html')

@study_tools_bp.route('/api/create-study-guide', methods=['POST'])
def api_create_study_guide():
    """API endpoint to create study guides"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        user_email = session['email']
        guide_title = request.form.get('guide_title', '').strip()
        content_source = request.form.get('content_source')
        guide_style = request.form.get('guide_style', 'outline')
        complexity_level = request.form.get('complexity_level', 'intermediate')
        estimated_length = int(request.form.get('estimated_length', 30))
        
        if not guide_title:
            return jsonify({'success': False, 'error': 'Guide title is required'}), 400
        
        # Get content based on source
        content_text = ""
        if content_source == 'text':
            content_text = request.form.get('content_text', '')
        elif content_source == 'file':
            # Handle file upload
            uploaded_file = request.files.get('content_file')
            if uploaded_file:
                content_text = f"Content from file: {uploaded_file.filename}"
        elif content_source == 'assignment':
            assignment_id = request.form.get('assignment_id')
            content_text = f"Content from assignment ID: {assignment_id}"
        
        if not content_text:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        # Get selected sections
        import json as json_module
        sections_json = request.form.get('sections_json', '[]')
        selected_sections = json_module.loads(sections_json) if sections_json else ['overview', 'key_concepts', 'summary']
        
        # Generate study guide content using AI service or fallback
        study_guide_sections = []
        ai_generated = False
        
        # Use AI service if available
        if AIService:
            try:
                ai_service = AIService()
                
                # Get actual assignment content if source is assignment
                if content_source == 'assignment' and request.form.get('assignment_id'):
                    assignment_id = request.form.get('assignment_id')
                    # Load assignment content from classrooms data
                    classrooms_data = load_classrooms()
                    assignment_content = None
                    
                    for classroom in classrooms_data.get('classrooms', []):
                        for assignment in classroom.get('assignments', []):
                            if assignment.get('id') == assignment_id or assignment.get('title') == assignment_id:
                                assignment_content = assignment.get('description', '') or assignment.get('content', '')
                                break
                        if assignment_content:
                            break
                    
                    if assignment_content:
                        content_text = assignment_content
                
                # Generate study guide using AI
                result = ai_service.generate_study_guide(
                    content=content_text,
                    subject=guide_title,
                    style=guide_style,
                    include_questions='questions' in selected_sections
                )
                
                if result['success']:
                    ai_guide_content = result['study_guide']
                    
                    # Use the AI-generated content directly as the main content
                    study_guide_sections.append({
                        'title': 'AI-Generated Study Guide',
                        'type': 'ai_content',
                        'content': ai_guide_content
                    })
                    
                    ai_generated = True
                else:
                    print(f"AI service error: {result.get('error')}")
                    
            except Exception as e:
                print(f"AI generation failed: {e}, falling back to template content")
        
        # Fallback to structured template content if AI is not available or failed
        if not ai_generated:
            # Create structured sections based on selected options
            if 'overview' in selected_sections:
                study_guide_sections.append({
                    'title': 'Overview',
                    'type': 'summary',
                    'content': f"This study guide provides a comprehensive overview of {guide_title}. The content covers essential concepts, practical applications, and key insights derived from the provided material. Understanding these concepts will help build a solid foundation for further learning and practical application."
                })
            
            if 'key_concepts' in selected_sections:
                study_guide_sections.append({
                    'title': 'Key Concepts',
                    'type': 'key_concepts',
                    'content': [
                        {
                            'term': f'Fundamental Concept of {guide_title}',
                            'definition': 'The core principle that underlies the understanding of this topic, providing the foundation for all related concepts.',
                            'example': 'Consider how this concept applies in practical scenarios and real-world applications.'
                        },
                        {
                            'term': f'Critical Understanding in {guide_title}',
                            'definition': 'Essential knowledge that bridges theoretical understanding with practical application.',
                            'example': 'This understanding enables problem-solving and analytical thinking in relevant contexts.'
                        },
                        {
                            'term': f'Advanced Application of {guide_title}',
                            'definition': 'Higher-level concepts that build upon fundamental understanding to enable complex analysis.',
                            'example': 'These applications demonstrate mastery and can be used in advanced scenarios.'
                        }
                    ]
                })
            
            if 'outline' in selected_sections:
                study_guide_sections.append({
                    'title': 'Study Outline',
                    'type': 'outline',
                    'content': [
                        {'level': 1, 'text': f'Introduction to {guide_title}'},
                        {'level': 2, 'text': 'Historical Context and Background'},
                        {'level': 2, 'text': 'Core Principles and Foundations'},
                        {'level': 1, 'text': 'Main Concepts and Theories'},
                        {'level': 2, 'text': 'Primary Theoretical Framework'},
                        {'level': 2, 'text': 'Supporting Concepts and Ideas'},
                        {'level': 1, 'text': 'Practical Applications'},
                        {'level': 2, 'text': 'Real-world Examples'},
                        {'level': 2, 'text': 'Problem-solving Approaches'},
                        {'level': 1, 'text': 'Conclusion and Next Steps'}
                    ]
                })
            
            if 'summary' in selected_sections:
                study_guide_sections.append({
                    'title': 'Summary',
                    'type': 'summary',
                    'content': f"In conclusion, {guide_title} encompasses a range of important concepts and practical applications. The key takeaways include understanding the fundamental principles, recognizing their real-world relevance, and developing the ability to apply these concepts in various contexts. Mastery of this material provides a strong foundation for continued learning and professional development in this field."
                })
            
            if 'questions' in selected_sections:
                study_guide_sections.append({
                    'title': 'Practice Questions',
                    'type': 'questions',
                    'content': [
                        {
                            'question': f'What are the core principles underlying {guide_title}?',
                            'answer': 'The core principles include fundamental concepts, practical applications, and theoretical frameworks that provide comprehensive understanding of the topic.'
                        },
                        {
                            'question': f'How can you apply the concepts from {guide_title} in practical scenarios?',
                            'answer': 'These concepts can be applied through analytical thinking, problem-solving approaches, and real-world implementations that demonstrate understanding.'
                        },
                        {
                            'question': f'What makes {guide_title} relevant to broader learning objectives?',
                            'answer': 'The relevance comes from its foundational nature, practical applicability, and connection to advanced topics in the field.'
                        },
                        {
                            'question': f'How would you explain {guide_title} to someone unfamiliar with the topic?',
                            'answer': 'I would start with basic concepts, provide clear examples, and gradually build up to more complex ideas while maintaining practical relevance.'
                        }
                    ]
                })
        
        # Create the final study guide content structure
        study_guide_content = {
            'title': guide_title,
            'style': guide_style,
            'complexity_level': complexity_level,
            'estimated_length': estimated_length,
            'sections': study_guide_sections,
            'assignment': request.form.get('assignment_id') if content_source == 'assignment' else None,
            'created_at': datetime.now().isoformat()
        }
        
        # Save study guide
        study_guides_data = load_study_guides()
        if user_email not in study_guides_data:
            study_guides_data[user_email] = {}
        
        study_guides_data[user_email][guide_title] = study_guide_content
        
        if save_study_guides(study_guides_data):
            return jsonify({'success': True, 'message': f'Study guide "{guide_title}" created successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save study guide'}), 500
            
    except Exception as e:
        print(f"Error creating study guide: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while creating the study guide'}), 500

@study_tools_bp.route('/api/generate-flashcards-from-guide', methods=['POST'])
def generate_flashcards_from_guide():
    """API endpoint to generate flashcards from a study guide"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        from urllib.parse import unquote
        user_email = session['email']
        data = request.get_json()
        
        guide_title = data.get('guide_title')
        # URL decode the guide title if needed
        if guide_title:
            guide_title = unquote(guide_title).strip()
        
        num_cards = int(data.get('num_cards', 15))
        
        if not guide_title:
            return jsonify({'success': False, 'error': 'Study guide title is required'}), 400
        
        # Load the study guide
        study_guides_data = load_study_guides()
        user_study_guides = study_guides_data.get(user_email, {})
        
        if guide_title not in user_study_guides:
            return jsonify({'success': False, 'error': 'Study guide not found'}), 404
        
        study_guide = user_study_guides[guide_title]
        
        # Extract content from the study guide
        study_guide_content = ""
        if isinstance(study_guide.get('sections'), list):
            # New format with sections
            for section in study_guide['sections']:
                study_guide_content += f"\n\n## {section['title']}\n"
                if section['type'] == 'key_concepts':
                    for concept in section['content']:
                        study_guide_content += f"\n**{concept['term']}**: {concept['definition']}\n"
                        if concept.get('example'):
                            study_guide_content += f"Example: {concept['example']}\n"
                elif section['type'] == 'questions':
                    for question in section['content']:
                        study_guide_content += f"\nQ: {question['question']}\nA: {question['answer']}\n"
                else:
                    study_guide_content += f"\n{section['content']}\n"
        else:
            # Fallback to raw content
            study_guide_content = str(study_guide.get('content', ''))
        
        if not study_guide_content.strip():
            return jsonify({'success': False, 'error': 'Study guide appears to be empty'}), 400
        
        # Generate flashcards using AI
        if AIService:
            ai_service = AIService()
            result = ai_service.generate_flashcards_from_study_guide(
                study_guide_content=study_guide_content,
                subject=guide_title,
                num_cards=num_cards
            )
            
            if result['success']:
                # Parse AI response (expecting JSON format)
                import json as json_module
                import re
                
                ai_text = result['flashcards']
                ai_cards = []
                
                try:
                    # First try to parse as direct JSON
                    ai_cards = json_module.loads(ai_text)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks
                    json_match = re.search(r'```json\s*(.*?)\s*```', ai_text, re.DOTALL)
                    if json_match:
                        try:
                            ai_cards = json_module.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            pass
                    
                    # If still no valid JSON, try to find JSON array patterns
                    if not ai_cards:
                        json_array_match = re.search(r'\[\s*\{.*?\}\s*\]', ai_text, re.DOTALL)
                        if json_array_match:
                            try:
                                ai_cards = json_module.loads(json_array_match.group(0))
                            except json.JSONDecodeError:
                                pass
                
                if ai_cards and isinstance(ai_cards, list):
                    # Convert AI cards to our format
                    cards = []
                    for i, ai_card in enumerate(ai_cards):
                        if isinstance(ai_card, dict) and 'question' in ai_card and 'answer' in ai_card:
                            cards.append({
                                'id': str(uuid.uuid4()),
                                'front': ai_card['question'],
                                'back': ai_card['answer'],
                                'difficulty': ai_card.get('difficulty', 'Medium'),
                                'type': ai_card.get('type', 'definition'),
                                'study_guide_section': ai_card.get('study_guide_section', ''),
                                'created_at': datetime.now().isoformat()
                            })
                    
                    if cards:
                        # Save flashcards
                        flashcard_set_name = f"{guide_title} - Flashcards"
                        flashcards_data = load_flashcards()
                        if user_email not in flashcards_data:
                            flashcards_data[user_email] = {}
                        
                        flashcards_data[user_email][flashcard_set_name] = {
                            'cards': cards,
                            'created_at': datetime.now().isoformat(),
                            'difficulty': 'Mixed',
                            'total_cards': len(cards),
                            'source': 'study_guide',
                            'source_guide': guide_title
                        }
                        
                        if save_flashcards(flashcards_data):
                            return jsonify({
                                'success': True,
                                'message': f'Generated {len(cards)} flashcards from study guide',
                                'flashcard_set_name': flashcard_set_name,
                                'cards_count': len(cards)
                            })
                        else:
                            return jsonify({'success': False, 'error': 'Failed to save flashcards'}), 500
                    else:
                        return jsonify({'success': False, 'error': 'No valid flashcards could be generated'}), 400
                else:
                    return jsonify({'success': False, 'error': 'AI did not return valid flashcard data'}), 400
            else:
                return jsonify({'success': False, 'error': f'AI generation failed: {result.get("error")}'}), 500
        else:
            return jsonify({'success': False, 'error': 'AI service not available'}), 503
            
    except Exception as e:
        print(f"Error generating flashcards from study guide: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while generating flashcards'}), 500# Flash Card viewing routes
@study_tools_bp.route('/flashcards/view/<set_name>')
def view_flashcard_set(set_name):
    """View a specific flash card set"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    flashcards_data = load_flashcards()
    user_flashcards = flashcards_data.get(user_email, {})
    
    if set_name not in user_flashcards:
        return "Flash card set not found", 404
    
    flashcard_set = user_flashcards[set_name]
    return render_template('view_flashcards.html', 
                         set_name=set_name, 
                         flashcard_set=flashcard_set)

@study_tools_bp.route('/flashcards/study/<set_name>')
def study_flashcards(set_name):
    """Study mode for flash cards"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    flashcards_data = load_flashcards()
    user_flashcards = flashcards_data.get(user_email, {})
    
    if set_name not in user_flashcards:
        return "Flash card set not found", 404
    
    flashcard_set = user_flashcards[set_name]
    return render_template('study_flashcards.html', 
                         set_name=set_name, 
                         flashcard_set=flashcard_set)

@study_tools_bp.route('/flashcards/delete/<set_name>', methods=['DELETE'])
def delete_flashcard_set(set_name):
    """Delete a flash card set"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        user_email = session['email']
        flashcards_data = load_flashcards()
        
        if user_email in flashcards_data and set_name in flashcards_data[user_email]:
            del flashcards_data[user_email][set_name]
            if save_flashcards(flashcards_data):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to save changes'}), 500
        else:
            return jsonify({'success': False, 'error': 'Flash card set not found'}), 404
            
    except Exception as e:
        print(f"Error deleting flash card set: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500

@study_tools_bp.route('/study-guides/view/<guide_title>')
def view_study_guide(guide_title):
    """View a specific study guide"""
    if 'user_type' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    # URL decode the guide title
    from urllib.parse import unquote
    guide_title = unquote(guide_title).strip()
    
    user_email = session['email']
    study_guides_data = load_study_guides()
    user_study_guides = study_guides_data.get(user_email, {})
    
    # Debug logging
    print(f"Looking for guide_title: '{guide_title}'")
    print(f"Available guides for {user_email}: {list(user_study_guides.keys())}")
    
    if guide_title not in user_study_guides:
        print(f"Guide '{guide_title}' not found. Available guides: {list(user_study_guides.keys())}")
        return "Study guide not found", 404
    
    study_guide = user_study_guides[guide_title]
    
    # Handle old data format by converting to new format
    if 'content' in study_guide and not 'sections' in study_guide:
        print(f"Converting old study guide format for: {guide_title}")
        # Convert old format to new format
        old_content = study_guide['content']
        new_sections = []
        
        if 'overview' in old_content:
            new_sections.append({
                'title': 'Overview',
                'type': 'summary',
                'content': old_content['overview']
            })
        
        if 'key_concepts' in old_content:
            new_sections.append({
                'title': 'Key Concepts',
                'type': 'key_concepts',
                'content': [
                    {
                        'term': f'Core Concept of {guide_title}',
                        'definition': old_content['key_concepts'],
                        'example': 'See examples section for practical applications.'
                    }
                ]
            })
        
        if 'examples' in old_content:
            new_sections.append({
                'title': 'Examples and Applications',
                'type': 'summary',
                'content': old_content['examples']
            })
        
        if 'practice' in old_content:
            new_sections.append({
                'title': 'Practice Questions',
                'type': 'questions',
                'content': [
                    {
                        'question': f'What are the main concepts in {guide_title}?',
                        'answer': old_content['practice']
                    }
                ]
            })
        
        if 'summary' in old_content:
            new_sections.append({
                'title': 'Summary',
                'type': 'summary',
                'content': old_content['summary']
            })
        
        # Update the study guide object with new format
        study_guide['sections'] = new_sections
        
        # Save the updated format
        study_guides_data[user_email][guide_title] = study_guide
        save_study_guides(study_guides_data)
    
    return render_template('view_study_guide.html', 
                         guide_title=guide_title, 
                         study_guide=study_guide)

@study_tools_bp.route('/study-guides/delete/<guide_title>', methods=['DELETE'])
def delete_study_guide(guide_title):
    """Delete a study guide"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    
    try:
        from urllib.parse import unquote
        guide_title = unquote(guide_title).strip()
        
        user_email = session['email']
        study_guides_data = load_study_guides()
        
        if user_email in study_guides_data and guide_title in study_guides_data[user_email]:
            del study_guides_data[user_email][guide_title]
            if save_study_guides(study_guides_data):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Failed to save changes'}), 500
        else:
            return jsonify({'success': False, 'error': 'Study guide not found'}), 404
            
    except Exception as e:
        print(f"Error deleting study guide: {e}")
        return jsonify({'success': False, 'error': 'An error occurred'}), 500

# API route for getting assignments
@study_tools_bp.route('/api/assignments')
def get_assignments():
    """Get user's assignments"""
    if 'user_type' not in session or 'email' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        user_email = session['email']
        user_type = session['user_type']
        
        # Load classrooms and assignments
        classrooms_data = load_classrooms()
        assignments = []
        
        if user_type == 'student':
            # Get student's classrooms and their assignments
            users = load_users()
            student = next((s for s in users['students'] if s['email'] == user_email), None)
            
            if student and 'classrooms' in student:
                for classroom_code in student['classrooms']:
                    classroom = next((c for c in classrooms_data['classrooms'] if c['code'] == classroom_code), None)
                    if classroom and 'assignments' in classroom:
                        for assignment in classroom['assignments']:
                            assignments.append({
                                'id': assignment.get('id', assignment.get('title', '')),
                                'title': assignment.get('title', 'Untitled Assignment'),
                                'classroom': classroom.get('name', 'Unknown Classroom'),
                                'due_date': assignment.get('due_date', ''),
                                'description': assignment.get('description', '')
                            })
        
        elif user_type == 'teacher':
            # Get teacher's classrooms and their assignments
            for classroom in classrooms_data['classrooms']:
                if classroom.get('teacher_email') == user_email and 'assignments' in classroom:
                    for assignment in classroom['assignments']:
                        assignments.append({
                            'id': assignment.get('id', assignment.get('title', '')),
                            'title': assignment.get('title', 'Untitled Assignment'),
                            'classroom': classroom.get('name', 'Unknown Classroom'),
                            'due_date': assignment.get('due_date', ''),
                            'description': assignment.get('description', '')
                        })
        
        return jsonify({'assignments': assignments})
        
    except Exception as e:
        print(f"Error loading assignments: {e}")
        return jsonify({'error': 'Failed to load assignments'}), 500

# Game Mode API Endpoints

@study_tools_bp.route('/api/check-answer', methods=['POST'])
def check_answer():
    """Check if user's answer matches the correct answer using AI"""
    try:
        if 'email' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        user_answer = data.get('user_answer', '').strip()
        correct_answer = data.get('correct_answer', '').strip()
        question = data.get('question', '').strip()
        
        if not user_answer or not correct_answer:
            return jsonify({'error': 'Missing answer data'}), 400
        
        # Use AI service to check the answer
        if AIService:
            try:
                ai_service = AIService()
                
                prompt = f"""
You are an expert educational assessment AI. Evaluate if the student's answer demonstrates understanding of the concept, even with different wording.

Question: {question}
Expected Answer: {correct_answer}
Student's Answer: {user_answer}

IMPORTANT EVALUATION CRITERIA:
- Focus on conceptual understanding, not exact word matching
- Be very lenient with spelling errors, typos, and capitalization
- Accept synonyms and equivalent terms
- Accept answers in different sentence structures
- Consider abbreviations and shorthand acceptable
- Reward partial understanding with encouraging feedback
- If the student shows ANY understanding of the core concept, mark as correct

EXAMPLES:
- For "coroutines": Accept "threads", "new script", "multitasking", "async"
- For "metatables": Accept "classes", "custom behavior", "special tables"
- For "pairs vs ipairs": Accept "all vs numbers", "everything vs integers"

You MUST respond with ONLY valid JSON in this exact format:

{{
  "is_correct": true,
  "feedback": "Great job! Your answer shows you understand that [concept]. [encouragement]",
  "confidence": 0.95
}}

OR for incorrect answers:

{{
  "is_correct": false,
  "feedback": "Good attempt! You're on the right track with [partial understanding]. The key concept is [explanation]. Try thinking about [hint].",
  "confidence": 0.90
}}

CRITICAL: Return ONLY the JSON object. No markdown, no extra text, no explanations outside the JSON.
"""
                
                response = ai_service.generate_response(prompt, max_tokens=300)
                
                print(f"🤖 AI Response for answer check: {response}")
                
                # Enhanced JSON parsing
                try:
                    import re
                    
                    # Clean the response first
                    response_cleaned = response.strip()
                    
                    # Remove any markdown formatting
                    if response_cleaned.startswith('```'):
                        response_cleaned = re.sub(r'^```(?:json)?\s*', '', response_cleaned)
                        response_cleaned = re.sub(r'\s*```$', '', response_cleaned)
                    
                    # First try to parse as direct JSON
                    try:
                        result = json.loads(response_cleaned)
                        if 'is_correct' in result:
                            # Ensure we have all required fields
                            result['is_correct'] = bool(result.get('is_correct', False))
                            result['feedback'] = str(result.get('feedback', 'Answer checked.'))
                            result['confidence'] = float(result.get('confidence', 0.8))
                            
                            print(f"✅ AI answer check result: {result}")
                            return jsonify(result)
                    except json.JSONDecodeError:
                        pass
                    
                    # Try to find JSON object within the response
                    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                    json_matches = re.findall(json_pattern, response_cleaned)
                    
                    for json_str in json_matches:
                        try:
                            result = json.loads(json_str)
                            if 'is_correct' in result:
                                # Ensure we have all required fields
                                result['is_correct'] = bool(result.get('is_correct', False))
                                result['feedback'] = str(result.get('feedback', 'Answer checked.'))
                                result['confidence'] = float(result.get('confidence', 0.8))
                                
                                print(f"✅ AI answer check result: {result}")
                                return jsonify(result)
                        except (json.JSONDecodeError, ValueError):
                            continue
                            
                    # If no valid JSON found, try to extract key information
                    response_lower = response.lower()
                    
                    # More sophisticated keyword analysis
                    correct_indicators = ['correct', 'right', 'accurate', 'good', 'excellent', 'perfect', 'yes', 'true', 'well done']
                    incorrect_indicators = ['incorrect', 'wrong', 'inaccurate', 'false', 'not quite', 'try again', 'no']
                    
                    correct_score = sum(1 for word in correct_indicators if word in response_lower)
                    incorrect_score = sum(1 for word in incorrect_indicators if word in response_lower)
                    
                    is_correct = correct_score > incorrect_score
                    
                    return jsonify({
                        'is_correct': is_correct,
                        'feedback': response.strip()[:200] if response.strip() else ("Good answer!" if is_correct else "Try again."),
                        'confidence': 0.85 if is_correct else 0.80
                    })
                    
                except Exception as parse_error:
                    print(f"JSON parsing error: {parse_error}")
                    # Final fallback to text analysis
                    response_lower = response.lower()
                    is_correct = any(word in response_lower for word in ['correct', 'right', 'accurate', 'yes', 'good'])
                
                return jsonify({
                    'is_correct': is_correct,
                    'feedback': response.strip()[:200],
                    'confidence': 0.8 if is_correct else 0.7
                })
                
            except Exception as ai_error:
                print(f"AI answer checking error: {ai_error}")
                # Fall through to simple comparison
        
        # Fallback to simple string comparison
        is_correct = user_answer.lower().strip() == correct_answer.lower().strip()
        
        # Check for close matches (allowing for minor typos)
        if not is_correct:
            # Simple Levenshtein-like distance check
            def simple_similarity(s1, s2):
                s1, s2 = s1.lower().strip(), s2.lower().strip()
                if len(s1) == 0 or len(s2) == 0:
                    return 0
                
                longer = s1 if len(s1) > len(s2) else s2
                shorter = s2 if len(s1) > len(s2) else s1
                
                # Simple substring check
                if shorter in longer:
                    return len(shorter) / len(longer)
                
                # Count matching characters
                matches = sum(1 for c in shorter if c in longer)
                return matches / len(longer)
            
            similarity = simple_similarity(user_answer, correct_answer)
            is_correct = similarity > 0.8  # 80% similarity threshold
        
        feedback = "Correct! Well done!" if is_correct else f"Not quite right. The correct answer is: {correct_answer}"
        
        return jsonify({
            'is_correct': is_correct,
            'feedback': feedback,
            'confidence': 0.9 if is_correct else 0.8
        })
        
    except Exception as e:
        print(f"Error checking answer: {e}")
        return jsonify({'error': 'Failed to check answer'}), 500

@study_tools_bp.route('/api/log-game-results', methods=['POST'])
def log_game_results():
    """Log game results to user's AI memory for personalized assistance"""
    try:
        if 'email' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        user_email = session['email']
        
        # Create game results record
        game_log = {
            'timestamp': datetime.now().isoformat(),
            'user_email': user_email,
            'flashcard_set_name': data.get('flashcard_set_name'),
            'total_score': data.get('total_score', 0),
            'total_questions': data.get('total_questions', 0),
            'correct_answers': data.get('correct_answers', 0),
            'accuracy': data.get('accuracy', 0),
            'is_win': data.get('is_win', False),
            'detailed_results': data.get('game_results', [])
        }
        
        # Save to a game results file
        game_results_file = os.path.join('data', 'game_results.json')
        os.makedirs('data', exist_ok=True)
        
        try:
            with open(game_results_file, 'r') as f:
                all_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_results = []
        
        all_results.append(game_log)
        
        # Keep only the last 100 game results to prevent file from growing too large
        if len(all_results) > 100:
            all_results = all_results[-100:]
        
        with open(game_results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Also save to user's individual record
        user_results_file = os.path.join('data', 'user_game_results', f"{user_email.replace('@', '_').replace('.', '_')}.json")
        os.makedirs(os.path.dirname(user_results_file), exist_ok=True)
        
        try:
            with open(user_results_file, 'r') as f:
                user_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            user_results = []
        
        user_results.append(game_log)
        
        # Keep only the last 50 results per user
        if len(user_results) > 50:
            user_results = user_results[-50:]
        
        with open(user_results_file, 'w') as f:
            json.dump(user_results, f, indent=2)
        
        return jsonify({'success': True, 'message': 'Game results logged successfully'})
        
    except Exception as e:
        print(f"Error logging game results: {e}")
        return jsonify({'error': 'Failed to log game results'}), 500

@study_tools_bp.route('/api/resources')
def get_resources():
    """Get all available resources for hyperlink processing"""
    try:
        if 'email' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user_email = session['email']
        resources = {
            'flashcards': [],
            'study_guides': [],
            'assignments': [],
            'rubrics': []
        }
        
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
                assignments_added = 0
                for assignment in classroom.get('assignments', []):
                    assignment_data = {
                        'id': assignment.get('id'),
                        'title': assignment.get('title'),
                        'class_code': class_code
                    }
                    # Only add if all required fields are present
                    if assignment_data['id'] and assignment_data['title'] and assignment_data['class_code']:
                        resources['assignments'].append(assignment_data)
                        assignments_added += 1
                    else:
                        print(f"⚠️ Skipping assignment with missing data: {assignment_data}")
                
                print(f"Added {assignments_added} assignments from class {class_code}")
                
                # Add rubrics
                rubrics_added = 0
                for rubric in classroom.get('rubrics', []):
                    rubric_data = {
                        'id': rubric.get('id'),
                        'title': rubric.get('title'),
                        'class_code': class_code
                    }
                    # Only add if all required fields are present
                    if rubric_data['id'] and rubric_data['title'] and rubric_data['class_code']:
                        resources['rubrics'].append(rubric_data)
                        rubrics_added += 1
                    else:
                        print(f"⚠️ Skipping rubric with missing data: {rubric_data}")
                
                print(f"Added {rubrics_added} rubrics from class {class_code}")
                    
        except Exception as e:
            print(f"Error loading classroom resources: {e}")
        
        print(f"DEBUG: Resources loaded for user {user_email}:")
        print(f"  Flashcards: {len(resources['flashcards'])}")
        print(f"  Study guides: {len(resources['study_guides'])}")
        print(f"  Assignments: {len(resources['assignments'])}")
        print(f"  Rubrics: {len(resources['rubrics'])}")
        
        # Debug assignment details
        if resources['assignments']:
            print("📝 Assignment details:")
            for i, assignment in enumerate(resources['assignments']):
                print(f"  {i+1}. '{assignment['title']}' (ID: {assignment['id']}, Class: {assignment['class_code']})")
        
        return jsonify(resources)
        
    except Exception as e:
        print(f"Error fetching resources: {e}")
        return jsonify({'error': 'Failed to fetch resources'}), 500
