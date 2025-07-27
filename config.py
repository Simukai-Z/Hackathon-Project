"""
Configuration file for StudyCoach application
Contains shared utility functions and configurations
"""

import json
import os

# File paths
USERS_FILE = 'users.json'
CLASSROOMS_FILE = 'classrooms.json'
UPLOAD_FOLDER = 'uploads'

def load_users():
    """Load users data from JSON file"""
    if not os.path.exists(USERS_FILE):
        return {"students": [], "teachers": []}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users data to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_classrooms():
    """Load classrooms data from JSON file"""
    if not os.path.exists(CLASSROOMS_FILE):
        return {"classrooms": []}
    with open(CLASSROOMS_FILE, 'r') as f:
        return json.load(f)

def save_classrooms(classrooms):
    """Save classrooms data to JSON file"""
    with open(CLASSROOMS_FILE, 'w') as f:
        json.dump(classrooms, f, indent=2)

# Study tools specific data files
FLASHCARDS_FILE = 'flashcards.json'
STUDY_GUIDES_FILE = 'study_guides.json'
STUDY_PROGRESS_FILE = 'study_progress.json'

def load_flashcards():
    """Load flashcards data from JSON file"""
    if not os.path.exists(FLASHCARDS_FILE):
        return {"sets": []}
    with open(FLASHCARDS_FILE, 'r') as f:
        return json.load(f)

def save_flashcards(flashcards):
    """Save flashcards data to JSON file"""
    with open(FLASHCARDS_FILE, 'w') as f:
        json.dump(flashcards, f, indent=2)

def load_study_guides():
    """Load study guides data from JSON file"""
    if not os.path.exists(STUDY_GUIDES_FILE):
        return {"guides": []}
    with open(STUDY_GUIDES_FILE, 'r') as f:
        return json.load(f)

def save_study_guides(study_guides):
    """Save study guides data to JSON file"""  
    with open(STUDY_GUIDES_FILE, 'w') as f:
        json.dump(study_guides, f, indent=2)

def load_study_progress():
    """Load study progress data from JSON file"""
    if not os.path.exists(STUDY_PROGRESS_FILE):
        return {"progress": {}}
    with open(STUDY_PROGRESS_FILE, 'r') as f:
        return json.load(f)

def save_study_progress(progress):
    """Save study progress data to JSON file"""
    with open(STUDY_PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_user_email():
    """Get current user email from session"""
    from flask import session
    return session.get('email', 'anonymous')

def get_user_type():
    """Get current user type from session"""
    from flask import session
    return session.get('user_type', 'guest')

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
