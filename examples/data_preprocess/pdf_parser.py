"""
Process PDFs via Mineru API and download results.
"""

import os
import argparse
from fttracer.tools.data_preprocess.pdf_parser import parse_pdfs


def main():
    """Process PDF files using Mineru API with configurable parameters."""
    parser = argparse.ArgumentParser(
        description="Process PDF documents using Mineru API for structured data extraction"
    )

    parser.add_argument(
        "-i",
        "--input_dir",
        type=str,
        default="raw_pdfs",
        help="Source directory containing PDF files",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default="parse_results",
        help="Output directory for processed results",
    )
    parser.add_argument(
        "-b",
        "--batch_size",
        type=int,
        default=200,
        help="Maximum number of files per processing batch",
    )
    parser.add_argument(
        "-l", "--language", type=str, default="en", help="Document language code"
    )
    parser.add_argument(
        "--no_check_pdf_limits",
        dest="check_pdf_limits",
        action="store_false",
        help="Disable automatic validation and splitting of oversized PDFs",
    )

    # Set default value for check_pdf_limits
    parser.set_defaults(check_pdf_limits=True)

    args = parser.parse_args()

    # Process PDFs using Mineru API
    parse_pdfs(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        language=args.language,
        check_pdf_limits=args.check_pdf_limits,
    )


if __name__ == "__main__":
    main()
