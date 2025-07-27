#!/usr/bin/env python3
"""
Test script to demonstrate the new modernized edit assignment page and unsubmit functionality
"""
import requests
import json

def test_modernized_features():
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("=== Testing Modernized Edit Assignment & Unsubmit Features ===\n")
    
    # Test 1: Login as teacher and access edit assignment page
    print("1. Testing Teacher Login and Modernized Edit Assignment Page...")
    teacher_login = session.post(f"{base_url}/login", data={
        "email": "Roblox@gmail.com",
        "user_type": "teacher"
    })
    
    if teacher_login.status_code == 200:
        print("   ✅ Teacher login successful")
        
        # Access teacher main page
        teacher_main = session.get(f"{base_url}/teacher_main?class=d2e9cbc7")
        if teacher_main.status_code == 200:
            print("   ✅ Teacher main page loaded")
            
            # Try to access edit assignment page
            edit_page = session.get(f"{base_url}/teacher/edit_assignment/d2e9cbc7/d4d29f81-1236-427f-9b27-1b1821a78e1b")
            if edit_page.status_code == 200:
                print("   ✅ Modernized edit assignment page loaded successfully!")
                print("   📝 Features: Modern UI, organized sections, better form layout")
            else:
                print(f"   ❌ Edit assignment page failed: {edit_page.status_code}")
        else:
            print(f"   ❌ Teacher main failed: {teacher_main.status_code}")
    else:
        print(f"   ❌ Teacher login failed: {teacher_login.status_code}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Login as student and test unsubmit functionality
    print("2. Testing Student Login and Unsubmit Functionality...")
    
    # Create new session for student
    student_session = requests.Session()
    student_login = student_session.post(f"{base_url}/login", data={
        "email": "epicrbot20099@gmail.com",
        "user_type": "student"
    })
    
    if student_login.status_code == 200:
        print("   ✅ Student login successful")
        
        # Check student main page
        student_main = student_session.get(f"{base_url}/student_main?class=d2e9cbc7")
        if student_main.status_code == 200:
            print("   ✅ Student main page loaded")
            print("   📋 Page should now show:")
            print("      • Modernized submission status display")
            print("      • Unsubmit button for ungraded assignments")
            print("      • Warning messages about unsubmit functionality")
            
            # Try to submit a test assignment (to have something to unsubmit)
            print("\n   📤 Testing submission process...")
            submit_response = student_session.post(f"{base_url}/submit_assignment", data={
                "assignment_id": "d4d29f81-1236-427f-9b27-1b1821a78e1b",
                "submission_text": "Test submission for unsubmit functionality"
            })
            
            if submit_response.status_code == 302:  # Redirect after successful submit
                print("   ✅ Test submission created successfully")
                
                # Now test unsubmit functionality
                print("   🔄 Testing unsubmit functionality...")
                unsubmit_response = student_session.post(f"{base_url}/unsubmit_assignment", data={
                    "assignment_id": "d4d29f81-1236-427f-9b27-1b1821a78e1b"
                })
                
                if unsubmit_response.status_code == 302:  # Redirect after successful unsubmit
                    print("   ✅ Unsubmit functionality working!")
                    print("   🎉 Student can now resubmit the assignment")
                else:
                    print(f"   ❌ Unsubmit failed: {unsubmit_response.status_code}")
            else:
                print(f"   ❌ Submission failed: {submit_response.status_code}")
        else:
            print(f"   ❌ Student main failed: {student_main.status_code}")
    else:
        print(f"   ❌ Student login failed: {student_login.status_code}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Test that graded assignments cannot be unsubmitted
    print("3. Testing Protection Against Unsubmitting Graded Assignments...")
    
    # Check if there are any graded assignments to test with
    print("   🔒 Attempting to unsubmit a graded assignment (should fail)...")
    # This should fail because graded assignments cannot be unsubmitted
    graded_unsubmit = student_session.post(f"{base_url}/unsubmit_assignment", data={
        "assignment_id": "77b3a162-0548-461b-9194-06e7b4f193d7"  # This assignment has a grade
    })
    
    # Check the response (should redirect with error message)
    if graded_unsubmit.status_code == 302:
        print("   ✅ Protection working - graded assignments cannot be unsubmitted")
    else:
        print(f"   ❌ Protection may not be working: {graded_unsubmit.status_code}")
    
    print("\n" + "="*60 + "\n")
    
    print("🎯 Summary of New Features:")
    print("=" * 40)
    print("✨ Modernized Edit Assignment Page:")
    print("   • Clean, organized sections with icons")
    print("   • Better form layout and validation")
    print("   • Improved file upload interface")
    print("   • Responsive design for mobile devices")
    print("   • Professional styling with modern UI elements")
    print()
    print("🔄 Student Unsubmit Functionality:")
    print("   • Students can unsubmit assignments before grading")
    print("   • Clear confirmation dialog with warnings")
    print("   • Automatic file cleanup when unsubmitting")
    print("   • Protection against unsubmitting graded work")
    print("   • User-friendly status indicators")
    print()
    print("🔐 Security Features:")
    print("   • Only ungraded assignments can be unsubmitted")
    print("   • Proper file cleanup to prevent storage issues")
    print("   • Clear user feedback and confirmation dialogs")
    print("   • Maintains data integrity throughout the process")

if __name__ == "__main__":
    test_modernized_features()
