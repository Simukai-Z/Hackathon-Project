#!/usr/bin/env python3
"""
Test the escapejs filter directly
"""
import sys
sys.path.append('/workspaces/Hackathon-Project')

from app import app

def test_escapejs_filter():
    """Test the escapejs filter"""
    with app.app_context():
        try:
            # Test the filter directly
            test_string = "Hello 'World' with \"quotes\" and \n newlines"
            
            # Get the filter function
            escapejs_filter = app.jinja_env.filters.get('escapejs')
            
            if escapejs_filter:
                result = escapejs_filter(test_string)
                print(f"Original: {repr(test_string)}")
                print(f"Escaped:  {repr(result)}")
                print("✅ escapejs filter is working!")
                return True
            else:
                print("❌ escapejs filter not found in Jinja environment")
                print("Available filters:", list(app.jinja_env.filters.keys()))
                return False
                
        except Exception as e:
            print(f"❌ Error testing escapejs filter: {e}")
            return False

if __name__ == "__main__":
    test_escapejs_filter()
