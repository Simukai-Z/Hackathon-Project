#!/bin/bash
# Start StudyCoach Development Server

echo "Starting StudyCoach Development Server..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Activated virtual environment"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Install dependencies
pip install -r requirements.txt

# Start the application
python app.py
