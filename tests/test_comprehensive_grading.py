#!/usr/bin/env python3
"""
Test the improved AI grading system with substantial content
"""
import requests
import json
import os

def create_test_file_with_good_content():
    """Create a test file with substantial content for AI grading"""
    content = """Artificial Intelligence in Education: Benefits and Challenges

Introduction:
Artificial Intelligence (AI) is revolutionizing many sectors, and education is no exception. This essay explores how AI is transforming educational practices, the benefits it offers, and the challenges that need to be addressed.

Benefits of AI in Education:

1. Personalized Learning:
AI can analyze student performance data to create personalized learning paths. This means each student receives content and exercises tailored to their learning pace and style, improving engagement and outcomes.

2. Automated Administrative Tasks:
AI helps reduce teachers' administrative burden by automating tasks like grading multiple-choice tests, scheduling, and tracking attendance. This gives educators more time to focus on teaching and student interaction.

3. Intelligent Tutoring Systems:
AI-powered tutoring systems can provide 24/7 support to students, offering explanations, hints, and feedback outside regular classroom hours.

Challenges and Concerns:

1. Data Privacy:
Educational AI systems collect vast amounts of student data, raising concerns about privacy protection and data security.

2. Digital Divide:
Not all students have equal access to technology, which could worsen educational inequalities.

3. Over-reliance on Technology:
There's a risk that excessive dependence on AI might reduce human interaction and critical thinking skills.

Conclusion:
While AI offers tremendous potential to enhance education through personalization and efficiency, careful implementation is needed to address privacy concerns and ensure equitable access. The goal should be to use AI as a tool that supports, rather than replaces, quality human instruction.
"""
    
    # Write to uploads directory with predictable filename
    filename = "test_comprehensive_ai_essay.txt"
    filepath = f"/workspaces/Hackathon-Project/uploads/epicrbot20099gmail.com_77b3a162-0548-461b-9194-06e7b4f193d7_{filename}"
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return f"epicrbot20099gmail.com_77b3a162-0548-461b-9194-06e7b4f193d7_{filename}"

def test_improved_ai_grading():
    """Test that AI grading no longer penalizes submission method choice"""
    
    # Create test file with good content
    test_filename = create_test_file_with_good_content()
    print(f"Created test file: {test_filename}")
    
    # Update the submission in classrooms.json to use this file
    # This simulates a student submitting a comprehensive essay
    
    session = requests.Session()
    
    # Login as teacher
    login_data = {
        'email': 'Roblox@gmail.com',
        'password': 'password',
        'user_type': 'teacher'
    }
    
    print("Logging in as teacher...")
    login_response = session.post("http://localhost:5000/login", data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Trigger AI grading
        ai_grade_data = {
            'classroom_id': 'd2e9cbc7',
            'assignment_id': '77b3a162-0548-461b-9194-06e7b4f193d7',
            'student_email': 'epicrbot20099@gmail.com'
        }
        
        print("\nTriggering AI grading with substantial content...")
        response = session.post("http://localhost:5000/ai_grade_assignment", data=ai_grade_data)
        print(f"AI grading response status: {response.status_code}")
        
        print("\n=== Test completed! Check terminal output for AI response ===")
        print("Look for:")
        print("✅ No complaints about missing text/link submissions")
        print("✅ Focus only on the quality of content provided")
        print("✅ Fair grading based on actual submission content")
    
test_improved_ai_grading()
