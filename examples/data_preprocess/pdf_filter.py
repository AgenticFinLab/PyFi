"""
Categorize downloaded PDFs into three folders (to_keep, to_delete, uncertain)
auto_cleanup=True: delete PDFs in to_delete/uncertain folders; else retain for review
"""

import argparse

from fttracer.tools.data_preprocess.pdf_filter import filter_pdfs
from fttracer.tools.data_preprocess.prompt import prompt_for_pdf_filter


def main():
    """Categorize PDFs with configurable input directory and cleanup behavior."""
    parser = argparse.ArgumentParser(
        description="Filter and classify PDF books using prior knowledge and Qwen."
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="raw_pdfs",
        help="Input directory containing PDF files (default: 'raw_pdfs').",
    )
    parser.add_argument(
        "--auto_cleanup",
        "-c",
        action="store_true",
        default=False,
        help="Automatically restore kept/uncertain files and remove temp folders.",
    )
    parser.add_argument(
        "--size_threshold",
        "-s",
        type=int,
        default=1,
        help="Minimum file size to retain (default: 1MB).",
    )

    args = parser.parse_args()

    prompt = prompt_for_pdf_filter()

    filter_pdfs(
        input_dir=args.input_dir,
        auto_cleanup=args.auto_cleanup,
        size_threshold=args.size_threshold,
        prompt=prompt,
    )


if __name__ == "__main__":
    main()
