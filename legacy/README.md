# Legacy Code

This folder contains the original StrataScribe implementation that was replaced by the new clean architecture.

## Files

- **`main.py`**: Original Flask application entry point
- **`run_new_app.py`**: Temporary file used during migration (can be deleted)
- **`sublib/`**: Legacy parsing and processing modules
  - `battle_parse.py`: Original BattleScribe parsing logic
  - `wahapedia_db.py`: Legacy Wahapedia data access
  - `prepare_html.py`: HTML template generation (still used by new app)
  - `faction_utils.py`: Faction mapping utilities
  - `file_utils.py`: File handling utilities
  - `wh40k_lists.py`: Game data constants
  - `stratagems/`: Stratagem filtering and utilities

## Status

- **Replaced**: Most functionality has been replaced by the new clean architecture
- **Still Used**: `prepare_html.py` is still imported by the new app for HTML generation
- **Future**: The HTML generation should be modernized to use proper templates or components

## Migration Notes

The new architecture provides the same functionality with:
- Better separation of concerns
- Type safety with dataclasses
- Comprehensive test coverage
- Proper dependency injection
- Cleaner error handling
- Configuration management