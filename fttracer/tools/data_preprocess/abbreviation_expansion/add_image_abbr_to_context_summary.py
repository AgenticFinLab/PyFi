import os
import json
from typing import Dict, Any


def add_image_abbr(
    image_acronyms_path: str, context_summary_path: str, output_path: str
) -> None:
    """
    Process acronym expansion files and integrate them into corresponding context summary files.

    This function reads acronym expansion JSON files from the image_acronyms_path directory,
    finds corresponding context summary files, adds the acronym expansions to the contextual
    information, and saves the updated content to a new directory.

    Args:
        image_acronyms_path: Path to directory containing acronym expansion JSON files
        context_summary_path: Path to directory containing context summary JSON files
        output_path: Path where processed files will be saved

    Returns:
        None
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    print(f"Created output directory: {output_path}")

    # Iterate through all JSON files in the acronym expansion directory
    for filename in os.listdir(image_acronyms_path):
        if not filename.endswith(".json"):
            continue

        # Extract the file name without extension
        file_id = filename.replace(".json", "")

        try:
            # Parse the file ID to extract xxxx and yyyy components
            parts = file_id.split("-")
            if len(parts) != 2:
                print(f"Warning: Invalid file naming format: {filename}")
                continue

            first_id, second_id = parts[0], parts[1]

            # Construct paths for input files
            acronym_file_path = os.path.join(image_acronyms_path, filename)
            context_file_path = os.path.join(
                context_summary_path, first_id, f"{second_id}.json"
            )
            output_file_path = os.path.join(output_path, first_id, f"{second_id}.json")

            # Create output subdirectory if it doesn't exist
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            # Read acronym expansion data from JSON file
            with open(acronym_file_path, "r", encoding="utf-8") as acronym_file:
                acronym_data = json.load(acronym_file)

            # Read context summary data from JSON file
            with open(context_file_path, "r", encoding="utf-8") as context_file:
                context_data = json.load(context_file)

            # Extract matched expansions from acronym data
            matched_expansions = acronym_data.get("matched_expansions", {})

            # Format acronym expansions as a readable string
            if matched_expansions:
                acronym_info = "\nAcronyms found in the image and their expansions:\n"
                for acronym, expansion in matched_expansions.items():
                    acronym_info += f"- {acronym}: {expansion}\n"
            else:
                acronym_info = "\n\nNo acronyms were found in the image."

            # Get the original contextual information
            original_context = context_data.get("contextual_information", "")

            # Find the position of the image path sentence and insert acronym info after it
            image_path_marker = "The path of this image is:"
            marker_position = original_context.find(image_path_marker)

            if marker_position != -1:
                # Find the end of the sentence containing the image path
                sentence_end = original_context.find(".\n\n", marker_position)
                if sentence_end != -1:
                    # Insert acronym info after the image path sentence
                    updated_context = (
                        original_context[: sentence_end + 2]
                        + acronym_info
                        + original_context[sentence_end + 2 :]
                    )
                else:
                    # If we can't find the sentence end, append to the end
                    updated_context = original_context + acronym_info
            else:
                # If we can't find the image path marker, append to the end
                updated_context = original_context + acronym_info

            # Create updated data dictionary with contextual information
            updated_data = {"contextual_information": updated_context}

            # Save updated data to output file in JSON format
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                json.dump(updated_data, output_file, indent=2, ensure_ascii=False)

            print(f"Successfully processed and saved: {output_file_path}")

        except FileNotFoundError as e:
            print(f"Error: File not found for {filename}: {e}")
        except json.JSONDecodeError as e:
            print(f"Error: JSON decode error for {filename}: {e}")
        except Exception as e:
            print(f"Error: Unexpected error processing {filename}: {e}")


# Execute main function if script is run directly
if __name__ == "__main__":
    print("Starting acronym expansion processing")

    # Process all acronym expansion files
    add_image_abbr(
        image_acronyms_path=r"E:\fttracer\4_sampled_data\image_acronyms_expansion",
        context_summary_path=r"E:\fttracer\4_sampled_data\context_summary_processed",
        output_path=r"E:\fttracer\4_sampled_data\context_summary_expanded",
    )

    print("Acronym expansion processing completed")
