#!/bin/bash

echo "📁 Easy Logo Upload Commands"
echo "============================"

echo ""
echo "🎯 QUICKEST METHOD - VS Code File Upload:"
echo ""
echo "1. In VS Code, click on the file explorer (left sidebar)"
echo "2. Navigate to: Hackathon-Project → static"
echo "3. Right-click in the static folder"
echo "4. Select 'Upload...'"
echo "5. Choose your Study Coach logo image"
echo "6. Make sure it's named 'study_coach_logo.png'"

echo ""
echo "🖱️ ALTERNATIVE - Drag & Drop:"
echo ""
echo "1. Open your file manager/finder"
echo "2. Find your Study Coach logo image"
echo "3. In VS Code, open the static folder"
echo "4. Drag the image from your file manager"
echo "5. Drop it into VS Code's static folder"
echo "6. Rename to 'study_coach_logo.png' if needed"

echo ""
echo "💻 TERMINAL METHOD (if file is in Downloads):"
echo ""
echo "# For macOS/Linux:"
echo "cp ~/Downloads/study_coach_logo.png /workspaces/Hackathon-Project/static/"
echo ""
echo "# For Windows (if in Downloads):"
echo "cp /mnt/c/Users/\$USER/Downloads/study_coach_logo.png /workspaces/Hackathon-Project/static/"

echo ""
echo "🔧 CURRENT FILE STATUS:"
file /workspaces/Hackathon-Project/static/study_coach_logo.png
echo ""
echo "File size: $(stat -f%z /workspaces/Hackathon-Project/static/study_coach_logo.png 2>/dev/null || stat -c%s /workspaces/Hackathon-Project/static/study_coach_logo.png) bytes"

echo ""
echo "✅ VERIFICATION:"
echo "After uploading, run: ls -la /workspaces/Hackathon-Project/static/study_coach_logo.png"
echo "The file should be larger than 379 bytes (current size)"

echo ""
echo "🚀 TEST THE LOGO:"
echo "Once uploaded, visit: http://127.0.0.1:5000"
echo "You should see your turtle logo in the header and other locations!"
