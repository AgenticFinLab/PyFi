"""
Extract rich context for each image from the Markdown file, then classify the image based on specific rules.
"""

import argparse

from fttracer.tools.data_preprocess.context_extractor import (
    extract_context,
    classification_statistics,
    abnormal_context_sample,
)


def main():
    parser = argparse.ArgumentParser(
        description="Extract context for each collected financial image"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="reorganized_results",
        help="Directory containing the reorganized files",
    )
    parser.add_argument(
        "--sample_rate",
        type=float,
        default=1.0,
        help="Sample rate for abnormal context files (percentage)",
    )

    args = parser.parse_args()

    # Extract context from reorganized results
    extract_context(args.input_dir)

    # Print classification statistics
    print(classification_statistics(args.input_dir))

    # Sample abnormal context files
    abnormal_context_sample(args.input_dir, args.sample_rate)


if __name__ == "__main__":
    main()
