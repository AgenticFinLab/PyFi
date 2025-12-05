"""Script to analyze compliance and complexity levels from JSON files, 
extract top complex images, and filter based on chart types and content themes."""

import os
import json
import statistics
from collections import Counter


def sample_images(
    base_dir=r"PyFi",
    compliance_thresholds=[9, 10],
    complexity_top_n=20000,
    output_filename="sampled_images_indices.txt",
    filtered_output_filename="sampled_images_indices_filtered.txt",
    keep_chart_types=None,
    sampling_limit_per_theme=200,
    show_stats=True,
):
    """
    Main function to process JSON files, compute statistics, extract top complex images,
    and filter based on chart types and content themes.

    Args:
        base_dir (str): Base directory path where evaluation and classification JSON files are stored
        compliance_thresholds (list): List of compliance levels to filter by. Default is [9, 10]
        complexity_top_n (int): Number of top complex images to extract. Default is 20000
        output_filename (str): Name of output file to save indices before filtering
        filtered_output_filename (str): Name of output file to save filtered indices
        keep_chart_types (set): Set of chart type IDs to keep (default: {1, 2, 6, 9, 11})
        sampling_limit_per_theme (int): Maximum number of images per content theme (default: 200)
        show_stats (bool): Whether to print detailed statistics. Default is True
    """

    # Set default chart types if none provided
    if keep_chart_types is None:
        keep_chart_types = {1, 2, 6, 9, 11}

    # Define paths based on base_dir
    json_evaluation_path = os.path.join(base_dir, "images_eval")
    json_classification_path = os.path.join(base_dir, "image_classification")

    # Initialize lists for collecting compliance and complexity data
    compliance_levels = []
    complexity_levels = []
    total_files = 0

    # Store records that meet the condition: compliance_level in specified thresholds
    # These are considered high compliance images that we want to analyze for complexity
    filtered_records = []

    # Traverse all subdirectories in base_path to process JSON files
    for folder_name in os.listdir(json_evaluation_path):
        folder_path = os.path.join(json_evaluation_path, folder_name)

        # Only process directories, skip files
        if not os.path.isdir(folder_path):
            continue

        # Process each JSON file in the current directory
        for file_name in os.listdir(folder_path):
            if not file_name.endswith(".json"):
                continue

            file_path = os.path.join(folder_path, file_name)

            try:
                # Load JSON data from file
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract and normalize compliance_level to integer
                compliance_level = data.get("compliance_level")
                if compliance_level is not None:
                    if isinstance(compliance_level, str):
                        # Convert string representation of number to integer
                        compliance_level = int(compliance_level)
                    compliance_levels.append(compliance_level)

                # Extract and normalize complexity_level to integer
                complexity_level = data.get("complexity_level")
                if complexity_level is not None:
                    if isinstance(complexity_level, str):
                        # Convert string representation of number to integer
                        complexity_level = int(complexity_level)
                    complexity_levels.append(complexity_level)

                    # Save record if compliance level meets threshold criteria
                    # This ensures we only consider well-compliant images for complexity analysis
                    if compliance_level in compliance_thresholds:
                        filtered_records.append(
                            (complexity_level, folder_name, file_name)
                        )

                total_files += 1

            except Exception as e:
                # Log any errors encountered while processing individual files
                print(f"Error processing file {file_path}: {e}")

    # Print summary of processed files to show progress
    print(f"Total number of JSON files processed: {total_files}")

    # Print detailed statistics for both compliance and complexity metrics if requested
    if show_stats:
        print_detailed_stats(compliance_levels, "compliance_level")
        print_detailed_stats(complexity_levels, "complexity_level")

    # Sort records by complexity in descending order to get most complex first
    # This allows us to easily extract the top complex images
    filtered_records.sort(key=lambda x: x[0], reverse=True)
    top_n_records = filtered_records[:complexity_top_n]

    # Write indices of top complex images to a text file for further processing
    with open(output_filename, "w") as f:
        for _, folder_name, file_name in top_n_records:
            # Extract base name without extension
            base_name = os.path.splitext(file_name)[0]
            # Zero-pad folder name to 6 digits for consistent formatting
            folder_id = folder_name.zfill(6)
            # Zero-pad file name to 6 digits for consistent formatting
            file_id = base_name.zfill(6)
            # Create index string in format: folder_id-file_id
            index_str = f"{folder_id}-{file_id}"
            f.write(index_str + "\n")

    print(
        f"\nTop {complexity_top_n} most complex image indices saved to {output_filename}"
    )

    # Now filter the sampled images based on chart types and content themes
    print("\nStarting filtering process...")

    # Initialize counter for content themes to track sampling limits
    content_theme_counter = {}

    # Initialize lists and counters for processing statistics
    filtered_lines = []  # Store lines that meet all filtering criteria
    total_processed = 0  # Total number of lines processed from input file
    total_kept = 0  # Total number of lines that passed all filters

    # Process each line in the input text file containing image indices
    with open(output_filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()  # Remove leading/trailing whitespace
            if not line:  # Skip empty lines to avoid processing errors
                continue

            total_processed += 1  # Increment counter for processed lines

            # Parse folder ID and file ID from the formatted line (format: folder_id-file_id)
            folder_id, file_id = line.split("-")

            # Construct JSON file path using folder ID and file ID
            # This creates the complete path to the corresponding JSON classification file
            json_filename = f"{file_id}.json"
            json_file_path = os.path.join(
                json_classification_path, folder_id, json_filename
            )

            # Check if JSON file exists before attempting to read it
            # Skip processing if file is missing to avoid errors
            if not os.path.exists(json_file_path):
                print(f"File not found: {json_file_path}")
                continue

            try:
                # Load JSON data from the classification file
                with open(json_file_path, "r", encoding="utf-8") as json_f:
                    data = json.load(json_f)

                # Extract chart types and content themes from JSON data
                # These fields contain the classification information for the image
                chart_types = data.get("chart_type", [])
                content_themes = data.get("content_theme", [])

                # Convert chart types and content themes to integers if they are strings or floats
                # This ensures consistent data type for comparison operations
                chart_types = [
                    int(t) if isinstance(t, (str, float)) else t for t in chart_types
                ]
                content_themes = [
                    int(t) if isinstance(t, (str, float)) else t for t in content_themes
                ]

                # Check if any chart type matches our keep list and content themes exist
                # Only process if the image has at least one valid chart type and content themes
                has_valid_chart_type = any(
                    chart_type in keep_chart_types for chart_type in chart_types
                )

                # Process line only if it has valid chart type and content themes
                if has_valid_chart_type and content_themes:
                    # Check if any content theme is within sampling limit
                    # We only need one content theme to be within limit for the line to be kept
                    should_keep_line = False
                    for content_theme in content_themes:
                        # Initialize counter for new content theme if not already present
                        if content_theme not in content_theme_counter:
                            content_theme_counter[content_theme] = 0

                        # Keep line if content theme count is below the specified limit
                        # This ensures balanced representation across different content themes
                        if (
                            content_theme_counter[content_theme]
                            < sampling_limit_per_theme
                        ):
                            should_keep_line = True
                            content_theme_counter[content_theme] += 1
                            break  # One valid theme is sufficient, exit loop early

                    # Add line to filtered results if it meets all criteria
                    if should_keep_line:
                        filtered_lines.append(line)
                        total_kept += 1

            except Exception as e:
                # Log any errors encountered while processing individual JSON files
                print(f"Error processing file {json_file_path}: {e}")

    # Write filtered results to output file, each line representing a valid image index
    with open(filtered_output_filename, "w", encoding="utf-8") as f:
        for line in filtered_lines:
            f.write(line + "\n")

    # Print processing statistics to show the filtering results
    print(f"Total lines processed: {total_processed}")
    print(f"Lines kept after filtering: {total_kept}")
    print(f"Filtered indices saved to: {filtered_output_filename}")

    # Print content theme distribution to verify balanced sampling
    print("\nContent theme counts:")
    for theme, count in sorted(content_theme_counter.items()):
        print(f"  content_theme {theme}: {count}")

    # Return some useful information about the process
    return {
        "total_files_processed": total_files,
        "compliance_levels_count": len(compliance_levels),
        "complexity_levels_count": len(complexity_levels),
        "filtered_records_count": len(filtered_records),
        "output_records_count": len(top_n_records),
        "filtered_output_records_count": len(filtered_lines),
        "output_file": output_filename,
        "filtered_output_file": filtered_output_filename,
    }


def print_detailed_stats(levels, name):
    """Print detailed statistical information for a list of numeric values.

    Args:
        levels: A list of numeric values representing compliance or complexity levels.
        name: The name of the metric being analyzed (e.g., "compliance_level").
    """
    if not levels:
        print(f"\n=== {name} has no data ===")
        return

    # Count occurrences of each level value
    counter = Counter(levels)
    print(f"\n=== Detailed statistics for {name} ===")
    print(f"Total count: {len(levels)}")
    print(f"Mean: {statistics.mean(levels):.2f}")
    print(f"Median: {statistics.median(levels):.2f}")
    print(f"Min: {min(levels)}")
    print(f"Max: {max(levels)}")
    print(
        f"Standard deviation: "
        f"{statistics.stdev(levels) if len(levels) > 1 else 0:.2f}"
    )

    print("\nDistribution by level:")
    # Print count and percentage for each unique level value
    for level in sorted(counter.keys()):
        percentage = (counter[level] / len(levels)) * 100
        print(f"  Level {level}: {counter[level]} entries ({percentage:.1f}%)")


# Example usage examples:
if __name__ == "__main__":
    result = sample_images(
        base_dir=r"PyFi",
        compliance_thresholds=[9, 10],
        complexity_top_n=20000,
        output_filename="sampled_images_indices.txt",
        filtered_output_filename="sampled_images_indices_filtered.txt",
        keep_chart_types={1, 2, 6, 9, 11},
        sampling_limit_per_theme=200,
        show_stats=True,
    )

    print("\nProcess completed. Results summary:")
    print(f"{result['output_records_count']} records saved before filtering")
    print(f"{result['filtered_output_records_count']} records saved after filtering")
