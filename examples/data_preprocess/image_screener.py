"""
Eliminate low-quality images via content rules
Manual review based on the JSON file of model responses
"""

import argparse

from fttracer.tools.data_preprocess.image_screener import screen_image


def main():

    parser = argparse.ArgumentParser(
        description="Eliminate low-quality images via content rules"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="reorganized_results",
        help="Directory containing the reorganized files (default: reorganized_results)",
    )

    args = parser.parse_args()
    screen_image(
        input_dir=args.input_dir,
    )


if __name__ == "__main__":
    main()
