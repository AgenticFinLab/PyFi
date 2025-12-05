"""
Script to collect and analyze statistics from image classification and evaluation JSON files.
"""

import argparse

from fttracer.tools.data_preprocess.image_statistics import analyze_image_statistics


def main():

    parser = argparse.ArgumentParser(
        description="Collect and analyze statistics from image classification and evaluation JSON files."
    )
    parser.add_argument(
        "--base_dir",
        "-i",
        type=str,
        default="PyFi",
        help="Directory containing the image classification and evaluation JSON files (default: PyFi)",
    )
    parser.add_argument(
        "--output_file",
        "-o",
        type=str,
        default="image_statistics_summary.txt",
        help="Output file to save the statistics summary (default: image_statistics_summary.txt)",
    )

    args = parser.parse_args()
    analyze_image_statistics(
        base_dir=args.base_dir,
        output_file=args.output_file,
    )


if __name__ == "__main__":
    main()
