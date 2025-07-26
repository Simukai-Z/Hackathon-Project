# StudyCoach - Comprehensive Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Features & Capabilities](#features--capabilities)
4. [Installation & Setup](#installation--setup)
5. [User Guide](#user-guide)
6. [API Documentation](#api-documentation)
7. [Development Guide](#development-guide)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)

## Project Overview

StudyCoach is an AI-powered educational platform that connects students and teachers in a collaborative learning environment. The platform leverages Azure OpenAI to provide intelligent tutoring, automated grading, and personalized feedback.

### Key Technologies
- **Backend**: Python Flask
- **AI Integration**: Azure OpenAI (GPT models)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Data Storage**: JSON files (easily portable to database)
- **Authentication**: Session-based
- **File Handling**: Secure file uploads with validation

### Core Philosophy
- **Student-Centered Learning**: AI adapts to individual learning styles and provides personalized guidance
- **Teacher Empowerment**: Automated grading and feedback tools to reduce workload
- **Academic Integrity**: AI guides learning without providing direct answers
- **Accessibility**: Clean, modern UI with dark/light theme support

## System Architecture

### Project Structure
```
studycoach/
├── app.py                 # Main Flask application (legacy, being refactored)
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create from .env.example)
├── users.json           # User data storage
├── classrooms.json      # Classroom and assignment data
├── utils/               # Utility modules
│   ├── error_handler.py # Error handling and logging
│   ├── validators.py    # Data validation utilities
│   ├── data_manager.py  # Data access layer
│   └── google_docs.py   # Google Docs integration
├── services/            # Business logic services
│   └── ai_service.py    # AI operations and chat handling
├── routes/              # Route handlers (Blueprint organization)
│   └── api.py          # API endpoints
├── templates/           # Jinja2 HTML templates
│   ├── base.html       # Base template with common elements
│   ├── home.html       # Landing page
│   ├── student_main.html # Student dashboard
│   ├── teacher_main.html # Teacher dashboard
│   ├── ai_assistant.html # AI chat interface
│   └── ...             # Other templates
├── static/             # Static assets
│   ├── modern.css     # Modern design system styles
│   ├── style.css      # Additional styles
│   ├── modern.js      # Frontend JavaScript utilities
│   └── study_coach_logo.png # Application logo
└── uploads/           # File upload storage
```

### Data Models

#### User Model
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "type": "student|teacher",
  "classrooms": ["classroom_codes"],
  "ai_personality": "string",
  "last_activity": "ISO_timestamp",
  "created_at": "ISO_timestamp",
  "updated_at": "ISO_timestamp"
}
```

#### Classroom Model
```json
{
  "code": "8_char_string",
  "teacher_email": "string",
  "class_name": "string",
  "school": "string",
  "students": ["student_emails"],
  "assignments": [Assignment],
  "rubrics": [Rubric],
  "created_at": "ISO_timestamp"
}
```

#### Assignment Model
```json
{
  "id": "uuid",
  "title": "string",
  "content": "string",
  "description": "string",
  "rubric_id": "string",
  "timestamp": "ISO_timestamp",
  "teacher_email": "string",
  "submissions": [Submission]
}
```

#### Submission Model
```json
{
  "id": "uuid",
  "student_email": "string",
  "assignment_id": "string",
  "submission_text": "string",
  "submission_link": "string",
  "filename": "string",
  "timestamp": "ISO_timestamp",
  "grade": "integer|null",
  "feedback": "string",
  "graded_by": "string",
  "graded_timestamp": "ISO_timestamp"
}
```

## Features & Capabilities

### 🎓 Student Features

#### AI-Powered Learning Assistant
- **Personalized Tutoring**: AI adapts to individual learning styles and preferences
- **Contextual Help**: AI understands the student's current assignments and past performance
- **Academic Integrity**: Provides guidance and hints rather than direct answers
- **Submission Analysis**: Automatically retrieves and analyzes student's past work for context

#### Assignment Management
- **Multiple Submission Types**: 
  - Text input for essays and written responses
  - File uploads (PDF, DOC, images, etc.)
  - External links (Google Docs, Drive files, etc.)
- **Resubmission Capability**: Students can update submissions before grading
- **Progress Tracking**: View grades, feedback, and performance metrics
- **Activity Monitoring**: Last activity tracking for teacher awareness

#### Classroom Integration
- **Easy Joining**: Join classrooms via unique codes or direct links
- **Multi-Class Support**: Participate in multiple classrooms simultaneously
- **Real-Time Updates**: See new assignments and rubrics immediately
- **Performance Analytics**: Track personal academic progress

### 👨‍🏫 Teacher Features

#### Intelligent Grading System
- **AI-Assisted Grading**: Automated grading with customizable rubrics
- **Manual Override**: Full control over AI-generated grades and feedback
- **Consistency**: AI maintains consistent grading standards across submissions
- **Multiple Content Types**: Grades text, files, and link submissions

#### Classroom Management
- **Student Activity Monitoring**: Real-time view of student engagement
- **Assignment Creation**: Rich assignment builder with rubric integration
- **Bulk Operations**: Manage multiple assignments and students efficiently
- **Performance Analytics**: Class-wide performance tracking and insights

#### Feedback Enhancement
- **AI-Enhanced Feedback**: Automatically improve and personalize feedback
- **Feedback History**: Track and reference previous feedback patterns
- **Template System**: Reuse effective feedback structures
- **Student-Specific Context**: Feedback considers individual student history

### 🤖 AI System Features

#### Advanced Context Awareness
- **Student Performance Analysis**: Tracks academic progress and learning patterns
- **Assignment History Integration**: References past work for personalized guidance
- **Multi-Class Context**: Understands assignments across different classrooms
- **Adaptive Personality**: Customizable AI personalities for different learning styles

#### Intelligent Grading
- **Rubric-Based Assessment**: Follows teacher-defined grading criteria
- **Consistent Evaluation**: Uses content hashing for reproducible grades
- **Multiple Content Formats**: Processes text, files, and linked content
- **Detailed Feedback Generation**: Creates comprehensive, constructive feedback

#### Conversation Management
- **Long-Term Memory**: Maintains conversation history with summarization
- **Context Switching**: Handles multiple topics and assignments seamlessly
- **Error Recovery**: Graceful handling of AI service interruptions
- **Usage Optimization**: Efficient token usage and response management

### 🔧 System Features

#### Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark/Light Theme**: Automatic theme detection with manual override
- **Accessibility**: WCAG-compliant design with keyboard navigation
- **Progressive Enhancement**: Core functionality works without JavaScript

#### Security & Privacy
- **Session Management**: Secure user sessions with timeout handling
- **Input Validation**: Comprehensive data validation and sanitization
- **File Security**: Safe file upload handling with type and size restrictions
- **Access Control**: Role-based permissions for students and teachers

#### Performance & Reliability
- **Error Handling**: Comprehensive error tracking and graceful degradation
- **Logging System**: Detailed application logging for debugging and monitoring
- **Data Integrity**: Consistent data validation and backup-friendly storage
- **Scalable Architecture**: Modular design ready for database migration

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Azure OpenAI account with API access
- Modern web browser

### Environment Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd studycoach
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_MODEL=gpt-35-turbo
   
   # Flask Configuration
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   
   # Optional: Custom file paths
   UPLOAD_FOLDER=uploads
   MAX_CONTENT_LENGTH=16777216  # 16MB
   ```

5. **Create Required Directories**
   ```bash
   mkdir -p uploads static/uploads
   ```

6. **Run the Application**
   ```bash
   python app.py
   ```

### Azure OpenAI Setup

1. Create an Azure OpenAI resource in the Azure portal
2. Deploy a GPT model (GPT-3.5-turbo or GPT-4)
3. Copy the endpoint URL and API key
4. Update your `.env` file with these credentials

### Production Deployment

#### Using Gunicorn (Recommended)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

#### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p uploads

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Environment Variables for Production
```env
FLASK_ENV=production
SECRET_KEY=your-secure-production-key
AZURE_OPENAI_ENDPOINT=your-production-endpoint
AZURE_OPENAI_API_KEY=your-production-key
```

## User Guide

### For Students

#### Getting Started
1. **Create Account**: Visit the homepage and click "Get Started as Student"
2. **Fill Registration**: Enter your name, email, and optional classroom code
3. **Join Classrooms**: Use classroom codes provided by teachers or join via direct links
4. **Access Dashboard**: Navigate assignments, view grades, and track progress

#### Using the AI Assistant
1. **Open AI Chat**: Click "AI Assistant" in the navigation
2. **Customize Personality**: Set AI personality to match your learning style
3. **Ask Questions**: Get help with assignments, concepts, or studying
4. **Upload Files**: Share documents for AI analysis and feedback
5. **Review History**: AI remembers your conversation and academic history

#### Submitting Assignments
1. **View Assignment**: Click on an assignment in your dashboard
2. **Choose Submission Method**:
   - **Text Response**: Type directly in the text area
   - **File Upload**: Upload documents, images, or other files
   - **External Link**: Share Google Docs, Drive files, or other links
3. **Submit Work**: Click submit to send your work to the teacher
4. **Track Status**: Monitor grading status and view feedback when available

### For Teachers

#### Setting Up Classrooms
1. **Create Account**: Register as a teacher with school information
2. **Classroom Creation**: Automatically created during registration
3. **Share Join Code**: Provide students with the 8-character classroom code
4. **Manage Students**: Monitor student activity and engagement

#### Creating Assignments
1. **Navigate to Classroom**: Select your classroom from the dashboard
2. **Add Assignment**: Click "Add Assignment" button
3. **Fill Details**:
   - Title and description
   - Assignment content/instructions
   - Optional rubric selection
4. **Publish**: Assignment immediately becomes available to students

#### Grading and Feedback
1. **Access Grading Center**: View all submissions in one place
2. **Grade Options**:
   - **Manual Grading**: Provide grade and written feedback
   - **AI Grading**: Let AI grade with rubric-based assessment
   - **AI-Enhanced Feedback**: Use AI to improve your written feedback
3. **Review Results**: Monitor class performance and individual progress

### For Administrators

#### System Monitoring
- Check application logs in `app.log`
- Monitor file upload storage usage
- Review error rates and performance metrics

#### User Management
- Access user data in `users.json` and `classrooms.json`
- Reset passwords by updating user records
- Monitor system usage and capacity

## API Documentation

### Authentication
All API endpoints require active user sessions. Include session cookies with requests.

### Endpoints

#### Chat API
```http
POST /api/chat
Content-Type: application/json

{
  "prompt": "string",
  "personality": "string (optional)",
  "fileContent": "string (optional)",
  "class_code": "string (optional)"
}
```

**Response:**
```json
{
  "response": "AI response string"
}
```

#### Grading API
```http
POST /api/grade_assignment
Content-Type: multipart/form-data

classroom_id: string
assignment_id: string  
student_email: string
grade: integer (0-100)
feedback: string
use_ai: boolean
```

**Response:**
```json
{
  "success": boolean,
  "message": "string"
}
```

#### AI Grading API
```http
POST /api/ai_grade_assignment
Content-Type: multipart/form-data

classroom_id: string
assignment_id: string
student_email: string
```

**Response:**
```json
{
  "success": boolean,
  "message": "string",
  "grade": integer,
  "feedback": "string"
}
```

#### Submission Viewing API
```http
GET /api/submission/{classroom_id}/{assignment_id}/{student_email}
```

**Response:**
```json
{
  "student_name": "string",
  "assignment_title": "string",
  "assignment_description": "string",
  "submission_text": "string",
  "submission_link": "string", 
  "filename": "string",
  "timestamp": "string",
  "grade": integer,
  "feedback": "string",
  "graded_by": "string",
  "graded_timestamp": "string",
  "google_docs_info": object
}
```

## Development Guide

### Code Organization

#### Module Structure
- **`utils/`**: Pure utility functions with no Flask dependencies
- **`services/`**: Business logic and external service integrations
- **`routes/`**: Flask route handlers organized by functionality
- **`templates/`**: Jinja2 templates with inheritance hierarchy
- **`static/`**: CSS, JavaScript, and static assets

#### Design Patterns
- **Blueprint Organization**: Routes grouped by functionality
- **Service Layer**: Business logic separated from presentation
- **Data Access Layer**: Centralized data operations
- **Error Handling**: Consistent error handling with proper logging

### Adding New Features

#### 1. Create Service Module
```python
# services/new_feature.py
class NewFeatureService:
    def __init__(self):
        self.config = Config()
    
    def perform_operation(self, data):
        # Business logic here
        pass
```

#### 2. Add Route Handler
```python
# routes/new_feature.py
from flask import Blueprint
from services.new_feature import NewFeatureService

feature_bp = Blueprint('feature', __name__)

@feature_bp.route('/feature')
@validate_session()
@handle_errors
def feature_endpoint():
    service = NewFeatureService()
    result = service.perform_operation(request.data)
    return jsonify(result)
```

#### 3. Register Blueprint
```python
# app.py
from routes.new_feature import feature_bp
app.register_blueprint(feature_bp)
```

### Testing Guidelines

#### Unit Testing
```python
import unittest
from services.new_feature import NewFeatureService

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.service = NewFeatureService()
    
    def test_operation(self):
        result = self.service.perform_operation(test_data)
        self.assertEqual(result.success, True)
```

#### Integration Testing
```python
import unittest
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True
    
    def test_endpoint(self):
        response = self.client.post('/api/endpoint', data=test_data)
        self.assertEqual(response.status_code, 200)
```

### Database Migration

The current JSON-based storage can be easily migrated to a proper database:

#### SQLAlchemy Models
```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Classroom(db.Model):
    code = db.Column(db.String(8), primary_key=True)
    teacher_email = db.Column(db.String(120), nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    school = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Migration Strategy
1. Create database models matching current JSON structure
2. Write migration script to transfer data
3. Update data_manager.py to use SQLAlchemy
4. Test thoroughly before switching production data

## Security Considerations

### Input Validation
- All user inputs are validated and sanitized
- File uploads restricted by type and size
- SQL injection prevention (when using database)
- XSS protection through template escaping

### Authentication & Authorization
- Session-based authentication with secure cookies
- Role-based access control (student/teacher)
- Session timeout and cleanup
- CSRF protection on state-changing operations

### Data Protection
- Sensitive data encrypted in storage
- API keys stored in environment variables
- User data access logged and monitored
- Regular security updates and patches

### AI Safety
- Prompt injection protection
- Content filtering for inappropriate material
- Usage monitoring and rate limiting
- Fallback mechanisms for AI service failures

## Troubleshooting

### Common Issues

#### AI Service Errors
**Problem**: "AI grading failed" or chat not working
**Solutions**:
1. Check Azure OpenAI credentials in `.env`
2. Verify model deployment in Azure portal
3. Check API quota and usage limits
4. Review application logs for specific errors

#### File Upload Issues
**Problem**: Files not uploading or displaying
**Solutions**:
1. Check `uploads/` directory permissions
2. Verify file size under limit (16MB default)
3. Ensure file extensions are allowed
4. Check disk space availability

#### Session Problems
**Problem**: Users getting logged out frequently
**Solutions**:
1. Check `SECRET_KEY` configuration
2. Verify session timeout settings
3. Clear browser cookies and cache
4. Check for server restarts or memory issues

#### Performance Issues
**Problem**: Slow response times or timeouts
**Solutions**:
1. Monitor AI API response times
2. Check file upload sizes and processing
3. Review database query performance (if using DB)
4. Enable caching for static content

### Debugging Tools

#### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug information")
```

#### Error Tracking
```python
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Handle gracefully
```

#### Performance Monitoring
```python
import time
start_time = time.time()
# Operation
duration = time.time() - start_time
logger.info(f"Operation took {duration:.2f} seconds")
```

## Contributing

### Development Process
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes following code style guidelines
4. Add tests for new functionality
5. Update documentation as needed
6. Submit pull request with detailed description

### Code Style Guidelines
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write descriptive docstrings
- Keep functions focused and small
- Use meaningful variable names

### Documentation Standards
- Update README.md for user-facing changes
- Add docstrings to all public functions
- Include code examples in documentation
- Keep API documentation current

### Testing Requirements
- Unit tests for all business logic
- Integration tests for API endpoints
- Manual testing checklist for UI changes
- Performance testing for AI operations

---

## Changelog

### Version 2.0.0 (Current Development)
- **New**: Modular architecture with Blueprint organization
- **New**: Comprehensive error handling and logging system
- **New**: Data validation and sanitization utilities
- **New**: AI service abstraction with improved context handling
- **New**: Google Docs integration utilities
- **Improved**: Configuration management system
- **Improved**: Database abstraction layer for easy migration
- **Fixed**: JavaScript button issues with special characters
- **Fixed**: Duplicate function definitions
- **Fixed**: Session management security issues

### Version 1.x (Legacy)
- Basic student/teacher functionality
- AI chat integration
- File upload system
- Manual and AI-assisted grading
- Classroom management

---

*Last Updated: July 26, 2025*
*Version: 2.0.0-dev*
