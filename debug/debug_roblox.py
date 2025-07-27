#!/usr/bin/env python3
"""
Debug script to test Roblox study guide URL encoding/decoding
"""

import json
import urllib.parse

# Load study guides
with open('study_guides.json', 'r') as f:
    study_guides = json.load(f)

user_email = 'epicrbot20099@gmail.com'
user_guides = study_guides.get(user_email, {})

print("=== Debug: Roblox Study Guide URL Issue ===")
print(f"User guides available: {list(user_guides.keys())}")
print()

# Test the specific guide
guide_name = 'Roblox study guide'
print(f"Looking for guide: '{guide_name}'")
print(f"Guide exists: {guide_name in user_guides}")

if guide_name in user_guides:
    print(f"✅ Guide found in JSON")
    guide_data = user_guides[guide_name]
    print(f"Guide title: {guide_data.get('title', 'No title')}")
else:
    print(f"❌ Guide not found in JSON")
    print("Available guides:")
    for key in user_guides.keys():
        print(f"  - '{key}' (length: {len(key)})")

print()
print("=== URL Encoding Tests ===")
encoded = urllib.parse.quote(guide_name)
print(f"URL encoded: {encoded}")
decoded = urllib.parse.unquote(encoded)
print(f"URL decoded: {decoded}")
print(f"Encoding/decoding works: {decoded == guide_name}")

print()
print("=== Character Analysis ===")
for i, char in enumerate(guide_name):
    print(f"  {i}: '{char}' (ord: {ord(char)})")
