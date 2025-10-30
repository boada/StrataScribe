# New Architecture Structure

This directory contains the refactored StrataScribe application using clean architecture principles.

## Directory Structure

```
app/
├── __init__.py          # Application factory
├── api/                 # Flask routes & request handling
├── core/               # Business logic & domain services
├── services/           # External integrations (Wahapedia API)
├── repositories/       # Data access layer
├── models/            # Data models & domain entities
├── utils/             # Shared utilities
└── config/            # Configuration management
```

## Migration Status

- [x] Directory structure created
- [x] Application factory pattern  
- [x] Configuration management
- [x] Data models
- [x] Test suite
- [ ] Service layer extraction

## Configuration System

The new config system centralizes all hardcoded values:

```python
from app.config import get_config, UNIT_RENAME_MAPPINGS

# Environment-specific settings
config = get_config()  # Gets dev/prod config automatically
upload_folder = config.UPLOAD_FOLDER
supported_files = config.SUPPORTED_EXTENSIONS

# Game constants
unit_mappings = UNIT_RENAME_MAPPINGS
```

### Benefits:
- ✅ Environment-specific settings (dev vs prod)
- ✅ Centralized configuration 
- ✅ Type safety and documentation
- ✅ Easy testing with TestingConfig

## Data Models

Type-safe dataclasses replace error-prone dictionaries:

```python
from app.models import Faction, Unit, Stratagem

# Old: Error-prone dictionaries
faction_dict = {'id': 'SM', 'name': 'Space Marines'}

# New: Type-safe with validation
faction = Faction(id='SM', name='Space Marines')
unit = Unit(id='cap1', name='Captain', faction_id='SM', keywords=['INFANTRY'])
stratagem = Stratagem(id='strat1', name='Test', type='Battle Tactic', ...)
```

### Benefits:
- ✅ Type safety and IDE autocompletion
- ✅ Data validation at creation time
- ✅ Clear property access (no more dict.get() everywhere)
- ✅ Immutable core models (frozen=True)
- ✅ Conversion utilities for external APIs

## Test Suite

Comprehensive test coverage with pytest:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file  
python -m pytest tests/test_models.py -v

# Run with coverage (if installed)
python -m pytest tests/ --cov=app
```

### Test Coverage:
- ✅ **Models**: 18 tests covering validation, immutability, properties
- ✅ **Configuration**: 10 tests covering environment configs, constants  
- ✅ **Application Factory**: 13 tests covering Flask app creation, routing, config integration
- ✅ **Type Safety**: All models are type-checked and validated
- ✅ **Error Handling**: Validation and error cases tested
- ✅ **Integration**: Route testing with real Flask test client

## Application Factory

Modern Flask application factory pattern:

```python
from app import create_app

# Create app for different environments
app = create_app('development')  # Debug mode, longer timeouts
app = create_app('production')   # Optimized for production
app = create_app('testing')      # Fast timeouts, temp directories
```

### New Entry Points:
- **`run.py`**: Development server with auto-config detection
- **`wsgi.py`**: Production WSGI with factory pattern
- **Routes**: Clean blueprint-based routing in `app/api/`

### Benefits:
- ✅ Environment-specific app instances
- ✅ Better testing (can create isolated app instances)
- ✅ Cleaner configuration management
- ✅ Blueprint-based modular routing

## Legacy Files

The original `sublib/` and `main.py` remain functional during migration.