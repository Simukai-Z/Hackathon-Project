#!/usr/bin/env python3
"""
Test script to verify the study guide URL encoding fix
"""
import json
import urllib.parse

def test_study_guide_titles():
    """Test that study guide titles work correctly with URL encoding"""
    try:
        # Load the current data
        with open('study_guides.json', 'r') as f:
            data = json.load(f)
        
        user_email = "epicrbot20099@gmail.com"
        if user_email not in data:
            print(f"User {user_email} not found in data")
            return False
        
        guides = data[user_email]
        print(f"Available study guides for {user_email}:")
        
        for title in guides.keys():
            print(f"  - '{title}' (length: {len(title)})")
            
            # Test URL encoding/decoding
            encoded = urllib.parse.quote(title)
            decoded = urllib.parse.unquote(encoded).strip()
            
            print(f"    Encoded: {encoded}")
            print(f"    Decoded: '{decoded}' (length: {len(decoded)})")
            print(f"    Match: {title == decoded}")
            
            # Check for trailing spaces
            if title != title.strip():
                print(f"    WARNING: Title has trailing spaces!")
            else:
                print(f"    OK: No trailing spaces")
            print()
        
        # Specific test for the problematic guide
        test_titles = ["Fortnite study guide", "Fortnite study guide "]
        print("Testing specific problematic titles:")
        for test_title in test_titles:
            print(f"  Testing: '{test_title}' (length: {len(test_title)})")
            found = test_title in guides
            print(f"    Found in guides: {found}")
            if not found:
                # Check if stripping helps
                stripped = test_title.strip()
                found_stripped = stripped in guides
                print(f"    Found after strip: {found_stripped}")
        
        return True
        
    except Exception as e:
        print(f"Error testing study guide titles: {e}")
        return False

if __name__ == "__main__":
    test_study_guide_titles()
