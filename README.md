# Hackathon-Project

## Configuration

This application uses dynamic URLs that adapt to your domain automatically. All classroom and assignment links use Flask's `url_for()` to generate proper URLs.

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-azure-openai-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here

# Flask Configuration (optional)
# Set this if you need to generate absolute URLs outside of request context
# or if your app is running behind a proxy with a different domain
SERVER_NAME=your-domain.com
```

### URL Generation

The application automatically generates proper URLs for:
- Classroom join links
- Assignment edit links
- API endpoints
- Static files
- All internal navigation

No hardcoded domains are used, ensuring the app works on any domain.

## Features

_**Feature ideas:​**_

1. **AI follows teachers rubric.**

1. **Ability to search for specific topics​.**

1. **Ability to message teachers.**

1. **Teacher notes uploaded to the website.​**

1. **Generated study guide/flash cards/notes based off of teacher impute.**

1. **The Ability to aid students in understanding homework.**

1. **Aid Students with different learning disabilitys, ADHD Dislexia ect.**

1. **Ability to help those with different learning styles.​**

(side note: make sure to fact check AI when gathering information)
