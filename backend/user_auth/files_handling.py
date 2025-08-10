"""
User and File Data Persistence Module

This module provides utility functions to load and save JSON data files
that store information about users and their uploaded files.

Functions:
----------
- load_json(filename):
    Loads and returns JSON data from the specified file, or returns an empty
    dictionary if the file does not exist.

- save_json(data, filename):
    Saves the given data as formatted JSON into the specified file.

- get_user_files():
    Returns the filenames for the users and uploaded files JSON databases.

Data Files:
-----------
- users_db.json: Stores user information.
- uploaded_files.json: Stores metadata about files uploaded by users.

This module facilitates persistent storage of user and file metadata for
application components that require access to user-related data.
"""

import os
import json
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go up from chroma_store to backend
USERS_FILE= os.path.join(BASE_DIR, "database", "users_db.json")
FILES_FILE= os.path.join(BASE_DIR, "database", "uploaded_files.json")
def load_json(filename):
    """
    Load JSON data from a file.

    Args:
        filename (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON data as a dictionary, or empty dict if file does not exist.
    """
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(data, filename):
    """
    Save data as formatted JSON to a file.

    Args:
        data (dict): Data to be saved.
        filename (str): Path to the JSON file.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_user_files():
    """
    Retrieve the filenames for users and uploaded files JSON databases.

    Returns:
        tuple: (users_filename, uploaded_files_filename)
    """
    return USERS_FILE, FILES_FILE
