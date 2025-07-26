#!/usr/bin/env python3
"""
Test script to verify AI knows user name and role
"""
import requests
import json

# Test AI chat endpoint for both student and teacher
def test_ai_chat(user_email, user_password, user_type, expected_name):
    session = requests.Session()
    
    # Login
    login_data = {
        'email': user_email,
        'password': 'password',
        'user_type': user_type
    }
    
    print(f"\n=== Testing {user_type.upper()}: {expected_name} ===")
    print(f"Logging in as {user_type}...")
    login_response = session.post("http://localhost:5000/login", data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        # Test AI chat
        chat_data = {
            'prompt': 'Hello! Can you introduce yourself and tell me what you know about me?',
            'personality': 'You are a helpful tutor.'
        }
        
        print("Sending chat message...")
        chat_response = session.post(
            "http://localhost:5000/chat", 
            headers={'Content-Type': 'application/json'},
            json=chat_data
        )
        
        print(f"Chat response status: {chat_response.status_code}")
        if chat_response.status_code == 200:
            response_data = chat_response.json()
            ai_response = response_data.get('response', '')
            print(f"\nAI Response:\n{ai_response}\n")
            
            # Check if AI knows the name and role
            name_mentioned = expected_name.lower() in ai_response.lower()
            # Check for various ways the role might be mentioned
            if user_type == 'student':
                role_mentioned = any(word in ai_response.lower() for word in ['student', 'your grade', 'your assignment', 'your submission', 'studying'])
            else:
                role_mentioned = any(word in ai_response.lower() for word in ['teacher', 'instructor', 'educator', 'teaching'])
            
            print(f"✓ Name mentioned: {name_mentioned}")
            print(f"✓ Role mentioned: {role_mentioned}")
            
            if name_mentioned and role_mentioned:
                print("🎉 SUCCESS: AI correctly identified user name and role!")
            else:
                print("❌ ISSUE: AI did not properly identify user information")
        else:
            print(f"Chat failed: {chat_response.text}")
    else:
        print("Login failed!")

# Test with student
test_ai_chat('epicrbot20099@gmail.com', 'password', 'student', 'EPic')

# Test with teacher
test_ai_chat('Roblox@gmail.com', 'password', 'teacher', 'Adrian')
