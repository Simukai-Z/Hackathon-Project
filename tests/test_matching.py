#!/usr/bin/env python3
"""
Direct test of AI assistant functionality
"""
import sys
import os
sys.path.append('/workspaces/Hackathon-Project')

from app import get_student_submissions

def test_submission_matching():
    print("🧪 Testing AI Assistant Submission Matching")
    print("=" * 60)
    
    # Test the student who has the TestAssignment
    email = 'epicrbot20099@gmail.com'
    
    # Get all submissions for this student
    submissions = get_student_submissions(email)
    
    print(f"📊 Found {len(submissions)} submissions for student {email}:")
    print("-" * 40)
    
    for i, submission in enumerate(submissions, 1):
        print(f"{i}. Assignment: '{submission.get('assignment_title', 'Unknown')}'")
        print(f"   Class: {submission.get('class_name', 'Unknown')}")
        print(f"   Submission: '{submission.get('submission_text', 'No text')[:100]}...'")
        print(f"   Grade: {submission.get('grade', 'Not graded')}")
        print(f"   Feedback: '{submission.get('feedback', 'No feedback')[:50]}...'")
        print(f"   Graded by: {submission.get('graded_by', 'Not graded')}")
        print()
    
    # Test the matching logic for "TestAssignment"
    print("🔍 Testing assignment matching for 'TestAssignment':")
    print("-" * 40)
    
    test_prompts = [
        "how did I do on TestAssignment?",
        "what about my TestAssignment grade?",
        "TestAssignment feedback please",
        "how did I do on the AI reflection assignment?",
        "what's my grade on the assignment about AI & Society?"
    ]
    
    for prompt in test_prompts:
        print(f"Testing prompt: '{prompt}'")
        
        matching_submissions = []
        user_prompt_lower = prompt.lower()
        
        for submission in submissions:
            assignment_title = submission.get('assignment_title', '').lower()
            
            # Multiple matching strategies
            matches = False
            
            # Strategy 1: Exact assignment title match
            if assignment_title and assignment_title in user_prompt_lower:
                matches = True
                print(f"  ✅ Exact match: '{assignment_title}'")
            
            # Strategy 2: Individual words from assignment title
            elif assignment_title:
                title_words = [word for word in assignment_title.split() if len(word) > 2]
                if title_words and any(word in user_prompt_lower for word in title_words):
                    matches = True
                    matching_words = [word for word in title_words if word in user_prompt_lower]
                    print(f"  ✅ Word match: '{assignment_title}' (matched: {matching_words})")
            
            # Strategy 3: Check if user mentions assignment-related keywords
            assignment_keywords = ['assignment', 'homework', 'essay', 'reflection', 'paper', 'submission']
            if any(keyword in user_prompt_lower for keyword in assignment_keywords):
                if assignment_title:
                    title_parts = assignment_title.replace(':', ' ').replace('-', ' ').split()
                    if any(part in user_prompt_lower for part in title_parts if len(part) > 2):
                        matches = True
                        matching_parts = [part for part in title_parts if part in user_prompt_lower and len(part) > 2]
                        print(f"  ✅ Keyword + partial match: '{assignment_title}' (matched: {matching_parts})")
            
            if matches:
                matching_submissions.append(submission)
        
        print(f"  📊 Result: {len(matching_submissions)} matching submission(s)")
        for match in matching_submissions:
            print(f"    - {match.get('assignment_title', 'Unknown')} (Grade: {match.get('grade', 'N/A')})")
        print()

if __name__ == "__main__":
    test_submission_matching()
