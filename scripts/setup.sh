#!/bin/bash
# Setup StudyCoach Development Environment

echo "Setting up StudyCoach Development Environment..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
echo "✓ Created and activated virtual environment"

# Install dependencies
pip install -r requirements.txt
echo "✓ Installed Python dependencies"

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from .env.example"
    echo "⚠️  Please edit .env with your Azure OpenAI credentials"
fi

# Create uploads directory
mkdir -p uploads
echo "✓ Created uploads directory"

echo ""
echo "Setup complete! Next steps:"
echo "1. Edit .env with your Azure OpenAI credentials"
echo "2. Run: ./scripts/start_dev.sh"
