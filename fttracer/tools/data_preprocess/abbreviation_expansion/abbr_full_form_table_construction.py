"""Extracts abbreviations and their full forms from Markdown files.

This script scans through Markdown files in a given directory and identifies
abbreviations (e.g., NASA) that are enclosed in parentheses. It then attempts
to match these abbreviations with the preceding capitalized words to form
a full form (e.g., National Aeronautics and Space Administration). Common
articles and prepositions are skipped during matching.

The results are saved as JSON files in a specified output directory.
"""

import os
import re
import json
import argparse
from collections import OrderedDict
from typing import List, Tuple, Dict, Optional


# Set of common articles, prepositions, and pronouns to skip during matching.
# These words are typically not part of meaningful abbreviations and would
# create false matches if included in the abbreviation matching process.
SKIP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "nor",
    "for",
    "yet",
    "so",
    "at",
    "by",
    "in",
    "of",
    "on",
    "to",
    "up",
    "as",
    "is",
    "it",
    "if",
    "be",
    "do",
    "we",
    "he",
    "she",
    "they",
    "them",
    "us",
    "with",
    "from",
    "into",
    "onto",
    "upon",
    "over",
    "under",
    "out",
    "off",
    "via",
    "per",
    "etc",
    "vs",
    "v",
}


def check_initials_match(abbreviation: str, full_form_words: List[str]) -> bool:
    """Check if each character in the abbreviation matches the first letter of corresponding word.

    This function verifies that:
    1. The abbreviation and word list have the same length
    2. Each word's first letter matches the corresponding character in the abbreviation
    3. No word in the list is composed entirely of uppercase letters (to avoid matching other abbreviations)
    4. Words are processed in strict left-to-right order
    5. Additional validation to avoid trivial or meaningless abbreviations

    Args:
        abbreviation (str): The abbreviation string (e.g., "NASA").
        full_form_words (list[str]): List of words that may form the abbreviation.

    Returns:
        bool: True if all initials match and no word is all uppercase; False otherwise.
    """
    # Abbreviation must have the same number of characters as there are words.
    # This is a fundamental requirement for an abbreviation to match its full form.
    if len(abbreviation) != len(full_form_words):
        return False

    # Avoid trivial abbreviations of length 2 that are common word combinations
    # This prevents false matches like "No Do" for "ND" or "Of From" for "OF"
    if len(abbreviation) == 2:
        # Check if this forms a common non-abbreviation pattern
        trivial_combinations = {
            ("N", "D"),  # Number, No, New, etc.
            ("O", "F"),  # Of, On, Or, etc.
            ("F", "O"),  # For, From, etc.
            ("B", "Y"),  # By, etc.
            ("I", "N"),  # In, etc.
            ("A", "T"),  # At, etc.
            ("T", "O"),  # To, etc.
            ("F", "R"),  # From, For, etc.
        }

        # Create a tuple of first letters from the words to compare with known trivial combinations
        first_letters = tuple([word[0].upper() for word in full_form_words])
        if first_letters in trivial_combinations:
            return False

    # Check each word in strict left-to-right order and verify it's not all uppercase
    # This loop ensures that each word's first letter matches the corresponding character in the abbreviation
    for i, word in enumerate(full_form_words):
        # If word is entirely uppercase, this is likely another abbreviation, so reject
        # This prevents matching abbreviations to other abbreviations (e.g., "USA" to "United States of America")
        if word.isupper():
            return False

        # Compare the first letter of the word with the corresponding character in abbreviation
        # Convert both to uppercase to ensure case-insensitive matching
        first_letter = word[0].upper()
        if abbreviation[i] != first_letter:
            return False

    # Additional validation: avoid abbreviations that are too short or consist of very common words
    if len(abbreviation) <= 2:
        # Count how many words are common function words
        common_words = 0
        for word in full_form_words:
            if word.lower() in {
                "no",
                "not",
                "of",
                "on",
                "in",
                "at",
                "to",
                "for",
                "from",
                "by",
                "or",
                "and",
                "the",
                "a",
                "an",
            }:
                common_words += 1

        # If all words are common function words, this is likely not a real abbreviation
        # This prevents false matches like "To Of" for "TO"
        if common_words == len(full_form_words):
            return False

    # If all checks pass, the abbreviation matches the full form
    return True


def extract_abbreviations_with_full_forms(file_path: str) -> Dict[str, str]:
    """Extracts abbreviations and their corresponding full forms from a Markdown file.

    This function identifies abbreviations as sequences of two or more consecutive
    uppercase letters. For parenthesized abbreviations like (NASA), it searches
    before the abbreviation. For non-parenthesized ones, it looks both before and
    after within a window of words.

    Args:
        file_path: Path to the Markdown file to process.

    Returns:
        An OrderedDict mapping abbreviations to their full forms, preserving the
        order of first occurrence.
    """
    # Read the content of the file with UTF-8 encoding
    # UTF-8 encoding ensures proper handling of international characters
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regular expression pattern to match abbreviations (2+ uppercase letters)
    # \b ensures word boundaries, [A-Z]{2,} matches 2 or more consecutive uppercase letters
    abbr_pattern = r"\b[A-Z]{2,}\b"

    # Find all matches of the abbreviation pattern in the content
    abbr_matches = list(re.finditer(abbr_pattern, content))

    # Ordered dictionary to store unique abbreviations and their full forms
    # OrderedDict preserves the order of first occurrence of each abbreviation
    abbreviations_dict = OrderedDict()

    # Iterate through each abbreviation found in the text
    for abbr_match in abbr_matches:
        # Extract the matched abbreviation string
        abbreviation = abbr_match.group()

        # Get the length of the abbreviation and its position in the text
        abbr_length = len(abbreviation)
        abbr_start = abbr_match.start()
        abbr_end = abbr_match.end()

        # Determine whether the abbreviation is enclosed in parentheses
        # This affects the search strategy (before only for parenthesized, before and after for non-parenthesized)
        is_parenthesized = (
            abbr_start >= 1
            and content[abbr_start - 1] == "("
            and abbr_end < len(content)
            and content[abbr_end] == ")"
        )

        # Extract all words before the abbreviation along with their positions
        # This allows us to look for potential full forms before the abbreviation
        text_before = content[:abbr_start]
        words_before_with_pos = [
            (m.group(), m.start(), m.end())
            for m in re.finditer(r"\b\w+\b", text_before)
        ]

        # Extract all words after the abbreviation along with their positions
        # This allows us to look for potential full forms after the abbreviation
        text_after = content[abbr_end:]
        words_after_with_pos = [
            (m.group(), m.start(), m.end()) for m in re.finditer(r"\b\w+\b", text_after)
        ]

        # Handle parenthesized abbreviations by prioritizing search before
        # For (NASA), we typically expect the full form to appear before it
        if is_parenthesized:
            # Use up to 15 words before the abbreviation for matching
            # This provides a reasonable window for finding the full form
            candidates_before = (
                words_before_with_pos[-15:] if words_before_with_pos else []
            )

            # Extract just the word strings from the candidates
            words = [w[0] for w in candidates_before]

            # Filter out common skip words
            # Create a boolean list indicating which words should be considered
            is_valid = [word.lower() not in SKIP_WORDS for word in words]

            # Get indices of valid (non-skip) words
            valid_indices = [i for i, valid in enumerate(is_valid) if valid]

            # Ensure there are enough valid words to match the abbreviation
            if len(valid_indices) >= abbr_length:
                # Select the last N valid indices where N = abbreviation length
                # This gets the most recent valid words that could form the abbreviation
                selected_valid_indices = valid_indices[-abbr_length:]

                # Include all words between the first and last selected valid word
                # This ensures we get a contiguous phrase that includes the full form
                first_index = selected_valid_indices[0]
                last_index = selected_valid_indices[-1]
                full_form_words = words[first_index : last_index + 1]
                full_form = " ".join(full_form_words)

                # Only use the selected valid words for initial checking
                # This ensures we only validate against the words that should match
                selected_valid_words = [words[i] for i in selected_valid_indices]

                # Validate that the initials match the abbreviation
                if check_initials_match(abbreviation, selected_valid_words):
                    if abbreviation not in abbreviations_dict:
                        abbreviations_dict[abbreviation] = full_form

        # If not found yet, search in non-parenthesized contexts
        # This handles cases where the abbreviation appears without parentheses
        if abbreviation not in abbreviations_dict:
            # Get up to 10 words before and after the abbreviation
            # This creates a reasonable search window around the abbreviation
            candidates_before = (
                list(reversed(words_before_with_pos[-10:]))
                if words_before_with_pos
                else []
            )
            candidates_after = words_after_with_pos[:10] if words_after_with_pos else []

            # Try to find a match in the words before the abbreviation
            if len(candidates_before) >= abbr_length:
                # Restore original order for processing
                candidates_before_original = list(reversed(candidates_before))
                words = [w[0] for w in candidates_before_original]

                # Filter out common skip words
                is_valid = [word.lower() not in SKIP_WORDS for word in words]
                valid_indices = [i for i, valid in enumerate(is_valid) if valid]

                if len(valid_indices) >= abbr_length:
                    # Select the last N valid indices
                    selected_valid_indices = valid_indices[-abbr_length:]

                    # Include all words between the first and last selected valid word
                    first_index = selected_valid_indices[0]
                    last_index = selected_valid_indices[-1]
                    full_form_words = words[first_index : last_index + 1]
                    full_form = " ".join(full_form_words)

                    # Only use the selected valid words for initial checking
                    selected_valid_words = [words[i] for i in selected_valid_indices]

                    if check_initials_match(abbreviation, selected_valid_words):
                        if abbreviation not in abbreviations_dict:
                            abbreviations_dict[abbreviation] = full_form

            # If still not found, try words after the abbreviation
            # This handles cases where the full form comes after the abbreviation
            if (
                abbreviation not in abbreviations_dict
                and len(candidates_after) >= abbr_length
            ):
                words = [w[0] for w in candidates_after]

                # Filter out common skip words
                is_valid = [word.lower() not in SKIP_WORDS for word in words]
                valid_indices = [i for i, valid in enumerate(is_valid) if valid]

                if len(valid_indices) >= abbr_length:
                    # Select the first N valid indices
                    selected_valid_indices = valid_indices[:abbr_length]

                    # Include all words between the first and last selected valid word
                    first_index = selected_valid_indices[0]
                    last_index = selected_valid_indices[-1]
                    full_form_words = words[first_index : last_index + 1]
                    full_form = " ".join(full_form_words)

                    # Only use the selected valid words for initial checking
                    selected_valid_words = [words[i] for i in selected_valid_indices]

                    if check_initials_match(abbreviation, selected_valid_words):
                        if abbreviation not in abbreviations_dict:
                            abbreviations_dict[abbreviation] = full_form

            # Cross-window search: combine words before and after the abbreviation
            # This handles cases where the full form spans across the abbreviation
            if abbreviation not in abbreviations_dict:
                # Combine before and after candidates
                candidates_before_original = (
                    list(reversed(candidates_before)) if candidates_before else []
                )
                combined_candidates = candidates_before_original + candidates_after
                words = [w[0] for w in combined_candidates]

                # Filter out common skip words
                is_valid = [word.lower() not in SKIP_WORDS for word in words]
                valid_indices = [i for i, valid in enumerate(is_valid) if valid]

                if len(valid_indices) >= abbr_length:
                    # Try to find a contiguous valid sequence of length abbr_length
                    found = False
                    for start_idx in range(len(valid_indices) - abbr_length + 1):
                        selected_valid_indices = valid_indices[
                            start_idx : start_idx + abbr_length
                        ]

                        # Include all words between the first and last selected valid word
                        first_index = selected_valid_indices[0]
                        last_index = selected_valid_indices[-1]
                        full_form_words = words[first_index : last_index + 1]
                        full_form = " ".join(full_form_words)

                        # Only use the selected valid words for initial checking
                        selected_valid_words = [
                            words[i] for i in selected_valid_indices
                        ]

                        if check_initials_match(abbreviation, selected_valid_words):
                            if abbreviation not in abbreviations_dict:
                                abbreviations_dict[abbreviation] = full_form
                                found = True
                                break

                    if found:
                        continue

    # Return the dictionary containing all found abbreviations and their full forms
    return abbreviations_dict


def construct_abbr_table(input_dir: str, output_dir: str) -> None:
    """Processes all matching Markdown files in a folder and extracts abbreviations.

    Only processes files with numeric names and .md extension (e.g., 123456789.md).
    Skips files that have already been processed (i.e., corresponding JSON exists).

    Args:
        input_dir (str): Path to the folder containing input Markdown files.
        output_dir (str): Path to the folder where JSON output files will be saved.
    """
    # Create output folder if it doesn't exist
    # This ensures we can write output files even if the output directory doesn't exist yet
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all files in the input folder
    for filename in os.listdir(input_dir):
        # Check if filename matches the pattern: numeric name + .md
        # This specific pattern (numeric + .md) is used to identify the target files
        if filename.endswith(".md") and filename[:-3].isdigit():
            # Construct the full path to the input file
            input_file_path = os.path.join(input_dir, filename)

            # Create the output filename by replacing .md with .json
            output_file_name = filename[:-3] + ".json"

            # Construct the full path to the output file
            output_file_path = os.path.join(output_dir, output_file_name)

            # Skip if JSON file already exists
            # This prevents reprocessing files that have already been processed
            if os.path.exists(output_file_path):
                print(f"Skipping {filename}: JSON already exists.")
                continue

            print(f"Processing file: {filename}")

            try:
                # Extract abbreviations and full forms from the current file
                abbreviations = extract_abbreviations_with_full_forms(input_file_path)

                # Write the extracted abbreviations to a JSON file
                with open(output_file_path, "w", encoding="utf-8") as json_file:
                    json.dump(abbreviations, json_file, ensure_ascii=False, indent=2)

                # Print a success message with the number of abbreviations found
                print(
                    f"Saved: {output_file_name} ({len(abbreviations)} abbreviations found)"
                )

            except Exception as e:
                # Handle any errors that occur during file processing
                print(f"Error processing file {filename}: {str(e)}")


if __name__ == "__main__":

    # Create argument parser to handle command line arguments
    parser = argparse.ArgumentParser(
        description="Extract abbreviations from Markdown files"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Path to the folder containing input Markdown files",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Path to the folder where JSON output files will be saved",
    )

    # Parse command line arguments
    args = parser.parse_args()

    # Process the Markdown files using the provided paths
    construct_abbr_table(args.input_dir, args.output_dir)

    # Print a completion message
    print("All files processed successfully!")
