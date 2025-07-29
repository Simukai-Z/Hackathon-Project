#!/bin/bash
# StudyCoach Service Installation and Setup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Setting up StudyCoach Auto-Start..."

# Make scripts executable
chmod +x "$PROJECT_DIR/scripts/autostart.sh"
chmod +x "$PROJECT_DIR/scripts/stop.sh"
chmod +x "$PROJECT_DIR/scripts/status.sh"
chmod +x "$PROJECT_DIR/scripts/setup_autostart.sh"

echo "✓ Made scripts executable"

# Create virtual environment if it doesn't exist
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    cd "$PROJECT_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✓ Created and configured virtual environment"
else
    echo "✓ Virtual environment already exists"
fi

# Check for .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  .env file not found. You'll need to create it before starting StudyCoach."
    echo "   Please copy .env.example to .env and configure your Azure OpenAI settings."
fi

echo ""
echo "StudyCoach Auto-Start Setup Complete!"
echo ""
echo "Available commands:"
echo "  Start:  $PROJECT_DIR/scripts/autostart.sh"
echo "  Stop:   $PROJECT_DIR/scripts/stop.sh"
echo "  Status: $PROJECT_DIR/scripts/status.sh"
echo ""
echo "For system-wide auto-start (requires sudo):"
echo "  sudo cp $PROJECT_DIR/studycoach.service /etc/systemd/system/"
echo "  sudo systemctl enable studycoach"
echo "  sudo systemctl start studycoach"
