#!/bin/bash
# StudyCoach Status Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/studycoach.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "StudyCoach is running (PID: $PID)"
        echo "Application should be accessible at: http://localhost:5000"
    else
        echo "StudyCoach is not running (stale PID file)"
        rm "$PID_FILE"
    fi
else
    echo "StudyCoach is not running (no PID file found)"
fi
