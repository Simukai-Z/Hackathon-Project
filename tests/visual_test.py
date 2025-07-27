#!/usr/bin/env python3
"""
Visual test to check server logs for the new features
"""
import requests
import time

def test_visual_features():
    base_url = "http://localhost:5000"
    
    print("🎯 Testing New Features - Check Server Logs and Browser")
    print("=" * 60)
    
    # Test the edit assignment page
    print("1. Accessing modernized edit assignment page...")
    print(f"   URL: {base_url}/teacher/edit_assignment/d2e9cbc7/d4d29f81-1236-427f-9b27-1b1821a78e1b")
    print("   👀 Check Simple Browser for:")
    print("      • Modern sectioned layout with icons")
    print("      • Professional form styling")
    print("      • Organized sections for details, description, and grading")
    print("      • Responsive design elements")
    
    print("\n2. Student main page with unsubmit functionality...")
    print(f"   URL: {base_url}/student_main?class=d2e9cbc7")
    print("   👀 Check Simple Browser for:")
    print("      • Unsubmit button on submitted assignments (if not graded)")
    print("      • Modern submission status display")
    print("      • Warning text about unsubmit functionality")
    
    print("\n3. Server should be running on:")
    print(f"   {base_url}")
    
    print("\n📋 To manually test:")
    print("   1. Login as teacher (Roblox@gmail.com)")
    print("   2. Go to classroom and click 'Edit' on an assignment")
    print("   3. See the modernized form layout")
    print("   4. Login as student (epicrbot20099@gmail.com)")
    print("   5. Submit an assignment")
    print("   6. See the unsubmit button appear")
    print("   7. Click unsubmit and confirm the dialog")

if __name__ == "__main__":
    test_visual_features()
