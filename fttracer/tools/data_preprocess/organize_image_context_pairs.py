"""File distribution utility for organizing image-context pairs into a structured directory.

This module provides functionality to distribute image files and their corresponding
context files into a predefined directory structure with multiple server and shell levels.
"""

import os
import shutil
import glob
from pathlib import Path


def create_directory_structure():
    """Create the target directory structure.

    Creates a main data folder containing 25 server folders, each with 20 shell folders.
    Each shell folder contains 'images' and 'context' subdirectories.
    """
    # Create main folder
    data_folder = Path("data_folder")
    data_folder.mkdir(exist_ok=True)

    # Create 25 data_server folders, each containing 20 data_shell folders
    for server_num in range(1, 26):  # 001-025
        server_name = f"data_server_{server_num:03d}"
        server_path = data_folder / server_name

        for shell_num in range(1, 21):  # 001-020
            shell_name = f"data_shell_{shell_num:03d}"
            shell_path = server_path / shell_name

            # Create images and context subdirectories
            (shell_path / "images").mkdir(parents=True, exist_ok=True)
            (shell_path / "context").mkdir(parents=True, exist_ok=True)

    print("Directory structure created successfully")


def get_all_image_context_pairs(images_root, context_root):
    """Find all valid image-context file pairs.

    Args:
        images_root: Root directory containing image files
        context_root: Root directory containing context JSON files

    Returns:
        List of dictionaries containing paths to matched image-context pairs
    """
    pairs = []
    missing_count = 0  # Track number of missing file pairs

    # Walk through all image files
    for root, dirs, files in os.walk(images_root):
        for file in files:
            if file.lower().endswith(".jpg"):
                # Build relative path
                rel_path = os.path.relpath(root, images_root)
                image_path = os.path.join(root, file)
                json_file = os.path.splitext(file)[0] + ".json"
                context_path = os.path.join(context_root, rel_path, json_file)

                # Check if corresponding context file exists
                if os.path.exists(context_path):
                    pairs.append(
                        {
                            "image": image_path,
                            "context": context_path,
                            "rel_path": os.path.join(rel_path, file),
                        }
                    )
                else:
                    # Output information about missing files
                    print(f"Missing context file: {image_path}")
                    print(f"Expected context path: {context_path}")
                    print("-" * 50)
                    missing_count += 1

    print(f"Found {len(pairs)} file pairs, missing {missing_count} pairs")
    return pairs


def distribute_files(pairs, data_folder):
    """Distribute file pairs evenly across all data_shell folders.

    Args:
        pairs: List of image-context file pairs to distribute
        data_folder: Root directory of the target structure
    """
    total_shells = 25 * 20  # 25 servers × 20 shells = 500 target folders
    print(f"Distributing {len(pairs)} file pairs across {total_shells} folders")

    # Calculate approximate number of files per shell
    files_per_shell = len(pairs) // total_shells
    remainder = len(pairs) % total_shells
    print(
        f"Approximately {files_per_shell} files per shell, with {remainder} extra files"
    )

    # Distribute files
    for idx, pair in enumerate(pairs):
        # Calculate target shell for this file pair
        shell_idx = idx % total_shells
        server_num = shell_idx // 20 + 1
        shell_num = shell_idx % 20 + 1

        server_name = f"data_server_{server_num:03d}"
        shell_name = f"data_shell_{shell_num:03d}"

        # Target paths
        target_base = Path(data_folder) / server_name / shell_name

        # Copy image file
        target_image_dir = target_base / "images"
        rel_dir = os.path.dirname(pair["rel_path"])
        (target_image_dir / rel_dir).mkdir(parents=True, exist_ok=True)
        target_image_path = target_image_dir / pair["rel_path"]
        shutil.copy2(pair["image"], target_image_path)

        # Copy context file
        target_context_dir = target_base / "context"
        (target_context_dir / rel_dir).mkdir(parents=True, exist_ok=True)
        context_filename = (
            os.path.splitext(os.path.basename(pair["rel_path"]))[0] + ".json"
        )
        target_context_path = target_context_dir / rel_dir / context_filename
        shutil.copy2(pair["context"], target_context_path)

        # Progress indicator
        if (idx + 1) % 1000 == 0:
            print(f"Processed {idx + 1} file pairs")


def main():
    """Main function to execute the file distribution process."""
    # Original data paths
    images_root = r"E:\fttracer\4_sampled_data\selected_images_folder"
    context_root = r"E:\fttracer\4_sampled_data\context_summary_202509141749"

    # Count total image files
    image_files = list(glob.glob(os.path.join(images_root, "**/*.jpg"), recursive=True))
    print("Total .jpg files:", len(image_files))

    # Count total context files
    context_files = list(
        glob.glob(os.path.join(context_root, "**/*.json"), recursive=True)
    )
    print("Total .json files:", len(context_files))

    # Verify source paths exist
    if not os.path.exists(images_root):
        print(f"Error: Image path does not exist - {images_root}")
        return
    if not os.path.exists(context_root):
        print(f"Error: Context path does not exist - {context_root}")
        return

    print("Creating directory structure...")
    create_directory_structure()

    print("Collecting file pairs...")
    pairs = get_all_image_context_pairs(images_root, context_root)
    print(f"Found {len(pairs)} valid image-context file pairs")

    if len(pairs) == 0:
        print("Warning: No valid file pairs found")
        return

    print("Distributing files...")
    distribute_files(pairs, "data_folder_202509141820")

    print("File distribution completed successfully!")


if __name__ == "__main__":
    main()
