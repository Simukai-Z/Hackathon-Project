#!/usr/bin/env python3
"""
Test study guide creation process to verify AI content is used
"""
import sys
import json
sys.path.append('/workspaces/Hackathon-Project')

# Mock the Flask session and request for testing
class MockRequest:
    def __init__(self):
        self.form_data = {
            'guide_title': 'Test AI Study Guide',
            'content_source': 'text',
            'content_text': 'Python is a programming language known for its simplicity and readability.',
            'guide_style': 'comprehensive',
            'complexity_level': 'intermediate',
            'estimated_length': '30',
            'sections_json': '["overview", "key_concepts", "summary"]'
        }
    
    def get(self, key, default=None):
        return self.form_data.get(key, default)

class MockSession:
    def __init__(self):
        self.data = {
            'user_type': 'student',
            'email': 'test@example.com'
        }
    
    def get(self, key):
        return self.data.get(key)

def test_study_guide_creation():
    """Test that study guide creation uses AI content properly"""
    from services.ai_service import AIService
    
    # Test AI service
    ai_service = AIService()
    result = ai_service.generate_study_guide(
        content="Python is a programming language known for its simplicity and readability.",
        subject="Test AI Study Guide",
        style="comprehensive",
        include_questions=True
    )
    
    if result['success']:
        ai_content = result['study_guide']
        print(f"AI generated content length: {len(ai_content)}")
        print(f"Content preview: {ai_content[:200]}...")
        
        # Simulate the route logic
        study_guide_sections = []
        
        # This is the new logic that should use AI content
        study_guide_sections.append({
            'title': 'AI-Generated Study Guide',
            'type': 'ai_content',
            'content': ai_content
        })
        
        print(f"\nCreated study guide with {len(study_guide_sections)} sections:")
        for section in study_guide_sections:
            print(f"- {section['title']} (type: {section['type']})")
            print(f"  Content length: {len(section['content'])}")
        
        return True
    else:
        print(f"AI generation failed: {result.get('error')}")
        return False

if __name__ == "__main__":
    test_study_guide_creation()
