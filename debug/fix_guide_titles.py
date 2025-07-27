#!/usr/bin/env python3
"""
Fix study guide titles by removing trailing spaces
"""
import json

def fix_study_guide_titles():
    """Remove trailing spaces from study guide titles"""
    try:
        # Load the current data
        with open('study_guides.json', 'r') as f:
            data = json.load(f)
        
        # Fix each user's study guides
        for user_email, guides in data.items():
            # Create a new dictionary with cleaned titles
            cleaned_guides = {}
            for title, guide_data in guides.items():
                cleaned_title = title.strip()
                if cleaned_title != title:
                    print(f"Fixing title: '{title}' -> '{cleaned_title}'")
                    # Update the title in the guide data as well
                    if isinstance(guide_data, dict) and 'title' in guide_data:
                        guide_data['title'] = cleaned_title
                cleaned_guides[cleaned_title] = guide_data
            
            # Replace the guides for this user
            data[user_email] = cleaned_guides
        
        # Save the cleaned data
        with open('study_guides.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print("Study guide titles have been cleaned successfully!")
        return True
        
    except Exception as e:
        print(f"Error fixing study guide titles: {e}")
        return False

if __name__ == "__main__":
    fix_study_guide_titles()
