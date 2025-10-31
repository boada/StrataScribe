# StrataScribe

A tool for analyzing Warhammer 40k BattleScribe rosters and showing all applicable stratagems.

## Deployment on Render

### Environment Variables
Set these in your Render environment:
- `SECRET_KEY`: A secure secret key for Flask sessions
- `FLASK_ENV`: Set to `production` (optional, defaults to production)

### Files Used by Render
- `Procfile`: Defines the web service command
- `requirements-prod.txt`: Production Python dependencies  
- `runtime.txt`: Python version (3.12.0)
- `wsgi.py`: WSGI entry point for Gunicorn

### Health Check
The app provides a health check endpoint at `/health` that Render can use for monitoring.

### Architecture
Built with clean architecture patterns:
- **Domain Models**: Core business logic and data structures
- **Services**: Application services for file handling, roster processing, and data access
- **Repositories**: Data access layer for Wahapedia integration
- **API**: Flask routes and request handlers

## Development

### Requirements
- Python 3.12+
- Dependencies in `requirements.txt`

### Running Locally
```bash
python run.py
```

### Testing
```bash
pytest tests/
```