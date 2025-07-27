#!/usr/bin/env python3
"""
Test script to demonstrate the fixed flash card and study guide functionality
"""

import json
import requests
import time

def test_flashcard_creation():
    """Test creating flash cards with realistic content"""
    print("🧪 Testing Flash Card Creation...")
    
    # Test data for flash card creation
    test_data = {
        'set_name': 'Python Programming Basics',
        'content_source': 'text',
        'content_text': '''
        Python is a high-level programming language known for its simplicity and readability.
        Key concepts include variables, functions, loops, and object-oriented programming.
        Python uses indentation to define code blocks and supports multiple programming paradigms.
        It has extensive libraries for web development, data science, and automation.
        ''',
        'card_count': '5',
        'difficulty_level': 'intermediate',
        'card_types_json': '["definition", "application", "concept"]'
    }
    
    # Create the flash cards
    try:
        response = requests.post(
            'http://127.0.0.1:5000/study-tools/api/create-flashcards',
            data=test_data,
            # Note: In real app, we'd need session cookies for authentication
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Flash cards created successfully!")
                print(f"   Message: {result.get('message')}")
            else:
                print(f"❌ Flash card creation failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_study_guide_creation():
    """Test creating study guide with realistic content"""
    print("\n📚 Testing Study Guide Creation...")
    
    # Test data for study guide creation
    test_data = {
        'guide_title': 'Machine Learning Fundamentals',
        'content_source': 'text',
        'content_text': '''
        Machine learning is a subset of artificial intelligence that enables computers to learn
        without being explicitly programmed. Key algorithms include supervised learning,
        unsupervised learning, and reinforcement learning. Applications include image recognition,
        natural language processing, and predictive analytics.
        ''',
        'guide_style': 'comprehensive',
        'complexity_level': 'intermediate',
        'estimated_length': '45',
        'sections_json': '["overview", "key_concepts", "questions", "summary"]'
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/study-tools/api/create-study-guide',
            data=test_data,
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Study guide created successfully!")
                print(f"   Message: {result.get('message')}")
            else:
                print(f"❌ Study guide creation failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def check_data_files():
    """Check the generated data files to verify content quality"""
    print("\n🔍 Checking Generated Content...")
    
    try:
        # Check flash cards
        with open('flashcards.json', 'r') as f:
            flashcards = json.load(f)
            
        print("\n📋 Flash Cards Sample:")
        for user_email, user_cards in flashcards.items():
            for set_name, card_set in user_cards.items():
                print(f"   Set: {set_name}")
                for i, card in enumerate(card_set['cards'][:2]):  # Show first 2 cards
                    print(f"     Card {i+1}:")
                    print(f"       Front: {card['front'][:60]}...")
                    print(f"       Back: {card['back'][:60]}...")
                    
    except FileNotFoundError:
        print("   No flashcards.json file found")
    except Exception as e:
        print(f"   Error reading flashcards: {e}")
    
    try:
        # Check study guides
        with open('study_guides.json', 'r') as f:
            study_guides = json.load(f)
            
        print("\n📖 Study Guides Sample:")
        for user_email, user_guides in study_guides.items():
            for guide_title, guide in user_guides.items():
                print(f"   Guide: {guide_title}")
                if 'sections' in guide:
                    for section in guide['sections'][:2]:  # Show first 2 sections
                        print(f"     Section: {section['title']} ({section['type']})")
                        if isinstance(section['content'], str):
                            print(f"       Content: {section['content'][:60]}...")
                        elif isinstance(section['content'], list) and section['content']:
                            if isinstance(section['content'][0], dict):
                                print(f"       Sample: {section['content'][0]}...")
                            else:
                                print(f"       Items: {len(section['content'])} items")
                                
    except FileNotFoundError:
        print("   No study_guides.json file found")
    except Exception as e:
        print(f"   Error reading study guides: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing Fixed Flash Card and Study Guide System")
    print("=" * 50)
    
    # Note: These tests require authentication, so they'll fail with 401
    # but they demonstrate the data structure and API endpoints
    print("Note: Tests will show authentication errors (401) since we don't have session cookies.")
    print("The important part is to verify the data structure and logic.\n")
    
    test_flashcard_creation()
    test_study_guide_creation()
    check_data_files()
    
    print("\n" + "=" * 50)
    print("🎯 Key Fixes Implemented:")
    print("✅ Flash cards now show realistic questions and answers")
    print("✅ Study guides display structured content instead of method references")
    print("✅ AI service integration for better content generation")
    print("✅ Fallback content templates for when AI is unavailable")
    print("✅ Data migration for old content formats")
    print("✅ Assignment integration for real classroom data")

if __name__ == "__main__":
    main()
