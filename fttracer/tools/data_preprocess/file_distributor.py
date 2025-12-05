"""File distribution utility for organizing image-context pairs into a structured directory.

This module provides functionality to distribute image files and their corresponding
context files into a predefined directory structure with multiple server and shell levels.
The structure is designed to distribute files evenly across a hierarchical organization
for better data management and potential parallel processing scenarios.
"""

import os
import shutil
import glob
from pathlib import Path
from socket import IPV6_UNICAST_HOPS


def create_directory_structure(
    data_folder_root, num_servers=25, num_shells_per_server=20
):
    """Create the target directory structure.

    Creates a main data folder containing server folders, each with shell folders.
    Each shell folder contains 'images' and 'context' subdirectories.

    Args:
        data_folder_root (str or Path): Root path where the directory structure will be created
        num_servers (int): Number of server folders to create (default: 25)
        num_shells_per_server (int): Number of shell folders per server (default: 20)
    """
    # Create main folder
    data_folder = Path(data_folder_root)
    data_folder.mkdir(exist_ok=True)

    # Create server folders, each containing shell folders
    for server_num in range(1, num_servers + 1):  # e.g., 001-025 if num_servers=25
        server_name = f"data_server_{server_num:03d}"
        server_path = data_folder / server_name

        for shell_num in range(
            1, num_shells_per_server + 1
        ):  # e.g., 001-020 if num_shells_per_server=20
            shell_name = f"data_shell_{shell_num:03d}"
            shell_path = server_path / shell_name

            # Create images and context subdirectories within each shell
            (shell_path / "images").mkdir(parents=True, exist_ok=True)
            (shell_path / "context").mkdir(parents=True, exist_ok=True)

    print(
        f"Directory structure created successfully: {num_servers} servers × {num_shells_per_server} shells per server"
    )


def get_all_image_context_pairs(images_root, context_root, image_extension=".jpg"):
    """Find all valid image-context file pairs.

    This function walks through the images_root directory to find all image files,
    then attempts to find corresponding context files in the same relative path
    within the context_root directory.

    Args:
        images_root (str or Path): Root directory containing image files
        context_root (str or Path): Root directory containing context JSON files
        image_extension (str): File extension for image files (default: ".jpg")

    Returns:
        List[dict]: List of dictionaries containing paths to matched image-context pairs
                   Each dictionary has keys: "image", "context", "rel_path"
    """
    pairs = []
    missing_count = 0  # Track number of missing file pairs

    # Walk through all image files in the images_root directory
    for root, dirs, files in os.walk(images_root):
        for file in files:
            if file.lower().endswith(image_extension.lower()):
                # Build relative path from images_root to maintain folder structure
                rel_path = os.path.relpath(root, images_root)
                image_path = os.path.join(root, file)

                # Construct corresponding context file path
                json_file = os.path.splitext(file)[0] + ".json"
                context_path = os.path.join(context_root, rel_path, json_file)

                # Check if corresponding context file exists
                if os.path.exists(context_path):
                    pairs.append(
                        {
                            "image": image_path,  # Full path to image file
                            "context": context_path,  # Full path to context file
                            "rel_path": os.path.join(
                                rel_path, file
                            ),  # Relative path including filename
                        }
                    )
                else:
                    # Output information about missing context files for debugging
                    print(f"Missing context file: {image_path}")
                    print(f"Expected context path: {context_path}")
                    print("-" * 50)
                    missing_count += 1

    print(f"Found {len(pairs)} file pairs, missing {missing_count} pairs")
    return pairs


def distribute_files(pairs, data_folder, num_servers=25, num_shells_per_server=20):
    """Distribute file pairs evenly across all data_shell folders using round-robin distribution.

    This function distributes the collected image-context pairs across the created
    directory structure in a round-robin fashion to ensure even distribution.

    Args:
        pairs (list): List of image-context file pairs to distribute
        data_folder (str or Path): Root directory of the target structure
        num_servers (int): Number of server folders (should match create_directory_structure)
        num_shells_per_server (int): Number of shells per server (should match create_directory_structure)
    """
    total_shells = num_servers * num_shells_per_server  # Total number of target folders
    print(f"Distributing {len(pairs)} file pairs across {total_shells} folders")

    # Calculate approximate number of files per shell and handle remainder
    files_per_shell = len(pairs) // total_shells
    remainder = len(pairs) % total_shells
    print(
        f"Approximately {files_per_shell} files per shell, with {remainder} extra files distributed to first shells"
    )

    # Distribute files using round-robin approach
    for idx, pair in enumerate(pairs):
        # Calculate target shell index using modulo operation for round-robin distribution
        shell_idx = idx % total_shells
        server_num = shell_idx // num_shells_per_server + 1  # Server number (1-indexed)
        shell_num = (
            shell_idx % num_shells_per_server + 1
        )  # Shell number within server (1-indexed)

        server_name = f"data_server_{server_num:03d}"
        shell_name = f"data_shell_{shell_num:03d}"

        # Define target base path for this file pair
        target_base = Path(data_folder) / server_name / shell_name

        # Copy image file to target location, preserving relative directory structure
        target_image_dir = target_base / "images"
        rel_dir = os.path.dirname(pair["rel_path"])  # Extract relative directory path
        (target_image_dir / rel_dir).mkdir(
            parents=True, exist_ok=True
        )  # Create necessary subdirectories
        target_image_path = (
            target_image_dir / pair["rel_path"]
        )  # Full target path for image
        shutil.copy2(pair["image"], target_image_path)  # Copy with metadata

        # Copy context file to target location, preserving relative directory structure
        target_context_dir = target_base / "context"
        (target_context_dir / rel_dir).mkdir(
            parents=True, exist_ok=True
        )  # Create necessary subdirectories
        context_filename = (
            os.path.splitext(os.path.basename(pair["rel_path"]))[0] + ".json"
        )  # Extract filename without extension and add .json
        target_context_path = (
            target_context_dir / rel_dir / context_filename
        )  # Full target path for context
        shutil.copy2(pair["context"], target_context_path)  # Copy with metadata

        # Progress indicator every 1000 files processed
        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1} file pairs")

    print(
        f"Successfully distributed {len(pairs)} file pairs across {total_shells} shells"
    )


def file_distribution(
    input_dir="PyFi",
    num_servers=25,
    num_shells_per_server=20,
    image_extension=".jpg",
):
    """Main function to execute the file distribution process with configurable parameters.

    Args:
        images_root (str): Path to the directory containing image files
        context_root (str): Path to the directory containing context JSON files
        data_folder_root (str): Path where the organized directory structure will be created
        num_servers (int): Number of server folders to create in the structure
        num_shells_per_server (int): Number of shell folders per server
        image_extension (str): File extension to look for in image files (e.g., ".jpg", ".png")
    """

    # Construct paths for input directories
    images_root = os.path.join(input_dir, "images")
    context_root = os.path.join(input_dir, "context_summary_LLM")
    data_folder_root = os.path.join(input_dir, "data_folder")

    # Create target directory structure
    print(f"Starting file distribution process...")
    print(f"Images source: {images_root}")
    print(f"Context source: {context_root}")
    print(f"Target directory: {data_folder_root}")
    print(
        f"Structure: {num_servers} servers * {num_shells_per_server} shells per server"
    )

    # Count total image files for information
    image_files = list(
        glob.glob(os.path.join(images_root, f"**/*{image_extension}"), recursive=True)
    )
    print(f"Total {image_extension} files found: {len(image_files)}")

    # Count total context files for information
    context_files = list(
        glob.glob(os.path.join(context_root, "**/*.json"), recursive=True)
    )
    print("Total .json files found:", len(context_files))

    # Verify source paths exist before proceeding
    if not os.path.exists(images_root):
        print(f"Error: Image path does not exist - {images_root}")
        return
    if not os.path.exists(context_root):
        print(f"Error: Context path does not exist - {context_root}")
        return

    print("Creating directory structure...")
    create_directory_structure(data_folder_root, num_servers, num_shells_per_server)

    print("Collecting file pairs...")
    pairs = get_all_image_context_pairs(images_root, context_root, image_extension)
    print(f"Found {len(pairs)} valid image-context file pairs")

    if len(pairs) == 0:
        print("Warning: No valid file pairs found")
        return

    print("Distributing files...")
    distribute_files(pairs, data_folder_root, num_servers, num_shells_per_server)

    print("File distribution completed successfully!")


if __name__ == "__main__":
    # Example usage with default parameters
    file_distribution(
        input_dir="PyFi",
        num_servers=25,
        num_shells_per_server=20,
        image_extension=".jpg",
    )
