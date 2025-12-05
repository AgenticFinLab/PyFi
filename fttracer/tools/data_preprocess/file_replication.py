"""Script to copy selected files based on indices from a text file.

This script reads file indices from a text file and copies corresponding files 
from a source directory structure to an output directory. It supports both 
flat and nested directory structures with automatic file extension detection.
"""

import os
import shutil
from typing import Optional, List


def copy_selected_files(
    txt_path: str,
    base_dir: str,
    output_dir: str,
) -> dict:
    """
    Copy selected files based on indices from a text file to output directory.

    Supports both flat directory structures (no subfolders) and nested structures
    (with subfolders). Automatically detects file extensions in the source directories.

    Args:
        txt_path (str): Path to the text file containing file indices (format: XXXXXX-XXXXXX)
        base_dir (str): Base directory path containing source files and folders
        output_dir (str): Output directory path for copied files

    Returns:
        dict: Statistics about the copy operation including counts and missing files
    """

    # Create output directory if it doesn't exist to ensure destination is ready
    os.makedirs(output_dir, exist_ok=True)

    # Initialize counters and tracking lists for operation statistics
    copied_count = 0
    missing_files = []
    processed_lines = 0

    # Get all subdirectories in base_dir to determine structure type for each folder
    base_subdirs = [
        d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))
    ]

    # Calculate the total number of subdirectories in the base directory for success rate calculation
    total_subdirs = len(base_subdirs)

    # Process each line in the input text file containing file indices
    with open(txt_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            # Read and clean the current line from the text file
            line = line.strip()

            # Skip empty lines to avoid processing invalid entries
            if not line:
                continue

            # Increment the counter for successfully processed lines
            processed_lines += 1

            try:
                # Parse folder ID and file ID from the current line using dash delimiter
                # Expected format: "XXXXXX-XXXXXX" where first part is folder_id and second is file_id
                folder_id, file_id = line.split("-")

                # Iterate through each subdirectory in base_dir to process all folders
                for subdir in base_subdirs:
                    # Construct the full path to the current source subdirectory
                    source_folder_path = os.path.join(base_dir, subdir)

                    # Determine if the current source folder has subdirectories (nested structure)
                    # This checks if there are additional subdirectories within each source folder
                    subfolders = [
                        d
                        for d in os.listdir(source_folder_path)
                        if os.path.isdir(os.path.join(source_folder_path, d))
                    ]

                    # Create corresponding destination folder in output directory
                    # This maintains the same folder structure as the source
                    dest_folder_path = os.path.join(output_dir, subdir)
                    os.makedirs(dest_folder_path, exist_ok=True)

                    if subfolders:
                        # Handle nested directory structure case
                        # Example structure: base_dir/source_folder/000001/000045.json
                        # In this case, folder_id refers to the subfolder name (000001)
                        # and file_id refers to the actual file name (000045)

                        # Construct path to the subfolder that should contain the target file
                        subfolder_path = os.path.join(source_folder_path, folder_id)

                        # Check if the expected subfolder exists in the source directory
                        if os.path.exists(subfolder_path):
                            # Find the file with file_id and any extension in the subfolder
                            # This handles cases where file extensions may vary (e.g., .json, .txt, .py)
                            source_file = None
                            for file in os.listdir(subfolder_path):
                                # Look for files that start with file_id followed by a dot and extension
                                if file.startswith(
                                    file_id + "."
                                ):  # File starts with file_id followed by dot
                                    source_file = file
                                    break

                            if source_file:
                                # Construct source and destination paths for nested structure
                                # Source: base_dir/source_folder/folder_id/file_id.extension
                                # Destination: output_dir/source_folder/folder_id/file_id.extension
                                source_path = os.path.join(subfolder_path, source_file)
                                dest_subfolder_path = os.path.join(
                                    dest_folder_path, folder_id
                                )
                                # Create destination subfolder if it doesn't exist
                                os.makedirs(dest_subfolder_path, exist_ok=True)
                                dest_path = os.path.join(
                                    dest_subfolder_path, source_file
                                )

                                # Copy the file with metadata preservation (copy2 preserves timestamps, etc.)
                                shutil.copy2(source_path, dest_path)
                                copied_count += 1
                                print(f"Copied: {source_path} -> {dest_path}")
                            else:
                                # Record missing file in nested structure for statistics
                                missing_file_info = (
                                    f"{subdir}/{folder_id}/{file_id}.* (any extension)"
                                )
                                missing_files.append(missing_file_info)
                                print(
                                    f"File not found in nested structure: {subfolder_path}/{file_id}.*"
                                )
                        else:
                            # Record missing subfolder for statistics
                            missing_file_info = (
                                f"{subdir}/{folder_id} subfolder not found"
                            )
                            missing_files.append(missing_file_info)
                            print(
                                f"Subfolder {folder_id} not found in {subfolder_path}"
                            )

                    else:
                        # Handle flat directory structure case
                        # Example structure: base_dir/markdown/000001.md
                        # In this case, folder_id is both the folder identifier from the text file
                        # and the actual filename (with extension) in the flat structure

                        # Find the file with folder_id as base name and any extension in the source folder
                        source_file = None
                        for file in os.listdir(source_folder_path):
                            # Look for files that start with folder_id followed by a dot and extension
                            if file.startswith(
                                folder_id + "."
                            ):  # File starts with folder_id followed by dot
                                source_file = file
                                break

                        if source_file:
                            # Construct source and destination paths for flat structure
                            # Source: base_dir/source_folder/folder_id.extension
                            # Destination: output_dir/source_folder/folder_id.extension
                            source_path = os.path.join(source_folder_path, source_file)
                            dest_path = os.path.join(dest_folder_path, source_file)

                            # Copy the file with metadata preservation
                            shutil.copy2(source_path, dest_path)
                            copied_count += 1
                            print(f"Copied: {source_path} -> {dest_path}")
                        else:
                            # Record missing file in flat structure for statistics
                            missing_file_info = (
                                f"{subdir}/{folder_id}.* (any extension)"
                            )
                            missing_files.append(missing_file_info)
                            print(
                                f"File not found in flat structure: {source_folder_path}/{folder_id}.*"
                            )

            except ValueError as e:
                # Handle malformed lines in the text file that don't match expected format
                # Expected format is "XXXXXX-XXXXXX" with a single dash separator
                print(f"Error parsing line {line_num}: '{line}' - {e}")
                continue
            except Exception as e:
                # Handle any other unexpected errors during file processing
                # This could include permission errors, disk space issues, etc.
                print(f"Unexpected error processing line {line_num}: {e}")
                continue

    # Prepare comprehensive statistics for return
    # Calculate success rate based on total number of subdirectories in base directory
    # This provides a more meaningful success rate than dividing by processed lines
    stats = {
        "total_processed": processed_lines,
        "files_copied": copied_count,
        "missing_files": missing_files,
        "missing_count": len(missing_files),
        "total_subdirs": total_subdirs,
        "success_rate": (
            (copied_count / total_subdirs / processed_lines * 100)
            if total_subdirs > 0
            else 0
        ),
    }

    # Print final operation statistics for user feedback
    print("\n=== COPY OPERATION SUMMARY ===")
    print(f"Lines processed from text file: {processed_lines}")
    print(f"Files copied successfully: {copied_count}")
    print(f"Missing files: {len(missing_files)}")
    print(f"Total source subdirectories in base directory: {total_subdirs}")
    print(f"Success rate: {stats['success_rate']:.1f}%")

    # Report any missing files for user awareness and troubleshooting
    if missing_files:
        print(f"\nThe following {len(missing_files)} files were not found:")
        for i, missing_file in enumerate(missing_files, 1):
            print(f"  {i}. {missing_file}")

    # Return statistics dictionary for potential external use
    return stats


if __name__ == "__main__":
    # Execute the main function with specified parameters
    # txt_path: Path to the text file containing file indices
    # base_dir: Base directory containing the source files and folder structure
    # output_dir: Directory where selected files will be copied
    copy_selected_files(
        txt_path="sampled_images_indices_filtered.txt",
        base_dir="PyFi",
        output_dir="PyFi_selected",
    )
