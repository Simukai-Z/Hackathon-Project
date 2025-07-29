#!/bin/bash
# Disable StudyCoach Codespace Auto-Start

echo "Disabling StudyCoach codespace auto-start..."

# Remove auto-start lines from .bashrc
if grep -q "# Auto-start StudyCoach in codespace" ~/.bashrc; then
    # Create a temporary file without the auto-start lines
    grep -v "# Auto-start StudyCoach in codespace" ~/.bashrc | \
    grep -v "if \[ -f /workspaces/Hackathon-Project/scripts/codespace_startup.sh \]" | \
    grep -v "/workspaces/Hackathon-Project/scripts/codespace_startup.sh &" | \
    grep -v "fi" > ~/.bashrc.tmp
    
    mv ~/.bashrc.tmp ~/.bashrc
    echo "✓ Removed auto-start from ~/.bashrc"
else
    echo "✓ Auto-start was not configured in ~/.bashrc"
fi

echo ""
echo "✅ Codespace auto-start disabled!"
echo "StudyCoach will no longer start automatically when you open this codespace."
echo ""
echo "To re-enable, run: ./scripts/setup_codespace_autostart.sh"
