# data_review_core.py
"""Core logic and utilities for the Book Image Data Review App."""
import os
import json
import copy
import glob
import hashlib
import streamlit as st
from pathlib import Path
from datetime import datetime

# Predefined reviewers and their hashed passwords
REVIEWERS = {
    "Yuqun": hashlib.sha256("DBaudewDwefha122181".encode()).hexdigest(),
    "Yuxuan": hashlib.sha256("Cahewvavhafdis391fd".encode()).hexdigest(),
    "Sijia": hashlib.sha256("Cauifewafsdahf911s".encode()).hexdigest(),
}

# --- Core Data Handling and Utility Functions ---


def init_session_state():
    """Initializes Streamlit session state variables."""
    defaults = {
        "authenticated": True,
        "current_step": 0,
        "json_files": [],
        "json_data": {},
        "main_file_idx": None,
        "link_fields": {},
        "has_images": False,
        "image_config": {},
        "current_index": 0,
        "modified_data": {},
        "output_dir": "",
        "reviewed_files": {},
        "input_mode": None,
        "directory_data": {},
        "current_file_idx": 0,
        "jump_to_index": 0,
        "reviewer": "",
        "current_time": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_json_files(file_paths):
    """Loads JSON data from a list of file paths."""
    json_data = {}
    for i, file_path in enumerate(file_paths):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                json_data[i] = {
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "data": data,
                }
        except Exception as e:
            # Let the calling function handle UI errors
            raise Exception(f"Error loading {file_path}: {str(e)}")
    return json_data


def load_json_directories(directory_paths, directory_types):
    """Loads JSON data from directories based on their type."""
    directory_data = {}
    for i, (dir_path, dir_type) in enumerate(zip(directory_paths, directory_types)):
        try:
            if dir_type == "Book Directory":
                json_files = glob.glob(os.path.join(dir_path, "*.json"))
                dir_data = {}
                for json_file in json_files:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    dir_data[os.path.basename(json_file)] = {
                        "path": json_file,
                        "data": data,
                    }
                directory_data[i] = {
                    "path": dir_path,
                    "type": dir_type,
                    "files": dir_data,
                }

            elif dir_type == "Image Directory":
                book_dirs = [
                    d
                    for d in os.listdir(dir_path)
                    if os.path.isdir(os.path.join(dir_path, d))
                ]
                dir_data = {}
                for book_dir in book_dirs:
                    book_path = os.path.join(dir_path, book_dir)
                    json_files = glob.glob(os.path.join(book_path, "*.json"))
                    for json_file in json_files:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        key = f"{book_dir}/{os.path.basename(json_file)}"
                        dir_data[key] = {"path": json_file, "data": data}
                directory_data[i] = {
                    "path": dir_path,
                    "type": dir_type,
                    "files": dir_data,
                }
        except Exception as e:
            raise Exception(f"Error loading directory {dir_path}: {str(e)}")
    return directory_data


def setup_linking_files(json_data, main_file_idx, selected_main_fields):
    """Sets up linking fields based on user selection for file mode."""
    link_fields = {"main": selected_main_fields}
    main_file_data = json_data[main_file_idx]["data"]

    for i, file_info in json_data.items():
        if i != main_file_idx:
            file_link_fields = {}
            file_data = file_info["data"]
            if file_data:
                file_fields = []
                if isinstance(file_data, list) and len(file_data) > 0:
                    file_fields = list(file_data[0].keys())
                elif isinstance(file_data, dict):
                    file_fields = list(file_data.keys())

                for main_field in selected_main_fields:
                    # This part needs user interaction, so we return the options
                    # The UI part will handle the selection and store results
                    if main_field in file_fields:
                        file_link_fields[main_field] = (
                            None  # Placeholder, needs selection
                        )
            link_fields[i] = file_link_fields
    return link_fields


def setup_linking_directories(directory_data, main_dir_idx, selected_main_fields):
    """Sets up linking fields based on user selection for directory mode."""
    link_fields = {"main": selected_main_fields}
    main_dir_info = directory_data[main_dir_idx]

    if main_dir_info["files"]:
        sample_key = list(main_dir_info["files"].keys())[0]
        sample_data = main_dir_info["files"][sample_key]["data"]

        for i, dir_info in directory_data.items():
            if i != main_dir_idx:
                dir_link_fields = {}
                if dir_info["files"]:
                    sample_key = list(dir_info["files"].keys())[0]
                    sample_data = dir_info["files"][sample_key]["data"]
                    dir_fields = []
                    if isinstance(sample_data, list) and len(sample_data) > 0:
                        dir_fields = list(sample_data[0].keys())
                    elif isinstance(sample_data, dict):
                        dir_fields = list(sample_data.keys())

                    for main_field in selected_main_fields:
                        if main_field in dir_fields:
                            dir_link_fields[main_field] = None  # Placeholder
                link_fields[i] = dir_link_fields
    return link_fields


def find_matching_records(main_record, json_data, link_fields, main_file_idx):
    """Finds records in other JSON files matching the main record based on link fields."""
    matches = {}
    for file_idx, file_info in json_data.items():
        if file_idx == main_file_idx:
            continue
        if file_idx in link_fields:
            file_link_fields = link_fields[file_idx]
            matches[file_idx] = []
            file_data = file_info["data"]
            if isinstance(file_data, list):
                for record in file_data:
                    match_found = True
                    for main_field, file_field in file_link_fields.items():
                        if main_field in main_record and file_field in record:
                            if str(main_record[main_field]) != str(record[file_field]):
                                match_found = False
                                break
                    if match_found:
                        matches[file_idx].append(record)
            elif isinstance(file_data, dict):
                match_found = True
                for main_field, file_field in file_link_fields.items():
                    if main_field in main_record and file_field in file_data:
                        if str(main_record[main_field]) != str(file_data[file_field]):
                            match_found = False
                            break
                if match_found:
                    matches[file_idx].append(file_data)
    return matches


def find_matching_directory_records(
    main_record, main_file_path, directory_data, link_fields, main_dir_idx
):
    """Finds records in other directories matching the main record based on link fields."""
    matches = {}
    main_dir_info = directory_data[main_dir_idx]
    if main_dir_info["type"] == "Image Directory":
        book_id = os.path.dirname(main_file_path)
        image_id = os.path.basename(main_file_path).replace(".json", "")
    else:
        book_id = os.path.basename(main_file_path).replace(".json", "")
        image_id = None

    for dir_idx, dir_info in directory_data.items():
        if dir_idx == main_dir_idx:
            continue
        if dir_idx in link_fields:
            dir_link_fields = link_fields[dir_idx]
            matches[dir_idx] = []

            if dir_info["type"] == "Book Directory":
                matching_file = f"{book_id}.json"
                if matching_file in dir_info["files"]:
                    file_data = dir_info["files"][matching_file]["data"]
                    if isinstance(file_data, list):
                        for record in file_data:
                            match_found = True
                            for main_field, dir_field in dir_link_fields.items():
                                if main_field in main_record and dir_field in record:
                                    if str(main_record[main_field]) != str(
                                        record[dir_field]
                                    ):
                                        match_found = False
                                        break
                            if match_found:
                                matches[dir_idx].append(record)
                    elif isinstance(file_data, dict):
                        match_found = True
                        for main_field, dir_field in dir_link_fields.items():
                            if main_field in main_record and dir_field in file_data:
                                if str(main_record[main_field]) != str(
                                    file_data[dir_field]
                                ):
                                    match_found = False
                                    break
                        if match_found:
                            matches[dir_idx].append(file_data)

            elif dir_info["type"] == "Image Directory":
                if book_id in [os.path.dirname(f) for f in dir_info["files"].keys()]:
                    matching_file = f"{book_id}/{image_id}.json"
                    if matching_file in dir_info["files"]:
                        file_data = dir_info["files"][matching_file]["data"]
                        if isinstance(file_data, list):
                            for record in file_data:
                                match_found = True
                                for main_field, dir_field in dir_link_fields.items():
                                    if (
                                        main_field in main_record
                                        and dir_field in record
                                    ):
                                        if str(main_record[main_field]) != str(
                                            record[dir_field]
                                        ):
                                            match_found = False
                                            break
                                if match_found:
                                    matches[dir_idx].append(record)
                        elif isinstance(file_data, dict):
                            match_found = True
                            for main_field, dir_field in dir_link_fields.items():
                                if main_field in main_record and dir_field in file_data:
                                    if str(main_record[main_field]) != str(
                                        file_data[dir_field]
                                    ):
                                        match_found = False
                                        break
                            if match_found:
                                matches[dir_idx].append(file_data)
    return matches


def construct_image_path(record, image_config):
    """Constructs the full path to an image based on record data and config."""
    if (
        image_config.get("book_id_field") in record
        and image_config.get("image_id_field") in record
    ):
        book_id = str(record[image_config["book_id_field"]]).zfill(6)
        image_id = str(record[image_config["image_id_field"]]).zfill(6)
        if not image_id.endswith((".jpg", ".png", ".jpeg")):  # Basic check
            image_id += ".jpg"
        image_path = os.path.join(image_config["base_path"], book_id, image_id)
        return image_path
    return None


def get_reviewed_path_directory(original_path, output_dir, main_dir_path):
    """Calculates the path for the reviewed file in directory mode."""
    # print(f"original_path: {original_path}")
    # print(f"main_dir_path: {main_dir_path}")
    # print(
    #     f"rel_path: {os.path.relpath(original_path, main_dir_path)}"
    # )  
    rel_path = os.path.relpath(original_path, main_dir_path)
    reviewed_path = os.path.join(output_dir, rel_path)
    # print(f"reviewed_path: {reviewed_path}")
    os.makedirs(os.path.dirname(reviewed_path), exist_ok=True)
    return reviewed_path


def save_current_review_file(
    output_dir,
    reviewer,
    main_file_idx,
    json_data,
    reviewed_files,
    modified_data,
    current_index,
):
    """Saves the current review state for file mode."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().isoformat()
    main_file_info = json_data[main_file_idx]
    reviewed_filename = f"{Path(main_file_info['path']).stem}_reviewed.json"
    reviewed_path = os.path.join(output_dir, reviewed_filename)

    if main_file_idx not in reviewed_files:
        reviewed_files[main_file_idx] = []

    main_file_data = json_data[main_file_idx]["data"]
    reviewed_record = copy.deepcopy(modified_data.get("main", {}))
    reviewed_record["review_info"] = {
        "reviewer": reviewer,
        "timestamp": timestamp,
        "original_index": current_index,
    }

    if isinstance(main_file_data, list):
        if current_index < len(reviewed_files[main_file_idx]):
            reviewed_files[main_file_idx][current_index] = reviewed_record
        else:
            reviewed_files[main_file_idx].append(reviewed_record)
    elif isinstance(main_file_data, dict):
        reviewed_files[main_file_idx] = reviewed_record

    with open(reviewed_path, "w", encoding="utf-8") as f:
        json.dump(reviewed_files[main_file_idx], f, indent=2, ensure_ascii=False)

    for file_idx, modified_records in modified_data.items():
        if file_idx != "main" and file_idx in json_data:
            file_info = json_data[file_idx]
            reviewed_filename = f"{Path(file_info['path']).stem}_reviewed.json"
            reviewed_path = os.path.join(output_dir, reviewed_filename)

            if file_idx not in reviewed_files:
                reviewed_files[file_idx] = []

            for record_idx, modified_record in modified_records.items():
                reviewed_record = copy.deepcopy(modified_record)
                reviewed_record["review_info"] = {
                    "reviewer": reviewer,
                    "timestamp": timestamp,
                    "original_index": current_index,
                }
                file_data = json_data[file_idx]["data"]
                if isinstance(file_data, list):
                    if record_idx < len(reviewed_files[file_idx]):
                        reviewed_files[file_idx][record_idx] = reviewed_record
                    else:
                        reviewed_files[file_idx].append(reviewed_record)
                elif isinstance(file_data, dict):
                    reviewed_files[file_idx] = reviewed_record

            with open(reviewed_path, "w", encoding="utf-8") as f:
                json.dump(reviewed_files[file_idx], f, indent=2, ensure_ascii=False)


def save_current_review_directory(
    current_file_key,
    output_dir,
    reviewer,
    main_dir_idx,
    directory_data,
    reviewed_files,
    current_index,
):
    """Saves the current review state for directory mode."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().isoformat()
    main_dir_info = directory_data[main_dir_idx]
    current_file_info = main_dir_info["files"][current_file_key]
    main_dir_path = main_dir_info["path"]
    reviewed_path = get_reviewed_path_directory(
        current_file_info["path"], output_dir, main_dir_path
    )

    # Get the current reviewed data or initialize if not exists
    if current_file_key not in reviewed_files:
        # Initialize with a copy of original data
        original_data = current_file_info["data"]
        if isinstance(original_data, list):
            reviewed_files[current_file_key] = copy.deepcopy(original_data)
        else:
            reviewed_files[current_file_key] = copy.deepcopy(original_data)

    reviewed_data = reviewed_files[current_file_key]

    # Update with modified data
    if (
        "main" in st.session_state.modified_data
        and st.session_state.modified_data["main"]
    ):
        if isinstance(reviewed_data, list):
            # Ensure we have enough records
            while current_index >= len(reviewed_data):
                reviewed_data.append({})

            # Update the specific record
            reviewed_data[current_index] = copy.deepcopy(
                st.session_state.modified_data["main"]
            )
            # Add review metadata
            reviewed_data[current_index]["review_info"] = {
                "reviewer": reviewer,
                "timestamp": timestamp,
                "original_index": current_index,
            }
        else:  # dict
            reviewed_data.update(copy.deepcopy(st.session_state.modified_data["main"]))
            reviewed_data["review_info"] = {
                "reviewer": reviewer,
                "timestamp": timestamp,
            }

    # Save the updated data
    with open(reviewed_path, "w", encoding="utf-8") as f:
        json.dump(reviewed_data, f, indent=2, ensure_ascii=False)
