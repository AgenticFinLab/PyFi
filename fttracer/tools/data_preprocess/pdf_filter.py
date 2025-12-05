"""
PDF Screening, Classification, and Quality Control Script

This script automates the filtering of PDF files based on:
1. File size and extension (initial screening)
2. Semantic classification using the Qwen LLM API to determine if a book
   is likely to contain rich visual content (e.g., charts, diagrams)

Designed primarily for financial/technical trading books, but easily adaptable
to other domains by modifying the classification prompt.

Key Features:
- Deletes non-PDF or very small files (<5MB by default)
- Uses LLM (Qwen) to classify books as 'keep', 'delete', or 'uncertain'
- Organizes results into subdirectories: `to_keep`, `to_delete`, `uncertain`
- Optional auto-cleanup mode to restore only kept/uncertain files to input dir

Environment:
    Requires DASHSCOPE_API_KEY set in environment variables.
"""

import os
import glob
import json
import time
import shutil
import http.client
from typing import List, Tuple

from fttracer.tools.data_preprocess.prompt import prompt_for_pdf_filter


def _create_directories(base_path: str) -> None:
    """
    Create output subdirectories for classified files.

    Args:
        base_path (str): Root directory where subfolders will be created.
    """
    # Define the names of subdirectories to create for organizing results
    folders = ["to_delete", "to_keep", "uncertain"]
    # Iterate through each folder name and create the directory if it doesn't exist
    for folder in folders:
        # Construct the full path for the subdirectory
        folder_path = os.path.join(base_path, folder)
        # Create the directory with exist_ok=True to avoid errors if it already exists
        os.makedirs(folder_path, exist_ok=True)


def _get_files_to_delete_initial(
    folder_path: str, size_threshold: int = 5 * 1024 * 1024  # Default: 5 MB
) -> Tuple[List[str], List[str]]:
    """
    Perform initial file screening:
    - Skip directories
    - Remove files smaller than `size_threshold`
    - Remove non-PDF files

    Args:
        folder_path (str): Path to input directory.
        size_threshold (int): Minimum file size in bytes to retain. Default is 5MB.

    Returns:
        Tuple[List[str], List[str]]:
            - List of file paths to delete immediately
            - List of valid PDFs above size threshold for further processing
    """
    # Get all files in the specified folder using glob pattern matching
    all_files = glob.glob(os.path.join(folder_path, "*"))

    # Initialize lists to store files that need different actions
    files_to_delete = []  # Files that fail initial screening criteria
    files_to_process = []  # Files that pass initial screening for further analysis

    # Process each file in the directory
    for file_path in all_files:
        # Skip directories - we only want to process actual files
        if os.path.isdir(file_path):
            continue

        # Extract the filename from the full path for extension checking
        file_name = os.path.basename(file_path)

        try:
            # Check if file size is below the threshold (too small to be useful)
            if os.path.getsize(file_path) < size_threshold:
                files_to_delete.append(file_path)  # Mark for immediate deletion
                continue  # Skip to next file
        except OSError as e:
            # Handle case where file access fails (permissions, corrupted, etc.)
            print(f"Cannot access file size for {file_path}: {e}")
            files_to_delete.append(file_path)  # Mark for deletion due to access issues
            continue

        # Check if file has PDF extension (case-insensitive comparison)
        if not file_name.lower().endswith(".pdf"):
            files_to_delete.append(file_path)  # Mark non-PDF files for deletion
            continue

        # If file passes all initial checks, add to processing list
        files_to_process.append(file_path)

    # Return both lists: files to delete immediately and files for further processing
    return files_to_delete, files_to_process


def _call_qwen_api(
    book_title: str,
    prior_knowledge_prompt: str,
    model_name: str = "qwen-plus",
    temperature: float = 0.3,
    max_tokens: int = 10,
) -> str:
    """
    Call the Qwen API (via DashScope) to classify a book based on its title.

    The classification determines whether the book likely contains rich visual
    content (charts, diagrams, etc.) and should be kept.

    Args:
        book_title (str): Title of the book (usually derived from filename).
        prior_knowledge_prompt (str): System prompt containing domain-specific rules.
        model_name (str): Qwen model to use (e.g., "qwen-plus").
        temperature (float): Sampling temperature for response variability.
        max_tokens (int): Maximum tokens in the response.

    Returns:
        str: One of 'keep', 'delete', or 'uncertain'
    """
    try:
        # Establish HTTPS connection to DashScope API endpoint
        conn = http.client.HTTPSConnection("dashscope.aliyuncs.com")

        # Retrieve the API key from environment variables for authentication
        API_KEY = os.getenv("DASHSCOPE_API_KEY")
        if not API_KEY:
            print("Error: DASHSCOPE_API_KEY environment variable not set.")
            return "uncertain"  # Return default value if API key is missing

        # Prepare the request payload with model parameters and classification instructions
        payload = {
            "model": model_name,  # Specify which Qwen model to use
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": f"""{prior_knowledge_prompt}""",  # Provide domain-specific classification rules
                    },
                    {
                        "role": "user",
                        "content": f"Classify this book based on title: {book_title}",  # Ask for classification of specific book
                    },
                ]
            },
            "parameters": {
                "temperature": temperature,  # Control randomness in model responses
                "max_tokens": max_tokens,  # Limit response length
            },
        }

        # Set up HTTP headers with authentication and content type
        headers = {
            "Authorization": f"Bearer {API_KEY}",  # Include API key for authentication
            "Content-Type": "application/json",  # Specify JSON payload format
        }

        # Send POST request to the text generation endpoint
        conn.request(
            "POST",
            "/api/v1/services/aigc/text-generation/generation",  # API endpoint for text generation
            json.dumps(payload),  # Convert Python object to JSON string
            headers,
        )

        # Get and process the API response
        res = conn.getresponse()  # Retrieve HTTP response object
        data = res.read()  # Read the response body
        response = json.loads(data.decode("utf-8"))  # Parse JSON response

        # Check if the response contains expected structure and extract classification
        if "output" in response and "text" in response["output"]:
            # Extract and normalize the classification result
            result = response["output"]["text"].strip().upper()
            # Map API response to our classification categories
            if "KEEP" in result:
                return "keep"  # Book contains visual content worth keeping
            elif "DELETE" in result:
                return "delete"  # Book likely lacks visual content
            else:
                return "uncertain"  # Classification was ambiguous
        else:
            # Handle unexpected API response format
            print(f"Unexpected API response format: {response}")
            return "uncertain"  # Default to uncertain on error

    except Exception as e:
        # Handle any API call failures gracefully
        print(f"API call failed for '{book_title}': {e}")
        return "uncertain"  # Default to uncertain on failure
    finally:
        # Ensure connection is properly closed to prevent resource leaks
        conn.close()


def _move_files(files: List[str], destination_folder: str, base_folder: str) -> int:
    """
    Move a list of files to a destination subfolder, handling name conflicts.

    If a file with the same name exists, appends a counter (e.g., file_1.pdf).

    Args:
        files (List[str]): List of source file paths.
        destination_folder (str): Name of subfolder (e.g., "to_keep").
        base_folder (str): Parent directory containing destination subfolder.

    Returns:
        int: Number of successfully moved files.
    """
    # Initialize counter to track successfully moved files
    moved_count = 0
    # Construct full path to destination directory
    dest_path = os.path.join(base_folder, destination_folder)

    # Process each file in the list
    for file_path in files:
        try:
            # Extract just the filename from the full path
            file_name = os.path.basename(file_path)
            # Construct destination file path
            dest_file_path = os.path.join(dest_path, file_name)

            # Handle potential filename conflicts by adding counter suffix
            counter = 1
            original_name = file_name  # Store original name for reference
            while os.path.exists(dest_file_path):
                # Split filename and extension to insert counter between them
                name, ext = os.path.splitext(original_name)
                # Create new filename with counter suffix
                dest_file_path = os.path.join(dest_path, f"{name}_{counter}{ext}")
                counter += 1  # Increment counter for next potential conflict

            # Actually move the file from source to destination
            shutil.move(file_path, dest_file_path)
            moved_count += 1  # Increment successful move counter
        except Exception as e:
            # Log any errors that occur during file moving
            print(f"Failed to move {file_path}: {e}")

    # Return total count of successfully moved files
    return moved_count


def _process_books_with_qwen(
    files_to_process: List[str],
    base_folder: str,
    prior_knowledge_prompt: str,
    model_name: str = "qwen-plus",
    temperature: float = 0.3,
    max_tokens: int = 10,
    delay_between_calls: float = 1.0,
) -> None:
    """
    Classify each book using the Qwen API and move to appropriate folders.

    Args:
        files_to_process (List[str]): List of PDF file paths to classify.
        base_folder (str): Root directory for output subfolders.
        prior_knowledge_prompt (str): Domain-specific classification rules.
        model_name (str): Qwen model name.
        temperature (float): LLM sampling temperature.
        max_tokens (int): Max tokens in LLM response.
        delay_between_calls (float): Seconds to wait between API calls (rate limiting).
    """
    # Print status message to indicate start of classification process
    print(f"Processing {len(files_to_process)} books with Qwen classification...")

    # Initialize lists to store files based on their classification results
    qwen_to_delete = []  # Files classified as not containing visual content
    qwen_to_keep = []  # Files classified as containing valuable visual content
    qwen_uncertain = []  # Files with ambiguous classification results

    # Process each file through the Qwen API classification
    for i, file_path in enumerate(files_to_process):
        # Extract book title from filename (remove extension)
        file_name = os.path.basename(file_path)
        title = os.path.splitext(file_name)[0]

        # Call the Qwen API to classify the current book based on its title
        result = _call_qwen_api(
            book_title=title,
            prior_knowledge_prompt=prior_knowledge_prompt,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Categorize the file based on API classification result
        if result == "keep":
            qwen_to_keep.append(file_path)  # Add to keep list
        elif result == "delete":
            qwen_to_delete.append(file_path)  # Add to delete list
        else:
            qwen_uncertain.append(file_path)  # Add to uncertain list

        # Implement rate limiting by adding delay between API calls (except for last file)
        if i < len(files_to_process) - 1:  # No delay after processing the last file
            time.sleep(delay_between_calls)

    # Move all classified files to their respective destination folders
    deleted_count = _move_files(qwen_to_delete, "to_delete", base_folder)
    kept_count = _move_files(qwen_to_keep, "to_keep", base_folder)
    uncertain_count = _move_files(qwen_uncertain, "uncertain", base_folder)

    # Print summary of classification results
    print(f"\nClassification Results:")
    print(f"Moved to 'to_delete': {deleted_count} files")
    print(f"Moved to 'to_keep': {kept_count} files")
    print(f"Moved to 'uncertain': {uncertain_count} files")


def process_books(
    input_dir: str,
    auto_cleanup: bool = False,
    size_threshold: int = 5 * 1024 * 1024,
    prior_knowledge_prompt: str = None,
    model_name: str = "qwen-plus",
    temperature: float = 0.3,
    max_tokens: int = 10,
    delay_between_calls: float = 1.0,
) -> None:
    """
    Main orchestration function for PDF classification pipeline.

    Steps:
    1. Validate input directory
    2. Create output subdirectories
    3. Initial screening (size + extension)
    4. Delete low-quality files
    5. Classify remaining PDFs via Qwen API
    6. (Optional) Auto-cleanup: restore files and remove classification folders

    Args:
        input_dir (str): Input directory containing PDFs.
        auto_cleanup (bool): If True, restore files and remove classification folders.
        size_threshold (int): Min file size in bytes to consider (default: 5MB).
        prior_knowledge_prompt (str): Custom prompt for Qwen classification.
        model_name (str): Qwen model to use.
        temperature (float): LLM temperature.
        max_tokens (int): Max tokens in response.
        delay_between_calls (float): Delay between API calls in seconds.
    """
    # Validate that the input directory exists before proceeding
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    # Use default classification prompt if none is provided by user
    if prior_knowledge_prompt is None:
        prior_knowledge_prompt = """
You are an expert book classifier tasked with determining whether a given book title, presented in either English or Chinese, is likely to contain a substantial number of clear images, illustrations, charts, or diagrams. Your classification must be based solely on the title and informed by established domain knowledge about typical content formats across genres.

Domain Knowledge Guidelines:

Books LIKELY to contain lots of images/illustrations (KEEP):
- Technical analysis books (技术分析)
- Chart pattern books (形态学, 图表分析)
- Trading strategy books (看盘, 趋势跟踪)
- Candlestick/K-line analysis (k线, 蜡烛图)
- Moving average analysis (均线)
- Short-term trading (短线交易)
- Elliott wave theory (艾略特波浪理论)
- Chart pattern recognition (形态识别)
- Technical indicators (技术指标)
- Diagram-based analysis (图解分析)

Books UNLIKELY to contain lots of images (DELETE):
- Biographies/Memoirs (人物传记)
- Personal finance theory (个人理财)
- Business management (公司管理)
- Forum discussions (论坛留言)
- Entrepreneurship courses (创业教学)
- Sales training (销售教学)
- Historical economics (历史经济)
- Theoretical finance (金融理论)
- Philosophy books (哲学类)
- Pure text-based analysis (纯文字分析)

Classification Protocol:
1. Examine the book title carefully, noting keywords, implied methodology, and subject domain.
2. Assess whether the topic inherently relies on visual representation (e.g., charts, graphs, annotated diagrams).
3. If the title clearly suggests a visually driven approach (e.g., "chart," "pattern," "illustrated," "K-line," "图解," "形态"), classify as KEEP.
4. If the title indicates a theoretical, narrative, or text-based treatment (e.g., "theory," "principles," "history," "management," "传记," "哲学"), classify as DELETE.
5. If the title is ambiguous or lacks sufficient contextual cues to determine visual density, classify as UNCERTAIN.

Examples:

- Technical Analysis of the Financial Markets return 'KEEP'  
- 股票技术分析入门 return 'KEEP'  
- The Intelligent Investor return 'DELETE'  
- 巴菲特传记 return 'DELETE'  
- Japanese Candlestick Charting Techniques return 'KEEP'  
- k线/蜡烛图实战精髓 return 'KEEP'  
- Principles of Corporate Finance return 'DELETE'  
- 看盘技巧图解 return 'KEEP'  
- Market Wizards: Interviews with Top Traders return 'DELETE'  
- 艾略特波浪理论实战 return 'KEEP'  

Output Requirement:  
Respond with EXACTLY ONE WORD: 'KEEP', 'DELETE', or 'UNCERTAIN'
"""

    # Step 1: Create the required output subdirectories for organizing results
    _create_directories(input_dir)

    # Step 2: Perform initial screening to filter out files that don't meet basic criteria
    files_to_delete, files_to_process = _get_files_to_delete_initial(
        input_dir, size_threshold=size_threshold
    )

    # Print initial screening statistics to user
    print(f"Initial screening:")
    print(
        f"Files to delete (under {size_threshold / (1024*1024):.1f}MB or non-PDF): {len(files_to_delete)}"
    )
    print(f"Files to process further: {len(files_to_process)}")

    # Step 3: Permanently delete files that failed initial screening
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            # Actually remove the file from the filesystem
            os.remove(file_path)
            deleted_count += 1
        except Exception as e:
            # Log any errors that occur during file deletion
            print(f"Failed to delete {file_path}: {e}")

    # Print summary of initial screening results
    print(
        f"\nDeleted {deleted_count}/{len(files_to_delete)} files in initial screening"
    )

    # Check if any files remain for further processing
    if not files_to_process:
        print("No files left for Qwen processing.")
        return

    # Step 4: Use Qwen API to perform semantic classification on remaining files
    _process_books_with_qwen(
        files_to_process=files_to_process,
        base_folder=input_dir,
        prior_knowledge_prompt=prior_knowledge_prompt,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        delay_between_calls=delay_between_calls,
    )

    # Print completion message
    print("\nProcessing complete!")

    # Step 5: Handle optional auto-cleanup based on user preference
    if not auto_cleanup:
        print(
            "Manual review mode: Skipping cleanup. Check 'to_keep', 'to_delete', 'uncertain' folders."
        )
        return

    # Restore files that should be kept (and uncertain files) back to main directory
    for folder_name in ["to_keep", "uncertain"]:
        folder_path = os.path.join(input_dir, folder_name)
        if os.path.exists(folder_path):
            # Move each file from the classification folder back to main directory
            for filename in os.listdir(folder_path):
                src = os.path.join(
                    folder_path, filename
                )  # Source path in classification folder
                dst = os.path.join(
                    input_dir, filename
                )  # Destination path in main directory
                shutil.move(src, dst)  # Move file back to main directory
            os.rmdir(folder_path)  # Remove empty classification folder
            print(f"Restored files from '{folder_name}' to '{input_dir}'")

    # Remove the to_delete folder entirely since we don't want those files back
    to_delete_path = os.path.join(input_dir, "to_delete")
    if os.path.exists(to_delete_path):
        shutil.rmtree(to_delete_path)  # Remove entire folder and its contents
        print(f"Deleted '{to_delete_path}' and its contents.")

    print("Auto-cleanup completed.")


def filter_pdfs(
    input_dir: str = "input",
    auto_cleanup: bool = False,
    size_threshold: int = 1,
    prompt: str = None,
    model_name: str = "qwen-plus",
    temperature: float = 0.3,
    max_tokens: int = 10,
    delay_between_calls: float = 1.0,
) -> None:
    """
    Public API for PDF classification. Validates inputs and starts processing.

    Args:
        input_dir (str): Directory with PDFs to classify.
        auto_cleanup (bool): Enable automatic post-processing cleanup.
        size_threshold (int): Minimum file size in bytes (default: 5MB).
        prior_knowledge_prompt (str): Path to a file containing the custom prompt for LLM classification.
                                      If None, uses built-in default prompt.
        model_name (str): Qwen model name.
        temperature (float): LLM temperature.
        max_tokens (int): Max tokens in LLM response.
        delay_between_calls (float): Delay between API calls (seconds).

    Raises:
        FileNotFoundError: If input_dir does not exist or prompt file is not found.
        NotADirectoryError: If input_dir is not a directory.
    """
    # Convert size threshold from MB to bytes (multiply by 1024*1024)
    size_threshold *= 1024 * 1024

    # Validate that the input directory exists and is actually a directory
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f"'{input_dir}' is not a valid directory.")

    # Print startup message to inform user about the process
    print(f"Starting PDF classification in '{input_dir}'...")

    # Call the main processing function with validated parameters
    process_books(
        input_dir=input_dir,
        auto_cleanup=auto_cleanup,
        size_threshold=size_threshold,
        prior_knowledge_prompt=prompt,  # pass the content, not the path
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        delay_between_calls=delay_between_calls,
    )


if __name__ == "__main__":
    # Example usage of the PDF filtering function
    filter_pdfs(
        input_dir="raw_pdfs",  # Directory containing PDFs to process
        auto_cleanup=False,  # Don't automatically restore files after classification
        size_threshold=1,  # Minimum size threshold (1MB converted to bytes in function)
        prompt=prompt_for_pdf_filter(),  # Custom classification rules
    )
