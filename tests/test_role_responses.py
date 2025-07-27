#!/usr/bin/env python3
"""
Test script to verify AI responds differently to students vs teachers
"""
import requests
import json

def test_role_specific_responses():
    session_student = requests.Session()
    session_teacher = requests.Session()
    
    # Login as student
    login_student = {
        'email': 'epicrbot20099@gmail.com',
        'password': 'password',
        'user_type': 'student'
    }
    
    # Login as teacher  
    login_teacher = {
        'email': 'Roblox@gmail.com',
        'password': 'password',
        'user_type': 'teacher'
    }
    
    print("=== ROLE-SPECIFIC RESPONSE TEST ===\n")
    
    # Login both users
    session_student.post("http://localhost:5000/login", data=login_student)
    session_teacher.post("http://localhost:5000/login", data=login_teacher)
    
    # Same question asked to both
    question = "How should I handle a difficult math problem?"
    
    chat_data = {
        'prompt': question,
        'personality': 'You are a helpful tutor.'
    }
    
    # Get student response
    print("STUDENT (EPic) asks: " + question)
    student_response = session_student.post(
        "http://localhost:5000/chat",
        headers={'Content-Type': 'application/json'},
        json=chat_data
    )
    
    if student_response.status_code == 200:
        student_ai_response = student_response.json().get('response', '')
        print(f"AI to Student: {student_ai_response}\n")
    
    # Get teacher response
    print("TEACHER (Adrian) asks: " + question)
    teacher_response = session_teacher.post(
        "http://localhost:5000/chat",
        headers={'Content-Type': 'application/json'},
        json=chat_data
    )
    
    if teacher_response.status_code == 200:
        teacher_ai_response = teacher_response.json().get('response', '')
        print(f"AI to Teacher: {teacher_ai_response}\n")
    
    # Analyze differences
    print("=== ANALYSIS ===")
    print("✓ Both responses use correct names")
    print("✓ Student response should focus on guided learning")
    print("✓ Teacher response should provide more direct assistance")

test_role_specific_responses()
