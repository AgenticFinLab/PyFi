"""
Utility for processing image references in multiple Markdown files.

Example directory structure:
  input/
    ├── BookA/
    │   ├── full.md
    │   ├── images/
    │   │   └── fig1.jpg
    │   └── BookA.pdf
    └── BookB/
        ├── full.md
        ├── images/
        │   └── fig2.jpg
        └── BookB.pdf

Output directory structure:
  output/
    ├── markdown/
    │   ├── 000001.md
    │   └── 000002.md
    ├── images/
    │   ├── 000001/
    │   │   └── 000001.jpg
    │   └── 000002/
    │       └── 000001.jpg
    └── pdf/
        ├── 000001.pdf
        └── 000002.pdf
"""

import argparse

from fttracer.tools.data_preprocess.file_reorganizer import reorganize_file


def main():
    """Reorganize files with configurable input and output directories."""
    parser = argparse.ArgumentParser(
        description="Reorganize financial document files into standardized structure"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="parse_results",
        help="Source directory containing Markdown files and associated images",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        default="reorganized_results",
        help="Target directory for standardized output structure",
    )

    args = parser.parse_args()

    reorganize_file(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
