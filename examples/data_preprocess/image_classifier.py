"""
Script to classify images using a large model API with concurrent batch inference.
"""

import asyncio
import argparse
from pathlib import Path

from fttracer.tools.data_preprocess.image_classification import run_classification


def main():
    parser = argparse.ArgumentParser(description="Run image classification.")
    parser.add_argument(
        "--input_dir",
        "-i",
        type=Path,
        default="reorganized_results",
        help="Root directory containing 'images' and 'context' folders.",
    )
    parser.add_argument(
        "--batch_size",
        "-b",
        type=int,
        default=1,
        help="Number of images per batch (default: 1).",
    )
    parser.add_argument(
        "--worker_count",
        "-w",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5).",
    )

    args = parser.parse_args()

    asyncio.run(run_classification(args.input_dir, args.batch_size, args.worker_count))


if __name__ == "__main__":
    main()
