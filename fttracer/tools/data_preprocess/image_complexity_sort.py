"""Script to sort images by complexity level and copy them to a new directory."""

import json
import os
import shutil
from pathlib import Path
from typing import List, Tuple


def get_json_files(images_eval_path: str) -> List[str]:
    """Get all JSON files from images_eval directory structure.

    Args:
        images_eval_path: Path to the images_eval directory.

    Returns:
        List of paths to all JSON files.
    """
    json_files = []
    for root, _, files in os.walk(images_eval_path):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files


def extract_complexity_info(
    json_file_path: str, report_dir: str
) -> Tuple[str, str, str, int]:
    """Extract complexity information from JSON file.

    Args:
        json_file_path: Path to the JSON file.
        report_dir: Path to the report directory containing images and images_eval.

    Returns:
        Tuple of (book_id, image_id, image_path, complexity_level).
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    book_id = data[0]["book_id"]
    image_id = data[0]["image_id"]
    complexity_level = data[0]["complexity_level"]

    # Construct image path - images is at the same level as images_eval
    images_dir = os.path.join(report_dir, "image_eval_yes_images")
    image_path = os.path.join(images_dir, f"{book_id}_{image_id}.jpg")

    return book_id, image_id, image_path, complexity_level


def create_sorted_filename(
    book_id: str, image_id: str, complexity_level: int, index: int
) -> str:
    """Create a sorted filename with complexity level prefix.

    Args:
        book_id: Book identifier.
        image_id: Image identifier.
        complexity_level: Complexity level of the image.
        index: Index for ordering within same complexity level.

    Returns:
        Formatted filename.
    """
    return f"{complexity_level:02d}_{index:04d}_{book_id}_{image_id}.jpg"


def main():
    """Main function to sort images by complexity and copy them to new directory."""
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_dir = os.path.join(script_dir, "report")
    images_eval_path = os.path.join(report_dir, "image_eval_yes")
    output_dir = os.path.join(script_dir, "images_complexity_sort")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get all JSON files
    print("Scanning for JSON files...")
    json_files = get_json_files(images_eval_path)
    total_files = len(json_files)
    print(f"Found {total_files} JSON files")

    # Extract complexity information for all images
    print("Processing JSON files...")
    image_info_list = []
    processed_count = 0

    for json_file in json_files:
        try:
            book_id, image_id, image_path, complexity_level = extract_complexity_info(
                json_file, report_dir
            )
            image_info_list.append((book_id, image_id, image_path, complexity_level))
            processed_count += 1
            print(
                f"\rProcessed {processed_count}/{total_files} JSON files",
                end="",
                flush=True,
            )
        except (KeyError, json.JSONDecodeError) as e:
            print(f"\nError processing {json_file}: {e}")
            processed_count += 1
            print(
                f"\rProcessed {processed_count}/{total_files} JSON files",
                end="",
                flush=True,
            )
            continue

    print(f"\nCompleted processing {processed_count}/{total_files} JSON files")

    # Sort by complexity level
    print("Sorting images by complexity level...")
    image_info_list.sort(key=lambda x: x[3])
    print(f"Sorted {len(image_info_list)} images")

    # Copy images to output directory with sorted names
    print("Copying images to output directory...")
    complexity_count = {}
    copied_count = 0
    total_images = len(image_info_list)

    for book_id, image_id, image_path, complexity_level in image_info_list:
        # Count images per complexity level for proper indexing
        if complexity_level not in complexity_count:
            complexity_count[complexity_level] = 0
        complexity_count[complexity_level] += 1

        # Create new filename
        new_filename = create_sorted_filename(
            book_id, image_id, complexity_level, complexity_count[complexity_level]
        )
        output_path = os.path.join(output_dir, new_filename)

        # Copy image if it exists
        if os.path.exists(image_path):
            try:
                shutil.copy2(image_path, output_path)
                copied_count += 1
                print(
                    f"\rCopied {copied_count}/{total_images} images", end="", flush=True
                )
            except Exception as e:
                print(f"\nError copying {image_path}: {e}")
                print(
                    f"\rCopied {copied_count}/{total_images} images", end="", flush=True
                )
        else:
            print(f"\nImage not found: {image_path}")
            print(f"\rCopied {copied_count}/{total_images} images", end="", flush=True)

    print(f"\nCompleted! Copied {copied_count}/{total_images} images to {output_dir}")

    # Print summary by complexity level
    print("\nSummary by complexity level:")
    for level in sorted(complexity_count.keys()):
        count = sum(1 for _, _, _, complexity in image_info_list if complexity == level)
        print(f"  Complexity {level}: {count} images")


if __name__ == "__main__":
    main()
