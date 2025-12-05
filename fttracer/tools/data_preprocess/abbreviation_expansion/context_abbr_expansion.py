from pathlib import Path
import json
import os
import re
from typing import Dict, Any


def expand_abbreviations_in_context(
    contextual_info: str, abbreviations_dict: Dict[str, str]
) -> str:
    """Expands abbreviations in the given text by appending their full forms."""
    # Return early if either input is empty or None
    if not contextual_info or not abbreviations_dict:
        return contextual_info

    # Regular expression pattern to match sequences of 2+ uppercase letters
    # \b ensures word boundaries to avoid matching parts of longer strings
    uppercase_pattern = r"\b([A-Z]{2,})\b"

    def replace_abbreviation(match):
        """Replacement function for regex substitution."""
        abbreviation = match.group(1)
        if abbreviation in abbreviations_dict:
            full_form = abbreviations_dict[abbreviation]
            return f"{abbreviation} ({full_form})"
        else:
            # If abbreviation not found, return original match
            return match.group(0)

    # Use re.sub with the replacement function - this handles all replacements correctly
    expanded_info = re.sub(uppercase_pattern, replace_abbreviation, contextual_info)

    return expanded_info


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


def context_abbr_expansion(
    input_dir: str, output_dir: str, abbreviations_folder: str
) -> None:
    """
    Traverse all JSON files in subdirectories and process contextual_information fields.

    Args:
        source_dir: Directory containing subdirectories with JSON files
        output_dir: Directory to save processed JSON files
        abbreviations_folder: Path to folder containing abbreviations files
    """
    # Convert source_dir and output_dir to Path objects
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Counter for processed files
    processed_count = 0

    # Traverse all subdirectories and JSON files
    for json_file_path in input_dir.rglob("*.json"):
        try:
            # Extract book_id from the parent directory name
            book_id = json_file_path.parent.name

            # Read the JSON file
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract contextual_information field
            if "contextual_information" not in data:
                print(f"Warning: No 'contextual_information' field in {json_file_path}")
                continue

            original_context = data["contextual_information"]

            # Load abbreviations for this book
            abbreviations_dict = load_abbreviations(book_id, abbreviations_folder)

            # Expand abbreviations in the context
            expanded_context = expand_abbreviations_in_context(
                original_context, abbreviations_dict
            )

            # Create processed item with expanded context
            processed_item = {"contextual_information": expanded_context}

            # Create output path maintaining the same directory structure
            relative_path = json_file_path.relative_to(input_dir)
            output_file_path = output_dir / relative_path

            # Create output directory if it doesn't exist
            output_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save processed data to new JSON file
            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(processed_item, f, ensure_ascii=False, indent=2)

            processed_count += 1
            print(f"Processed: {json_file_path} -> {output_file_path}")

        except Exception as e:
            print(f"Error processing {json_file_path}: {e}")

    print(f"Processing complete. Total files processed: {processed_count}")


# Main execution
if __name__ == "__main__":

    # Process all JSON files
    context_abbr_expansion(
        input_dir=r"PyFi\\context_summary",
        output_dir=r"PyFi\\context_summary_processed",
        abbreviations_folder=r"PyFi\\abbreviations_table",
    )
