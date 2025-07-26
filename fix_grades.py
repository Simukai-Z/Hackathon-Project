#!/usr/bin/env python3
"""
Fix script to convert all string grades to integers
"""
import json

def load_classrooms():
    try:
        with open('classrooms.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'classrooms': []}

def save_classrooms(data):
    with open('classrooms.json', 'w') as f:
        json.dump(data, f, indent=2)

def fix_grade_types():
    classrooms = load_classrooms()
    
    print("=== Fixing Grade Types ===")
    fixes_made = 0
    
    for classroom_idx, classroom in enumerate(classrooms.get('classrooms', [])):
        print(f"\nClassroom: {classroom.get('class_name', 'Unknown')} ({classroom.get('code', 'Unknown')})")
        
        for assignment_idx, assignment in enumerate(classroom.get('assignments', [])):
            print(f"  Assignment: {assignment.get('title', 'Unknown')}")
            
            for submission_idx, submission in enumerate(assignment.get('submissions', [])):
                grade = submission.get('grade')
                
                if grade is not None and isinstance(grade, str):
                    print(f"    Student: {submission.get('student_email', 'Unknown')}")
                    print(f"      Found string grade: '{grade}'")
                    
                    try:
                        int_grade = int(grade)
                        submission['grade'] = int_grade
                        print(f"      ✅ Fixed: '{grade}' → {int_grade}")
                        fixes_made += 1
                    except (ValueError, TypeError) as e:
                        print(f"      ❌ Could not convert '{grade}' to int: {e}")
    
    if fixes_made > 0:
        save_classrooms(classrooms)
        print(f"\n✅ Made {fixes_made} fixes and saved to classrooms.json")
    else:
        print("\n✅ No fixes needed - all grades are already integers!")
    
    return fixes_made

if __name__ == "__main__":
    fix_grade_types()
