#!/bin/bash
# StudyCoach Auto-Start Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/studycoach.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

echo "$(date): Starting StudyCoach Auto-Start..." >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "$(date): Activated virtual environment" >> "$LOG_FILE"
else
    echo "$(date): No virtual environment found, using system Python" >> "$LOG_FILE"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "$(date): ERROR - .env file not found. Please copy .env.example to .env and configure it." >> "$LOG_FILE"
    exit 1
fi

# Install/update dependencies
echo "$(date): Installing dependencies..." >> "$LOG_FILE"
pip install -r requirements.txt >> "$LOG_FILE" 2>&1

# Start the application in background
echo "$(date): Starting StudyCoach application..." >> "$LOG_FILE"
nohup python app.py >> "$LOG_FILE" 2>&1 &

# Save the PID for later management
echo $! > "$PROJECT_DIR/studycoach.pid"

echo "$(date): StudyCoach started with PID $(cat $PROJECT_DIR/studycoach.pid)" >> "$LOG_FILE"
echo "StudyCoach started successfully! Check $LOG_FILE for details."
echo "PID: $(cat $PROJECT_DIR/studycoach.pid)"
echo "To stop: kill $(cat $PROJECT_DIR/studycoach.pid)"
