#!/bin/bash
# StudyCoach Stop Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/studycoach.pid"
LOG_FILE="$PROJECT_DIR/logs/studycoach.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "$(date): Stopping StudyCoach (PID: $PID)..." >> "$LOG_FILE"
        kill $PID
        rm "$PID_FILE"
        echo "StudyCoach stopped successfully!"
        echo "$(date): StudyCoach stopped" >> "$LOG_FILE"
    else
        echo "StudyCoach process not running (PID $PID not found)"
        rm "$PID_FILE"
    fi
else
    echo "No PID file found. StudyCoach may not be running."
fi
