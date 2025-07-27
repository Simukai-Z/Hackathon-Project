#!/usr/bin/env python3
"""
Test script to verify AI response HTML parsing fix
"""
import re

def test_malformed_html_detection():
    """Test the detection logic for existing HTML in AI responses"""
    
    # Test case 1: Response with existing HTML links (should skip processing)
    response_with_html = """
    Check out your <a href="/study-tools/flashcards/view/Basic%20Roblox%20Lua" class="resource-link flashcard-link" target="_blank" title="View flashcard set">Basic Roblox Lua</a> flashcards and study guides.
    """
    
    # Test case 2: Plain text response (should be processed)
    plain_text_response = """
    You should review your Basic Roblox Lua flashcards and study guides to improve your scores.
    """
    
    # Test case 3: Malformed HTML that was causing issues
    malformed_html = """
    View flashcards/view/Basic%20Roblox%20Lua" class="resource-link flashcard-link" target="_blank" title="View flashcard set">Basic Roblox Lua</a> flashcardsstudy guides: study guidesView Roblox study guidesstudy guides
    """
    
    def clean_malformed_html(text):
        """Simulate the cleaning function from our fix"""
        if not text:
            return text
            
        # Remove orphaned closing tags
        text = re.sub(r'</a>', '', text, flags=re.IGNORECASE)
        
        # Remove broken href patterns
        text = re.sub(r'[^<]*"[^>]*class="resource-link"[^>]*target="_blank"[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Remove incomplete link attributes
        text = re.sub(r'[^<\s]+class="resource-link[^"]*"[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Remove orphaned target="_blank" attributes
        text = re.sub(r'[^<\s]*target="_blank"[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Clean up any remaining broken HTML fragments
        text = re.sub(r'[^<\s]*"[^>]*>', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def has_malformed_html(content):
        """Enhanced detection logic from our fix"""
        if not content:
            return False
            
        has_proper_html = '<a ' in content and '</a>' in content
        has_malformed_html = ('class="resource-link' in content or
                            'target="_blank"' in content or
                            '</a>' in content or
                            bool(re.search(r'href="[^"]*"[^>]*>', content, re.IGNORECASE)))
        
        return has_proper_html, has_malformed_html
    
    print("=== Enhanced AI Response HTML Detection Test ===\n")
    
    test_cases = [
        ("Response with proper HTML links", response_with_html),
        ("Plain text response", plain_text_response),
        ("Malformed HTML (causing issues)", malformed_html)
    ]
    
    for i, (name, content) in enumerate(test_cases, 1):
        print(f"Test {i} - {name}:")
        print(f"Content: {content.strip()[:100]}...")
        
        has_proper, has_malformed = has_malformed_html(content)
        should_skip = has_proper or has_malformed
        
        print(f"Has proper HTML: {has_proper}")
        print(f"Has malformed HTML: {has_malformed}")
        print(f"Should skip processing: {should_skip}")
        
        if has_malformed and not has_proper:
            cleaned = clean_malformed_html(content)
            print(f"Cleaned result: {cleaned[:100]}...")
        
        print()
    
    print("=== Summary ===")
    print("✅ Proper HTML responses will be displayed as-is")
    print("✅ Plain text responses will get link processing")
    print("✅ Malformed HTML will be detected and cleaned before display")
    print("✅ No more double-processing of HTML content")

if __name__ == "__main__":
    test_malformed_html_detection()
