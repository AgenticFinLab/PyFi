# data_review_app.py
"""Streamlit application for reviewing book image data."""
import os
import json
import time
import copy
import hashlib
import streamlit as st
from pathlib import Path

# Assuming data_review_core.py is in the same directory or properly installed/importable
import fttracer.data_review.data_review_core as core

# --- Streamlit UI Components (Layout and Structure) ---


# Password hashing for security (could also be in core)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Authentication component
def authentication_component():
    st.header("Authentication")
    reviewer = st.selectbox("Select reviewer name", list(core.REVIEWERS.keys()))
    password = st.text_input("Enter password", type="password")
    if st.button("Authenticate"):
        if hash_password(password) == core.REVIEWERS[reviewer]:
            st.session_state.authenticated = True
            st.session_state.reviewer = reviewer
            st.success("Authentication successful!")
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")


# Display JSON file fields
def display_json_fields(json_data):
    for i, file_info in json_data.items():
        st.subheader(f"File: {file_info['filename']}")
        if file_info["data"]:
            if isinstance(file_info["data"], list) and len(file_info["data"]) > 0:
                sample_item = file_info["data"][0]
                st.write("Fields:", list(sample_item.keys()))
                st.json(sample_item)
            elif isinstance(file_info["data"], dict):
                st.write("Fields:", list(file_info["data"].keys()))
                st.json(file_info["data"])
            else:
                st.warning("This file contains no valid data")
        else:
            st.warning("This file contains no data")


# Display directory structure and fields
def display_directory_fields(directory_data):
    for i, dir_info in directory_data.items():
        st.subheader(f"Directory: {dir_info['path']} ({dir_info['type']})")
        if dir_info["files"]:
            sample_key = list(dir_info["files"].keys())[0]
            sample_file = dir_info["files"][sample_key]
            st.write(f"Sample file: {sample_key}")
            if sample_file["data"]:
                if (
                    isinstance(sample_file["data"], list)
                    and len(sample_file["data"]) > 0
                ):
                    sample_item = sample_file["data"][0]
                    st.write("Fields:", list(sample_item.keys()))
                    st.json(sample_item)
                elif isinstance(sample_file["data"], dict):
                    st.write("Fields:", list(sample_file["data"].keys()))
                    st.json(sample_file["data"])
                else:
                    st.warning("This file contains no valid data")
            else:
                st.warning("This file contains no data")
        else:
            st.warning("This directory contains no JSON files")


# Setup linking fields UI (File Mode)
def setup_linking_files_ui(json_data):
    st.subheader("Select Main JSON File")
    file_options = [f["filename"] for f in json_data.values()]
    main_file_idx = st.selectbox(
        "Select the main JSON file (data will be traversed based on this file)",
        range(len(file_options)),
        format_func=lambda x: file_options[x],
    )
    link_fields = {}
    main_file_data = json_data[main_file_idx]["data"]
    main_fields = []
    if isinstance(main_file_data, list) and len(main_file_data) > 0:
        main_fields = list(main_file_data[0].keys())
    elif isinstance(main_file_data, dict):
        main_fields = list(main_file_data.keys())
    if main_fields:
        st.write("Available fields in main file:", main_fields)
        selected_main_fields = st.multiselect(
            "Select linking fields from the main file", main_fields
        )
        if selected_main_fields:
            link_fields["main"] = selected_main_fields
            for i, file_info in json_data.items():
                if i != main_file_idx:
                    st.subheader(f"Linking fields for {file_info['filename']}")
                    if file_info["data"]:
                        file_fields = []
                        if (
                            isinstance(file_info["data"], list)
                            and len(file_info["data"]) > 0
                        ):
                            file_fields = list(file_info["data"][0].keys())
                        elif isinstance(file_info["data"], dict):
                            file_fields = list(file_info["data"].keys())
                        if file_fields:
                            file_link_fields = {}
                            for main_field in selected_main_fields:
                                # Key is crucial for uniqueness
                                corresponding_field = st.selectbox(
                                    f"Select field in {file_info['filename']} corresponding to '{main_field}'",
                                    ["None"] + file_fields,
                                    key=f"link_{i}_{main_field}",
                                )
                                if corresponding_field != "None":
                                    file_link_fields[main_field] = corresponding_field
                            if file_link_fields:
                                link_fields[i] = file_link_fields
                        else:
                            st.warning(
                                f"{file_info['filename']} contains no valid data"
                            )
                    else:
                        st.warning(f"{file_info['filename']} contains no data")
    return main_file_idx, link_fields


# Setup linking fields UI (Directory Mode)
def setup_linking_directories_ui(directory_data):
    st.subheader("Select Main Directory")
    main_dir_options = []
    for i, dir_info in directory_data.items():
        if dir_info["type"] == "Image Directory" or (
            dir_info["type"] == "Book Directory"
            and not any(d["type"] == "Image Directory" for d in directory_data.values())
        ):
            main_dir_options.append(i)
    if not main_dir_options:
        st.error(
            "No suitable main directory found. Please add an Image Directory or Book Directory."
        )
        return None, None
    main_dir_idx = st.selectbox(
        "Select the main directory",
        main_dir_options,
        format_func=lambda x: f"{directory_data[x]['path']} ({directory_data[x]['type']})",
    )
    link_fields = {}
    main_dir_info = directory_data[main_dir_idx]
    if main_dir_info["files"]:
        sample_key = list(main_dir_info["files"].keys())[0]
        sample_data = main_dir_info["files"][sample_key]["data"]
        main_fields = []
        if isinstance(sample_data, list) and len(sample_data) > 0:
            main_fields = list(sample_data[0].keys())
        elif isinstance(sample_data, dict):
            main_fields = list(sample_data.keys())
        if main_fields:
            st.write("Available fields in main directory:", main_fields)
            selected_main_fields = st.multiselect(
                "Select linking fields from the main directory", main_fields
            )
            if selected_main_fields:
                link_fields["main"] = selected_main_fields
                for i, dir_info in directory_data.items():
                    if i != main_dir_idx:
                        st.subheader(
                            f"Linking fields for {dir_info['path']} ({dir_info['type']})"
                        )
                        if dir_info["files"]:
                            sample_key = list(dir_info["files"].keys())[0]
                            sample_data = dir_info["files"][sample_key]["data"]
                            dir_fields = []
                            if isinstance(sample_data, list) and len(sample_data) > 0:
                                dir_fields = list(sample_data[0].keys())
                            elif isinstance(sample_data, dict):
                                dir_fields = list(sample_data.keys())
                            if dir_fields:
                                dir_link_fields = {}
                                for main_field in selected_main_fields:
                                    # Key is crucial for uniqueness
                                    corresponding_field = st.selectbox(
                                        f"Select field in {dir_info['path']} corresponding to '{main_field}'",
                                        ["None"] + dir_fields,
                                        key=f"link_{i}_{main_field}",
                                    )
                                    if corresponding_field != "None":
                                        dir_link_fields[main_field] = (
                                            corresponding_field
                                        )
                                if dir_link_fields:
                                    link_fields[i] = dir_link_fields
                            else:
                                st.warning(f"{dir_info['path']} contains no valid data")
    return main_dir_idx, link_fields


# Setup image configuration UI
def setup_image_configuration_ui(json_data=None, directory_data=None):
    st.subheader("Image Configuration")
    has_images = st.radio("Does the data contain images?", ("Yes", "No"))
    if has_images == "Yes":
        image_config = {}
        image_config["base_path"] = st.text_input("Enter the base image path")
        if json_data:
            file_options = [f["filename"] for f in json_data.values()]
            file_with_ids_idx = st.selectbox(
                "Select the file containing book and image ID fields",
                range(len(file_options)),
                format_func=lambda x: file_options[x],
            )
            if json_data[file_with_ids_idx]["data"]:
                fields = []
                if (
                    isinstance(json_data[file_with_ids_idx]["data"], list)
                    and len(json_data[file_with_ids_idx]["data"]) > 0
                ):
                    fields = list(json_data[file_with_ids_idx]["data"][0].keys())
                elif isinstance(json_data[file_with_ids_idx]["data"], dict):
                    fields = list(json_data[file_with_ids_idx]["data"].keys())
                if fields:
                    image_config["book_id_field"] = st.selectbox(
                        "Select the book ID field", fields
                    )
                    image_config["image_id_field"] = st.selectbox(
                        "Select the image ID field", fields
                    )
                else:
                    st.warning("Selected file contains no valid data")
            else:
                st.warning("Selected file contains no data")
        elif directory_data:
            dir_options = []
            for i, dir_info in directory_data.items():
                dir_options.append((i, f"{dir_info['path']} ({dir_info['type']})"))
            dir_with_ids_idx = st.selectbox(
                "Select the directory containing book and image ID fields",
                range(len(dir_options)),
                format_func=lambda x: dir_options[x][1],
            )
            dir_info = directory_data[dir_with_ids_idx]
            if dir_info["files"]:
                sample_key = list(dir_info["files"].keys())[0]
                sample_data = dir_info["files"][sample_key]["data"]
                fields = []
                if isinstance(sample_data, list) and len(sample_data) > 0:
                    fields = list(sample_data[0].keys())
                elif isinstance(sample_data, dict):
                    fields = list(sample_data.keys())
                if fields:
                    image_config["book_id_field"] = st.selectbox(
                        "Select the book ID field", fields
                    )
                    image_config["image_id_field"] = st.selectbox(
                        "Select the image ID field", fields
                    )
                else:
                    st.warning("Selected directory contains no valid data")
        return True, image_config
    else:
        return False, {}


# Jump to specific record UI (File Mode)
def jump_to_specific_record_file_mode_ui(main_file_idx, json_data):
    st.subheader("Jump to Specific Record")
    main_file_data = json_data[main_file_idx]["data"]
    num_records = 0
    if isinstance(main_file_data, list):
        num_records = len(main_file_data)
    elif isinstance(main_file_data, dict):
        num_records = 1
    if num_records > 0:
        record_index = st.number_input(
            "Record index (0-based)",
            min_value=0,
            max_value=max(0, num_records - 1),
            value=st.session_state.current_index,
            key="jump_index_input",
        )
        if st.button("Jump to Record"):
            if (time.time() - st.session_state.current_time) <= 2:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()
                st.session_state.current_index = record_index
                st.rerun()
    else:
        st.warning("No records available in the main file")


# Jump to specific file and record UI (Directory Mode)
def jump_to_specific_file_directory_mode_ui(main_dir_idx, directory_data):
    st.subheader("Jump to Specific File and Record")
    main_dir_info = directory_data[main_dir_idx]
    file_options = list(main_dir_info["files"].keys())
    if file_options:
        selected_file_idx = st.selectbox(
            "Select file to jump to",
            range(len(file_options)),
            format_func=lambda x: file_options[x],
            index=st.session_state.current_file_idx,
            key="jump_file_select",
        )
        selected_file_key = file_options[selected_file_idx]
        file_data = main_dir_info["files"][selected_file_key]["data"]
        num_records = 0
        if isinstance(file_data, list):
            num_records = len(file_data)
        elif isinstance(file_data, dict):
            num_records = 1

        if st.session_state.current_index > (num_records - 1):
            here_value = 0
        else:
            here_value = st.session_state.current_index

        record_index = st.number_input(
            "Record index (0-based)",
            min_value=0,
            max_value=max(0, num_records - 1),
            value=here_value,
            key="jump_index_input",
        )
        if st.button("Jump to Selected File and Record"):
            st.session_state.current_file_idx = selected_file_idx
            st.session_state.current_index = record_index
            st.rerun()
    else:
        st.warning("No files available in the main directory")


def display_record_data(
    main_record, matching_records, context="full", record_index=None, file_key=None
):
    """
    Displays record data dynamically based on context.
    Args:
        main_record (dict): The main record data to display.
        matching_records (dict): Dictionary of matching records.
        context (str): 'image_column' to show only image-related fields,
                       'full' (default) to show all data.
        record_index (int): The index of the current record for unique key generation.
        file_key (str): The key of the current file for unique key generation.
    """
    # --- Dynamic Layout Handling based on context ---
    if (
        context == "image_column"
        and st.session_state.get("has_images", False)
        and st.session_state.get("image_config")
    ):
        # --- Display ONLY image-related fields (e.g., in col2) ---
        image_config = st.session_state.image_config
        image_related_keys = {
            image_config.get("book_id_field"),
            image_config.get("image_id_field"),
        }
        image_related_keys.discard(None)

        st.subheader("Image-Related Fields")
        edited_main_img = {}
        for key in image_related_keys:
            if key in main_record:
                value = main_record[key]
                # Use unique key with record index and file key
                unique_parent_key = (
                    f"main_img_{file_key}_{record_index}"
                    if file_key
                    else f"main_img_{record_index}"
                )
                edited_main_img[key] = display_edit_field(
                    key, value, parent_key=unique_parent_key
                )

        # Store edits for image-related fields
        if "main" not in st.session_state.modified_data:
            st.session_state.modified_data["main"] = {}
        st.session_state.modified_data["main"].update(edited_main_img)

    else:  # context == "full" or no image config
        # --- Display ALL data in a single column (e.g., below the two-column section or when no images) ---
        if (
            context == "full"
            and st.session_state.get("has_images", False)
            and st.session_state.get("image_config")
        ):
            # If full display is requested AND images are configured,
            # we display the *non-image* fields of the main record first.
            image_config = st.session_state.image_config
            image_related_keys = {
                image_config.get("book_id_field"),
                image_config.get("image_id_field"),
            }
            image_related_keys.discard(None)
            non_image_data = {
                k: v for k, v in main_record.items() if k not in image_related_keys
            }

            if non_image_data:  # Only display if there are non-image fields
                st.subheader("Main Record Data (Other Fields)")
                edited_main_other = {}
                for key, value in non_image_data.items():
                    # Use unique key with record index and file key
                    unique_parent_key = (
                        f"main_other_{file_key}_{record_index}"
                        if file_key
                        else f"main_other_{record_index}"
                    )
                    edited_main_other[key] = display_edit_field(
                        key, value, parent_key=unique_parent_key
                    )
                # Store edits for non-image fields
                st.session_state.modified_data["main"].update(edited_main_other)

        else:
            # If no images configured, or context is explicitly 'full' without image logic,
            # display the entire main record.
            st.subheader("Main Record Data")
            edited_main_all = {}
            for key, value in main_record.items():
                # Use unique key with record index and file key
                unique_parent_key = (
                    f"main_{file_key}_{record_index}"
                    if file_key
                    else f"main_{record_index}"
                )
                edited_main_all[key] = display_edit_field(
                    key, value, parent_key=unique_parent_key
                )
            st.session_state.modified_data["main"] = edited_main_all

        # --- Always display matching records below main record data ---
        for source_idx, records in matching_records.items():
            if records:
                if st.session_state.input_mode == "file":
                    source_name = st.session_state.json_data[source_idx]["filename"]
                else:  # directory mode
                    source_name = f"{st.session_state.directory_data[source_idx]['path']} ({st.session_state.directory_data[source_idx]['type']})"
                st.subheader(f"Data from {source_name}")

                if source_idx not in st.session_state.modified_data:
                    st.session_state.modified_data[source_idx] = {}

                for i, record in enumerate(records):
                    edited_record = {}
                    for key, value in record.items():
                        # Use unique parent key for matching records with record index and file key
                        unique_parent_key = (
                            f"source_{source_idx}_record_{i}_{file_key}_{record_index}"
                            if file_key
                            else f"source_{source_idx}_record_{i}_{record_index}"
                        )
                        edited_record[key] = display_edit_field(
                            key, value, parent_key=unique_parent_key
                        )
                    st.session_state.modified_data[source_idx][i] = edited_record


def display_edit_field(key, value, parent_key="", depth=0):
    """
    Recursively displays and edits a field.
    For leaf nodes (non-dict, non-list), displays key and value on the same line
    using a text area for the value to allow for expansion.
    """
    import math  # Import math for ceiling function

    indent = "  " * depth
    if isinstance(value, dict):
        st.markdown(f"**{indent}{key}:**")
        edited_dict = {}
        for k, v in value.items():
            edited_dict[k] = display_edit_field(
                k, v, f"{parent_key}_{key}" if parent_key else key, depth + 1
            )
        return edited_dict
    elif isinstance(value, list):
        st.markdown(f"{indent}{key}:")
        edited_list = []
        for i, item in enumerate(value):
            edited_list.append(
                display_edit_field(
                    f"{key}[{i}]",
                    item,
                    f"{parent_key}_{key}" if parent_key else key,
                    depth + 1,
                )
            )
        return edited_list
    else:  # Leaf node: int, float, string, bool, None
        # --- Key Change: Dynamically size the text_area ---
        key_col, value_col = st.columns([1, 3])  # Adjust ratio as needed

        # Use the parent_key which now includes record index and file key for uniqueness
        unique_key = f"{parent_key}_{key}" if parent_key else key

        with key_col:
            st.markdown(f"{indent}{key}:")

        with value_col:
            str_value = str(value) if value is not None else ""
            str_value = str_value.strip()
            # --- Calculate dynamic height ---
            lines = str_value.splitlines()
            if not lines:
                lines = [""]
            num_lines = len(lines)
            estimated_visual_rows = sum(
                max(1, math.ceil(len(line) / 80)) for line in lines
            )
            calculated_height = max(num_lines * 15, estimated_visual_rows * 18 + 12)
            min_height = 35
            max_height = 300
            final_height = max(min_height, min(calculated_height, max_height))

            edited_value = st.text_area(
                label="",
                value=str_value,
                key=unique_key,
                height=int(final_height),
                label_visibility="collapsed",
            )
            return edited_value


# --- MODIFIED review_interface_file function ---
def review_interface_file():
    """Review interface for file mode with dynamic layout."""
    st.header("Data Review Interface")

    # Select output directory
    output_dir = st.text_input(
        "Enter output directory for reviewed files",
        value=(
            st.session_state.output_dir
            if st.session_state.output_dir
            else "./examples/data_review/reviewed/context"
        ),
    )
    st.session_state.output_dir = output_dir

    # --- UI Function Call: Jump to specific record ---
    jump_to_specific_record_file_mode_ui(
        st.session_state.main_file_idx, st.session_state.json_data
    )

    st.markdown("---")

    # --- State Initialization (Simplified, relies on session state) ---
    if not st.session_state.reviewed_files:
        for i, file_info in st.session_state.json_data.items():
            reviewed_filename = f"{Path(file_info['path']).stem}_reviewed.json"
            reviewed_path = os.path.join(output_dir, reviewed_filename)
            if os.path.exists(reviewed_path):
                with open(reviewed_path, "r", encoding="utf-8") as f:
                    reviewed_data = json.load(f)
                st.session_state.reviewed_files[i] = reviewed_data
            else:
                st.session_state.reviewed_files[i] = []  # Initialize as empty list

    # Determine starting index and current record, using session state
    main_file_idx = st.session_state.main_file_idx
    main_file_data = st.session_state.json_data[main_file_idx]["data"]

    # Get number of records in the main file
    num_records = 0
    if isinstance(main_file_data, list):
        num_records = len(main_file_data)
    elif isinstance(main_file_data, dict):
        num_records = 1

    if st.session_state.current_index >= num_records:
        st.info("All records have been reviewed!")
        # return

    # Get the current record based on index, prioritizing reviewed data
    if isinstance(main_file_data, list):
        # Check if there's a reviewed version of this record
        if (
            main_file_idx in st.session_state.reviewed_files
            and isinstance(st.session_state.reviewed_files[main_file_idx], list)
            and st.session_state.current_index
            < len(st.session_state.reviewed_files[main_file_idx])
        ):
            reviewed_record = copy.deepcopy(
                st.session_state.reviewed_files[main_file_idx][
                    st.session_state.current_index
                ]
            )
            reviewed_record.pop("review_info", None)  # Remove review metadata
            current_record = reviewed_record
        else:
            current_record = main_file_data[st.session_state.current_index]
    elif isinstance(main_file_data, dict):
        if main_file_idx in st.session_state.reviewed_files and isinstance(
            st.session_state.reviewed_files[main_file_idx], dict
        ):
            reviewed_record = copy.deepcopy(
                st.session_state.reviewed_files[main_file_idx]
            )
            reviewed_record.pop("review_info", None)  # Remove review metadata
            current_record = reviewed_record
        else:
            current_record = main_file_data

    # --- Core Logic: Find matching records ---
    matching_records = core.find_matching_records(
        current_record,
        st.session_state.json_data,
        st.session_state.link_fields,
        main_file_idx,
    )

    # Display current file and record information
    st.subheader(
        f"Current File: {st.session_state.json_data[main_file_idx]['filename']}"
    )
    st.subheader(f"Record {st.session_state.current_index + 1} of {num_records}")

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Previous") and st.session_state.current_index > 0:
            if (time.time() - st.session_state.current_time) <= 2:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()
                core.save_current_review_file(
                    output_dir=st.session_state.output_dir,
                    reviewer=st.session_state.reviewer,
                    main_file_idx=st.session_state.main_file_idx,
                    json_data=st.session_state.json_data,
                    reviewed_files=st.session_state.reviewed_files,
                    modified_data=st.session_state.modified_data,
                    current_index=st.session_state.current_index,
                )
                st.session_state.current_index -= 1
                st.session_state.modified_data = (
                    {}
                )  # Reset modifications when moving to previous
                st.rerun()
        # else:
        #     # Already at first record
        #     st.info("This is the first record.")
        #     # return
    with col2:
        if st.button("Save and Next"):

            if (time.time() - st.session_state.current_time) <= 2:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()
                core.save_current_review_file(
                    output_dir=st.session_state.output_dir,
                    reviewer=st.session_state.reviewer,
                    main_file_idx=st.session_state.main_file_idx,
                    json_data=st.session_state.json_data,
                    reviewed_files=st.session_state.reviewed_files,
                    modified_data=st.session_state.modified_data,
                    current_index=st.session_state.current_index,
                )
                if st.session_state.current_index < num_records - 1:
                    st.session_state.current_index += 1
                else:
                    st.info("Reached the end of current file!")
                st.session_state.modified_data = (
                    {}
                )  # Reset modifications when moving to next
                st.rerun()
    with col3:
        if st.button("Finish Review"):
            if (time.time() - st.session_state.current_time) <= 2:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()
                core.save_current_review_file(
                    output_dir=st.session_state.output_dir,
                    reviewer=st.session_state.reviewer,
                    main_file_idx=st.session_state.main_file_idx,
                    json_data=st.session_state.json_data,
                    reviewed_files=st.session_state.reviewed_files,
                    modified_data=st.session_state.modified_data,
                    current_index=st.session_state.current_index,
                )
                st.info("Review completed! All data has been saved.")

    # --- MODIFIED section for dynamic layout ---
    # Display image and image-related data side-by-side if configured
    if st.session_state.has_images and st.session_state.image_config:
        # --- PART 1: Two-column layout for image and image-related fields ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Image")
            image_path = core.construct_image_path(
                current_record, st.session_state.image_config
            )
            if image_path and os.path.exists(image_path):
                st.image(
                    image_path,
                    caption=os.path.basename(image_path),
                    use_container_width=True,
                )
            else:
                st.warning(f"Image not found: {image_path}")
        with col2:
            # Pass record index for unique key generation
            display_record_data(
                current_record,
                matching_records,
                context="image_column",
                record_index=st.session_state.current_index,
            )

        # --- PART 2: Single-column layout for other fields and matching records, below the two columns ---
        display_record_data(
            current_record,
            matching_records,
            context="full",
            record_index=st.session_state.current_index,
        )

    else:
        # If no images or image_config, display all data in single column as before
        display_record_data(
            current_record,
            matching_records,
            context="full",
            record_index=st.session_state.current_index,
        )


# --- MODIFIED review_interface_directory function ---
def review_interface_directory():
    """Review interface for directory mode with dynamic layout."""
    st.header("Data Review Interface")
    # Select output directory
    output_dir = st.text_input(
        "Enter output directory for reviewed files",
        value=(
            st.session_state.output_dir
            if st.session_state.output_dir
            else "./examples/data_review/reviewed/context"
        ),
    )
    st.session_state.output_dir = output_dir

    # --- UI Function Call: Jump to specific file and record ---
    jump_to_specific_file_directory_mode_ui(
        st.session_state.main_file_idx, st.session_state.directory_data
    )

    st.markdown("---")

    # --- State Management and Data Access ---
    main_dir_idx = st.session_state.main_file_idx
    main_dir_info = st.session_state.directory_data[main_dir_idx]

    if "current_file_idx" not in st.session_state:
        st.session_state.current_file_idx = 0

    # Get list of files in the main directory
    file_keys = list(main_dir_info["files"].keys())

    # Check if all files have been reviewed
    if st.session_state.current_file_idx >= len(file_keys):
        st.info("All files have been reviewed!")
        # return

    # Get the current file key and info based on index
    current_file_key = file_keys[st.session_state.current_file_idx]
    current_file_info = main_dir_info["files"][current_file_key]
    current_file_data = current_file_info["data"]

    # Initialize reviewed data for this specific file if not exists in session state
    if current_file_key not in st.session_state.reviewed_files:
        reviewed_path = core.get_reviewed_path_directory(
            current_file_info["path"], output_dir, main_dir_info["path"]
        )
        if os.path.exists(reviewed_path):
            with open(reviewed_path, "r", encoding="utf-8") as f:
                reviewed_data = json.load(f)
            st.session_state.reviewed_files[current_file_key] = reviewed_data
        else:
            st.session_state.reviewed_files[current_file_key] = copy.deepcopy(
                current_file_data
            )

    # Get number of records in the current file
    num_records = 0
    if isinstance(current_file_data, list):
        num_records = len(current_file_data)
    elif isinstance(current_file_data, dict):
        num_records = 1

    # Check if all records in the *current* file have been reviewed
    if st.session_state.current_index >= num_records:
        if (st.session_state.current_file_idx + 1) >= len(file_keys):
            st.info("All files and records have been reviewed!")
            # return
        else:
            st.session_state.current_file_idx += 1
            st.session_state.current_index = 0
            st.rerun()

    # Get the current record, prioritizing reviewed data
    if isinstance(current_file_data, list):
        # Check if there's a reviewed version of this record
        if (
            current_file_key in st.session_state.reviewed_files
            and isinstance(st.session_state.reviewed_files[current_file_key], list)
            and st.session_state.current_index
            < len(st.session_state.reviewed_files[current_file_key])
        ):
            # Use modified data but remove review metadata
            reviewed_record = copy.deepcopy(
                st.session_state.reviewed_files[current_file_key][
                    st.session_state.current_index
                ]
            )
            reviewed_record.pop("review_info", None)
            current_record = reviewed_record
        else:
            current_record = current_file_data[st.session_state.current_index]
    elif isinstance(current_file_data, dict):
        if current_file_key in st.session_state.reviewed_files and isinstance(
            st.session_state.reviewed_files[current_file_key], dict
        ):
            reviewed_record = copy.deepcopy(
                st.session_state.reviewed_files[current_file_key]
            )
            reviewed_record.pop("review_info", None)
            current_record = reviewed_record
        else:
            current_record = current_file_data

    # --- Core Logic: Find matching records ---
    matching_records = core.find_matching_directory_records(
        current_record,
        current_file_key,
        st.session_state.directory_data,
        st.session_state.link_fields,
        main_dir_idx,
    )

    # Display current file information
    st.subheader(f"Current File: {current_file_key}")
    st.subheader(f"Record {st.session_state.current_index + 1} of {num_records}")
    st.subheader(f"File {st.session_state.current_file_idx + 1} of {len(file_keys)}")

    # Navigation buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Previous Record"):
            if (time.time() - st.session_state.current_time) <= 1:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()
                core.save_current_review_directory(
                    current_file_key=current_file_key,
                    output_dir=st.session_state.output_dir,
                    reviewer=st.session_state.reviewer,
                    main_dir_idx=st.session_state.main_file_idx,
                    directory_data=st.session_state.directory_data,
                    reviewed_files=st.session_state.reviewed_files,
                    current_index=st.session_state.current_index,
                )

                if st.session_state.current_index > 0:
                    # If not the first record, just go to previous record
                    st.session_state.current_index -= 1
                else:
                    # If first record, try to go to previous file's last record
                    if st.session_state.current_file_idx > 0:
                        # Move to previous file
                        st.session_state.current_file_idx -= 1

                        # Get previous file info
                        prev_file_key = file_keys[st.session_state.current_file_idx]
                        prev_file_info = main_dir_info["files"][prev_file_key]
                        prev_file_data = prev_file_info["data"]

                        # Set index to last record of previous file
                        if isinstance(prev_file_data, list):
                            st.session_state.current_index = len(prev_file_data) - 1
                        else:  # dict
                            st.session_state.current_index = 0
                    else:
                        # Already at first file and first record
                        st.info("This is the first record of the first file")
                        # return

                st.session_state.modified_data = (
                    {}
                )  # Reset modifications when navigating
                st.rerun()
    with col2:
        if st.button("Save and Next Record"):

            if (time.time() - st.session_state.current_time) <= 1:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()

                core.save_current_review_directory(
                    current_file_key=current_file_key,
                    output_dir=st.session_state.output_dir,
                    reviewer=st.session_state.reviewer,
                    main_dir_idx=st.session_state.main_file_idx,
                    directory_data=st.session_state.directory_data,
                    reviewed_files=st.session_state.reviewed_files,
                    current_index=st.session_state.current_index,
                )
                if st.session_state.current_index < num_records - 1:
                    st.session_state.current_index += 1
                else:
                    if st.session_state.current_file_idx + 1 >= len(file_keys):
                        st.info("All files and records have been reviewed!")
                    else:
                        st.session_state.current_file_idx += 1
                        st.session_state.current_index = 0

                        # return
                st.session_state.modified_data = (
                    {}
                )  # Reset modifications when navigating
                st.rerun()
    with col3:
        if st.button("Next File"):
            if (time.time() - st.session_state.current_time) <= 1:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()
                core.save_current_review_directory(
                    current_file_key=current_file_key,
                    output_dir=st.session_state.output_dir,
                    reviewer=st.session_state.reviewer,
                    main_dir_idx=st.session_state.main_file_idx,
                    directory_data=st.session_state.directory_data,
                    reviewed_files=st.session_state.reviewed_files,
                    current_index=st.session_state.current_index,
                )

                if st.session_state.current_file_idx + 1 >= len(file_keys):
                    st.info("All files have been reviewed!")
                else:
                    st.session_state.current_file_idx += 1
                    st.session_state.current_index = 0

                    # return
                st.session_state.modified_data = (
                    {}
                )  # Reset modifications when navigating
                st.rerun()
    with col4:
        if st.button("Finish Review"):
            if (time.time() - st.session_state.current_time) <= 1:
                st.info("Click too fast!")
            else:
                st.session_state.current_time = time.time()
                core.save_current_review_directory(
                    current_file_key=current_file_key,
                    output_dir=st.session_state.output_dir,
                    reviewer=st.session_state.reviewer,
                    main_dir_idx=st.session_state.main_file_idx,
                    directory_data=st.session_state.directory_data,
                    reviewed_files=st.session_state.reviewed_files,
                    current_index=st.session_state.current_index,
                )
                st.info("Review completed! All data has been saved.")

    # --- MODIFIED section for dynamic layout ---
    # Display image and image-related data side-by-side if configured
    if st.session_state.has_images and st.session_state.image_config:
        # --- PART 1: Two-column layout for image and image-related fields ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Image")
            image_path = core.construct_image_path(
                current_record, st.session_state.image_config
            )
            if image_path and os.path.exists(image_path):
                st.image(
                    image_path,
                    caption=os.path.basename(image_path),
                    use_container_width=True,
                )
            else:
                st.warning(f"Image not found: {image_path}")
        with col2:
            # Pass both record index and file key for unique key generation
            display_record_data(
                current_record,
                matching_records,
                context="image_column",
                record_index=st.session_state.current_index,
                file_key=current_file_key,
            )

        # --- PART 2: Single-column layout for other fields and matching records, below the two columns ---
        display_record_data(
            current_record,
            matching_records,
            context="full",
            record_index=st.session_state.current_index,
            file_key=current_file_key,
        )

    else:
        # If no images or image_config, display all data in single column as before
        display_record_data(
            current_record,
            matching_records,
            context="full",
            record_index=st.session_state.current_index,
            file_key=current_file_key,
        )


# --- Main App Logic ---
def main():
    st.title("Book Image Data Review and Modification App")
    core.init_session_state()  # Initialize state using core function

    if not st.session_state.authenticated:
        authentication_component()
        return

    # Step 0: Authentication completed
    # Step 1: Input mode selection
    if st.session_state.current_step == 0:
        st.header("Step 1: Input Mode Selection")
        input_mode = st.radio(
            "Select input mode", ("File Path Mode", "Directory Path Mode")
        )
        if st.button("Continue"):
            st.session_state.input_mode = (
                "file" if input_mode == "File Path Mode" else "directory"
            )
            st.session_state.current_step = 1
            st.rerun()

    # Step 2: JSON file/directory selection and loading
    elif st.session_state.current_step == 1:
        st.header("Step 2: Data Source Selection")
        if st.session_state.input_mode == "file":
            num_files = st.number_input(
                "Number of JSON files to load", min_value=1, max_value=10, value=1
            )
            file_paths = []
            for i in range(num_files):
                file_path = st.text_input(f"Path to JSON file {i+1}", key=f"file_{i}")
                file_paths.append(file_path)
            if st.button("Load JSON Files"):
                try:
                    json_data = core.load_json_files(file_paths)
                    st.session_state.json_data = json_data
                    st.session_state.current_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            if st.button("Previous Step"):
                try:
                    st.session_state.current_step = 0
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        else:  # directory mode
            num_dirs = st.number_input(
                "Number of directories to load", min_value=1, max_value=10, value=1
            )
            dir_paths = []
            dir_types = []
            for i in range(num_dirs):
                dir_path = st.text_input(f"Path to directory {i+1}", key=f"dir_{i}")
                dir_type = st.selectbox(
                    f"Type of directory {i+1}",
                    ["Book Directory", "Image Directory"],
                    key=f"dir_type_{i}",
                )
                dir_paths.append(dir_path)
                dir_types.append(dir_type)

            if st.button("Load Directories"):
                try:
                    directory_data = core.load_json_directories(dir_paths, dir_types)
                    st.session_state.directory_data = directory_data
                    st.session_state.current_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            if st.button("Previous Step"):
                try:
                    st.session_state.current_step = 0
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    # Step 3: Display JSON file/directory fields
    elif st.session_state.current_step == 2:
        st.header("Step 3: Data Structure")
        if st.session_state.input_mode == "file":
            display_json_fields(st.session_state.json_data)
        else:
            display_directory_fields(st.session_state.directory_data)
        if st.button("Continue to Linking Setup"):
            st.session_state.current_step = 3
            st.rerun()
        if st.button("Previous Step"):
            try:
                st.session_state.current_step = 1
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # Step 4: Setup linking between data sources
    elif st.session_state.current_step == 3:
        st.header("Step 4: Setup Linking Between Data Sources")
        if st.session_state.input_mode == "file":
            if len(st.session_state.json_data) > 1:
                main_file_idx, link_fields = setup_linking_files_ui(
                    st.session_state.json_data
                )
                if link_fields and "main" in link_fields and link_fields["main"]:
                    st.session_state.main_file_idx = main_file_idx
                    st.session_state.link_fields = link_fields
                    if st.button("Confirm Linking (File Mode)"):
                        st.session_state.current_step = 4
                        st.rerun()
            else:
                st.session_state.main_file_idx = 0
                st.session_state.link_fields = {}
                st.info("Only one JSON file loaded, using it as the main file.")
                if st.button("Continue to Image Configuration"):
                    st.session_state.current_step = 4
                    st.rerun()
                if st.button("Previous Step"):
                    try:
                        st.session_state.current_step = 2
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        else:
            if len(st.session_state.directory_data) > 1:
                main_dir_idx, link_fields = setup_linking_directories_ui(
                    st.session_state.directory_data
                )
                if link_fields and "main" in link_fields and link_fields["main"]:
                    st.session_state.main_file_idx = main_dir_idx
                    st.session_state.link_fields = link_fields
                    if st.button("Confirm Linking (Directory Mode)"):
                        st.session_state.current_step = 4
                        st.rerun()
                    if st.button("Previous Step"):
                        try:
                            st.session_state.current_step = 2
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
            else:
                st.session_state.main_file_idx = 0
                st.session_state.link_fields = {}
                st.info("Only one directory loaded, using it as the main directory.")
                if st.button("Continue to Image Configuration"):
                    st.session_state.current_step = 4
                    st.rerun()
                if st.button("Previous Step"):
                    try:
                        st.session_state.current_step = 2
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # Step 5: Image configuration
    elif st.session_state.current_step == 4:
        st.header("Step 5: Image Configuration")
        if st.session_state.input_mode == "file":
            has_images, image_config = setup_image_configuration_ui(
                json_data=st.session_state.json_data
            )
        else:
            has_images, image_config = setup_image_configuration_ui(
                directory_data=st.session_state.directory_data
            )
        st.session_state.has_images = has_images
        st.session_state.image_config = image_config
        if st.button("Continue to Output Directory"):
            st.session_state.current_step = 5
            st.rerun()
        if st.button("Previous Step"):
            try:
                st.session_state.current_step = 3
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # Step 6: Input output directory
    elif st.session_state.current_step == 5:
        st.header("Step 6: Output Directory")
        # Input output directory
        output_dir = st.text_input(
            "Enter output directory for reviewed files",
            value=(
                st.session_state.output_dir
                if st.session_state.output_dir
                else "./examples/data_review/reviewed"
            ),
        )
        st.session_state.output_dir = output_dir
        if st.button("Start Review"):
            st.session_state.current_step = 6
            st.rerun()
        if st.button("Previous Step"):
            try:
                st.session_state.current_step = 4
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # Step 7: Review interface
    elif st.session_state.current_step == 6:
        st.session_state.current_time == time.time()
        if st.session_state.input_mode == "file":
            review_interface_file()
        else:
            review_interface_directory()


if __name__ == "__main__":
    main()
