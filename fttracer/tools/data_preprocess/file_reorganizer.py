"""Utility for processing image references in multiple Markdown files.

This script processes a directory structure containing book folders, each with:
- A full.md file containing Markdown content with image references
- An images/ folder containing the referenced images
- Optionally, a PDF file

The script performs the following operations:
1. Validates input directory structure
2. Processes each book's Markdown file to update image references
3. Copies and renames images to a standardized output structure
4. Creates a new directory structure with sequential numbering

Example directory structure:
  input/
    ├── BookA/
    │   ├── full.md
    │   ├── images/
    │   │   └── fig1.jpg
    │   └── BookA.pdf
    └── BookB/
        ├── full.md
        ├── images/
        │   └── fig2.jpg
        └── BookB.pdf

Output directory structure:
  output/
    ├── markdown/
    │   ├── 000001.md
    │   └── 000002.md
    ├── images/
    │   ├── 000001/
    │   │   └── 000001.jpg
    │   └── 000002/
    │       └── 000001.jpg
    └── pdf/
        ├── 000001.pdf
        └── 000002.pdf
"""

import os
import re
import shutil

from typing import List, Optional


def check_input(root_dir: str = "input") -> None:
    """Check if input folders contain required files and delete folders with missing files.
    Also sanitize folder names by removing invalid characters and truncating long names.

    This function validates that each book folder contains the necessary files:
    - images folder with at least one image file
    - PDF file
    - full.md file

    Folders missing any required components are deleted to maintain data integrity.

    Args:
        root_dir: Root directory containing subfolders to check.
    """
    # Check if root directory exists
    if not os.path.exists(root_dir):
        print(f"Error: {root_dir} directory does not exist")
        return

    # Sanitize folder names first to ensure valid directory names
    _sanitize_folder_names(root_dir)

    # Counter to track how many folders were deleted during validation
    deleted_count = 0

    # Iterate through all subdirectories in the root directory
    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)

        # Only process directories, not files
        if os.path.isdir(folder_path):
            # Track which required components are present in this folder
            has_images = False  # Flag indicating presence of images folder with files
            has_pdf = False  # Flag indicating presence of PDF file
            has_full_md = False  # Flag indicating presence of full.md file

            # Check all items in the folder to determine which required components exist
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)

                # Check if item is an images folder and contains files
                if item == "images" and os.listdir(item_path):
                    has_images = True
                # Check if item is a PDF file and is actually a file (not directory)
                elif item.endswith(".pdf") and os.path.isfile(item_path):
                    has_pdf = True
                # Check if item is the required full.md file and is actually a file
                elif item == "full.md" and os.path.isfile(item_path):
                    has_full_md = True

            # Check if any required items are missing from this folder
            missing_items = []
            if not has_images:
                missing_items.append("images folder")
            if not has_pdf:
                missing_items.append("pdf file")
            if not has_full_md:
                missing_items.append("full.md file")

            # If any required components are missing, delete the entire folder
            if missing_items:
                # Delete the incomplete folder to maintain data integrity
                try:
                    shutil.rmtree(folder_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting folder {folder_name}: {e}")

    print(f"Total deleted folders: {deleted_count}")


def _sanitize_folder_names(root_dir: str) -> None:
    """Sanitize folder names by removing invalid characters and truncating long names.

    This function ensures that all folder names are valid for the file system by:
    - Removing characters that are invalid in file/directory names
    - Truncating names that are too long
    - Handling potential naming conflicts

    Args:
        root_dir: Root directory containing subfolders to sanitize.
    """
    # Iterate through all items in the root directory
    for folder_name in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder_name)

        # Only process directories, not files
        if os.path.isdir(folder_path):
            # Remove invalid characters and replace with underscore
            # These characters are invalid on Windows and problematic on other systems:
            # < > : " / \ | ? * and control characters (0x00-0x1F)
            sanitized_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", folder_name)

            # Truncate if name is too long (limit to 100 characters for safety)
            if len(sanitized_name) > 100:
                sanitized_name = sanitized_name[:100]

            # Remove leading/trailing whitespace and dots which can cause issues
            sanitized_name = sanitized_name.strip(". ")

            # If name becomes empty after sanitization, use a default name
            if not sanitized_name:
                sanitized_name = "unnamed_folder"

            # Rename folder if the sanitized name is different from original
            if sanitized_name != folder_name:
                new_path = os.path.join(root_dir, sanitized_name)

                # Handle potential name conflicts by adding a counter suffix
                counter = 1
                original_name = sanitized_name
                while os.path.exists(new_path) and new_path != folder_path:
                    sanitized_name = f"{original_name}_{counter}"
                    new_path = os.path.join(root_dir, sanitized_name)
                    counter += 1

                # Attempt to rename the folder
                try:
                    os.rename(folder_path, new_path)
                    print(f"Renamed folder: {folder_name} -> {sanitized_name}")
                except Exception as e:
                    print(f"Error renaming folder {folder_name}: {e}")


def _collect_image_references(content: str) -> List[str]:
    """Return all relative image paths found in the Markdown content.

    This function uses a regular expression to find all Markdown image references
    that follow the pattern ![](images/...). It extracts the relative path
    from the parentheses, which should start with "images/".

    Args:
        content: The Markdown file content as a string.

    Returns:
        A list of relative image paths matching the pattern.
    """
    # Regular expression pattern to match Markdown image references
    # Pattern explanation:
    # ![] - literal characters for Markdown image syntax
    # (images/[^)]+) - capturing group for relative path starting with "images/"
    # [^)]+ - matches one or more characters that are not closing parenthesis
    pattern = r"!\[\]\((images/[^)]+)\)"
    return re.findall(pattern, content)


def _copy_and_rename_image(
    source_path: str,
    destination_dir: str,
    sequence: int,
) -> Optional[str]:
    """Copy an image to the destination directory with a zero-padded filename.

    This function copies an image file to a new location and renames it using
    a sequential number with zero-padding (e.g., 000001.jpg, 000002.jpg).

    Args:
        source_path: Absolute path to the original image.
        destination_dir: Absolute path to the directory where the image will be copied.
        sequence: Integer used to generate the new filename.

    Returns:
        The new filename (without directory) on success, or None if the
        source file does not exist.
    """
    # Check if the source file exists before attempting to copy
    if not os.path.isfile(source_path):
        print(f"Warning: Image file does not exist – {source_path}")
        return None

    # Extract the file extension from the original filename
    extension = os.path.splitext(source_path)[1]

    # Generate the new filename using zero-padded sequence number
    new_filename = f"{sequence:06d}{extension}"

    # Create the full destination path
    destination_path = os.path.join(destination_dir, new_filename)

    # Copy the file preserving metadata (shutil.copy2 preserves timestamps and permissions)
    shutil.copy2(source_path, destination_path)
    return new_filename


def process_markdown_images(
    md_file_path: str,
    output_base_dir: str,
    book_number: int,
    image_counter: int,
) -> int:
    """Process image references in a Markdown file.

    Images referenced as `![](images/xxx.jpg)` are copied to
    `{output_base_dir}/images/{book_number:06d}` and renamed sequentially.
    A new Markdown file with updated references is saved to
    `{output_base_dir}/markdown/{book_number:06d}.md`.

    This function performs the core image processing logic:
    1. Reads the Markdown file
    2. Finds all image references
    3. Copies and renames images to standardized locations
    4. Updates the Markdown content with new image references
    5. Saves the processed Markdown file

    Args:
        md_file_path: Path to the Markdown file to process.
        output_base_dir: Base directory where markdown, images, pdf will be saved.
        book_number: Current book index for naming.
        image_counter: Starting number for image sequence.

    Returns:
        Updated image counter after processing, or unchanged counter if no images found.
    """
    # Get the directory containing the Markdown file to resolve relative paths
    md_dir = os.path.dirname(os.path.abspath(md_file_path))

    # Read the Markdown file content
    with open(md_file_path, encoding="utf-8") as file_handle:
        content = file_handle.read()

    # Find all image references in the Markdown content
    image_references = _collect_image_references(content)
    if not image_references:
        print("No image references found.")
        return image_counter

    print(f"Found {len(image_references)} image reference(s).")

    # Create output directories only when we have images to process
    # This ensures we don't create empty directories for books without images
    markdown_output_dir = os.path.join(output_base_dir, "markdown")
    images_output_dir = os.path.join(output_base_dir, "images", f"{book_number:06d}")
    os.makedirs(markdown_output_dir, exist_ok=True)
    os.makedirs(images_output_dir, exist_ok=True)

    # Process each image reference found in the Markdown file
    counter = 1
    for rel_path in image_references:
        # Convert relative path to absolute path based on the Markdown file location
        original_abs_path = os.path.join(md_dir, rel_path)

        # Copy and rename the image file with sequential numbering
        new_filename = _copy_and_rename_image(
            source_path=original_abs_path,
            destination_dir=images_output_dir,
            sequence=counter,
        )

        # Skip processing this image if the source file doesn't exist
        if new_filename is None:
            continue

        # Update the Markdown content to reference the new image location
        # The new reference points to the standardized location with sequential naming
        new_ref = f"![](../images/{book_number:06d}/{new_filename})"
        content = content.replace(f"![]({rel_path})", new_ref)
        counter += 1

    # Save the processed Markdown file only if we had images to process
    new_md_filename = f"{book_number:06d}.md"
    new_md_path = os.path.join(markdown_output_dir, new_md_filename)
    with open(new_md_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(content)

    return counter


def _count_files_in_directory(directory: str) -> int:
    """Count the number of files in a directory recursively.

    This helper function walks through a directory tree and counts all files,
    including those in subdirectories. It's used for generating statistics.

    Args:
        directory: Path to the directory to count files in.

    Returns:
        Total number of files found in the directory and its subdirectories.
    """
    count = 0
    # Walk through directory tree, counting files in each subdirectory
    for root, _, files in os.walk(directory):
        count += len(files)
    return count


def _print_statistics(output_base_dir: str) -> None:
    """Print statistics about the processed files.

    This function generates and displays summary statistics about the
    processing operation, showing how many files were created in each category.

    Args:
        output_base_dir: Base directory where output files were saved.
    """
    # Define paths to the output subdirectories
    markdown_dir = os.path.join(output_base_dir, "markdown")
    images_dir = os.path.join(output_base_dir, "images")
    pdf_dir = os.path.join(output_base_dir, "pdf")

    # Count files in each directory, handling cases where directories don't exist
    markdown_count = (
        _count_files_in_directory(markdown_dir) if os.path.exists(markdown_dir) else 0
    )
    images_count = (
        _count_files_in_directory(images_dir) if os.path.exists(images_dir) else 0
    )
    pdf_count = _count_files_in_directory(pdf_dir) if os.path.exists(pdf_dir) else 0

    # Display the processing statistics in a formatted manner
    print("\nPROCESSING STATISTICS\n")
    print(f"Markdown files: {markdown_count}")
    print(f"Image files: {images_count}")
    print(f"PDF files: {pdf_count}")


def reorganize_file(input_dir: str, output_dir: str) -> None:
    """Traverse root directory, process each book folder.

    Each book folder should contain:
        - full.md
        - images/ folder
        - optionally, a .pdf file

    Books without image references will be deleted entirely.

    This is the main processing function that orchestrates the entire workflow:
    1. Validates input structure
    2. Processes each book sequentially
    3. Handles both image processing and PDF copying
    4. Manages the output directory structure

    Args:
        input_dir: Root directory containing book folders.
        output_dir: Base directory for output files.
    """
    # First, validate and clean up the input directory
    check_input(input_dir)

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get list of book folders and sort them for consistent processing order
    book_folders = [
        d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))
    ]
    book_folders.sort()  # Sort for consistent numbering

    # Handle case where no valid book folders exist
    if not book_folders:
        print(f"No book folders found in {input_dir}")
        return

    # Initialize counters for tracking processing progress
    image_counter = 1  # Counter for sequential image numbering
    processed_books = 0  # Count of successfully processed books
    deleted_books = 0  # Count of books deleted due to missing images

    # Use a while loop to handle dynamic folder list changes
    # This is necessary because folders may be deleted during processing
    idx = 1  # Sequential book number for output naming
    folder_index = 0  # Current index in the folder list

    while folder_index < len(book_folders):
        # Get the current book folder name and path
        book_folder = book_folders[folder_index]
        book_path = os.path.join(input_dir, book_folder)
        full_md_path = os.path.join(book_path, "full.md")

        # Refresh folder list in case folders were deleted during processing
        current_folders = [
            d
            for d in os.listdir(input_dir)
            if os.path.isdir(os.path.join(input_dir, d))
        ]
        current_folders.sort()

        # Update book_folders if needed due to deletions
        if len(current_folders) != len(book_folders):
            book_folders = current_folders
            if folder_index >= len(book_folders):
                break

        # Skip processing if the required full.md file doesn't exist
        if not os.path.isfile(full_md_path):
            print(f"Skipping {book_folder}: no full.md found.")
            folder_index += 1
            continue

        print(f"\nProcessing book {idx}")

        # Process markdown and images for the current book
        original_image_counter = image_counter
        image_counter = process_markdown_images(
            md_file_path=full_md_path,
            output_base_dir=output_dir,
            book_number=idx,
            image_counter=image_counter,
        )

        # Only process PDF and finalize book processing if images were found
        if image_counter > original_image_counter:
            # Increment the count of processed books
            processed_books += 1

            # Reset image counter for next book (start from 1 again)
            image_counter = 1

            # Handle PDF file processing - only if the book had images
            pdf_files = [f for f in os.listdir(book_path) if f.endswith(".pdf")]
            if pdf_files:
                # Take the first PDF file found (assuming only one per book)
                pdf_file = pdf_files[0]
                src_pdf = os.path.join(book_path, pdf_file)

                # Create PDF output directory and copy the PDF file
                dst_pdf_dir = os.path.join(output_dir, "pdf")
                os.makedirs(dst_pdf_dir, exist_ok=True)
                dst_pdf = os.path.join(dst_pdf_dir, f"{idx:06d}.pdf")
                shutil.copy2(src_pdf, dst_pdf)

            # Move to next folder and increment book number
            folder_index += 1
            idx += 1
        else:
            # No images were found in this book, so reset counter and delete the book
            image_counter = 1
            print(f"Deleting {book_folder}: no images found.")

            # Delete the entire book folder since it has no images
            try:
                shutil.rmtree(book_path)
                print(f"Successfully deleted folder: {book_folder}")
                deleted_books += 1

                # Refresh the folder list after deletion since structure changed
                book_folders = [
                    d
                    for d in os.listdir(input_dir)
                    if os.path.isdir(os.path.join(input_dir, d))
                ]
                book_folders.sort()
            except Exception as e:
                # If deletion fails, still move to next folder to avoid infinite loop
                print(f"Error deleting folder {book_folder}: {e}")
                folder_index += 1
                idx += 1

    # Print final processing statistics
    _print_statistics(output_dir)


if __name__ == "__main__":
    # Default input and output directories
    input_dir = "input"  # Directory containing book folders to process
    output_dir = "output"  # Directory where processed files will be saved

    # Execute the main reorganization process
    reorganize_file(input_dir, output_dir)
