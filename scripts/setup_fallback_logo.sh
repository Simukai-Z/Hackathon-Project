#!/bin/bash

echo "🔄 Logo Fallback Setup"
echo "====================="

echo ""
echo "Creating temporary backup of corrupted logo..."
mv /workspaces/Hackathon-Project/static/study_coach_logo.png /workspaces/Hackathon-Project/static/study_coach_logo.png.corrupted 2>/dev/null || echo "No existing PNG to backup"

echo ""
echo "Converting SVG fallback to PNG..."
# Try to convert SVG to PNG using available tools
if command -v convert >/dev/null 2>&1; then
    echo "Using ImageMagick convert..."
    convert /workspaces/Hackathon-Project/static/study_coach_logo_fallback.svg /workspaces/Hackathon-Project/static/study_coach_logo.png
elif command -v rsvg-convert >/dev/null 2>&1; then
    echo "Using rsvg-convert..."
    rsvg-convert -w 400 -h 200 /workspaces/Hackathon-Project/static/study_coach_logo_fallback.svg > /workspaces/Hackathon-Project/static/study_coach_logo.png
else
    echo "No PNG conversion tools available. Using SVG directly..."
    # Just copy the SVG as a temporary solution
    cp /workspaces/Hackathon-Project/static/study_coach_logo_fallback.svg /workspaces/Hackathon-Project/static/study_coach_logo.png
fi

echo ""
echo "✅ Fallback logo created!"
echo "File info:"
ls -la /workspaces/Hackathon-Project/static/study_coach_logo*

echo ""
echo "🧪 Testing the fallback logo:"
curl -I http://127.0.0.1:5000/static/study_coach_logo.png

echo ""
echo "🚀 Ready to test!"
echo "Visit: http://127.0.0.1:5000"
echo "The logo should now appear (may need browser refresh)"

echo ""
echo "📝 TO FIX PERMANENTLY:"
echo "1. Re-upload your original Study Coach PNG logo"
echo "2. Make sure to upload it as a binary file (not text)"
echo "3. Replace the fallback with your actual logo"
