"""Script to Check Image Requirement Compliance.

This script iterates through image files in a specified input directory,
sends each image to the Qwen-VL model with a predefined prompt to assess
if it meets specific financial chart criteria, and saves the model's JSON
response to a corresponding output file.
"""

import re
import os
import time
import json
import base64
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, List, Set

from PIL import Image
from tqdm import tqdm
from openai import OpenAI, APIError, RateLimitError

from fttracer.tools.data_preprocess.prompt import prompt_for_image_screener

# Constants
# Define valid image file extensions that the script will process
VALID_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


def get_image_size_mb(image_path: str) -> float:
    """Gets the size of an image file in megabytes.

    Args:
        image_path: Path to the image file.

    Returns:
        Size of the image file in megabytes.
    """
    # Get the file size in bytes using os.path.getsize
    size_bytes = os.path.getsize(image_path)
    # Convert bytes to megabytes (1 MB = 1024 * 1024 bytes)
    size_mb = size_bytes / (1024 * 1024)
    return size_mb


def compress_image(
    input_path: str, output_path: str, max_size_mb: float = 9.0, quality: int = 85
) -> bool:
    """Compresses an image until it is smaller than the specified size.

    Args:
        input_path: Input image path.
        output_path: Output image path.
        max_size_mb: Maximum size in megabytes.
        quality: JPEG compression quality (1-100).

    Returns:
        True if compression succeeds, False otherwise.
    """
    try:
        # Open the original image using PIL
        with Image.open(input_path) as img:
            # Convert to RGB mode if necessary to ensure JPEG compatibility
            # RGBA, LA, and P modes need to be converted to RGB for JPEG format
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            # Gradually reduce quality until size requirement is met
            current_quality = quality
            while current_quality > 10:
                # Save the image with current quality setting
                img.save(output_path, "JPEG", optimize=True, quality=current_quality)
                # Check if the compressed image meets the size requirement
                compressed_size = get_image_size_mb(output_path)

                if compressed_size < max_size_mb:
                    print(
                        f"Image compression successful: {compressed_size:.2f}MB (quality: {current_quality})"
                    )
                    return True

                # Reduce quality by 5 points for next iteration
                current_quality -= 5

            # If quality adjustment is insufficient, try resizing
            if current_quality <= 10:
                # Get original dimensions
                width, height = img.size
                # Start with 90% of original size
                scale_factor = 0.9
                while current_quality <= 10 and scale_factor > 0.1:
                    # Calculate new dimensions based on scale factor
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    # Resize the image using LANCZOS resampling for high quality
                    resized_img = img.resize(
                        (new_width, new_height), Image.Resampling.LANCZOS
                    )
                    # Save the resized image with minimum quality
                    resized_img.save(output_path, "JPEG", optimize=True, quality=10)
                    # Check if the resized image meets the size requirement
                    compressed_size = get_image_size_mb(output_path)

                    if compressed_size < max_size_mb:
                        print(
                            f"Image compression successful (resized): {compressed_size:.2f}MB (scale: {scale_factor})"
                        )
                        return True

                    # Reduce scale factor by 10% for next iteration
                    scale_factor -= 0.1

            print(
                f"Image compression failed: Cannot compress image below {max_size_mb}MB"
            )
            return False

    except Exception as e:
        print(f"Error during image compression: {e}")
        return False


def encode_image(image_path: str) -> str:
    """Encodes an image to base64 string.

    Args:
        image_path: Path to the image file.

    Returns:
        Base64 encoded string of the image.
    """
    # Open the image file in binary read mode
    with open(image_path, "rb") as image_file:
        # Read the binary content and encode it to base64 string
        return base64.b64encode(image_file.read()).decode("utf-8")


def prepare_image_for_model(image_path: Path, max_size_mb: float = 9.0) -> str:
    """Prepares an image for model inference, compressing if necessary.

    Args:
        image_path: Path to the image file.
        max_size_mb: Maximum allowed size in megabytes.

    Returns:
        Path to the processed image.

    Raises:
        Exception: If image cannot be compressed to required size.
    """
    # Get the original image size in MB
    original_size = get_image_size_mb(str(image_path))

    # If original size is already within limits, return original path
    if original_size <= max_size_mb:
        return str(image_path)

    # Image needs compression
    print(f"Image too large ({original_size:.2f}MB > {max_size_mb}MB), compressing...")

    # Create temporary compressed file path by inserting "_compressed" before extension
    temp_compressed_path = str(image_path).replace(".", "_compressed.")
    # Attempt to compress the image
    if not compress_image(str(image_path), temp_compressed_path, max_size_mb):
        # Raise exception if compression fails to meet size requirements
        raise Exception(f"Cannot compress image below {max_size_mb}MB")

    return temp_compressed_path


def evaluate_image_with_model(
    image_path: Path, client: OpenAI, model_name: str, prompt_text: str
) -> Optional[str]:
    """Sends an image to the Qwen-VL model and retrieves the response.

    Args:
        image_path: Path object representing the local image file.
        client: Configured OpenAI client instance.
        model_name: The name of the Qwen-VL model to use.
        prompt_text: The text prompt to send with the image.

    Returns:
        The model's response content as a string, or None if an error occurred.
    """
    try:
        # Check and prepare image - compress if necessary to meet size limits
        processed_image_path = prepare_image_for_model(image_path)

        # Encode the processed image to base64 for API transmission
        base64_image = encode_image(processed_image_path)

        # Check encoded data size to ensure it's within API limits
        encoded_size_mb = len(base64_image) / (1024 * 1024)
        print(f"Base64 encoded size: {encoded_size_mb:.2f}MB")

        # Verify encoded size doesn't exceed 10MB limit
        if encoded_size_mb >= 10:
            raise Exception(
                f"Encoded image size {encoded_size_mb:.2f}MB exceeds 10MB limit"
            )

        # Create the API request to the Qwen-VL model
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are a financial image understanding expert, and you are now tasked with performing a financial image evaluation.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                        {"type": "text", "text": prompt_text},
                    ],
                },
            ],
        )

        # Clean up temporary compressed file if it was created during processing
        if processed_image_path != str(image_path):
            try:
                os.remove(processed_image_path)
                print("Temporary compressed file cleaned up")
            except:
                pass

        # Extract and return the model's response content
        response_content = completion.choices[0].message.content
        return response_content

    except RateLimitError as e:
        # Handle rate limit errors from the API
        print(f"Rate limit exceeded for {image_path.name}: {e}")
        return None
    except APIError as e:
        # Handle general API errors
        print(f"API error processing {image_path.name}: {e}")
        return None
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Unexpected error processing {image_path.name}: {e}")
        return None


def extract_json_from_response(response_text):
    """Extract pure JSON from response that may contain Markdown code blocks"""
    # Return None if the response text is empty or None
    if not response_text:
        return None

    # Use regex to extract content from JSON code blocks (with or without 'json' language specifier)
    json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", response_text, re.DOTALL)
    if json_match:
        # Return the extracted JSON string
        return json_match.group(1)

    # If no code blocks, try to parse the entire response directly
    # Clean leading and trailing whitespace
    cleaned = response_text.strip()
    # Check if the cleaned text looks like a JSON object
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    # If all extraction attempts fail, return the original content
    return response_text


def screen_image(input_dir: str) -> None:
    """Main function to orchestrate the image evaluation process.

    Recursively searches for images within an 'images' subdirectory of input_dir.
    Saves evaluation results in a parallel 'images_eval' directory structure.
    Skips directories where all outputs already exist.
    Shows progress with a progress bar.
    """
    # Get the API key from environment variables
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("DASHSCOPE_API_KEY environment variable not set.")
        return

    # Initialize the OpenAI client with DashScope API configuration
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # Define the model name and prompt text to use for image evaluation
    model_name = "qwen-vl-max"
    prompt_text = prompt_for_image_screener()

    # Convert input directory string to Path object for easier path manipulation
    input_path_obj = Path(input_dir)

    # Verify that the input directory exists and is actually a directory
    if not input_path_obj.exists() or not input_path_obj.is_dir():
        print(f"Input path '{input_path_obj}' does not exist or is not a directory.")
        return

    # Define the images search root (input_path_obj / "images")
    images_search_root = input_path_obj / "images"
    # Verify that the expected 'images' subdirectory exists
    if not images_search_root.exists() or not images_search_root.is_dir():
        print(f"Expected 'images' subdirectory not found at '{images_search_root}'.")
        return

    # Define the evaluation output root directory where results will be saved
    evaluation_output_root = input_path_obj / "images_eval"
    try:
        # Create the output directory structure if it doesn't exist
        evaluation_output_root.mkdir(parents=True, exist_ok=True)
        print(f"Ensured evaluation output directory exists: {evaluation_output_root}")
    except OSError as e:
        # Handle errors in creating the output directory
        print(
            f"Failed to create evaluation output directory '{evaluation_output_root}': {e}"
        )
        return

    # Step 1: Collect all valid image files from the images directory and subdirectories
    image_files = [
        f
        for f in images_search_root.rglob("*")
        if f.is_file() and f.suffix.lower() in VALID_IMAGE_EXTENSIONS
    ]

    # Exit if no valid image files were found
    if not image_files:
        print("No valid image files found.")
        return

    # Step 2: Group images by their relative directory path to enable batch processing
    # This allows us to skip entire directories if all outputs already exist
    dir_to_images: Dict[Path, List[Path]] = defaultdict(list)
    for image_file in image_files:
        try:
            # Calculate the relative path from the images root to determine the directory
            relative_dir = image_file.relative_to(images_search_root).parent
            # Add the image file to its corresponding directory group
            dir_to_images[relative_dir].append(image_file)
        except ValueError as e:
            # Handle errors in calculating relative paths
            print(f"Error calculating relative path for {image_file}: {e}")

    # Step 3: Count total images to process and determine which directories need processing
    total_images = 0
    dirs_to_process: Dict[Path, List[Path]] = {}

    for relative_dir, images_in_dir in dir_to_images.items():
        # Track which output files already exist
        output_files_exist: Set[Path] = set()
        # Track which output files are needed
        output_files_needed: List[Path] = []

        for image_file in images_in_dir:
            # Calculate the relative path from images root to maintain directory structure
            relative_path = image_file.relative_to(images_search_root)
            # Create the corresponding output file path (JSON instead of image)
            output_path = (evaluation_output_root / relative_path).with_name(
                f"{relative_path.stem}.json"
            )
            output_files_needed.append(output_path)
            # Check if the output file already exists
            if output_path.exists():
                output_files_exist.add(output_path)

        # If not all outputs exist, we need to process this directory
        if len(output_files_exist) != len(output_files_needed):
            # Add this directory to the list of directories to process
            dirs_to_process[relative_dir] = images_in_dir
            # Add the number of images in this directory to the total count
            total_images += len(images_in_dir)
        else:
            # All outputs exist for this directory, skip it
            print(
                f"Skipping entire directory '{relative_dir}', all outputs already exist."
            )

    # Exit if all directories have been fully processed
    if not dirs_to_process:
        print("All directories already fully processed.")
        return

    # Step 4: Process images with progress bar to show processing status
    processed_count = 0  # Count of successfully processed images
    error_count = 0  # Count of images that failed to process
    start_time = time.time()  # Record start time for performance tracking

    # Create a progress bar with tqdm to show processing progress
    with tqdm(total=total_images, desc="Processing Images", unit="img") as pbar:
        # Iterate through each directory that needs processing
        for relative_dir, images_in_dir in dirs_to_process.items():
            # Process each image in the current directory
            for image_file in images_in_dir:
                # Calculate the relative path from images root for the current image
                try:
                    relative_path_from_images = image_file.relative_to(
                        images_search_root
                    )
                except ValueError as e:
                    # Handle errors in calculating relative path
                    print(f"Error calculating relative path for {image_file}: {e}")
                    error_count += 1
                    pbar.update(1)
                    continue

                # Calculate the output file path for the current image
                output_file_path = (
                    evaluation_output_root / relative_path_from_images
                ).with_name(f"{relative_path_from_images.stem}.json")

                # Create the parent directory for the output file if it doesn't exist
                try:
                    output_file_path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    # Handle errors in creating parent directories
                    print(
                        f"Failed to create parent directory for output file '{output_file_path}': {e}"
                    )
                    error_count += 1
                    pbar.update(1)
                    continue

                # Send the image to the model for evaluation
                model_response = evaluate_image_with_model(
                    image_file, client, model_name, prompt_text
                )
                # Print raw model response for debugging (commented out by default)
                # print(f"Raw model response for {image_file}: {repr(model_response)}")

                # Check if the model returned a valid response
                if model_response:
                    try:
                        # Extract clean JSON from the model response (handles code blocks)
                        clean_json_str = extract_json_from_response(model_response)
                        # Parse the JSON response and save it with proper formatting
                        response_data = json.loads(model_response)
                        with open(output_file_path, "w", encoding="utf-8") as f:
                            json.dump(response_data, f, ensure_ascii=False, indent=2)
                        processed_count += 1
                    except (json.JSONDecodeError, IOError) as e:
                        # Handle errors in parsing JSON or writing to file
                        print(
                            f"Failed to process JSON response for {image_file} to {output_file_path}: {e}"
                        )
                        # Create a default response in case of JSON parsing errors
                        default_response = {
                            "is_compliant": "null",
                            "compliance_level": -1,
                            "complexity_level": -1,
                        }
                        try:
                            # Write the default response to the output file
                            with open(output_file_path, "w", encoding="utf-8") as f:
                                json.dump(
                                    default_response, f, ensure_ascii=False, indent=2
                                )
                        except IOError as io_error:
                            # Handle errors in writing the default response
                            print(
                                f"Failed to write default response for {image_file}: {io_error}"
                            )
                        error_count += 1
                else:
                    # Handle cases where the model didn't return a valid response
                    print(f"Failed to get a valid response for {image_file}")
                    print(f"Response content: {repr(model_response)}")
                    # Create a default response when model fails
                    default_response = {
                        "is_compliant": "null",
                        "compliance_level": -1,
                        "complexity_level": -1,
                    }
                    try:
                        # Write the default response to the output file
                        with open(output_file_path, "w", encoding="utf-8") as f:
                            json.dump(default_response, f, ensure_ascii=False, indent=2)
                    except IOError as io_error:
                        # Handle errors in writing the default response
                        print(
                            f"Failed to write default response for {image_file}: {io_error}"
                        )
                    error_count += 1

                # Update the progress bar
                pbar.update(1)

    # Print final processing statistics
    print(f"\nProcessing complete. Processed: {processed_count}, Errors: {error_count}")
    end_time = time.time()
    # Print total processing time
    print(f"Total time: {end_time - start_time:.2f}s")


if __name__ == "__main__":
    # Execute the main function with the specified input directory
    screen_image(input_dir="report")
