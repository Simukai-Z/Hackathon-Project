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
