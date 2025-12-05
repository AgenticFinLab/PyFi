"""
Extract complete reference information for each image from the Markdown file and save it as a JSON file.
"""

import argparse

from fttracer.tools.data_preprocess.ref_info_extractor import extract_ref_info


def main():
    parser = argparse.ArgumentParser(
        description="Extract reference info for each collected financial image"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="reorganized_results",
        help="Directory containing the reorganized files",
    )
    args = parser.parse_args()
    # Extract reference info from markdown file using LLM
    extract_ref_info(input_dir=args.input_dir)


if __name__ == "__main__":
    main()
