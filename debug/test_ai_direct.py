#!/usr/bin/env python3
"""
Test the AI service directly to see if it generates comprehensive study guides
"""
import sys
sys.path.append('/workspaces/Hackathon-Project')

from services.ai_service import AIService

def test_ai_study_guide():
    """Test AI study guide generation"""
    try:
        ai_service = AIService()
        
        # Test content
        test_content = """
        Python is a high-level, interpreted programming language. It was created by Guido van Rossum and first released in 1991. Python is known for its simple syntax and readability, making it an excellent choice for beginners. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python has extensive libraries and frameworks that make it suitable for web development, data science, artificial intelligence, automation, and more.
        """
        
        print("Testing AI study guide generation...")
        result = ai_service.generate_study_guide(
            content=test_content,
            subject="Python Programming Basics",
            style="comprehensive",
            include_questions=True
        )
        
        if result['success']:
            study_guide = result['study_guide']
            print(f"Success! Generated study guide length: {len(study_guide)} characters")
            print("\nFirst 500 characters:")
            print(study_guide[:500])
            print("\nLast 500 characters:")
            print(study_guide[-500:])
            return True
        else:
            print(f"Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    test_ai_study_guide()
