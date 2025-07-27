# StudyCoach - AI-Powered Educational Platform

An intelligent tutoring and classroom management system that connects students and teachers through AI-assisted learning.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Azure OpenAI account with API access

### Installation
```bash
# Clone the repository
git clone <https://github.com/Simukai-Z/Hackathon-Project>
cd studycoach

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Edit .env with your Azure OpenAI credentials
nano .env

# Start the development server
./scripts/start_dev.sh
```


## 📖 Documentation

- **[Complete Documentation](docs/DOCUMENTATION.md)** - Comprehensive guide covering all features
- **[API Documentation](docs/)** - API endpoints and integration guide
- **[Development Guide](docs/DOCUMENTATION.md#development-guide)** - Contributing and development setup

## ✨ Key Features

### For Students
- 🤖 **AI-Powered Tutoring** - Personalized learning assistance
- 📝 **Multiple Submission Types** - Text, files, and links
- 📊 **Progress Tracking** - Monitor grades and performance
- 🎯 **Contextual Help** - AI understands your academic history

### For Teachers  
- ⚡ **AI-Assisted Grading** - Automated grading with custom rubrics
- 👥 **Classroom Management** - Student activity monitoring
- 📈 **Analytics Dashboard** - Class performance insights
- 💬 **Enhanced Feedback** - AI-improved student feedback

### System Features
- 🌙 **Dark/Light Theme** - Automatic theme detection
- 📱 **Responsive Design** - Works on all devices
- 🔒 **Secure** - Role-based access and data protection
- 🔗 **Google Docs Integration** - Support for external document links

## 🏗️ Architecture

- **Backend**: Python Flask with modular Blueprint organization
- **AI**: Azure OpenAI integration with context-aware responses
- **Frontend**: Modern HTML/CSS/JS with no framework dependencies
- **Data**: JSON-based storage (easily migrated to database)

## 🛠️ Development

### Project Structure
```
studycoach/
├── app.py              # Main Flask application
├── config.py          # Configuration management  
├── utils/             # Utility modules
├── services/          # Business logic services
├── routes/            # Route handlers (Blueprints)
├── templates/         # Jinja2 HTML templates
├── static/           # CSS, JS, and assets
├── scripts/          # Development and deployment scripts
├── debug/            # Debug utilities and fix scripts
├── tests/            # Unit and integration tests
└── docs/             # Documentation and guides
```

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Add tests for new features

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Azure OpenAI (Required)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Features
ENABLE_AI_GRADING=True
ENABLE_FILE_UPLOADS=True
ENABLE_GOOGLE_DOCS_INTEGRATION=False
```

## 📋 Requirements

- Python 3.8+
- Azure OpenAI API access
- Modern web browser
- 16MB+ available storage for file uploads

## 🚀 Deployment

### Production Setup
```bash
# Set production environment
export FLASK_ENV=production

# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker Deployment
```bash
docker build -t studycoach .
docker run -p 8000:8000 studycoach
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following the code style guidelines
4. Add tests for new functionality
5. Update documentation as needed
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Azure OpenAI for AI capabilities
- Flask community for the excellent web framework
- Contributors and testers who helped improve the platform

## 📞 Support

- **Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md)
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas

---

*Built with ❤️ for educators and students*
