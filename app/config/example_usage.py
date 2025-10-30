"""
Example of using the new configuration system.

This shows how the old hardcoded values are now accessed through config classes.
"""
from app.config import get_config, UNIT_RENAME_MAPPINGS

def example_usage():
    """Demonstrate the new configuration system."""
    
    # Get configuration for current environment
    config = get_config()
    
    # OLD WAY (scattered throughout codebase):
    # FILE_EXT_ROS = ".ros"
    # upload_directory = os.path.abspath("./battlescribe")
    # WAHAPEDIA_URL = "https://wahapedia.ru/wh40k10ed/"
    
    # NEW WAY (centralized and environment-aware):
    supported_extensions = config.SUPPORTED_EXTENSIONS  # {'.ros', '.rosz'}
    upload_folder = config.UPLOAD_FOLDER              # ./battlescribe 
    wahapedia_url = config.WAHAPEDIA_BASE_URL         # https://wahapedia.ru/wh40k10ed/
    
    # Game constants are imported directly
    unit_mappings = UNIT_RENAME_MAPPINGS
    
    print(f"Upload folder: {upload_folder}")
    print(f"Supported extensions: {supported_extensions}")
    print(f"Wahapedia URL: {wahapedia_url}")
    print(f"Debug mode: {config.DEBUG}")
    print(f"Request timeout: {config.REQUEST_TIMEOUT}")
    
    # Different environments get different settings
    dev_config = get_config('development')
    prod_config = get_config('production')
    
    print(f"Dev timeout: {dev_config.REQUEST_TIMEOUT}")    # 60 seconds
    print(f"Prod timeout: {prod_config.REQUEST_TIMEOUT}")  # 15 seconds

if __name__ == "__main__":
    example_usage()