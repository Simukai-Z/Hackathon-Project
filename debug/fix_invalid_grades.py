import json

# Load classrooms data
with open('/workspaces/Hackathon-Project/classrooms.json', 'r') as f:
    data = json.load(f)

print("Checking for invalid grades...")

fixed_count = 0
for classroom in data.get('classrooms', []):
    for assignment in classroom.get('assignments', []):
        for submission in assignment.get('submissions', []):
            if submission.get('grade') is not None:
                try:
                    grade = int(submission['grade'])
                    if grade < 0 or grade > 100:
                        print(f"Found invalid grade: {grade} for {submission.get('student_email')} in assignment {assignment.get('title')}")
                        # Set to a reasonable default based on previous feedback
                        if 'GRADE: 75' in submission.get('feedback', ''):
                            submission['grade'] = 75
                            print(f"  -> Fixed to 75 (found in feedback)")
                        else:
                            submission['grade'] = 75
                            print(f"  -> Fixed to default 75")
                        fixed_count += 1
                except (ValueError, TypeError):
                    print(f"Found non-numeric grade: {submission['grade']} for {submission.get('student_email')}")
                    submission['grade'] = 75
                    print(f"  -> Fixed to default 75")
                    fixed_count += 1

if fixed_count > 0:
    # Save the fixed data
    with open('/workspaces/Hackathon-Project/classrooms.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nFixed {fixed_count} invalid grades and saved to classrooms.json")
else:
    print("No invalid grades found!")
