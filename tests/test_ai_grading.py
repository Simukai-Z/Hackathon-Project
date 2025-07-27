#!/usr/bin/env python3
"""
Test script to trigger AI grading directly
"""
import requests
import json

# Test AI grading endpoint
url = "http://localhost:5000/ai_grade_assignment"
data = {
    'classroom_id': 'd2e9cbc7',
    'assignment_id': '77b3a162-0548-461b-9194-06e7b4f193d7',
    'student_email': 'epicrbot20099@gmail.com'
}

print("Triggering AI grading...")
print(f"Data: {data}")

# First need to login as teacher
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
    # Now trigger AI grading
    print("Sending AI grading request...")
    response = session.post(url, data=data)
    print(f"AI grading response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    if response.text:
        print(f"Response content: {response.text[:500]}...")
else:
    print("Login failed!")
