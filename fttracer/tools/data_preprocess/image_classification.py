"""
Script for classifying images using both visual content and contextual information 
through concurrent batch inference with a large model API.
This script processes images in batches using asynchronous workers to improve
throughput and efficiency when calling the Ark API for image classification.
"""

import os
import sys
import json
import base64
import asyncio
import argparse
from pathlib import Path
from typing import Any, Dict, List

from tqdm import tqdm
from volcenginesdkarkruntime import AsyncArk

from fttracer.tools.data_preprocess.prompt import prompt_for_image_classification


def encode_image(image_path: Path) -> str:
    """Encodes an image file to base64 string.

    Args:
        image_path: Path to the image file.

    Returns:
        Base64 encoded string of the image.
    """
    # Open the image file in binary read mode
    with open(image_path, "rb") as img_file:
        # Read the image data and encode it to base64 string
        return base64.b64encode(img_file.read()).decode("utf-8")


def get_all_images(images_root: Path) -> List[Path]:
    """Gets all image files to process.

    Args:
        images_root: Root directory containing book folders with images.

    Returns:
        List of paths to image files.
    """
    # Initialize list to store image file paths
    image_files = []

    # Iterate through each book folder in the images root directory
    for book_folder in images_root.iterdir():
        # Skip if not a directory
        if not book_folder.is_dir():
            continue

        # Iterate through each file in the book folder
        for image_file in book_folder.iterdir():
            # Check if it's a file and has a valid image extension
            if image_file.is_file() and image_file.suffix.lower() in [
                ".jpg",
                ".jpeg",
                ".png",
            ]:
                # Add the image file path to the list
                image_files.append(image_file)

    # Return the list of all image file paths
    return image_files


def build_single_request(
    root_dir: Path, image_path: Path, book_id: str, image_id: str
) -> List[Dict[str, Any]]:
    """Builds a single request for image classification.

    Args:
        root_dir: Root directory containing context and image data.
        image_path: Path to the image file.
        book_id: Book identifier.
        image_id: Image identifier.

    Returns:
        List containing the message data for the request.
    """
    # Encode the image to base64 format for API transmission
    base64_img = encode_image(image_path)

    # Generate the classification prompt with context information
    prompt = prompt_for_image_classification(root_dir, book_id, image_id)

    # Construct the request message structure for the API call
    return [
        {
            # Set the role as user to indicate this is the user's input
            "role": "user",
            # Define the content as both text (prompt) and image
            "content": [
                # Text component containing the classification instructions
                {"type": "text", "text": prompt},
                # Image component with base64 encoded image data
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"},
                },
            ],
        }
    ]


async def worker(
    worker_id: int,
    client: AsyncArk,
    request_queue: asyncio.Queue,
    output_root: Path,
    progress_bar: tqdm,
) -> None:
    """Worker coroutine that processes batches of image classification requests.

    Args:
        worker_id: Unique identifier for this worker.
        client: AsyncArk client for API calls.
        request_queue: Queue containing batches of requests.
        output_root: Root directory for output files.
        progress_bar: Progress bar for tracking completion.
    """
    # Print message indicating worker has started processing
    print(f"Worker {worker_id} started")

    # Infinite loop to continuously process requests from the queue
    while True:
        # Wait for and retrieve a batch of requests from the queue
        batch = await request_queue.get()

        try:
            # Process each item in the batch
            for item in batch:
                try:
                    # Send the classification request to the Ark API
                    response = await client.batch.chat.completions.create(
                        model="ep-bi-20250918150137-fljck",  # Specify the model to use, default is Doubao-Seed-1.6-flash
                        messages=item["messages"],  # Provide the prepared messages
                    )

                    # Extract book and image identifiers from the request item
                    book_id = item["book_id"]
                    image_id = item["image_id"]

                    # Create output directory for the book
                    output_dir = output_root / book_id
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Define the output file path for the classification result
                    output_path = output_dir / f"{image_id}.json"

                    # Extract the text response from the API
                    result_text = response.choices[0].message.content.strip()

                    try:
                        # Attempt to parse the API response as JSON
                        result_json = json.loads(result_text)
                    except json.JSONDecodeError:
                        # If parsing fails, create an error response with raw text
                        result_json = {
                            "error": "Failed to parse response",
                            "raw_response": result_text,
                        }

                    # Write the classification result to the output file
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(result_json, f, indent=2, ensure_ascii=False)

                except Exception as e:
                    # Handle any errors during individual item processing
                    print(
                        f"[Worker {worker_id}] Error processing {item.get('book_id', 'unknown')}/{item.get('image_id', 'unknown')}: {e}",
                        file=sys.stderr,
                    )

                    # If book_id and image_id are available, create error output file
                    if "book_id" in item and "image_id" in item:
                        book_id = item["book_id"]
                        image_id = item["image_id"]

                        # Create output directory for the book
                        output_dir = output_root / book_id
                        output_dir.mkdir(parents=True, exist_ok=True)

                        # Define the output file path for the error result
                        output_path = output_dir / f"{image_id}.json"

                        # Create error result dictionary
                        error_result = {"error": str(e)}

                        # Write the error result to the output file
                        with open(output_path, "w", encoding="utf-8") as f:
                            json.dump(error_result, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # Handle batch processing errors
            print(f"[Worker {worker_id}] Batch processing error: {e}", file=sys.stderr)
        finally:
            # Mark the queue task as done and update progress
            request_queue.task_done()
            progress_bar.update(len(batch))


async def run_classification(
    input_dir: Path,
    batch_size: int = 1,
    worker_count: int = 5,
) -> None:
    """Main function to orchestrate image classification using async workers.

    Args:
        root_dir: Root directory containing 'images' and 'context' folders.
        batch_size: Number of images per batch (default is 1).
        worker_count: Number of concurrent worker coroutines.
    """
    # Define paths for input images and output classification results
    images_root = input_dir / "images"
    output_root = input_dir / "image_classification"
    output_root.mkdir(parents=True, exist_ok=True)

    # Get all image files to process
    all_images = get_all_images(images_root)
    total_images = len(all_images)

    # Check if there are any images to process
    if total_images == 0:
        print("No images found to process.")
        return

    # Verify that the ARK API key is set in environment variables
    if not os.environ.get("ARK_API_KEY"):
        print("Error: ARK_API_KEY environment variable is not set!")
        return

    # Initialize async client with timeout settings
    client = AsyncArk(
        api_key=os.environ.get("ARK_API_KEY"),  # Use API key from environment
        base_url="https://ark.cn-beijing.volces.com/api/v3",  # Set the API base URL
        timeout=24 * 3600,  # Set timeout to 24 hours
    )

    # Create a queue for managing request batches
    request_queue = asyncio.Queue()

    # Lists to store pending images and request data
    pending_images = []
    request_batches = []

    # Build list of unprocessed images by checking if output files already exist
    for image_path in all_images:
        # Extract book ID from the parent directory name
        book_id = image_path.parent.name
        # Extract image ID from the file stem (filename without extension)
        image_id = image_path.stem
        # Define the expected output path for this image
        output_path = output_root / book_id / f"{image_id}.json"

        # Skip if the output file already exists (image already processed)
        if output_path.exists():
            continue

        # Add to pending images list
        pending_images.append(image_path)

        # Prepare request data for this image
        request_data = {
            "book_id": book_id,  # Store book identifier
            "image_id": image_id,  # Store image identifier
            "messages": build_single_request(
                input_dir, image_path, book_id, image_id
            ),  # Build API request
        }
        # Add request data to batches list
        request_batches.append(request_data)

    # Group requests into batches of specified size
    for i in range(0, len(request_batches), batch_size):
        # Create a batch slice from the request batches
        batch = request_batches[i : i + batch_size]
        # Add the batch to the request queue
        await request_queue.put(batch)

    # Check if there are no pending images to process
    if not pending_images:
        print("All images already processed.")
        await client.close()  # Close the API client
        return

    # Print processing information
    print(f"Processing {len(pending_images)} images with {worker_count} workers...")

    # Initialize progress bar to track classification progress
    progress_bar = tqdm(
        total=len(pending_images),  # Total number of images to process
        desc="Classifying images",  # Description for the progress bar
        unit="img",  # Unit for the progress bar
    )

    # Create worker tasks for concurrent processing
    tasks = [
        # Create an async task for each worker
        asyncio.create_task(worker(i, client, request_queue, output_root, progress_bar))
        for i in range(worker_count)  # Create specified number of workers
    ]

    try:
        # Wait for all requests in the queue to be processed
        await request_queue.join()
    except KeyboardInterrupt:
        # Handle user interruption gracefully
        print("\nInterrupted by user, cancelling tasks...")
    finally:
        # Cancel all worker tasks
        for task in tasks:
            task.cancel()

        # Wait for all tasks to complete cancellation
        await asyncio.gather(*tasks, return_exceptions=True)

        # Close the API client connection
        await client.close()

        # Close the progress bar
        progress_bar.close()

    # Print completion message
    print("Classification completed!")


if __name__ == "__main__":
    # Create argument parser for command line interface
    parser = argparse.ArgumentParser(description="Run image classification.")

    # Add argument for input directory
    parser.add_argument(
        "--input_dir",
        "-i",
        type=Path,
        default="reorganized_results",  # Default directory if not specified
        help="Root directory containing 'images' and 'context' folders.",
    )

    # Add argument for batch size
    parser.add_argument(
        "--batch_size",
        "-b",
        type=int,
        default=1,  # Default batch size of 1
        help="Number of images per batch (default: 1).",
    )

    # Add argument for worker count
    parser.add_argument(
        "--worker_count",
        "-w",
        type=int,
        default=5,  # Default of 5 concurrent workers
        help="Number of concurrent workers (default: 5).",
    )

    # Parse command line arguments
    args = parser.parse_args()

    # Run the classification process with provided arguments
    asyncio.run(run_classification(args.input_dir, args.batch_size, args.worker_count))
