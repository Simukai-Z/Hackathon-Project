import os
import sys
sys.path.append('/workspaces/Hackathon-Project')

# Test file content reading
file_path = '/workspaces/Hackathon-Project/uploads/epicrbot20099gmail.com_77b3a162-0548-461b-9194-06e7b4f193d7_Testassinmen.txt'

if os.path.exists(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"File exists and content is: '{content}'")
        print(f"Content length: {len(content)} characters")
    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print("File does not exist!")

# Also check what files are in the uploads directory
uploads_dir = '/workspaces/Hackathon-Project/uploads'
if os.path.exists(uploads_dir):
    files = os.listdir(uploads_dir)
    print(f"\nFiles in uploads directory: {files}")
else:
    print("Uploads directory does not exist!")
