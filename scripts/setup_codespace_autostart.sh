#!/bin/bash
# GitHub Codespaces Auto-Start Setup for StudyCoach

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up StudyCoach to auto-start when codespace starts..."

# Create the codespace startup script
cat > "$PROJECT_DIR/scripts/codespace_startup.sh" << 'EOF'
#!/bin/bash
# StudyCoach Codespace Auto-Start Script

# Wait a bit for codespace to fully initialize
sleep 5

# Change to project directory
cd /workspaces/Hackathon-Project

# Check if StudyCoach is already running
if [ -f "studycoach.pid" ]; then
    PID=$(cat studycoach.pid)
    if ps -p $PID > /dev/null; then
        echo "StudyCoach is already running (PID: $PID)"
        exit 0
    fi
fi

# Start StudyCoach
echo "Auto-starting StudyCoach..."
./scripts/autostart.sh

echo "StudyCoach auto-started! Access it at: https://$CODESPACE_NAME-5000.app.github.dev"
EOF

# Make the codespace startup script executable
chmod +x "$PROJECT_DIR/scripts/codespace_startup.sh"

# Add auto-start to .bashrc if not already there
BASHRC_LINE="# Auto-start StudyCoach in codespace"
if ! grep -q "$BASHRC_LINE" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "$BASHRC_LINE" >> ~/.bashrc
    echo "if [ -f /workspaces/Hackathon-Project/scripts/codespace_startup.sh ]; then" >> ~/.bashrc
    echo "    /workspaces/Hackathon-Project/scripts/codespace_startup.sh &" >> ~/.bashrc
    echo "fi" >> ~/.bashrc
    echo "✓ Added auto-start to ~/.bashrc"
else
    echo "✓ Auto-start already configured in ~/.bashrc"
fi

echo ""
echo "✅ Codespace auto-start setup complete!"
echo ""
echo "StudyCoach will now automatically start when you open this codespace."
echo "The application will be available at:"
echo "  https://\$CODESPACE_NAME-5000.app.github.dev"
echo ""
echo "To disable auto-start, remove the lines from ~/.bashrc or run:"
echo "  ./scripts/disable_codespace_autostart.sh"
