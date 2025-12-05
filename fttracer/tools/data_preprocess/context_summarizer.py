"""Script to extract and structure contextual information from JSON files."""

import re
import os
import json

from pathlib import Path
from typing import Dict, Any, List, Tuple

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set random seed for consistent results
DetectorFactory.seed = 0


def is_chinese_text(text: str, min_confidence: float = 0.5) -> bool:
    """Check if text is Chinese using language detection with regex fallback.

    Uses langdetect library for primary language detection with a fallback to regex
    pattern matching for short texts or when language detection fails.

    Args:
        text: Input text to check for Chinese language.
        min_confidence: Minimum confidence threshold (not used in current implementation
            but kept for future compatibility).

    Returns:
        True if text is detected as Chinese, False otherwise.

    Raises:
        None: All exceptions are handled internally with fallback to regex method.
    """
    # Handle empty or whitespace-only input
    if not text or not text.strip():
        return False

    # Preprocess: remove extra whitespace and normalize
    cleaned_text = " ".join(text.split())

    # For very short texts, use character ratio check instead of language detection
    if len(cleaned_text) < 3:
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", cleaned_text)
        # Consider text Chinese if more than 50% of characters are Chinese
        return len(chinese_chars) / len(cleaned_text) > 0.5 if cleaned_text else False

    try:
        # Primary method: use language detection library
        language = detect(cleaned_text)
        # Return True for any Chinese language variant
        return language in ["zh-cn", "zh-tw", "zh"]
    except LangDetectException:
        # Fallback method: regex pattern matching for Chinese characters
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", cleaned_text)
        return len(chinese_chars) > 0


def trim_text_to_sentences(text: str, max_chars: int = 1000) -> str:
    """Trim text to approximately max_chars while keeping complete sentences.

    This function ensures that the trimmed text starts and ends with complete sentences
    by finding the nearest sentence boundaries around the middle of the text. It supports
    multiple sentence-ending punctuation marks in both English and Chinese.

    Args:
        text: The text to be trimmed.
        max_chars: Maximum number of characters to keep.

    Returns:
        Trimmed text with complete sentences at beginning and end.

    Raises:
        ValueError: If max_chars is less than 1.
    """
    # Validate input parameters
    if max_chars < 1:
        raise ValueError("max_chars must be at least 1")

    # Return original text if it's already within the limit
    if len(text) <= max_chars:
        return text

    # Define sentence ending characters for both English and Chinese
    SENTENCE_ENDERS = (".", "?", "!", "。", "？", "！")

    # Find the middle point of the text
    middle = len(text) // 2
    half_max = max_chars // 2

    # Calculate initial start and end indices around the middle
    start_idx = max(0, middle - half_max - 200)
    end_idx = min(len(text), middle + half_max + 200)

    # Find the last sentence end before the start index
    last_ender_before = -1
    for ender in SENTENCE_ENDERS:
        pos = text.rfind(ender, 0, start_idx)
        if pos > last_ender_before:
            last_ender_before = pos

    # Adjust start index if a sentence end is found within a reasonable distance
    if last_ender_before != -1 and start_idx - last_ender_before < 200:
        start_idx = last_ender_before + 1

    # Find the first sentence end after the end index
    first_ender_after = len(text)
    for ender in SENTENCE_ENDERS:
        pos = text.find(ender, end_idx)
        if pos != -1 and pos < first_ender_after:
            first_ender_after = pos

    # Adjust end index if a sentence end is found within a reasonable distance
    if first_ender_after != len(text) and first_ender_after - end_idx < 200:
        end_idx = first_ender_after + 1

    # If the text is still too long after initial adjustment, try a different approach
    if end_idx - start_idx > max_chars:
        # Look for a sentence end near the middle of the text
        middle_ender = -1
        for ender in SENTENCE_ENDERS:
            pos = text.find(ender, middle - 100, middle + 100)
            if pos != -1 and (
                middle_ender == -1 or abs(pos - middle) < abs(middle_ender - middle)
            ):
                middle_ender = pos

        # If a sentence end is found near the middle, use it as a new anchor point
        if middle_ender != -1:
            start_idx = max(0, middle_ender - half_max)
            end_idx = min(len(text), middle_ender + half_max)

            # Try to find sentence boundaries again with the new anchor point
            last_ender_before = -1
            for ender in SENTENCE_ENDERS:
                pos = text.rfind(ender, 0, start_idx)
                if pos > last_ender_before:
                    last_ender_before = pos

            if last_ender_before != -1 and start_idx - last_ender_before < 200:
                start_idx = last_ender_before + 1

            first_ender_after = len(text)
            for ender in SENTENCE_ENDERS:
                pos = text.find(ender, end_idx)
                if pos != -1 and pos < first_ender_after:
                    first_ender_after = pos

            if first_ender_after != len(text) and first_ender_after - end_idx < 200:
                end_idx = first_ender_after + 1

    # # Final check to ensure we're within limits
    # if end_idx - start_idx > max_chars:
    #     # If still too long, just take the middle portion and add ellipsis
    #     start_idx = middle - (max_chars // 2)
    #     end_idx = middle + (max_chars // 2)
    #     return text[start_idx:end_idx].strip() + "..."

    # Return the trimmed text
    return text[start_idx:end_idx].strip()


def load_abbreviations(book_id: str, abbreviations_folder: str) -> Dict[str, str]:
    """Loads the abbreviation dictionary for a given book from a JSON file."""
    # Construct the full path to the abbreviation file
    abbreviations_file = os.path.join(abbreviations_folder, f"{book_id}.json")

    # Check if the abbreviation file exists
    if os.path.exists(abbreviations_file):
        try:
            # Open and load the JSON file containing abbreviations
            with open(abbreviations_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as error:
            # Log any errors that occur during file loading
            print(f"Error loading abbreviation file {book_id}.json: {error}")
            return {}
    else:
        # Log a message if the abbreviation file is not found
        print(f"Abbreviation file not found: {book_id}.json")
        return {}


def expand_abbreviations_in_context(
    contextual_info: str, abbreviations_dict: Dict[str, str]
) -> str:
    """Expands abbreviations in the given text by appending their full forms."""
    # Return early if either input is empty or None
    if not contextual_info or not abbreviations_dict:
        return contextual_info

    # Regular expression pattern to match sequences of 2+ uppercase letters
    # \b ensures word boundaries to avoid matching parts of longer strings
    uppercase_pattern = r"([A-Z]{2,})"

    # Find all matches of the pattern in the text
    matches = list(re.finditer(uppercase_pattern, contextual_info))

    # Start with the original text and apply replacements
    expanded_info = contextual_info

    # Offset to track position changes due to previous replacements
    offset = 0

    # Process matches in reverse order to maintain correct indices
    # This prevents index shifting issues when making replacements
    for match in reversed(matches):
        # print(offset)
        # Extract the matched abbreviation
        abbreviation = match.group(1)

        # Calculate the actual start and end positions in the modified text
        start_pos = match.start() + offset
        end_pos = match.end() + offset

        # Check if the abbreviation exists in our dictionary
        if abbreviation in abbreviations_dict:
            # print(abbreviation)
            # Get the full form of the abbreviation
            full_form = abbreviations_dict[abbreviation]

            # Create the replacement string: "ABBR (Full Form)"
            replacement = f"{abbreviation} ({full_form})"
            # print(replacement)

            # Perform the replacement in the text
            expanded_info = (
                expanded_info[:start_pos] + replacement + expanded_info[end_pos:]
            )

            # Update the offset to account for the length change
            offset += len(replacement) - len(abbreviation)

    return expanded_info


def extract_context_summary(json_file_path: Path, output_base_dir: Path) -> None:
    """Extract and save context information from a JSON file for LLM processing.

    Each item is processed and saved individually to reduce memory usage.

    Args:
        json_file_path: Path to the JSON file containing context data.
        output_base_dir: Base directory to save the output JSON files.
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            context_data = json.load(file)
    except Exception as error:
        print(f"Error reading context file {json_file_path}: {error}")
        return

    abbreviations_folder = r"E:\\fttracer\\4_sampled_data\\abbreviations_table"

    for item in context_data:
        try:
            image_filename = item.get("image_filename", "")
            book_id = item.get("book_id", "")
            image_surround_text = item.get("image_surround_text", "")

            # Skip items missing essential identifiers
            if not image_filename or not book_id:
                continue

            classification = item.get("classification", "")
            image_path = f"images/{book_id}/{image_filename}"

            # Handle different classification types
            if classification == "normal":
                caption = item.get("nearest_caption", "")
                caption_references = item.get("caption_references", [])

                # Determine max_chars based on language
                max_chars = 4000 if not is_chinese_text(image_surround_text) else 1000

                # Trim the surrounding text to appropriate number of characters
                if image_surround_text and len(image_surround_text) > max_chars:
                    image_surround_text = trim_text_to_sentences(
                        image_surround_text, max_chars
                    )

                contextual_info_parts = [f"The path of this image is: [{image_path}]."]

                # Add caption information if available
                if caption:
                    contextual_info_parts.append(
                        f"\n\nThe caption for this image is: {caption}"
                    )

                # Process caption references if available
                exact_references = []
                if caption_references:
                    for ref_group in caption_references:
                        for ref in ref_group.get("references", []):
                            if ref.get("is_exact_match", False):
                                reference_extension = ref.get(
                                    "reference_paragraph_extension", ""
                                )
                                ref_max_chars = (
                                    4000
                                    if not is_chinese_text(reference_extension)
                                    else 1000
                                )
                                if (
                                    reference_extension
                                    and len(reference_extension) > ref_max_chars
                                ):
                                    reference_extension = trim_text_to_sentences(
                                        reference_extension, ref_max_chars
                                    )
                                exact_references.append(reference_extension)

                    # Add exact references if found
                    if exact_references and exact_references[0]:
                        contextual_info_parts.append(
                            "\n\nThis image is referenced in the following content:"
                        )
                        contextual_info_parts.append(f"- {exact_references[0]}")
                    else:
                        contextual_info_parts.append(
                            f"\n\nThe context surrounding this image is as follows: {image_surround_text}"
                        )
                else:
                    if image_surround_text:
                        contextual_info_parts.append(
                            f"\n\nThe context surrounding this image is as follows: {image_surround_text}"
                        )
            else:
                contextual_info_parts = [
                    f"The path of this image is: [{image_path}]. Refer to the context below to locate where this image appears in the document."
                ]
                image_surround_text = item.get("image_surround_text", "")
                max_chars = 4000 if not is_chinese_text(image_surround_text) else 1000
                if image_surround_text and len(image_surround_text) > max_chars:
                    image_surround_text = trim_text_to_sentences(
                        image_surround_text, max_chars
                    )
                if image_surround_text:
                    contextual_info_parts.append(
                        f"\n\nThe context surrounding this image is as follows: {image_surround_text}"
                    )

            # Combine all parts into a single contextual information string

            if len(contextual_info_parts) < 500:
                contextual_info_parts.append(
                    f"\n\nThe context surrounding this image is as follows: {image_surround_text}"
                )
                contextual_info = "".join(contextual_info_parts)

            contextual_info = "".join(contextual_info_parts)

            # # Load abbreviations and expand
            # abbreviations_dict = load_abbreviations(book_id, abbreviations_folder)
            # expanded_contextual_info = expand_abbreviations_in_context(image_surround_text, abbreviations_dict)

            # Final structured item
            extracted_item = {"contextual_information": contextual_info}

            # Save immediately to disk
            book_output_dir = output_base_dir / book_id
            book_output_dir.mkdir(parents=True, exist_ok=True)
            output_file_path = book_output_dir / f"{image_filename[:-4]}.json"

            if output_file_path.exists():
                print(f"Skipping {output_file_path} - already exists")
                continue

            with open(output_file_path, "w", encoding="utf-8") as file:
                json.dump(extracted_item, file, ensure_ascii=False, indent=2)
            print(f"Saved extracted data to {output_file_path}")

        except Exception as error:
            print(f"Error processing item {image_filename} in {book_id}: {error}")

    print(f"Finished processing {json_file_path.name}")


def context_summarizer(input_dir: str) -> None:
    """Process all JSON files in the context directory and save extracted information.

    Args:
        root_dir: Root directory containing the context folder.
    """
    input_dir = Path(input_dir)
    context_dir = input_dir / "context"
    output_base_dir = input_dir / "context_summary"

    # Create output base directory if it doesn't exist
    output_base_dir.mkdir(exist_ok=True)

    # Process each JSON file in the context directory
    for json_file_path in context_dir.glob("*.json"):
        # print(f"Processing {json_file_path.name}...")

        # Save each extracted item into its own JSON file under book_id folder
        extract_context_summary(json_file_path, output_base_dir)


# Example usage
if __name__ == "__main__":
    # Replace with your actual root directory path
    context_summarizer("E:\\fttracer\\4_sampled_data")
