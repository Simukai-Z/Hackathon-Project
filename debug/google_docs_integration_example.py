"""
Google Docs Integration Example for StudyCoach Assignment System

This file provides example code for integrating Google Docs API to read document content
directly for AI grading. This requires setting up Google Cloud credentials and enabling
the Google Docs API.

SETUP REQUIREMENTS:
1. Create a Google Cloud Project
2. Enable Google Docs API and Google Drive API
3. Create service account credentials
4. Download credentials JSON file
5. Install google-api-python-client: pip install google-api-python-client

SECURITY NOTE: This implementation requires proper authentication and permission handling.
Students must share their documents with the service account email or make them publicly readable.
"""

import json
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

class GoogleDocsIntegration:
    def __init__(self, credentials_file_path=None):
        """
        Initialize Google Docs integration with service account credentials
        
        Args:
            credentials_file_path (str): Path to the service account JSON credentials file
        """
        self.credentials_file_path = credentials_file_path or os.getenv('GOOGLE_CREDENTIALS_FILE')
        self.scopes = [
            'https://www.googleapis.com/auth/documents.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        self.docs_service = None
        self.drive_service = None
        
        if self.credentials_file_path and os.path.exists(self.credentials_file_path):
            self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google API services"""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_file_path, 
                scopes=self.scopes
            )
            self.docs_service = build('docs', 'v1', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Failed to initialize Google services: {e}")
    
    def extract_document_id(self, url):
        """Extract Google Docs document ID from URL"""
        import re
        patterns = [
            r'/document/d/([a-zA-Z0-9-_]+)',
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def can_access_document(self, document_id):
        """Check if the service account can access the document"""
        if not self.drive_service:
            return False, "Google Drive service not initialized"
        
        try:
            # Try to get basic file info
            file_info = self.drive_service.files().get(
                fileId=document_id,
                fields='id,name,permissions'
            ).execute()
            return True, f"Access granted to: {file_info.get('name', 'Unknown')}"
        except Exception as e:
            return False, f"Access denied: {str(e)}"
    
    def get_document_content(self, document_id):
        """
        Retrieve the text content from a Google Docs document
        
        Args:
            document_id (str): The Google Docs document ID
            
        Returns:
            dict: Contains success status, content, and any error messages
        """
        if not self.docs_service:
            return {
                'success': False,
                'content': '',
                'error': 'Google Docs service not initialized. Check credentials.'
            }
        
        try:
            # Get the document
            document = self.docs_service.documents().get(documentId=document_id).execute()
            
            # Extract text content
            content = self._extract_text_from_document(document)
            
            return {
                'success': True,
                'content': content,
                'title': document.get('title', 'Untitled Document'),
                'document_id': document_id
            }
            
        except Exception as e:
            error_msg = str(e)
            if 'Permission denied' in error_msg or 'Forbidden' in error_msg:
                return {
                    'success': False,
                    'content': '',
                    'error': 'Permission denied. Document must be shared with the service account or made publicly readable.'
                }
            else:
                return {
                    'success': False,
                    'content': '',
                    'error': f'Failed to retrieve document: {error_msg}'
                }
    
    def _extract_text_from_document(self, document):
        """Extract text content from Google Docs document structure"""
        content = []
        
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                paragraph_text = []
                
                for text_element in paragraph.get('elements', []):
                    if 'textRun' in text_element:
                        text_content = text_element['textRun'].get('content', '')
                        paragraph_text.append(text_content)
                
                content.append(''.join(paragraph_text))
        
        return '\n'.join(content).strip()
    
    def get_document_from_url(self, url):
        """
        Get document content from a Google Docs URL
        
        Args:
            url (str): Google Docs URL
            
        Returns:
            dict: Document content and metadata
        """
        document_id = self.extract_document_id(url)
        if not document_id:
            return {
                'success': False,
                'content': '',
                'error': 'Invalid Google Docs URL'
            }
        
        return self.get_document_content(document_id)

# Example usage and integration with the main app
def integrate_with_studycoach():
    """
    Example of how to integrate Google Docs reading with the StudyCoach AI grading system
    """
    
    def enhanced_ai_grading_with_google_docs(submission, assignment, student_name):
        """
        Enhanced AI grading that can read Google Docs content
        """
        submission_content = submission.get('submission_text', '')
        google_docs_content = ''
        
        # Check if there's a Google Docs link
        if submission.get('submission_link'):
            google_docs = GoogleDocsIntegration()
            docs_result = google_docs.get_document_from_url(submission['submission_link'])
            
            if docs_result['success']:
                google_docs_content = docs_result['content']
                submission_content += f"\n\n[Google Docs Content]:\n{google_docs_content}"
            else:
                # Include error information for the teacher
                submission_content += f"\n\n[Google Docs Access Error]: {docs_result['error']}"
        
        # Enhanced grading prompt with Google Docs content
        grading_prompt = f"""
        Please grade this student assignment and provide constructive feedback.
        
        Student Name: {student_name}
        Assignment Title: {assignment.get('title', 'Assignment')}
        Assignment Description: {assignment.get('description', 'No description provided')}
        
        Student Submission:
        Text: {submission.get('submission_text', 'No text submission')}
        Link: {submission.get('submission_link', 'No link submission')}
        
        {"Google Docs Content Retrieved:" if google_docs_content else "Google Docs Content: Could not access (see error above)"}
        {google_docs_content if google_docs_content else ""}
        
        File: {'File attached: ' + submission.get('filename', '') if submission.get('filename') else 'No file attached'}
        
        Please provide:
        1. A numerical grade (0-100)
        2. Constructive feedback highlighting strengths and areas for improvement
        3. Specific suggestions for improvement
        4. Encouraging words to motivate continued learning
        
        Format your response as:
        GRADE: [number]
        FEEDBACK: [detailed feedback addressing the student by name]
        
        Be encouraging and constructive while maintaining academic standards.
        """
        
        return grading_prompt

# Configuration instructions for deployment
CONFIG_INSTRUCTIONS = """
To enable Google Docs integration in your StudyCoach deployment:

1. GOOGLE CLOUD SETUP:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing one
   - Enable Google Docs API and Google Drive API
   - Go to "Credentials" and create a Service Account
   - Download the JSON credentials file

2. ENVIRONMENT SETUP:
   - Place the credentials JSON file in a secure location
   - Set environment variable: GOOGLE_CREDENTIALS_FILE=/path/to/credentials.json
   - Install required package: pip install google-api-python-client

3. SHARING INSTRUCTIONS FOR STUDENTS:
   - Students must share their Google Docs with the service account email
   - OR set sharing to "Anyone with the link can view"
   - The service account email can be found in the credentials JSON file

4. SECURITY CONSIDERATIONS:
   - Store credentials securely
   - Use least-privilege access (readonly scopes only)
   - Consider implementing rate limiting for API calls
   - Log API access for audit purposes

5. INTEGRATION WITH STUDYCOACH:
   - Import this module in app.py
   - Replace the AI grading function with the enhanced version
   - Handle API errors gracefully
   - Provide clear feedback to teachers about document access issues
"""

if __name__ == "__main__":
    print("Google Docs Integration Example for StudyCoach")
    print("=" * 50)
    print(CONFIG_INSTRUCTIONS)
    
    # Example test (requires valid credentials)
    # google_docs = GoogleDocsIntegration()
    # result = google_docs.get_document_from_url("https://docs.google.com/document/d/YOUR_DOCUMENT_ID")
    # print(result)
