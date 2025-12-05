# Web Interface User Guide for Book Image Data Review Application  
## Table of Contents  
1. [Introduction](#1-introduction)  
2. [Prerequisites](#2-prerequisites)  
3. [Step-by-Step Usage](#3-step-by-step-usage)  
4. [Key Features Explained](#4-key-features-explained)  
5. [Frequently Asked Questions (FAQs)](#5-frequently-asked-questions-faqs)  


## 1. Introduction  
The **Book Image Data Review Web Interface** is a user-friendly tool for reviewing, editing, and linking book/image-related JSON data. It runs in a web browser and supports two workflows:  
- **File Path Mode**: Load and review individual JSON files.  
- **Directory Path Mode**: Load and review structured directories of JSON files (e.g., book-specific folders with image metadata).  

Core capabilities include:  
- Previewing images alongside their metadata.  
- Editing records in real time.  
- Linking related data across files/directories.  
- Saving reviewed data with audit trails (who reviewed, when).  


## 2. Prerequisites  
Before using the interface:  
1. Ensure the application is running (see [Section 5 of the Development Guide](./development_guide.md#5-application-execution-flow)).  
2. Have your JSON data ready:  
   - For `File Mode`: 1–10 valid JSON files (e.g., `book_metadata.json`, `image_metadata.json`).  
   - For `Directory Mode`: 1–10 directories (marked as `Book Directory` or `Image Directory`).  
3. (Optional) If using images: Have a folder with structured image files (e.g., `base_path/000001/000001.jpg`).  


## 3. Step-by-Step Usage  
The interface guides you through a 7-step workflow. Follow these steps to review your data:  

### 3.1 Launch the Application  
1. Run the app from the project root:  
   ```bash
   streamlit run examples/data_review/run.py
   ```  
2. Open the URL provided by Streamlit (default: `http://localhost:8501`) in your browser.  

### 3.2 Authentication (If Required)  
By default, authentication is disabled (`st.session_state.authenticated = True`). If enabled:  
1. Under **Authentication**:  
   - Select your name from the `Select reviewer name` dropdown.  
   - Enter your password in the `Enter password` field (hidden for security).  
2. Click **Authenticate**.  
   - Success: A green `Authentication successful!` message appears, and the app proceeds to the workflow.  
   - Failure: A red `Incorrect password` message appears. Re-enter your password.  

### 3.3 Select Input Mode  
1. Under **Step 1: Input Mode Selection**:  
   - Choose `File Path Mode` if you want to load individual JSON files.  
   - Choose `Directory Path Mode` if you want to load structured directories.  
2. Click **Continue** to proceed.  

### 3.4 Load Data Source  
#### Option A: File Path Mode  
1. Under **Step 2: Data Source Selection**:  
   - Use the `Number of JSON files to load` input to specify how many files you want to load (1–10).  
   - For each file (e.g., `Path to JSON file 1`), enter the full path to your JSON file (e.g., `C:/data/book_metadata.json` or `./data/image_metadata.json`).  
2. Click **Load JSON Files**.  
   - Success: The app proceeds to Step 3 (Data Structure View).  
   - Failure: A red error message appears (e.g., "File not found" or "Invalid JSON"). Verify the file path and JSON validity.  
3. (Optional) Click **Previous Step** to return to Input Mode Selection.  

#### Option B: Directory Path Mode  
1. Under **Step 2: Data Source Selection**:  
   - Use the `Number of directories to load` input to specify how many directories you want to load (1–10).  
   - For each directory:  
     - Enter the full path (e.g., `C:/data/books` or `./data/images`).  
     - Select a type from `Type of directory`:  
       - `Book Directory`: For flat directories of JSON files (e.g., `000001.json`, `000002.json`).  
       - `Image Directory`: For nested directories (e.g., `000001/000001.json`, `000002/000001.json`).  
2. Click **Load Directories**.  
   - Success: The app proceeds to Step 3 (Data Structure View).  
   - Failure: A red error message appears (e.g., "Directory not found"). Verify the directory path.  
3. (Optional) Click **Previous Step** to return to Input Mode Selection.  

### 3.5 View Data Structure  
1. Under **Step 3: Data Structure**:  
   - The app displays the structure of your loaded data:  
     - For `File Mode`: Each file’s name, fields, and a sample record.  
     - For `Directory Mode`: Each directory’s path, type, sample file, and sample record.  
2. Verify that the data is loaded correctly (e.g., fields like `book_id`, `image_id`, or `title` are present).  
3. Click **Continue to Linking Setup** to proceed.  
4. (Optional) Click **Previous Step** to re-load your data.  

### 3.6 Setup Linking Between Data Sources  
Linking helps the app find related records across files/directories (e.g., match a book’s metadata to its image metadata using `book_id`).  

#### If 1 File/Directory Is Loaded:  
- The app skips manual linking and uses the single file/directory as the "main" data source.  
- Click **Continue to Image Configuration** to proceed.  

#### If >1 File/Directory Is Loaded:  
1. Under **Step 4: Setup Linking Between Data Sources**:  
   - **Select Main Data Source**:  
     - For `File Mode`: Choose the "main" JSON file (e.g., `book_metadata.json`).  
     - For `Directory Mode`: Choose the "main" directory (prioritizes `Image Directory`; falls back to `Book Directory`).  
   - **Select Linking Fields**:  
     - From the main data source, select fields to use for linking (e.g., `book_id`, `image_id`).  
   - **Map Linking Fields to Other Sources**:  
     - For each non-main file/directory, map the main fields to corresponding fields (e.g., map `book_id` in the main file to `book_identifier` in another file).  
     - Select `None` if a field has no match.  
2. Click **Confirm Linking (File Mode)** or **Confirm Linking (Directory Mode)**.  
3. (Optional) Click **Previous Step** to re-view the data structure.  

### 3.7 Image Configuration  
Configure image previews (skip if your data has no images).  

1. Under **Step 5: Image Configuration**:  
   - Select `Yes` for `Does the data contain images?`.  
   - Enter the `base image path` (full path to the root folder of your images, e.g., `C:/data/images` or `./data/images`).  
   - For `Select the file/directory containing book and image ID fields`: Choose the file/directory with `book_id` and `image_id` fields.  
   - Select `book ID field` (e.g., `book_id`) and `image ID field` (e.g., `image_id`) from the dropdowns.  
   - If your data has no images, select `No` (the app skips image previews).  
2. Click **Continue to Output Directory** to proceed.  
3. (Optional) Click **Previous Step** to reconfigure linking.  

### 3.8 Set Output Directory  
Specify where to save your reviewed data.  

1. Under **Step 6: Output Directory**:  
   - Enter a path in `Enter output directory for reviewed files` (default: `./examples/data_review/reviewed`).  
   - The app will save edited records as `_reviewed.json` files (e.g., `book_metadata.json` → `book_metadata_reviewed.json`).  
2. Click **Start Review** to launch the review interface.  
3. (Optional) Click **Previous Step** to reconfigure image settings.  

### 3.9 Review & Modify Data  
This is the core step where you review, edit, and save records. The interface varies slightly by mode, but key features are consistent.  

#### Common Elements (Both Modes)  
- **Progress Tracking**:  
  - `File Mode`: Shows `Record X of Y` (e.g., `Record 3 of 50`).  
  - `Directory Mode`: Shows `Record X of Y` and `File A of B` (e.g., `Record 2 of 10 | File 1 of 5`).  
- **Navigation Buttons**:  
  | Button | Function |  
  |--------|----------|  
  | `Previous`/`Previous Record` | Move to the previous record (saves current edits first). |  
  | `Save and Next`/`Save and Next Record` | Save current edits and move to the next record. |  
  | `Next File` (Directory Mode) | Save current edits and move to the first record of the next file. |  
  | `Finish Review` | Save all edits and mark the review as complete. |  
- **Click Throttling**: Buttons are disabled for 2–4 seconds after use to prevent accidental duplicate clicks.  

#### Image Preview (If Configured)  
- A two-column layout appears:  
  - **Left Column**: Displays the image (if found) with its filename as the caption.  
    - If the image is missing: A `Image not found` warning appears (verify `base_path` and ID fields).  
  - **Right Column**: Shows image-related fields (e.g., `book_id`, `image_id`) for quick editing.  

#### Edit Records  
1. **Edit Fields**:  
   - All fields are displayed as editable text areas (dynamic height adjusts to content length).  
   - For nested data (dicts/lists): Fields are indented for clarity (e.g., `author.name`, `tags[0]`).  
2. **View Matching Records**:  
   - Below the main record, the app displays related records from other files/directories (e.g., image metadata linked to a book).  
   - Matching records are also editable.  
3. **Save Edits**:  
   - Click `Save and Next`/`Save and Next Record` to save edits and proceed.  
   - Edits are saved to `_reviewed.json` files in the output directory, with audit metadata (your name, timestamp).  

#### Jump to a Specific Record/File  
- **File Mode**: Use the `Jump to Specific Record` section:  
  1. Enter a 0-based index (e.g., `10` for the 11th record).  
  2. Click `Jump to Record`.  
- **Directory Mode**: Use the `Jump to Specific File and Record` section:  
  1. Select a file from the dropdown.  
  2. Enter a 0-based record index.  
  3. Click `Jump to Selected File and Record`.  

### 3.10 Complete the Review  
1. When you reach the last record/file:  
   - A green `All records have been reviewed!` or `All files and records have been reviewed!` message appears.  
2. Click **Finish Review** to save any final edits.  
3. A green `Review completed! All data has been saved.` message confirms success.  
4. Locate your reviewed files in the output directory (e.g., `./examples/data_review/reviewed`).  


## 4. Key Features Explained  
### 4.1 Dynamic Field Editing  
- The app supports editing of **all data types**: primitives (strings, numbers, booleans), dicts, and lists.  
- Text areas auto-resize based on content length (min: 35px, max: 300px) for readability.  
- Unique UI keys prevent duplicate elements or glitches when editing multiple records.  

### 4.2 Image Preview  
- Images are loaded using `book_id` (padded to 6 digits) and `image_id` (padded to 6 digits).  
- Example path: `base_path/000001/000001.jpg` (where `book_id=1` and `image_id=1`).  
- If the image format is not specified (e.g., `image_id=000001`), the app appends `.jpg` as a fallback.  

### 4.3 Audit Trails  
Every reviewed record includes a `review_info` field with:  
- `reviewer`: Your name (from authentication).  
- `timestamp`: The time of editing (ISO format, e.g., `2024-05-20T14:30:00`).  
- `original_index`: The original position of the record in the source file.  

### 4.4 Linking Logic  
- The app matches records by comparing **string values** of linked fields (e.g., `book_id=123` in the main file matches `book_identifier=123` in another file).  
- For `Image Directory` in `Directory Mode`, the app first uses the directory structure (book ID subdirectories) to narrow matches, then checks linked fields.  


## 5. Frequently Asked Questions (FAQs)  
### Q1: Why is my image not loading?  
A1: Check these three things:  
1. **Base Path**: Ensure `base_image_path` points to the root folder of your images (e.g., if images are in `C:/data/images/000001`, the base path is `C:/data/images`).  
2. **ID Fields**: Verify `book_id_field` and `image_id_field` are correctly selected (e.g., not `bookId` if the field is `book_id`).  
3. **ID Format**: IDs are padded to 6 digits (e.g., `book_id=5` becomes `000005`). Ensure your image directories/filenames use 6-digit IDs.  

### Q2: Where are my reviewed files saved?  
A2: Reviewed files are saved to the **output directory** you specified in Step 6. By default, this is `./examples/data_review/reviewed`.  
- For `File Mode`: Each file is saved as `[original_filename]_reviewed.json` (e.g., `book.json` → `book_reviewed.json`).  
- For `Directory Mode`: The original directory structure is preserved (e.g., `./data/books/book1.json` → `./reviewed/books/book1_reviewed.json`).  

### Q3: Why am I getting a `JSONDecodeError` when loading files?  
A5: This means your JSON file is corrupt or not well-formed. Fix it by:  
1. Using a JSON validator (e.g., [JSONLint](https://jsonlint.com/)) to find errors.  
2. Ensuring the file uses valid syntax (e.g., commas between objects, double quotes for keys/values).  

### Q4: How do I return to a previous step?  
A6: Each step has a **Previous Step** button (except Step 0). Click it to go back and reconfigure settings (e.g., re-load data, re-map linking fields).  

