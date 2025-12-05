# Code Development Guide for Book Image Data Review Application  
## Table of Contents  
1. [Overview](#1-overview)  
2. [Project Structure](#2-project-structure)  
3. [Dependencies](#3-dependencies)  
4. [Detailed Code Breakdown](#4-detailed-code-breakdown)  
   4.1 [data_review_core.py](#41-data_review_corepy)  
   4.2 [data_review_app.py](#42-data_review_apppy)  
5. [Application Execution Flow](#5-application-execution-flow)  
6. [Development & Extension Guidelines](#6-development--extension-guidelines)  
7. [Troubleshooting](#7-troubleshooting)  


## 1. Overview  
The **Book Image Data Review Application** is a Streamlit-based tool designed to load, review, edit, and link book/image-related JSON data. It supports two input modes (`File Path Mode` for individual JSON files and `Directory Path Mode` for structured directories) and enables users to:  
- Authenticate via predefined reviewer accounts.  
- Load and inspect JSON data structures.  
- Link related data across multiple files/directories using common fields.  
- Preview images (if configured) alongside corresponding data.  
- Edit records in real time and save reviewed data with audit trails (reviewer name, timestamp).  

The application is split into two core files (under `fttracer/data_review/`) and a lightweight entry point (`run.py`):  
- `data_review_core.py`: Contains backend logic (data loading, record matching, saving, utility functions).  
- `data_review_app.py`: Implements the Streamlit UI and user workflow.  
- `examples/data_review/run.py`: Entry point to launch the app.  


## 2. Project Structure  
| File Path | Purpose |  
|-----------|---------|  
| `fttracer/data_review/data_review_core.py` | Backend logic: session state init, data loading, record matching, review saving. |  
| `fttracer/data_review/data_review_app.py` | Frontend UI: authentication, step-by-step workflow, record editing, image preview. |  
| `examples/data_review/run.py` | Entry point: Imports `main()` from `data_review_app.py` to launch the app. |  


## 3. Dependencies  
Ensure the following are installed before running the application:  

| Dependency | Version Requirement | Installation Command |  
|------------|---------------------|----------------------|  
| Python | 3.8+ | (Install via [python.org](https://www.python.org/)) |  
| Streamlit | Latest stable | `pip install streamlit` |  
| Other Utilities | Built-in (hashlib, json, os, pathlib, datetime, glob) | No additional installation needed |  


## 4. Detailed Code Breakdown  

### 4.1 data_review_core.py  
This file encapsulates the application’s core logic, isolated from UI concerns. It is organized into **6 key modules**:  

#### 4.1.1 Session State Initialization  
- **Function**: `init_session_state()`  
  - Initializes Streamlit `st.session_state` variables with default values to avoid `KeyError`.  
  - Critical variables:  
    - `authenticated`: Tracks if the user has passed authentication (default: `True`).  
    - `current_step`: Manages the 7-step workflow (0 = input mode selection, 6 = review interface).  
    - `json_data`/`directory_data`: Stores loaded JSON data (file/directory mode).  
    - `modified_data`: Tracks real-time edits to records.  
    - `reviewed_files`: Caches reviewed data to persist edits across sessions.  

#### 4.1.2 Data Loading  
Loads JSON data from files or directories, with validation for corrupt files/directories.  

| Function | Purpose | Key Logic |  
|----------|---------|-----------|  
| `load_json_files(file_paths)` | Loads 1–10 individual JSON files. | For each file path: <br> 1. Opens and parses JSON. <br> 2. Stores metadata (path, filename) and data in a dictionary. <br> 3. Raises exceptions for invalid files/paths. |  
| `load_json_directories(directory_paths, directory_types)` | Loads JSON data from two directory types: <br> - `Book Directory`: Flat directory of JSON files. <br> - `Image Directory`: Nested (book ID → JSON files). | For `Book Directory`: <br> - Globs all `.json` files and stores them by filename. <br> For `Image Directory`: <br> - Scans subdirectories (book IDs) and stores JSON files with keys like `book_id/file.json`. |  

#### 4.1.3 Linking Setup  
Prepares templates for linking fields across data sources (used by the UI to collect user input).  

| Function | Purpose |  
|----------|---------|  
| `setup_linking_files(json_data, main_file_idx, selected_main_fields)` | Creates a placeholder structure for linking fields in `File Mode` (maps main file fields to other files). |  
| `setup_linking_directories(directory_data, main_dir_idx, selected_main_fields)` | Creates a placeholder structure for linking fields in `Directory Mode` (maps main directory fields to other directories). |  

#### 4.1.4 Record Matching  
Finds related records across files/directories using user-defined linking fields.  

| Function | Purpose | Key Logic |  
|----------|---------|-----------|  
| `find_matching_records(main_record, json_data, link_fields, main_file_idx)` | Matches records in `File Mode`. | For each non-main file: <br> 1. Compares values of linked fields (from `link_fields`). <br> 2. Collects records where all linked fields match the main record. |  
| `find_matching_directory_records(...)` | Matches records in `Directory Mode`. | Uses directory structure (e.g., book ID subdirectories) + linked fields to find matches. <br> - For `Image Directory`: Matches via `book_id` (subdirectory) and `image_id` (filename). |  

#### 4.1.5 Image & Path Utilities  
| Function | Purpose |  
|----------|---------|  
| `construct_image_path(record, image_config)` | Builds the full path to an image using: <br> - `base_path` (user-provided). <br> - `book_id_field` and `image_id_field` (from record data). <br> - Pads IDs with leading zeros (6 digits) and appends `.jpg` if missing. |  
| `get_reviewed_path_directory(original_path, output_dir, main_dir_path)` | Calculates the save path for reviewed files in `Directory Mode` (preserves relative directory structure). |  

#### 4.1.6 Review Saving  
Saves edited records with audit metadata (reviewer name, timestamp) to the specified output directory.  

| Function | Purpose | Key Logic |  
|----------|---------|-----------|  
| `save_current_review_file(...)` | Saves reviews in `File Mode`. | 1. Creates the output directory if missing. <br> 2. Appends/updates the reviewed record in `reviewed_files`. <br> 3. Writes `_reviewed.json` files (e.g., `data.json` → `data_reviewed.json`). |  
| `save_current_review_directory(...)` | Saves reviews in `Directory Mode`. | 1. Preserves the original directory structure in the output folder. <br> 2. Merges edits from `modified_data` into the reviewed record. <br> 3. Adds `review_info` (audit metadata) to each edited record. |  

#### 4.1.7 Predefined Reviewers  
- A dictionary `REVIEWERS` stores reviewer names and their **SHA-256 hashed passwords** (e.g., `Yuqun`: Hashed value of `DBaudewDwefha122181`).  


### 4.2 data_review_app.py  
This file implements the Streamlit UI and user workflow. It is organized into **3 key modules**:  

#### 4.2.1 UI Components  
Reusable UI elements for authentication, data display, and configuration.  

| Component Function | Purpose |  
|--------------------|---------|  
| `hash_password(password)` | Hashes user input passwords (SHA-256) to compare with `REVIEWERS` in `authentication_component()`. |  
| `authentication_component()` | Displays a header, reviewer dropdown, password input, and "Authenticate" button. <br> - Updates `st.session_state.authenticated` and `reviewer` on success. |  
| `display_json_fields(json_data)` | Renders the structure of loaded JSON files (fields and sample records) in `File Mode`. |  
| `display_directory_fields(directory_data)` | Renders the structure of loaded directories (path, type, sample files/fields) in `Directory Mode`. |  
| `setup_linking_files_ui(json_data)` / `setup_linking_directories_ui(directory_data)` | UI for selecting a "main" file/directory and mapping its fields to other data sources (links). |  
| `setup_image_configuration_ui(...)` | UI for enabling image previews: <br> - Radio button to select "Yes"/"No" for images. <br> - Input for `base_path` (image root directory). <br> - Dropdowns to select `book_id_field` and `image_id_field`. |  
| `jump_to_specific_record_file_mode_ui(...)` / `jump_to_specific_file_directory_mode_ui(...)` | UI to jump to a specific record (file mode) or file+record (directory mode) via index input. |  
| `display_edit_field(key, value, parent_key, depth)` | Recursively renders editable fields for records (supports dicts, lists, and primitive types). <br> - Uses dynamic text area heights (based on content length) for readability. <br> - Generates unique `key` values to avoid Streamlit UI conflicts. |  
| `display_record_data(...)` | Renders record data in two contexts: <br> - `image_column`: Shows only image-related fields (side-by-side with images). <br> - `full`: Shows all non-image fields + matching records from other sources. |  

#### 4.2.2 Review Interfaces  
Dedicated UIs for reviewing records in `File Mode` and `Directory Mode`.  

| Function | Purpose | Key Features |  
|----------|---------|--------------|  
| `review_interface_file()` | Review UI for `File Mode`. | 1. Output directory input. <br> 2. "Previous"/"Save and Next"/"Finish Review" buttons (with 2-second click throttling). <br> 3. Two-column layout (image + image fields) if images are enabled. <br> 4. Single-column layout for non-image fields + matching records. |  
| `review_interface_directory()` | Review UI for `Directory Mode`. | 1. "Previous Record"/"Save and Next Record"/"Next File"/"Finish Review" buttons (4-second throttling). <br> 2. Tracks progress across files (e.g., "File 1 of 5"). <br> 3. Same dynamic layout as `File Mode` for images/fields. |  

#### 4.2.3 Main App Logic (`main()`)  
Manages the 7-step user workflow using `st.session_state.current_step`:  

| Step | Name | Action |  
|------|------|--------|  
| 0 | Input Mode Selection | Let user choose `File Path Mode` or `Directory Path Mode`. |  
| 1 | Data Source Selection | Load JSON files (file mode) or directories (directory mode). |  
| 2 | Data Structure View | Display loaded data fields/samples for verification. |  
| 3 | Linking Setup | Configure field links (skipped if only 1 file/directory is loaded). |  
| 4 | Image Configuration | Enable/disable image previews and set image-related fields. |  
| 5 | Output Directory | Let user specify where to save reviewed files. |  
| 6 | Review Interface | Launch the appropriate review UI (file/directory mode). |  


## 5. Application Execution Flow  
To run the app, follow these steps (from the **project root directory**):  

1. **Install Dependencies** (if not already installed):  
   ```bash
   pip install streamlit
   ```  

2. **Launch the App** via `run.py`:  
   ```bash
   streamlit run examples/data_review/run.py
   ```  

3. **Access the UI**:  
   Streamlit will start a local server (default: `http://localhost:8501`). Open this URL in a web browser.  

4. **Workflow Execution**:  
   The app guides users through the 7-step workflow (see Section 4.2.3). Edits are saved to `_reviewed.json` files in the specified output directory.  


## 6. Development & Extension Guidelines  
### 6.1 Add a New Reviewer  
1. Open `data_review_core.py`.  
2. Add a new entry to the `REVIEWERS` dictionary:  
   ```python
   REVIEWERS = {
       # Existing entries...
       "NewReviewer": hashlib.sha256("NewPassword123".encode()).hexdigest(),
   }
   ```  
3. Generate the hashed password (run this in a Python shell):  
   ```python
   import hashlib
   print(hashlib.sha256("YourPasswordHere".encode()).hexdigest())
   ```  

### 6.2 Support Additional Data Formats  
To load CSV/Excel files (instead of just JSON):  
1. In `data_review_core.py`, add a new function (e.g., `load_csv_files(file_paths)`).  
2. Use `pandas` to read CSV/Excel files and convert them to dictionaries.  
3. Update the UI in `data_review_app.py` (Step 1) to let users select file types (JSON/CSV/Excel).  

### 6.3 Extend UI Features  
- **Bulk Edit**: Add a "Bulk Edit" button in `review_interface_file()`/`review_interface_directory()` to apply edits to multiple records.  
- **Search**: Add a text input to search for records by keyword (filter `main_file_data` in the review UI).  

### 6.4 Modify Image Logic  
To support additional image formats (e.g., `.png`, `.jpeg`):  
1. Update `construct_image_path()` in `data_review_core.py` to check for multiple extensions:  
   ```python
   extensions = [".jpg", ".png", ".jpeg"]
   if not any(image_id.endswith(ext) for ext in extensions):
       image_id += ".jpg"  # Fallback
   ```  


## 7. Troubleshooting  
| Issue | Root Cause | Solution |  
|-------|------------|----------|  
| `ModuleNotFoundError: No module named 'fttracer'` | The project root is not in Python’s `sys.path`. | Run the app from the **project root directory** (not `examples/data_review/`). |  
| `JSONDecodeError` when loading files | Corrupt JSON file or invalid file path. | Verify the file path and ensure the JSON is well-formed (use [JSONLint](https://jsonlint.com/)). |  
| Image not found | Incorrect `base_path` or missing `book_id`/`image_id` fields. | 1. Check `base_path` (ensure it points to the root of image directories). <br> 2. Verify `book_id_field` and `image_id_field` are correctly mapped. |  
| UI Elements Duplicate/Glitch | Streamlit `key` values are not unique. | Ensure `display_edit_field()` generates unique `key` values (use `parent_key` + `key` + `record_index`). |  


