"""
Script to extract and structure contextual information from JSON files.
"""

import argparse

from fttracer.tools.data_preprocess.context_summarizer_via_LLM import (
    context_summarizer_via_LLM,
)


def main():
    parser = argparse.ArgumentParser(
        description="Extract and structure contextual information"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="PyFi",
        help="Source directory containing JSON files of contextual information",
    )
    args = parser.parse_args()

    context_summarizer_via_LLM(
        input_dir=args.input_dir,
    )


if __name__ == "__main__":
    main()
