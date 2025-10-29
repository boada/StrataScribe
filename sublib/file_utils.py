"""
File operation utilities for BattleScribe parser.
Handles reading, parsing, and managing battlescribe files.
"""
import os
import zipfile
from datetime import datetime, timedelta
from typing import Dict, Any
import xmltodict

def read_ros_file(file_name: str, battlescribe_folder: str) -> Dict[str, Any]:
    """
    Read and parse a .ros or .rosz battlescribe file.
    
    Args:
        file_name: Name of the file to read
        battlescribe_folder: Path to the battlescribe directory
        
    Returns:
        Parsed roster data from the file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid
    """
    ros_file_name = file_name
    
    try:
        if file_name.endswith(".rosz"):
            print(f"📁 Processing .rosz archive: {file_name}")
            
            # Extract .rosz file (it's a zip archive)
            rosz_path = os.path.join(battlescribe_folder, file_name)
            if not os.path.exists(rosz_path):
                raise FileNotFoundError(f"Archive file not found: {file_name}")
            
            with zipfile.ZipFile(rosz_path, "r") as zip_file:
                file_list = zip_file.namelist()
                ros_files = [f for f in file_list if f.endswith(".ros")]
                
                if not ros_files:
                    raise ValueError(f"No .ros file found in archive: {file_name}")
                
                # Use the first .ros file found
                ros_file_name = ros_files[0]
                print(f"📄 Extracting roster file: {ros_file_name}")
                
                # Extract to battlescribe folder
                zip_file.extract(ros_file_name, battlescribe_folder)
        
        # Parse the .ros file
        return get_dict_from_xml(ros_file_name, battlescribe_folder)
        
    except zipfile.BadZipFile:
        raise ValueError(f"Invalid archive file: {file_name}")
    except Exception as e:
        print(f"❌ Error processing file {file_name}: {e}")
        raise


def get_dict_from_xml(xml_file_name: str, battlescribe_folder: str) -> Dict[str, Any]:
    """
    Convert XML roster file to dictionary format.
    
    Args:
        xml_file_name: Name of the XML file
        battlescribe_folder: Path to the battlescribe directory
        
    Returns:
        Parsed XML data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or has invalid structure
    """
    xml_file_path = os.path.join(battlescribe_folder, xml_file_name)
    
    try:
        if not os.path.exists(xml_file_path):
            raise FileNotFoundError(f"Roster file not found: {xml_file_name}")
        
        if os.path.getsize(xml_file_path) == 0:
            raise ValueError(f"Empty roster file: {xml_file_name}")
        
        with open(xml_file_path, encoding="utf8", errors="replace") as xml_file:
            content = xml_file.read()
            if not content.strip():
                raise ValueError(f"Roster file contains no data: {xml_file_name}")
            
            data_dict = xmltodict.parse(content)
            
            # Validate basic roster structure
            if "roster" not in data_dict:
                raise ValueError(f"Invalid roster structure: missing 'roster' element")
            
            print(f"✅ Successfully parsed roster file: {xml_file_name}")
            return data_dict
            
    except (OSError, IOError) as e:
        print(f"❌ File system error reading {xml_file_name}: {e}")
        raise FileNotFoundError(f"Cannot access file: {xml_file_name}")
    except Exception as e:
        print(f"❌ Error parsing XML file {xml_file_name}: {e}")
        raise ValueError(f"Failed to parse roster file: {xml_file_name}")


def delete_old_files(battlescribe_folder: str) -> int:
    """
    Delete .ros files older than 24 hours to prevent disk space issues.
    
    Args:
        battlescribe_folder: Path to the battlescribe directory
        
    Returns:
        Number of files deleted
    """
    try:
        if not os.path.exists(battlescribe_folder):
            return 0
            
        file_list = os.listdir(battlescribe_folder)
        deleted_count = 0
        
        for single_file in file_list:
            if not single_file.endswith('.ros'):
                continue
                
            single_file_path = os.path.join(battlescribe_folder, single_file)
            
            try:
                creation_time = datetime.fromtimestamp(os.path.getctime(single_file_path))
                file_time_delta = datetime.now() - creation_time
                
                # Delete files older than 24 hours
                if file_time_delta > timedelta(hours=24):
                    os.remove(single_file_path)
                    deleted_count += 1
                    print(f"🗑️ Deleted old roster file: {single_file}")
                    
            except OSError as e:
                print(f"⚠️ Could not process file {single_file}: {e}")
                continue
        
        if deleted_count > 0:
            print(f"🧹 Cleanup completed: {deleted_count} old files deleted")
        
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error during file cleanup: {e}")
        return 0