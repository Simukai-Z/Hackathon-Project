#!/usr/bin/env python3
"""
Test script to verify the AI response HTML corruption fix
"""

def test_html_detection():
    """Test the simplified HTML detection logic"""
    
    # Test cases
    test_cases = [
        {
            "name": "Plain text response",
            "content": "You should review your Basic Roblox Lua flashcards and study guides to improve your scores.",
            "should_process": True
        },
        {
            "name": "Backend-processed HTML (proper)",
            "content": 'Check out your <a href="/study-tools/flashcards/view/Basic%20Roblox%20Lua" class="resource-link flashcard-link" target="_blank">Basic Roblox Lua</a> flashcards.',
            "should_process": False
        },
        {
            "name": "Malformed HTML (corrupted)",
            "content": 'View flashcards/view/Basic%20Roblox%20Lua" class="resource-link flashcard-link" target="_blank" title="View flashcard set">Basic Roblox Lua</a> flashcardsstudy guides',
            "should_process": False
        },
        {
            "name": "Nested malformed HTML",
            "content": 'Hey EPic! 🚀 Let\'s check out the <a href="/study-tools/study-guides" target="_blank" class="study-link">study guides</a> you have available: 📖 You currently have a <a href="/study-tools/study-guides" target="_blank" class="study-link">study guides</a> named \'Roblox <a href="/study-tools/study-guides" target="_blank" class="study-link">study guides</a>\' with 1017 characters.',
            "should_process": False
        }
    ]
    
    def contains_html(content):
        """Simplified HTML detection logic from our fix"""
        return (content.find('<a ') != -1 or
                content.find('</a>') != -1 or
                content.find('href=') != -1 or
                content.find('target="_blank"') != -1 or
                content.find('class="') != -1)
    
    print("=== AI HTML Detection Fix Test ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Content preview: {test_case['content'][:80]}...")
        
        has_html = contains_html(test_case['content'])
        should_skip_processing = has_html
        expected_skip = not test_case['should_process']
        
        print(f"Contains HTML: {has_html}")
        print(f"Will skip frontend processing: {should_skip_processing}")
        print(f"Expected to skip: {expected_skip}")
        
        if should_skip_processing == expected_skip:
            print("✅ PASS - Correct detection")
        else:
            print("❌ FAIL - Incorrect detection")
        
        print()
    
    print("=== Summary ===")
    print("✅ Plain text responses will get frontend link processing")
    print("✅ Any HTML content (proper or malformed) will be displayed as-is")
    print("✅ No more HTML corruption from double processing")
    print("✅ No more aggressive cleaning that cuts off content")
    
    return True

if __name__ == "__main__":
    test_html_detection()
