#!/usr/bin/env python3
"""
Debug script to identify any string grades in the system
"""
import json

def load_classrooms():
    try:
        with open('classrooms.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'classrooms': []}

def check_grade_types():
    classrooms = load_classrooms()
    
    print("=== Checking Grade Types ===")
    issues_found = False
    
    for classroom_idx, classroom in enumerate(classrooms.get('classrooms', [])):
        print(f"\nClassroom: {classroom.get('class_name', 'Unknown')} ({classroom.get('code', 'Unknown')})")
        
        for assignment_idx, assignment in enumerate(classroom.get('assignments', [])):
            print(f"  Assignment: {assignment.get('title', 'Unknown')}")
            
            for submission_idx, submission in enumerate(assignment.get('submissions', [])):
                grade = submission.get('grade')
                grade_type = type(grade).__name__
                
                if grade is not None:
                    print(f"    Student: {submission.get('student_email', 'Unknown')}")
                    print(f"      Grade: {grade} (type: {grade_type})")
                    
                    if isinstance(grade, str):
                        print(f"      ⚠️  STRING GRADE FOUND! Value: '{grade}'")
                        issues_found = True
                        
                        # Try to see if it can be converted to int
                        try:
                            int_grade = int(grade)
                            print(f"      ✅ Can be converted to int: {int_grade}")
                        except (ValueError, TypeError):
                            print(f"      ❌ Cannot be converted to int")
    
    if not issues_found:
        print("\n✅ All grades are integers - no type issues found!")
    else:
        print("\n❌ String grades found - these need to be fixed!")
    
    return not issues_found

if __name__ == "__main__":
    check_grade_types()
