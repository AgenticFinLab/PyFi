import os
import json
import shutil
import argparse


def process_json_files(input_dir, images_dir, output_dir):
    """
    Process JSON files and copy corresponding images

    Args:
        input_dir: Path to images_eval_refactor_yes directory
        images_dir: Path to original images directory
        output_dir: Path to output images directory
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Statistics
    total_files = 0
    successful_copies = 0
    errors = 0

    # Walk through all subdirectories and files in input_dir
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                total_files += 1

                try:
                    # Read JSON file
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Process JSON data (assuming each file contains one object)
                    if isinstance(data, list) and len(data) > 0:
                        item = data[0]

                        # Extract field data
                        is_compliant = item.get("is_compliant", "")
                        compliance_level = item.get("compliance_level", "")
                        complexity_level = item.get("complexity_level", "")
                        book_id = item.get("book_id", "")
                        image_id = item.get("image_id", "")

                        print(f"Processing file: {file}")
                        print(f"  is_compliant: {is_compliant}")
                        print(f"  compliance_level: {compliance_level}")
                        print(f"  complexity_level: {complexity_level}")
                        print(f"  book_id: {book_id}")
                        print(f"  image_id: {image_id}")

                        # Build original image path and destination path with .jpg extension
                        original_image_filename = f"{image_id}.jpg"
                        original_image_path = os.path.join(
                            images_dir, book_id, original_image_filename
                        )
                        new_filename = f"{book_id}_{image_id}.jpg"
                        destination_path = os.path.join(output_dir, new_filename)

                        # Check if original image exists
                        if os.path.exists(original_image_path):
                            # Copy image

                            shutil.copy2(original_image_path, destination_path)
                            successful_copies += 1
                            print(
                                f"  Copied: {original_image_path} -> {destination_path}"
                            )
                        else:
                            print(
                                f"  Warning: Original image not found - {original_image_path}"
                            )
                            errors += 1

                    else:
                        print(f"  Warning: Invalid JSON file format - {json_path}")
                        errors += 1

                except json.JSONDecodeError as e:
                    print(f"  Error: JSON parsing failed - {json_path}: {e}")
                    errors += 1
                except Exception as e:
                    print(
                        f"  Error: Exception occurred while processing file - {json_path}: {e}"
                    )
                    errors += 1

    # Output statistics
    print("\nProcessing completed!")
    print(f"Total JSON files processed: {total_files}")
    print(f"Successfully copied images: {successful_copies}")
    print(f"Number of errors: {errors}")


def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Process JSON files and copy corresponding images"
    )
    parser.add_argument(
        "--input", required=True, help="Path to images_eval_refactor_yes directory"
    )
    parser.add_argument(
        "--images", required=True, help="Path to original images directory"
    )
    parser.add_argument(
        "--output", required=True, help="Path to output images directory"
    )

    args = parser.parse_args()

    # Check if input directories exist
    if not os.path.exists(args.input):
        print(f"Error: Input directory does not exist - {args.input}")
        return

    if not os.path.exists(args.images):
        print(f"Error: Original images directory does not exist - {args.images}")
        return

    # Execute processing
    process_json_files(args.input, args.images, args.output)


if __name__ == "__main__":
    main()
