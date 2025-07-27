#!/bin/bash

echo "🔍 Study Coach Logo Diagnostic Report"
echo "====================================="

echo ""
echo "📊 FILE STATUS:"
echo "Logo file: $(ls -la /workspaces/Hackathon-Project/static/study_coach_logo.png)"
echo "File type: $(file /workspaces/Hackathon-Project/static/study_coach_logo.png)"
echo "File size: $(stat -c%s /workspaces/Hackathon-Project/static/study_coach_logo.png) bytes"

echo ""
echo "🌐 HTTP STATUS:"
echo "Direct logo access:"
curl -I http://127.0.0.1:5000/static/study_coach_logo.png 2>/dev/null | head -1

echo ""
echo "📝 HTML VERIFICATION:"
echo "Checking if logo appears in HTML:"
curl -s http://127.0.0.1:5000 | grep -c "study_coach_logo.png" && echo "✅ Logo references found in HTML" || echo "❌ No logo references in HTML"

echo ""
echo "🎨 CSS VERIFICATION:"
echo "Header logo CSS class:"
grep -A5 "\.header-logo" /workspaces/Hackathon-Project/static/modern.css

echo ""
echo "🧪 TEMPLATE VERIFICATION:"
echo "Base template header section:"
grep -A3 -B1 "header-logo" /workspaces/Hackathon-Project/templates/base.html

echo ""
echo "📱 BROWSER CACHE CLEAR:"
echo "To see the logo, you may need to:"
echo "1. Hard refresh (Ctrl+F5 or Cmd+Shift+R)"
echo "2. Clear browser cache"
echo "3. Open in incognito/private mode"

echo ""
echo "🚀 TESTING URLS:"
echo "Main site: http://127.0.0.1:5000"
echo "Logo direct: http://127.0.0.1:5000/static/study_coach_logo.png"

echo ""
echo "💡 TROUBLESHOOTING:"
if curl -s http://127.0.0.1:5000/static/study_coach_logo.png > /dev/null; then
    echo "✅ Logo is accessible via HTTP"
else
    echo "❌ Logo is NOT accessible via HTTP"
fi

if curl -s http://127.0.0.1:5000 | grep -q "study_coach_logo.png"; then
    echo "✅ Logo is referenced in HTML"
else
    echo "❌ Logo is NOT referenced in HTML"
fi

echo ""
echo "🎯 FINAL CHECK:"
echo "Opening browser to test logo visibility..."
