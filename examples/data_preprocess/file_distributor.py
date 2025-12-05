"""
File distribution utility for organizing image-context pairs into a structured directory.

This module provides functionality to distribute image files and their corresponding
context files into a predefined directory structure with multiple server and shell levels.
The structure is designed to distribute files evenly across a hierarchical organization
for better data management and potential parallel processing scenarios.

Example directory structure:
  PyFi/
    ├── images/
    │   ├── folder1/
    │   │   ├── image1.jpg
    │   │   └── image2.jpg
    │   └── folder2/
    │       └── image3.jpg
    ├── context_summary_LLM/
    │   ├── folder1/
    │   │   ├── image1.json
    │   │   └── image2.json
    │   └── folder2/
    │       └── image3.json
    └── data_folder/
        ├── data_server_001/
        │   ├── data_shell_001/
        │   │   ├── images/
        │   │   │   └── folder1/
        │   │   │       └── image1.jpg
        │   │   └── context/
        │   │       └── folder1/
        │   │           └── image1.json
        │   └── data_shell_002/
        │       ├── images/
        │       │   └── folder2/
        │       │       └── image3.jpg
        │       └── context/
        │           └── folder2/
        │               └── image3.json
        └── data_server_002/
            └── ...
"""

import argparse

from fttracer.tools.data_preprocess.file_distributor import file_distribution


def main():
    """Distribute image-context pairs with configurable parameters."""
    parser = argparse.ArgumentParser(
        description="Distribute image and context files into hierarchical directory structure"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="PyFi",
        help="Source directory containing images and context_summary_LLM",
    )
    parser.add_argument(
        "--num_servers",
        "-s",
        type=int,
        default=25,
        help="Number of server folders to create in the structure (default: 25)",
    )
    parser.add_argument(
        "--num_shells_per_server",
        "-sh",
        type=int,
        default=20,
        help="Number of shell folders per server (default: 20)",
    )
    parser.add_argument(
        "--image_extension",
        "-ext",
        type=str,
        default=".jpg",
        help="File extension to look for in image files (default: .jpg)",
    )

    args = parser.parse_args()

    file_distribution(
        input_dir=args.input_dir,
        num_servers=args.num_servers,
        num_shells_per_server=args.num_shells_per_server,
        image_extension=args.image_extension,
    )


if __name__ == "__main__":
    main()
