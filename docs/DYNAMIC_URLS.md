# Dynamic URL Implementation Summary

This document summarizes the changes made to implement dynamic URL generation throughout the StudyCoach Flask application.

## Changes Made

### 1. Flask App Configuration (app.py)
- Added `PREFERRED_URL_SCHEME = 'https'` for proper external URL generation
- Added optional `SERVER_NAME` configuration from environment variables
- Created helper functions for dynamic URL generation
- Added context processor to make URL helpers available in templates

### 2. Template Updates

#### teacher_main.html
- **BEFORE:** `{{ request.url_root }}classroom/join/{{ class_obj.code }}`
- **AFTER:** `{{ url_for('join_classroom_link', code=class_obj.code, _external=True) }}`

#### ai_assistant.html
Updated all AJAX fetch calls to use url_for():
- `/chat` → `{{ url_for("chat") }}`
- `/save_personality` → `{{ url_for("save_personality") }}`
- `/reset_history` → `{{ url_for("reset_history") }}`
- `/get_personality` → `{{ url_for("get_personality") }}`

### 3. Already Properly Implemented
The following were already using url_for() correctly:
- All form actions in templates
- All navigation links
- Static file references
- Internal page links
- Edit assignment links

### 4. Utility Functions Added

#### generate_url(endpoint, **kwargs)
Helper function for generating URLs programmatically in Python code.

#### regenerate_classroom_urls()
Utility function to update classroom join URLs if stored in database (future-proofing).

### 5. Configuration Files
- Created `.env.example` with SERVER_NAME configuration example
- Updated README.md with configuration documentation

### 6. Debug Endpoint
Added `/debug/urls` endpoint (debug mode only) to test URL generation.

## Benefits

1. **Domain Independence:** App works on any domain without configuration changes
2. **HTTPS Support:** Automatically generates HTTPS URLs when appropriate
3. **Proxy Compatibility:** Works correctly behind reverse proxies
4. **Future-Proof:** Easy to add new URLs without hardcoding
5. **Development Friendly:** Same code works in development and production

## Environment Variables

```bash
# Optional: Set if deploying behind proxy or need specific domain
SERVER_NAME=your-domain.com

# Examples:
SERVER_NAME=studycoach.example.com
SERVER_NAME=localhost:5000  # for local development
```

## URL Examples

With these changes, URLs are generated dynamically:

- **Join Links:** `https://your-domain.com/classroom/join/ABC123`
- **API Endpoints:** `https://your-domain.com/chat`
- **Static Files:** `https://your-domain.com/static/style.css`
- **Navigation:** `https://your-domain.com/student_main`

All URLs automatically adapt to the current domain and protocol.

## Testing

1. Run the app on different domains/ports
2. Check `/debug/urls` endpoint in debug mode
3. Verify join links work correctly
4. Test AJAX calls in AI assistant
5. Confirm all navigation works

## Notes

- No hardcoded domains remain in the codebase
- External services (Google Fonts, Icons8, Azure OpenAI) retain their proper URLs
- All internal links use Flask's url_for() system
- The app is now fully portable between environments
