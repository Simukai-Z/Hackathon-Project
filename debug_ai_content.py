import os
import json

# Debug the AI grading content preparation
uploads_dir = '/workspaces/Hackathon-Project/uploads'

# Simulate the AI grading process
filename = 'epicrbot20099gmail.com_77b3a162-0548-461b-9194-06e7b4f193d7_Testassinmen.txt'
file_path = os.path.join(uploads_dir, filename)

print(f"File path: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

if os.path.exists(file_path):
    try:
        # Try to read as text file
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        print(f"File content: '{file_content}'")
        print(f"Content length: {len(file_content)} characters")
        
        # Simulate the hash creation
        import hashlib
        content_for_hash = f"No text submission{'No link submission'}{filename}{file_content}EYAHHH IT WORKED!!No description provided"
        content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
        print(f"Content hash: {content_hash[:8]}")
        
        # Show what would be sent to AI
        prompt_content = f"""
        STUDENT SUBMISSION:
        Text Submission: No text submission
        Link Submission: No link submission  
        File Name: {filename}
        File Content: {file_content if file_content else 'No file content available'}
        """
        print("AI Prompt content:")
        print(prompt_content)
        
    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print("File does not exist!")
