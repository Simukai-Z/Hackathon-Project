import json

# Load and display current classroom data to understand the structure
with open('/workspaces/Hackathon-Project/classrooms.json', 'r') as f:
    data = json.load(f)

print("Current Classrooms Data:")
print("=" * 50)

for classroom in data.get('classrooms', []):
    print(f"\nClassroom: {classroom.get('class_name')} (Code: {classroom.get('code')})")
    print(f"Teacher: {classroom.get('teacher_email')}")
    
    for assignment in classroom.get('assignments', []):
        print(f"\n  Assignment: {assignment.get('title')} (ID: {assignment.get('id')})")
        print(f"  Due Date: {assignment.get('due_date')}")
        
        for submission in assignment.get('submissions', []):
            print(f"\n    Student: {submission.get('student_email')}")
            print(f"    Grade: {submission.get('grade', 'Not graded')}")
            print(f"    Feedback: {submission.get('feedback', 'No feedback')}")
            print(f"    File: {submission.get('filename', 'No file')}")
            print(f"    Link: {submission.get('submission_link', 'No link')}")
            print(f"    Graded by: {submission.get('graded_by', 'Not graded')}")
            print(f"    Graded timestamp: {submission.get('graded_timestamp', 'Not graded')}")
