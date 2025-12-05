"""Script for extracting bibliographic reference information from Markdown files.

This module provides functions to extract reference details (like authors, title,
year, ISBN for books, or report number, institution for reports) from the
beginning and end of Markdown files.
"""

import os
import re
import json
from typing import Dict, Optional, Any

from openai import OpenAI
from regex import P

from fttracer.tools.data_preprocess.prompt import prompt_for_ref_info_extraction


def _extract_with_llm(
    text_snippet: str,
    llm_client: OpenAI,
) -> Dict[str, Any]:
    """Extracts reference info by calling a Large Language Model.

    Args:
        text_snippet: The combined text snippet (front + back) from the Markdown file.
        llm_client: An initialized OpenAI client instance.
        custom_prompt: An optional custom prompt. If None, a default prompt is used.

    Returns:
        A dictionary with extracted fields from the LLM response.
        Returns a default dict with an 'error' key if LLM call fails.
    """
    response_text = "null"
    # Use custom prompt if provided, otherwise use the default one
    prompt = prompt_for_ref_info_extraction(text_snippet=text_snippet)

    try:
        # Call the LLM API with the formatted prompt
        completion = llm_client.chat.completions.create(
            model="doubao-1-5-pro-32k-250115",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert bibliographic information extractor.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,  # Use deterministic output
            response_format={"type": "json_object"},  # Request JSON response
        )
        # Extract the response content
        response_text = completion.choices[0].message.content.strip()

        # Remove Markdown code block formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```

        response_text = response_text.strip()

        # Fix issues like `"key": : value` (extra colon)
        response_text = re.sub(r'"\s*:\s*:\s*', '": ', response_text)

        # Debug print
        # print("Before JSON parsing:", repr(response_text))

        # Use built-in method to handle duplicate keys
        extracted_info = json.loads(
            response_text, object_pairs_hook=lambda pairs: dict(pairs)
        )

        return extracted_info

    except json.JSONDecodeError as e:
        print("Failed to parse LLM response as JSON:", str(e))
        print("Response was:", repr(response_text))
        raise

    except json.JSONDecodeError as e:
        error_msg = (
            f"Failed to parse LLM response as JSON: {e}. Response was: {response_text}"
        )
        print(error_msg)
        return {"error": error_msg, "raw_response": response_text}


def _extract_reference_info(
    md_file_path: str,
    preview_length: int = 2000,
    llm_client: Optional[OpenAI] = None,
) -> Dict[str, Any]:
    """Extracts bibliographic reference information from a Markdown file.

    This function reads the beginning and end of a Markdown file and attempts
    to extract standard bibliographic fields. It can use either rule-based
    regex matching or a Large Language Model (LLM) for extraction.

    Args:
        md_file_path: The path to the Markdown file.
        preview_length: The number of characters to read from the start and
            end of the file. Defaults to 2000.
        llm_client: An initialized OpenAI client instance. Required if using LLM.
        llm_prompt: An optional custom prompt for the LLM. If None, a default
            prompt is used.

    Returns:
        A dictionary containing the extracted reference information. Fields
        not found will have a value of None (or null in the final JSON).
        If an error occurs, the dictionary may contain an 'error' key with details.
    """
    if not os.path.exists(md_file_path):
        raise FileNotFoundError(f"The file {md_file_path} does not exist.")

    if llm_client is None:
        raise ValueError(
            "An `llm_client` instance is required when using LLM extraction."
        )

    with open(md_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract front and back portions of the file content
    front = content[:preview_length]
    back = content[-preview_length:]
    # Combine front and back for LLM analysis
    text_snippet = front + back

    # Extract reference information using the LLM
    return _extract_with_llm(text_snippet, llm_client)


def process_directory(
    root_path: str,
    llm_client: Optional[OpenAI] = None,
) -> None:
    """Processes all Markdown files in a directory to extract reference info.

    This function iterates through all '.md' files in the 'markdown/'
    subdirectory of `root_path`. It calls `_extract_reference_info` for each
    file and saves the results as a corresponding '.json' file in the
    'reference_info/' subdirectory.

    Args:
        root_path: The root directory path. It should contain a 'markdown/'
            subdirectory.
        llm_client: An initialized OpenAI client instance. Required if using LLM.
        llm_prompt: An optional custom prompt for the LLM.
    """
    # Define paths for markdown and reference info directories
    markdown_dir = os.path.join(root_path, "markdown")
    ref_info_dir = os.path.join(root_path, "reference_info")

    # Check if markdown directory exists
    if not os.path.exists(markdown_dir):
        print(f"Markdown directory not found: {markdown_dir}")
        return  # Gracefully handle missing directory

    # Create reference info directory if it doesn't exist
    os.makedirs(ref_info_dir, exist_ok=True)
    print(f"Processing files in {markdown_dir}, saving to {ref_info_dir}")

    # Process each markdown file in the directory
    for filename in os.listdir(markdown_dir):
        if filename.endswith(".md"):
            md_path = os.path.join(markdown_dir, filename)
            json_filename = filename.replace(".md", ".json")
            json_path = os.path.join(ref_info_dir, json_filename)

            # Skip if reference info already exists
            if os.path.exists(json_path):
                print(f"Skipping {md_path}, reference info already exists: {json_path}")
                continue

            print(f"Processing file: {md_path}")
            try:
                # Extract reference information from the markdown file
                ref_info = _extract_reference_info(
                    md_file_path=md_path,
                    llm_client=llm_client,
                )

                # Save the extracted information to a JSON file
                with open(json_path, "w", encoding="utf-8") as f_out:
                    json.dump(ref_info, f_out, ensure_ascii=False, indent=2)
                print(f"Saved reference info to: {json_path}")
            except Exception as e:  # Catch any unexpected errors during processing
                print(f"Failed to process {md_path}: {e}")
                # Optionally, save an error report
                error_info = {"error_during_processing": str(e)}
                with open(json_path, "w", encoding="utf-8") as f_out:
                    json.dump(error_info, f_out, ensure_ascii=False, indent=2)


def extract_ref_info(input_dir: str) -> None:
    """Main entry point for the application.

    Args:
        input_dir: Root directory path containing markdown/ subdirectory.
    """
    llm_client = None
    # Get the default LLM prompt for reference information extraction

    try:
        # Initialize OpenAI client with Ark API key from environment
        llm_client = OpenAI(
            api_key=os.environ.get("ARK_API_KEY"),
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )
    except Exception as e:
        print(f"Failed to initialize LLM client: {e}")
        return

    # Process all markdown files in the directory
    process_directory(
        root_path=input_dir,
        llm_client=llm_client,
    )

    print("All files processed successfully!")


if __name__ == "__main__":
    extract_ref_info(input_dir="report")
