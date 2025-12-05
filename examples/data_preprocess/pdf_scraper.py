"""
Crawl PDFs from example sources: Bank of China macro reports and World Bank reports
"""

import argparse
from fttracer.tools.data_preprocess.pdf_scraper import crawl_boc, crawl_worldbank


def main():
    """Execute the complete data preprocessing pipeline with configurable options."""
    parser = argparse.ArgumentParser(
        description="Crawl PDFs from financial and economic report sources"
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        default="raw_pdfs",
        help="Directory to save the downloaded PDFs (default: raw_pdfs)",
    )
    parser.add_argument(
        "--sources",
        "-s",
        nargs="+",
        choices=["boc", "worldbank", "all"],
        default=["all"],
        help="Data sources to crawl (default: all)",
    )

    parser.add_argument(
        "--keywords",
        "-k",
        type=str,
        default="finance OR economics OR economic OR financial OR "
        "fiscal OR budget OR trade OR investment OR banking",
        help="Keywords to filter World Bank reports",
    )

    args = parser.parse_args()

    sources = args.sources
    if "all" in sources or ["all"] == sources:
        sources = ["boc", "worldbank"]

    if "boc" in sources:
        crawl_boc(output_dir=args.output_dir)
    if "worldbank" in sources:
        crawl_worldbank(output_dir=args.output_dir, keywords=args.keywords)


if __name__ == "__main__":
    main()
