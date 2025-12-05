"""Script to Check Image Requirement Compliance using Async Batch Processing."""

import os
import re
import sys
import json
import base64
import asyncio
import argparse
from pathlib import Path
from typing import Optional, Dict, List, Any

from PIL import Image
from tqdm import tqdm
from volcenginesdkarkruntime import AsyncArk

from fttracer.tools.data_preprocess.prompt import prompt_for_image_screener

# Define valid image extensions for processing
# These are the only file types that will be considered as valid images
VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def get_image_size_mb(image_path: str) -> float:
    """Gets the size of an image file in megabytes.

    Args:
        image_path: Path to the image file

    Returns:
        Size of the image in megabytes as a float
    """
    size_bytes = os.path.getsize(image_path)
    size_mb = size_bytes / (1024 * 1024)  # Convert bytes to megabytes
    return size_mb


def compress_image(
    input_path: str, output_path: str, max_size_mb: float = 9.0, quality: int = 85
) -> bool:
    """Compresses an image until it is smaller than the specified size.

    This function attempts to compress an image by reducing quality first,
    then by resizing if quality reduction is insufficient.

    Args:
        input_path: Path to the original image file
        output_path: Path where compressed image will be saved
        max_size_mb: Maximum allowed size in megabytes (default 9.0MB)
        quality: Initial JPEG quality setting (default 85)

    Returns:
        True if compression succeeds, False otherwise
    """
    try:
        # Open the image file
        with Image.open(input_path) as img:
            # Convert images with transparency or palette modes to RGB for JPEG compatibility
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            # First attempt: reduce quality to meet size requirements
            current_quality = quality
            while current_quality > 10:
                # Save with current quality setting
                img.save(output_path, "JPEG", optimize=True, quality=current_quality)
                compressed_size = get_image_size_mb(output_path)

                # Check if size is within limit
                if compressed_size < max_size_mb:
                    return True
                current_quality -= 5  # Reduce quality further

            # If quality reduction isn't sufficient, resize the image
            width, height = img.size
            scale_factor = 0.9  # Start with 90% of original size
            while current_quality <= 10 and scale_factor > 0.1:
                # Calculate new dimensions
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)

                # Resize image using high-quality resampling
                resized_img = img.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )

                # Save resized image with minimum quality
                resized_img.save(output_path, "JPEG", optimize=True, quality=10)
                compressed_size = get_image_size_mb(output_path)

                # Check if size is within limit
                if compressed_size < max_size_mb:
                    return True
                scale_factor -= 0.1  # Reduce size further

            return False  # Compression failed to meet size requirements

    except Exception as e:
        print(f"Error during image compression: {e}")
        return False


def encode_image(image_path: str) -> str:
    """Encodes an image to base64 string for API transmission.

    Args:
        image_path: Path to the image file to encode

    Returns:
        Base64 encoded string of the image data
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def check_image(image_path: Path, max_size_mb: float = 9.0) -> str:
    """Prepares an image for model inference, compressing if necessary.

    This function checks if the image exceeds size limits and compresses it if needed.

    Args:
        image_path: Path to the original image
        max_size_mb: Maximum allowed file size in megabytes

    Returns:
        Path to the prepared image (original or compressed)

    Raises:
        Exception: If image cannot be compressed below the size limit
    """
    original_size = get_image_size_mb(str(image_path))

    # If image is already within size limits, return original path
    if original_size <= max_size_mb:
        return str(image_path)

    # Create path for compressed version
    temp_compressed_path = str(image_path).replace(".", "_compressed.")

    # Attempt compression
    if not compress_image(str(image_path), temp_compressed_path, max_size_mb):
        raise Exception(f"Cannot compress image below {max_size_mb}MB")

    return temp_compressed_path


def get_all_images(images_root: Path) -> List[Path]:
    """Gets all image files to process from subdirectories.

    This function recursively searches through all book folders to find valid images.

    Args:
        images_root: Root directory containing book subdirectories with images

    Returns:
        List of paths to all valid image files found
    """
    image_files = []

    # Iterate through each book folder in the images root
    for book_folder in images_root.iterdir():
        if not book_folder.is_dir():
            continue  # Skip if not a directory

        # Iterate through each file in the book folder
        for image_file in book_folder.iterdir():
            if (
                image_file.is_file()
                and image_file.suffix.lower() in VALID_IMAGE_EXTENSIONS
            ):
                image_files.append(image_file)

    return image_files


def build_single_request(image_path: Path) -> List[Dict[str, Any]]:
    """Builds a single request for image screening API call.

    Creates the message structure required by the AI model for image analysis.

    Args:
        image_path: Path to the image file to analyze

    Returns:
        List containing the message structure for the API call

    Raises:
        Exception: If encoded image exceeds 10MB size limit
    """
    # Get the screening prompt template
    prompt = prompt_for_image_screener()

    # Encode the image for API transmission
    base64_img = encode_image(check_image(image_path))

    # Calculate encoded image size
    encoded_size_mb = len(base64_img) / (1024 * 1024)

    # Check if encoded image exceeds API size limit
    if encoded_size_mb >= 10:
        raise Exception(
            f"Encoded image size {encoded_size_mb:.2f}MB exceeds 10MB limit"
        )

    # Construct the API message with both text prompt and image
    return [
        {
            "role": "user",  # Indicate this is a user message
            "content": [
                {"type": "text", "text": prompt},  # Text prompt for image analysis
                {
                    "type": "image_url",  # Image content type
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    },  # Base64 encoded image
                },
            ],
        }
    ]


def extract_json_from_response(response_text):
    """Extract pure JSON from response that may contain Markdown code blocks.

    The AI model may return JSON wrapped in Markdown code blocks, so this function
    extracts the clean JSON content.

    Args:
        response_text: Raw response text from the AI model

    Returns:
        Clean JSON string or the original text if no JSON found
    """
    if not response_text:
        return None

    # Use regex to extract content from code blocks (```json or ``` without language)
    json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", response_text, re.DOTALL)
    if json_match:
        return json_match.group(1)  # Return the captured JSON content

    # If no code blocks found, try to parse the entire response directly
    cleaned = response_text.strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    return response_text  # Return original if no JSON structure found


async def worker(
    worker_id: int,
    client: AsyncArk,
    request_queue: asyncio.Queue,
    output_root: Path,
    progress_bar: tqdm,
) -> None:
    """Worker coroutine that processes batches of image screening requests.

    Each worker continuously pulls batches from the queue and processes them
    using the AI model API.

    Args:
        worker_id: Unique identifier for this worker
        client: AsyncArk API client for making requests
        request_queue: Queue containing batches of requests to process
        output_root: Root directory for saving results
        progress_bar: Progress bar to update with processing status
    """
    print(f"Worker {worker_id} started")

    # Continuously process batches until queue is empty
    while True:
        batch = await request_queue.get()
        try:
            # Process each item in the current batch
            for item in batch:
                try:
                    # Make API call to screen the image
                    response = await client.batch.chat.completions.create(
                        model="ep-bi-20250918150137-fljck",  # Specific model for image screening, default is doubao-seed-1-6-flash
                        messages=item["messages"],  # Prepared message structure
                    )

                    # Extract identifiers for organizing output
                    book_id = item["book_id"]
                    image_id = item["image_id"]

                    # Create output directory structure
                    output_dir = output_root / book_id
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"{image_id}.json"

                    # Get the response text from the API
                    result_text = response.choices[0].message.content.strip()

                    # Attempt to parse the response as JSON
                    try:
                        clean_json_str = extract_json_from_response(result_text)
                        result_json = json.loads(clean_json_str)
                    except (json.JSONDecodeError, TypeError) as e:
                        # If parsing fails, save error information
                        result_json = {
                            "error": "Failed to parse response",
                            "raw_response": result_text,
                            "parse_error": str(e),
                        }

                    # Save the result to a JSON file
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result_json, f, indent=2, ensure_ascii=False)

                except Exception as e:
                    # Handle errors during individual item processing
                    print(
                        f"[Worker {worker_id}] Error processing {item.get('book_id', 'unknown')}/{item.get('image_id', 'unknown')}: {e}",
                        file=sys.stderr,
                    )

                    # Create error result file even when processing fails
                    if "book_id" in item and "image_id" in item:
                        book_id = item["book_id"]
                        image_id = item["image_id"]
                        output_dir = output_root / book_id
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_path = output_dir / f"{image_id}.json"
                        error_result = {"error": str(e)}
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(error_result, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # Handle errors during batch processing
            print(f"[Worker {worker_id}] Batch processing error: {e}", file=sys.stderr)
        finally:
            # Mark task as done and update progress
            request_queue.task_done()
            progress_bar.update(len(batch))


async def run_screening(
    input_dir: Path,
    batch_size: int = 1,
    worker_count: int = 5,
) -> None:
    """Main function to orchestrate image screening using async workers.

    This function sets up the processing pipeline, manages workers, and coordinates
    the image screening process.

    Args:
        input_dir: Root directory containing images to process
        batch_size: Number of images to process in each batch
        worker_count: Number of concurrent workers to use
    """
    # Define input and output directory paths
    images_root = input_dir / "images"
    output_root = input_dir / "images_eval"
    output_root.mkdir(parents=True, exist_ok=True)

    # Get list of all images to process
    all_images = get_all_images(images_root)
    total_images = len(all_images)

    # Check if any images were found
    if total_images == 0:
        print("No images found to process.")
        return

    # Verify API key is available
    if not os.environ.get("ARK_API_KEY"):
        print("Error: ARK_API_KEY environment variable is not set!")
        return

    # Initialize the AsyncArk API client
    client = AsyncArk(
        api_key=os.environ.get("ARK_API_KEY"),  # API key from environment
        base_url="https://ark.cn-beijing.volces.com/api/v3",  # API endpoint
        timeout=24 * 3600,  # 24-hour timeout for long-running requests
    )

    # Create queue for managing work distribution
    request_queue = asyncio.Queue()
    pending_images = []  # Track images that need processing
    request_batches = []  # Track prepared requests

    # Prepare requests for each image
    for image_path in all_images:
        book_id = image_path.parent.name  # Extract book ID from parent directory
        image_id = image_path.stem  # Extract image ID from filename (without extension)
        output_path = output_root / book_id / f"{image_id}.json"

        # Skip images that have already been processed
        if output_path.exists():
            continue

        pending_images.append(image_path)

        # Prepare request data structure
        request_data = {
            "book_id": book_id,
            "image_id": image_id,
            "messages": build_single_request(image_path),  # Build API message
        }
        request_batches.append(request_data)

    # Create batches and add them to the queue
    for i in range(0, len(request_batches), batch_size):
        batch = request_batches[i : i + batch_size]
        await request_queue.put(batch)

    # Check if there are any pending images to process
    if not pending_images:
        print("All images already processed.")
        await client.close()
        return

    print(f"Processing {len(pending_images)} images with {worker_count} workers...")

    # Create progress bar to track processing
    progress_bar = tqdm(total=len(pending_images), desc="Screening images", unit="img")

    # Create worker tasks
    tasks = [
        asyncio.create_task(worker(i, client, request_queue, output_root, progress_bar))
        for i in range(worker_count)  # Create specified number of workers
    ]

    try:
        # Wait for all queue items to be processed
        await request_queue.join()
    except KeyboardInterrupt:
        print("\nInterrupted by user, cancelling tasks...")
    finally:
        # Clean up: cancel all tasks and close resources
        for task in tasks:
            task.cancel()  # Cancel each worker task
        await asyncio.gather(*tasks, return_exceptions=True)  # Wait for cancellation
        await client.close()  # Close the API client
        progress_bar.close()  # Close the progress bar

    print("Screening completed!")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run image screening.")
    parser.add_argument(
        "--input_dir",
        "-i",
        type=Path,
        default="reorganized_results",
        help="Root directory containing 'images' and 'context' folders.",
    )
    parser.add_argument(
        "--batch_size",
        "-b",
        type=int,
        default=1,
        help="Number of images per batch (default: 1).",
    )
    parser.add_argument(
        "--worker_count",
        "-w",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5).",
    )

    args = parser.parse_args()

    # Run the main screening function with parsed arguments
    asyncio.run(run_screening(args.input_dir, args.batch_size, args.worker_count))
