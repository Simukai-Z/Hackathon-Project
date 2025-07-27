#!/usr/bin/env python3
"""
Test script for enhanced study guide system with automatic flashcard generation
"""

import requests
import json
import time

def test_enhanced_study_guide_creation():
    """Test creating an enhanced study guide with the new AI system"""
    print("\n🎓 Testing Enhanced Study Guide Creation...")
    
    # Test data for creating a comprehensive study guide
    test_data = {
        'guide_title': 'Roblox Scripting Basics',
        'content_source': 'text',
        'content_text': '''
        Roblox scripting uses Lua programming language to create interactive experiences in games. 
        The main components include Scripts and LocalScripts. Scripts run on the server and handle 
        game logic that affects all players, while LocalScripts run on individual clients and 
        handle user interface and player-specific effects.
        
        Key concepts in Roblox scripting:
        
        1. Game Structure: Roblox games are organized into a hierarchy with Workspace, Players, 
           ReplicatedStorage, and other services. Understanding this structure is crucial for 
           effective scripting.
        
        2. Events and Functions: Roblox uses an event-driven system where scripts respond to 
           user actions, game events, and custom triggers. Functions like part.Touched or 
           player.CharacterAdded are fundamental.
        
        3. Remote Events: For client-server communication, RemoteEvents and RemoteFunctions 
           allow scripts to communicate across the network boundary while maintaining security.
        
        4. Variables and Data Types: Lua supports various data types including strings, numbers, 
           booleans, tables, and Roblox-specific types like Vector3, CFrame, and Instance.
        
        5. Control Structures: Loops (for, while, repeat) and conditionals (if-then-else) 
           control program flow and game logic.
        
        Practical examples:
        - Creating a simple part that changes color when touched
        - Making a teleportation script
        - Building a basic GUI interface
        - Implementing a scoring system
        
        Best practices include commenting code, using meaningful variable names, handling errors 
        gracefully, and testing thoroughly in various scenarios.
        ''',
        'guide_style': 'comprehensive',
        'complexity_level': 'intermediate',
        'estimated_length': '30',
        'sections_json': '["overview", "key_concepts", "questions", "summary"]'
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/study-tools/api/create-study-guide',
            data=test_data,
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Enhanced study guide created successfully!")
                print(f"📘 Guide: {test_data['guide_title']}")
                return True
            else:
                print(f"❌ Failed to create study guide: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_flashcard_generation_from_guide():
    """Test generating flashcards from the study guide"""
    print("\n🃏 Testing Flashcard Generation from Study Guide...")
    
    # Wait a moment for the study guide to be saved
    time.sleep(2)
    
    test_data = {
        'guide_title': 'Roblox Scripting Basics',
        'num_cards': 12
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/study-tools/api/generate-flashcards-from-guide',
            headers={'Content-Type': 'application/json'},
            json=test_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Flashcards generated successfully!")
                print(f"🃏 Set: {result['flashcard_set_name']}")
                print(f"📊 Cards: {result['cards_count']}")
                return True
            else:
                print(f"❌ Failed to generate flashcards: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_french_revolution_guide():
    """Test with French Revolution content"""
    print("\n🇫🇷 Testing French Revolution Study Guide...")
    
    test_data = {
        'guide_title': 'The French Revolution Summary',
        'content_source': 'text',
        'content_text': '''
        The French Revolution (1789-1799) was a period of radical political and social transformation 
        in France that had lasting effects on French history and the broader world.
        
        Causes of the Revolution:
        1. Financial Crisis: France was deeply in debt from wars, including the American Revolution
        2. Social Inequality: The Three Estates system created unfair tax burdens
        3. Enlightenment Ideas: New political philosophies challenged absolute monarchy
        4. Economic Problems: Food shortages and inflation affected the common people
        
        Key Events:
        - 1789: Estates-General convenes, Tennis Court Oath, Storming of the Bastille
        - 1791: Declaration of the Rights of Man and Citizen
        - 1792: France declared a republic, King Louis XVI executed
        - 1793-1794: Reign of Terror under Robespierre
        - 1799: Napoleon Bonaparte rises to power
        
        Important Figures:
        - Louis XVI: The last king of France before the revolution
        - Marie Antoinette: The unpopular queen, executed during the revolution
        - Maximilien Robespierre: Leader during the Reign of Terror
        - Jacques Danton: Revolutionary leader and orator
        - Napoleon Bonaparte: Military leader who eventually became Emperor
        
        Consequences:
        - End of absolute monarchy in France
        - Rise of nationalism and democratic ideals
        - Spread of revolutionary ideas across Europe
        - Economic and social reforms
        - Establishment of civil rights and freedoms
        
        The revolution transformed France from a feudal society into a modern nation-state 
        and influenced democratic movements worldwide.
        ''',
        'guide_style': 'comprehensive',
        'complexity_level': 'intermediate',
        'estimated_length': '25',
        'sections_json': '["overview", "key_concepts", "questions", "summary"]'
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/study-tools/api/create-study-guide',
            data=test_data,
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ French Revolution study guide created!")
                
                # Now generate flashcards
                time.sleep(2)
                flashcard_data = {
                    'guide_title': 'The French Revolution Summary',
                    'num_cards': 15
                }
                
                flashcard_response = requests.post(
                    'http://127.0.0.1:5000/study-tools/api/generate-flashcards-from-guide',
                    headers={'Content-Type': 'application/json'},
                    json=flashcard_data
                )
                
                if flashcard_response.status_code == 200:
                    flashcard_result = flashcard_response.json()
                    if flashcard_result['success']:
                        print("✅ French Revolution flashcards generated!")
                        print(f"🃏 Cards: {flashcard_result['cards_count']}")
                        return True
                
        print(f"❌ Failed: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_python_functions_guide():
    """Test with Python Functions content"""
    print("\n🐍 Testing Python Functions Study Guide...")
    
    test_data = {
        'guide_title': 'Intro to Python Functions',
        'content_source': 'text',
        'content_text': '''
        Python functions are reusable blocks of code that perform specific tasks. They are 
        fundamental building blocks of Python programming that help organize code and avoid repetition.
        
        Function Basics:
        - Definition: Functions are defined using the 'def' keyword
        - Parameters: Input values that functions can accept
        - Return values: Output that functions can provide back to the caller
        - Scope: Variables inside functions have local scope
        
        Function Syntax:
        def function_name(parameters):
            """Docstring describing the function"""
            # Function body
            return value  # Optional
        
        Types of Functions:
        1. Built-in Functions: print(), len(), max(), min(), etc.
        2. User-defined Functions: Functions you create yourself
        3. Lambda Functions: Anonymous functions for simple operations
        4. Recursive Functions: Functions that call themselves
        
        Parameters and Arguments:
        - Positional Arguments: Arguments passed in order
        - Keyword Arguments: Arguments passed by parameter name
        - Default Parameters: Parameters with default values
        - *args: Variable number of positional arguments
        - **kwargs: Variable number of keyword arguments
        
        Best Practices:
        - Use descriptive function names
        - Write docstrings to document functions
        - Keep functions focused on single tasks
        - Avoid global variables when possible
        - Handle errors appropriately
        - Test functions thoroughly
        
        Examples:
        def greet(name, message="Hello"):
            return f"{message}, {name}!"
        
        def calculate_area(length, width):
            """Calculate area of rectangle"""
            return length * width
        
        lambda x: x ** 2  # Square function
        
        Functions are essential for writing clean, maintainable, and efficient Python code.
        ''',
        'guide_style': 'detailed',
        'complexity_level': 'beginner',
        'estimated_length': '20',
        'sections_json': '["overview", "key_concepts", "questions", "summary"]'
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/study-tools/api/create-study-guide',
            data=test_data,
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Python Functions study guide created!")
                
                # Generate flashcards
                time.sleep(2)
                flashcard_data = {
                    'guide_title': 'Intro to Python Functions',
                    'num_cards': 10
                }
                
                flashcard_response = requests.post(
                    'http://127.0.0.1:5000/study-tools/api/generate-flashcards-from-guide',
                    headers={'Content-Type': 'application/json'},
                    json=flashcard_data
                )
                
                if flashcard_response.status_code == 200:
                    flashcard_result = flashcard_response.json()
                    if flashcard_result['success']:
                        print("✅ Python Functions flashcards generated!")
                        print(f"🃏 Cards: {flashcard_result['cards_count']}")
                        return True
                
        print(f"❌ Failed: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Study Guide System")
    print("=" * 50)
    
    # Test all three example titles from the requirements
    tests = [
        test_enhanced_study_guide_creation,
        test_flashcard_generation_from_guide,
        test_french_revolution_guide,
        test_python_functions_guide
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print("-" * 30)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print("-" * 30)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced study guide system is working properly.")
    else:
        print("⚠️ Some tests failed. Check the system configuration and try again.")
    
    return passed == total

if __name__ == "__main__":
    main()
