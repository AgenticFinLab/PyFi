"""Script to analyze images using Volcengine Ark API and extract acronyms.

This script scans a directory of JPEG images, encodes each image to base64,
sends it to a vision-language model via Volcengine Ark API, and asks the model
to identify acronyms present in the image. Each result is saved individually in
JSON format in a specified output folder.

The script includes error handling, progress tracking, and supports resuming 
processing from where it left off by skipping already processed files.
"""

import os
import json
import base64
import argparse
from typing import List, Dict, Any

# Install via: pip install volcengine-python-sdk[ark]
from sympy import im
from volcenginesdkarkruntime import Ark


def encode_image_to_base64(image_path: str) -> str:
    """Encodes an image file to base64 string.

    This function reads the binary content of an image file and converts it
    to a base64 encoded string that can be sent to the API.

    Args:
        image_path: Path to the image file that needs to be encoded.

    Returns:
        Base64 encoded string representation of the image content.
    """
    with open(image_path, "rb") as image_file:
        # Read the binary content of the image file
        # Encode it to base64 and decode to utf-8 string
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_files(directory: str, file_extension: str = ".jpg") -> List[str]:
    """Lists all image files with specified extension in the given directory and its subdirectories.

    Scans the provided directory recursively and returns paths to all files that match
    the specified file extension (case-insensitive).

    Args:
        directory: Directory path to scan for image files.
        file_extension: File extension to filter (default is ".jpg").

    Returns:
        A list of full paths to image files matching the extension.
    """
    image_files = []
    # Use os.walk to recursively traverse the directory tree
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(file_extension.lower()):
                # Construct the full file path
                full_path = os.path.join(root, file)
                image_files.append(full_path)
    return image_files


def analyze_image(
    client: Ark,
    image_path: str,
    image_format: str = "jpeg",
    prompt: str = None,
) -> Dict[str, Any]:
    """Analyzes an image and returns the model's JSON response directly.

    Sends the image to the vision-language model and asks it to identify acronyms.
    The function constructs the appropriate message format for the API call.

    Args:
        client: Initialized Ark API client instance.
        image_path: Path to the image file to analyze.
        model_id: ID of the model to use for inference (default: doubao-seed-1-6-flash-250828).
        image_format: Format of the image for API (default: jpeg).
        prompt: Custom prompt to use instead of default acronym identification prompt.

    Returns:
        Dictionary containing the parsed JSON response from the model.

    Raises:
        ValueError: If the model returns invalid JSON response.
    """
    # Encode the image to base64 format required by the API
    base64_image = encode_image_to_base64(image_path)

    # Use default prompt if none provided
    if prompt is None:
        prompt = """
            Please identify and list any acronyms present in this image. Return only the acronyms found, in JSON format as a list.
            Example:
            {
                "acronyms": ["GDP", "MACD", "ETH"]
            }
            """

    # Construct the message content with image and text prompt
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        # Format the base64 image data with proper MIME type
                        "url": f"data:image/{image_format};base64,{base64_image}"
                    },
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }
    ]

    # Send request to the model with JSON response format
    response = client.chat.completions.create(
        model="doubao-seed-1-6-flash-250828",
        messages=messages,
        response_format={"type": "json_object"},  # Request JSON formatted response
    )

    # Parse the model's response (assuming it returns valid JSON)
    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        # Raise error if model response is not valid JSON
        raise ValueError(
            f"Model returned invalid JSON: {response.choices[0].message.content}"
        ) from e

    return result


def save_result_to_json(result: Dict[str, Any], output_dir: str, image_name: str):
    """Saves the model's JSON result to a file named after the image.

    Creates a JSON file with the same base name as the original image file
    to store the analysis results.

    Args:
        result: Dictionary containing the analysis results to save.
        output_dir: Directory where the JSON file should be saved.
        image_name: Original image file name (used to create corresponding JSON filename).
    """
    # Create JSON filename by replacing image extension with .json
    json_filename = os.path.splitext(image_name)[0] + ".json"
    json_path = os.path.join(output_dir, json_filename)

    # Write the result dictionary to JSON file with proper formatting
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Saved result to {json_path}")


def image_abbr_extraction(
    image_dir: str,
    output_dir: str,
    image_format: str = "jpeg",
    file_extension: str = ".jpg",
    prompt: str = None,
):
    """Main function to process all images and save results individually as JSON.

    This function orchestrates the entire image analysis process:
    1. Initializes the API client
    2. Finds all image files in the input directory
    3. Creates output directory if it doesn't exist
    4. Processes each image (skipping already processed ones)
    5. Saves results as individual JSON files
    6. Handles errors gracefully by saving error information

    Args:
        image_dir: Directory containing images to be analyzed.
        output_dir: Directory where JSON results will be saved.
        api_key: API key for Volcengine Ark service (optional).
        model_id: Model ID to use for inference (default: doubao-seed-1-6-flash-250828).
        image_format: Format of images for API (default: jpeg).
        file_extension: Extension of image files to process (default: .jpg).
        prompt: Custom prompt for acronym identification (optional).
    """
    # Initialize the API client
    client = Ark(
        api_key=os.environ.get("ARK_API_KEY"),
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )

    # Get list of all image files in the directory
    image_files = get_image_files(image_dir, file_extension)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Process each image file
    for idx, image_path in enumerate(image_files):
        # Extract the image name and create corresponding JSON filename
        image_name = os.path.basename(image_path)
        image_name_without_ext = os.path.splitext(image_name)[0]

        # Get parent directory name as prefix
        parent_dir = os.path.basename(os.path.dirname(image_path))

        # Json name format：parent_dir-image_name.json
        json_filename = f"{parent_dir}-{image_name_without_ext}.json"
        json_path = os.path.join(output_dir, json_filename)

        # Check if result file already exists (resume functionality)
        if os.path.exists(json_path):
            print(
                f"[{idx + 1}/{len(image_files)}] Skipping {image_path} (already processed)"
            )
            continue

        # Process the current image
        print(f"[{idx + 1}/{len(image_files)}] Processing {image_path}")
        try:
            # Analyze the image and get results
            result = analyze_image(client, image_path, image_format, prompt)
            # Save the successful result to JSON file with new naming format
            save_result_to_json(result, output_dir, json_filename)
        except Exception as e:
            # Handle errors by saving error information
            print(f"Error processing {image_path}: {e}")
            error_result = {"error": str(e)}
            save_result_to_json(error_result, output_dir, json_filename)


if __name__ == "__main__":

    # Process all images with provided or default parameters
    image_abbr_extraction(
        image_dir=r"PyFi\\images",
        output_dir=r"PyFi\\image_acronyms",
        image_format="jpeg",
        file_extension=".jpg",
    )
