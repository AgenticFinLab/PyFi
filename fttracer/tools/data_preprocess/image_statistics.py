"""Script to collect and analyze statistics from image classification and evaluation JSON files."""

import os
import json
from collections import Counter


def collect_statistics(classification_dir, eval_dir):
    """Collect statistics from classification and evaluation JSON files.

    Args:
        classification_dir: Path to directory containing classification JSON files.
        eval_dir: Path to directory containing evaluation JSON files.

    Returns:
        Dictionary containing counters for different statistics categories.
    """

    # Initialize statistics data structure to store counters for different categories
    stats = {
        "content_theme": Counter(),  # Counter for content themes
        "chart_type": Counter(),  # Counter for chart types
        "compliance_level": Counter(),  # Counter for compliance levels
        "complexity_level": Counter(),  # Counter for complexity levels
    }

    # Process classification directory for content themes and chart types
    # Walk through all subdirectories and files in the classification directory
    for root, dirs, files in os.walk(classification_dir):
        for file in files:
            # Only process JSON files
            if not file.endswith(".json"):
                continue

            # Construct full file path
            file_path = os.path.join(root, file)

            try:
                # Load JSON data from classification files
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract and count content themes from the JSON data
                if "content_theme" in data:
                    for theme in data["content_theme"]:
                        # Convert theme to integer and increment counter
                        theme_num = int(theme) if isinstance(theme, str) else int(theme)
                        stats["content_theme"][theme_num] += 1

                # Extract and count chart types from the JSON data
                if "chart_type" in data:
                    for chart in data["chart_type"]:
                        # Convert chart type to integer and increment counter
                        chart_num = int(chart) if isinstance(chart, str) else int(chart)
                        stats["chart_type"][chart_num] += 1

            except Exception as e:
                # Print error message if file processing fails
                print(f"Error processing {file_path}: {e}")

    # Process evaluation directory for compliance and complexity levels
    # Walk through all subdirectories and files in the evaluation directory
    for root, dirs, files in os.walk(eval_dir):
        for file in files:
            # Only process JSON files
            if not file.endswith(".json"):
                continue

            # Construct full file path
            file_path = os.path.join(root, file)

            try:
                # Load JSON data from evaluation files
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract and count compliance levels from the JSON data
                if "compliance_level" in data:
                    compliance = data["compliance_level"]
                    # Convert compliance level to integer and increment counter
                    compliance_num = (
                        int(compliance)
                        if isinstance(compliance, str)
                        else int(compliance)
                    )
                    stats["compliance_level"][compliance_num] += 1

                # Extract and count complexity levels from the JSON data
                if "complexity_level" in data:
                    complexity = data["complexity_level"]
                    # Convert complexity level to integer and increment counter
                    complexity_num = (
                        int(complexity)
                        if isinstance(complexity, str)
                        else int(complexity)
                    )
                    stats["complexity_level"][complexity_num] += 1

            except Exception as e:
                # Print error message if file processing fails
                print(f"Error processing {file_path}: {e}")

    return stats


def print_statistics(stats):
    """Print formatted statistics to console in a readable format.

    Args:
        stats: Dictionary containing statistics counters.
    """

    # Print header for the statistics report
    print("=" * 50)
    print("Image Information Statistics Results")
    print("=" * 50)

    # Print content theme statistics with percentages
    print("\n1. Content Theme (content_theme) Statistics:")
    print("-" * 30)
    total_content_theme = sum(stats["content_theme"].values())
    for theme, count in sorted(stats["content_theme"].items()):
        # Calculate percentage for each content theme
        percentage = (
            (count / total_content_theme) * 100 if total_content_theme > 0 else 0
        )
        print(f"   Theme {theme:2d}: {count:6d} images ({percentage:5.2f}%)")
    print(f"   Total: {total_content_theme} images")

    # Print chart type statistics with percentages
    print("\n2. Chart Type (chart_type) Statistics:")
    print("-" * 30)
    total_chart_type = sum(stats["chart_type"].values())
    for chart, count in sorted(stats["chart_type"].items()):
        # Calculate percentage for each chart type
        percentage = (count / total_chart_type) * 100 if total_chart_type > 0 else 0
        print(f"   Type {chart:2d}: {count:6d} images ({percentage:5.2f}%)")
    print(f"   Total: {total_chart_type} images")

    # Print compliance level statistics with percentages
    print("\n3. Compliance Level (compliance_level) Statistics:")
    print("-" * 30)
    total_compliance = sum(stats["compliance_level"].values())
    for level, count in sorted(stats["compliance_level"].items()):
        # Calculate percentage for each compliance level
        percentage = (count / total_compliance) * 100 if total_compliance > 0 else 0
        print(f"   Level {level:2d}: {count:6d} images ({percentage:5.2f}%)")
    print(f"   Total: {total_compliance} images")

    # Print complexity level statistics with percentages
    print("\n4. Complexity Level (complexity_level) Statistics:")
    print("-" * 30)
    total_complexity = sum(stats["complexity_level"].values())
    for level, count in sorted(stats["complexity_level"].items()):
        # Calculate percentage for each complexity level
        percentage = (count / total_complexity) * 100 if total_complexity > 0 else 0
        print(f"   Level {level:2d}: {count:6d} images ({percentage:5.2f}%)")
    print(f"   Total: {total_complexity} images")

    print("\n" + "=" * 50)
    print("Statistics completed!")


def save_statistics_to_txt(stats, output_file="image_statistics_summary.txt"):
    """Save statistics to a text file in English for permanent record.

    Args:
        stats: Dictionary containing statistics counters.
        output_file: Path to output text file where statistics will be saved.
    """

    with open(output_file, "w", encoding="utf-8") as f:
        # Write header information to the output file
        f.write("=" * 50 + "\n")
        f.write("Image Information Statistics Summary\n")
        f.write("=" * 50 + "\n")

        # Write content theme statistics with percentages to file
        f.write("\n1. Content Theme (content_theme) Statistics:\n")
        f.write("-" * 30 + "\n")
        total_content_theme = sum(stats["content_theme"].values())
        for theme, count in sorted(stats["content_theme"].items()):
            # Calculate percentage for each content theme
            percentage = (
                (count / total_content_theme) * 100 if total_content_theme > 0 else 0
            )
            f.write(f"   Theme {theme:2d}: {count:6d} images ({percentage:5.2f}%)\n")
        f.write(f"   Total: {total_content_theme} images\n")

        # Write chart type statistics with percentages to file
        f.write("\n2. Chart Type (chart_type) Statistics:\n")
        f.write("-" * 30 + "\n")
        total_chart_type = sum(stats["chart_type"].values())
        for chart, count in sorted(stats["chart_type"].items()):
            # Calculate percentage for each chart type
            percentage = (count / total_chart_type) * 100 if total_chart_type > 0 else 0
            f.write(f"   Type {chart:2d}: {count:6d} images ({percentage:5.2f}%)\n")
        f.write(f"   Total: {total_chart_type} images\n")

        # Write compliance level statistics with percentages to file
        f.write("\n3. Compliance Level (compliance_level) Statistics:\n")
        f.write("-" * 30 + "\n")
        total_compliance = sum(stats["compliance_level"].values())
        for level, count in sorted(stats["compliance_level"].items()):
            # Calculate percentage for each compliance level
            percentage = (count / total_compliance) * 100 if total_compliance > 0 else 0
            f.write(f"   Level {level:2d}: {count:6d} images ({percentage:5.2f}%)\n")
        f.write(f"   Total: {total_compliance} images\n")

        # Write complexity level statistics with percentages to file
        f.write("\n4. Complexity Level (complexity_level) Statistics:\n")
        f.write("-" * 30 + "\n")
        total_complexity = sum(stats["complexity_level"].values())
        for level, count in sorted(stats["complexity_level"].items()):
            # Calculate percentage for each complexity level
            percentage = (count / total_complexity) * 100 if total_complexity > 0 else 0
            f.write(f"   Level {level:2d}: {count:6d} images ({percentage:5.2f}%)\n")
        f.write(f"   Total: {total_complexity} images\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("Statistics completed!\n")


def analyze_image_statistics(base_dir, output_file="image_statistics_summary.txt"):
    """Main function to analyze image statistics from JSON files with configurable base directory.

    Args:
        base_dir: Base directory containing both classification and evaluation subdirectories
        output_file: Name of the output file to save statistics (default: image_statistics_summary.txt)
    """

    # Construct full paths for classification and evaluation directories
    # Classification directory path: base_dir + "/image_classification"
    classification_dir = os.path.join(base_dir, "image_classification")

    # Evaluation directory path: base_dir + "/images_eval"
    eval_dir = os.path.join(base_dir, "images_eval")

    # Verify that both directories exist before processing
    if not os.path.exists(classification_dir):
        raise FileNotFoundError(
            f"Classification directory does not exist: {classification_dir}"
        )

    if not os.path.exists(eval_dir):
        raise FileNotFoundError(f"Evaluation directory does not exist: {eval_dir}")

    print(f"Starting image statistics collection from base directory: {base_dir}")
    print(f"Classification directory: {classification_dir}")
    print(f"Evaluation directory: {eval_dir}")

    # Collect statistics from both directories
    stats = collect_statistics(classification_dir, eval_dir)

    # Display statistics in console for immediate viewing
    print_statistics(stats)

    # Save statistics to text file for permanent record
    save_statistics_to_txt(stats, output_file=output_file)

    print(f"Statistics saved to: {output_file}")


if __name__ == "__main__":

    # Execute the statistics analysis with default parameters
    analyze_image_statistics(
        base_dir="/root/autodl-tmp/PyFi",
        output_file="image_statistics_summary.txt",
    )
