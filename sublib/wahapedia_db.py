import csv
import json
import os
import time
from datetime import datetime, timedelta

import requests

# URLs and File Names
WAHAPEDIA_URL = "https://wahapedia.ru/wh40k10ed/"
CSV_DATASHEETS = "Datasheets.csv"
CSV_DATASHEETS_STRATAGEMS = "Datasheets_stratagems.csv"
CSV_DETACHMENT_ABILITIES = "Detachment_abilities.csv"
CSV_FACTIONS = "Factions.csv"
CSV_STRATAGEM_PHASES = "StratagemPhases.csv"
CSV_STRATAGEMS = "Stratagems.csv"
CSV_LAST_UPDATE = "Last_update.csv"
JSON_FILE_LIST = "_file_list.json"

# URL for the Wahapedia website
wahapedia_url = WAHAPEDIA_URL

# List of all CSV files to be downloaded from the website
wahapedia_csv_list = [
    CSV_DATASHEETS,
    CSV_DATASHEETS_STRATAGEMS,
    CSV_DETACHMENT_ABILITIES,
    CSV_FACTIONS,
    CSV_STRATAGEM_PHASES,
    CSV_STRATAGEMS,
    CSV_LAST_UPDATE,
]

# Path to the local directory where the CSV files will be saved
wahapedia_path = os.path.abspath("./wahapedia")

# Path to the file that keeps track of the last time the CSV files were updated
file_list_path = os.path.abspath(os.path.join(wahapedia_path, JSON_FILE_LIST))


def init_db():
    """
    Initializes the local database by checking if the CSV files need to be updated.
    If the local directory or the file list do not exist, they will be created.
    If a CSV file does not exist or is older than 1 day, it will be downloaded from the website.
    :return: True if any of the CSV files were updated, False otherwise
    """
    check_csv_update = False
    if not os.path.exists(wahapedia_path):
        os.mkdir(wahapedia_path)
        _create_file_list()

    if _wahapedia_has_update():
        for wahapedia_csv in wahapedia_csv_list:
            check_result = _check_csv(wahapedia_csv)
            if check_result is True:
                check_csv_update = True

    return check_csv_update


def _wahapedia_has_update():
    """
    Checks if the Wahapedia website has any new updates by comparing the last_update field from the Last_update.csv file.
    If the file does not exist or the last_update field has changed, it will download the file.
    :return: True if the website has new updates, False otherwise
    """
    last_update_path = os.path.join(wahapedia_path, CSV_LAST_UPDATE)

    if not os.path.exists(last_update_path):
        print("Initializing Wahapedia database...")
        return True

    last_update_dict_old = get_dict_from_csv(last_update_path)
    _check_csv("Last_update.csv")
    last_update_dict_new = get_dict_from_csv(last_update_path)

    if (last_update_dict_old[0]["last_update"]) != (
        last_update_dict_new[0]["last_update"]
    ):
        print("Updating Wahapedia database...")
        return True
    return False


def _check_csv(csv_name):
    """
        Checks if the specified CSV file needs to be updated by comparing its last update time with the file list.
        If the file does not exist or is older than 1 day, it will be downloaded from the website and the file list will be updated.
    :param csv_name: the name of the CSV file to be checked
    :return: True if the file was updated, False otherwise
    """

    csv_updated = False
    if not (
        os.path.exists(os.path.join(wahapedia_path, csv_name))
        and _check_file_list(csv_name)
    ):
        print(f"Updating {csv_name}...")
        csv_path = _download_file(wahapedia_url + csv_name, wahapedia_path)
        _register_file_list(csv_name)
        print(f"Updated {csv_name} successfully")
        csv_updated = True

    return csv_updated


def _check_file_list(csv_name):
    """
    Checks if the specified CSV file is in the file list and if it was updated in the last 1 day.
    If the file list does not exist, it will be created.
    :param csv_name: the name of the CSV file to be checked
    :return: True if the file is in the file list and was updated in the last 1 day, False otherwise
    """
    if not os.path.exists(file_list_path):
        _create_file_list()

    with open(file_list_path, "r") as fl:
        current_file_list_json = json.load(fl)

    if csv_name in current_file_list_json:
        csv_time_delta = datetime.now() - datetime.fromisoformat(
            current_file_list_json[csv_name]
        )
        if csv_time_delta > timedelta(days=1):
            return False
        return True


def _create_file_list():
    """
    Creates the file list with the current time for all the CSV files in the wahapedia_csv_list.
    """
    empty_file_list = {}
    with open(file_list_path, "w") as fl:
        for wahapedia_csv in wahapedia_csv_list:
            empty_file_list[wahapedia_csv] = datetime.min.isoformat()
        json.dump(empty_file_list, fl)


def _register_file_list(csv_path):
    """
    Registers the specified CSV file in the file list with the current time.
    :param csv_path: the path of the CSV file to be registered
    """
    with open(file_list_path, "r") as fl:
        current_file_list_json = json.load(fl)

    current_file_list_json[csv_path] = str(datetime.now().isoformat())

    with open(file_list_path, "w") as fl:
        json.dump(current_file_list_json, fl)


def _download_file(file_url, folder_name):
    """
    Downloads a file from a specified url and saves it to a specified folder.
    :param file_url: the url of the file to be downloaded
    :param folder_name: the folder where the file will be saved
    :return: the path where the file was saved
    """
    file_name = file_url.split("/")[-1]
    save_path = os.path.abspath(os.path.join(folder_name, file_name))

    file_downloaded = False

    # Keep trying to download the file until it is successfully downloaded
    max_retries = 5
    retry_count = 0
    
    while not file_downloaded and retry_count < max_retries:
        try:
            get_response = requests.get(file_url, stream=True, timeout=30)
            get_response.raise_for_status()  # Raise an exception for bad status codes
            
            # Open the file and write the content in chunks
            with open(save_path, "wb") as f:
                for chunk in get_response.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            
            file_size = os.stat(save_path).st_size
            # Check if the file size is smaller than 2048 bytes, which could indicate that anti-spam is working
            if file_size < 2048 and _is_html(save_path):
                print("Rate limited. Waiting 5 seconds before retry...")
                time.sleep(5)
                retry_count += 1
            else:
                file_downloaded = True
                
        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise ConnectionError(f"Failed to download {file_name} after {max_retries} attempts: {e}")
            print(f"Download attempt {retry_count} failed, retrying in 3 seconds...")
            time.sleep(3)
        except (OSError, IOError) as e:
            raise IOError(f"Failed to save file {file_name}: {e}")
    
    if not file_downloaded:
        raise ConnectionError(f"Failed to download {file_name}: Maximum retry attempts exceeded")

    return save_path


def _is_html(file_path):
    html_string = "<!DOCTYPE html>"
    with open(file_path, "r", encoding="ascii", errors="ignore") as f:
        content = f.read()
        return html_string in content


def get_dict_from_csv(csv_path):
    """
    Converts a CSV file to a list of dictionaries.
    Strips out any trailing empty columns caused by malformed delimiters.

    :param csv_path: the path of the CSV file to be converted
    :return: a list of cleaned dictionaries
    """
    results = []
    csv_file_path = os.path.abspath(os.path.join(wahapedia_path, csv_path))
    with open(csv_file_path, "r", encoding="ascii", errors="ignore") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="|", quoting=csv.QUOTE_NONE)
        for row in reader:
            # Remove any keys that are empty strings
            clean_row = {k: v for k, v in row.items() if k.strip() != ""}
            results.append(clean_row)

    return results
