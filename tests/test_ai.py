#!/usr/bin/env python3
"""
Test script to verify AI assistant functionality
"""
import requests
import json

# Test the AI assistant directly
def test_ai_assistant():
    url = "http://127.0.0.1:5000/chat"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, simulate logging in as a student by setting session data
    # This is a simplified approach - in the real app, login would set these values
    
    # Test data
    test_data = {
        "prompt": "how did I do on TestAssignment?",
        "personality": "You are a helpful tutor that follows rubrics and teaches through guidance.",
        "class_code": "",
        "fileContent": ""
    }
    
    # Set session cookies to simulate being logged in as the student
    session.cookies.set('user_type', 'student')
    session.cookies.set('email', 'epicrbot20099@gmail.com')
    
    print("🧪 Testing AI Assistant - Student asking about TestAssignment")
    print("=" * 60)
    print(f"Student: {test_data['prompt']}")
    print("=" * 60)
    
    try:
        response = session.post(url, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', 'No response received')
            print("🤖 AI Response:")
            print(ai_response)
            print("\n" + "=" * 60)
            
            # Check if the response mentions the submission content
            if "Test submission for unsubmit functionality" in ai_response:
                print("✅ SUCCESS: AI found the student's submission content!")
            elif "grade" in ai_response.lower() or "100" in ai_response:
                print("✅ PARTIAL SUCCESS: AI found grade information")
            else:
                print("❌ ISSUE: AI didn't access submission data - still asking for upload?")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ai_assistant()
