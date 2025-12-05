"""Script to match acronyms with their expansions from JSON files."""

import os
import json
from typing import Dict, List, Any


def image_abbr_expansion(
    image_acronyms_dir: str, abbreviations_table_dir: str, output_dir: str
) -> None:
    """Process all acronym files and match them with their expansions.

    This function iterates through all JSON files in the image_acronyms directory,
    extracts acronyms from each file, finds corresponding abbreviation tables,
    matches the acronyms with their expansions, and saves the results.

    Args:
        image_acronyms_dir: Path to directory containing acronym files (xxxxxx-yyyyyy.json)
        abbreviations_table_dir: Path to directory containing abbreviation tables (xxxxxx.json)
        output_dir: Path to directory where matched results will be saved
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all files in the image_acronyms directory
    for filename in os.listdir(image_acronyms_dir):
        # Process only JSON files with dash in filename (xxxxxx-yyyyyy.json format)
        if filename.endswith(".json") and "-" in filename:
            # Construct full path to the current acronym file
            image_acronym_file_path = os.path.join(image_acronyms_dir, filename)

            # Extract the first 6 digits from filename to get the document ID
            # Example: from "000197-000004.json" extract "000197"
            document_id = filename.split("-")[0]

            # Construct path to the corresponding abbreviations table file
            abbreviations_file_path = os.path.join(
                abbreviations_table_dir, f"{document_id}.json"
            )

            # Check if the corresponding abbreviations table file exists
            if not os.path.exists(abbreviations_file_path):
                print(
                    f"Warning: Cannot find corresponding abbreviations file {abbreviations_file_path}"
                )
                continue

            try:
                # Load the acronym data from the current image acronym file
                acronym_data = _load_json_file(image_acronym_file_path)

                # Load the abbreviation table data
                abbreviations_data = _load_json_file(abbreviations_file_path)

                # Extract the list of acronyms from the acronym data
                acronyms_list = acronym_data.get("acronyms", [])

                # Match acronyms with their expansions from the abbreviation table
                matched_expansions = _match_acronyms_with_expansions(
                    acronyms_list, abbreviations_data
                )

                # Prepare the output data structure
                output_data = {"matched_expansions": matched_expansions}

                # Construct the output file path
                output_file_path = os.path.join(output_dir, filename)

                # Save the matched results to the output file
                _save_json_file(output_file_path, output_data)

                # Log the processing result
                print(
                    f"Processing completed: {filename} -> Matched {len(matched_expansions)} acronyms"
                )

            except Exception as e:
                # Handle any exceptions that occur during file processing
                print(f"Error processing file {filename}: {str(e)}")


def _load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file.

    Args:
        file_path: Path to the JSON file to load

    Returns:
        Dictionary containing the parsed JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file with proper formatting.

    Args:
        file_path: Path where the JSON file will be saved
        data: Data to be saved as JSON
    """
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def _match_acronyms_with_expansions(
    acronyms_list: List[str], abbreviations_data: Dict[str, str]
) -> Dict[str, str]:
    """Match acronyms with their expansions from the abbreviation table.

    Args:
        acronyms_list: List of acronyms to match
        abbreviations_data: Dictionary mapping acronyms to their expansions

    Returns:
        Dictionary containing matched acronyms and their expansions
    """
    matched_expansions = {}

    # Iterate through each acronym and check if it exists in the abbreviation table
    for acronym in acronyms_list:
        if acronym in abbreviations_data:
            # If found, add the acronym and its expansion to the results
            matched_expansions[acronym] = abbreviations_data[acronym]

    return matched_expansions


if __name__ == "__main__":
    # Process all acronym files
    image_abbr_expansion(
        image_acronyms_dir=r"PyFi\\image_acronyms",
        abbreviations_table_dir=r"PyFi\\abbreviations_table",
        output_dir=r"PyFi\\image_acronyms_expansion",
    )

    # Log completion message
    print("All files processing completed!")
