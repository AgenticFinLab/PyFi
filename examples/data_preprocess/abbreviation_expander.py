import argparse
import os

from fttracer.tools.data_preprocess.abbreviation_expansion.abbr_full_form_table_construction import (
    construct_abbr_table,
)
from fttracer.tools.data_preprocess.abbreviation_expansion.image_abbr_extraction import (
    image_abbr_extraction,
)
from fttracer.tools.data_preprocess.abbreviation_expansion.image_abbr_expansion import (
    image_abbr_expansion,
)
from fttracer.tools.data_preprocess.abbreviation_expansion.context_abbr_expansion import (
    context_abbr_expansion,
)
from fttracer.tools.data_preprocess.abbreviation_expansion.add_image_abbr_to_context_summary import (
    add_image_abbr,
)


def main():
    parser = argparse.ArgumentParser(
        description="Process abbreviations in Markdown and image files, and expand them in context summaries."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="PyFi",
        help="Root input directory containing 'markdown' and 'images' subfolders.",
    )

    args = parser.parse_args()

    # Define subdirectory paths based on convention
    markdown_dir = os.path.join(args.input_dir, "markdown")
    images_dir = os.path.join(args.input_dir, "images")

    abbreviations_table_dir = os.path.join(args.input_dir, "abbreviations_table")
    image_acronyms_dir = os.path.join(args.input_dir, "image_acronyms")
    image_acronyms_expansion_dir = os.path.join(
        args.input_dir, "image_acronyms_expansion"
    )
    context_summary_dir = os.path.join(args.input_dir, "context_summary")
    context_summary_processed_dir = os.path.join(
        args.input_dir, "context_summary_processed"
    )
    context_summary_expanded_dir = os.path.join(
        args.input_dir, "context_summary_expanded"
    )

    # Ensure output subdirectories exist (optional but recommended)
    for d in [
        abbreviations_table_dir,
        image_acronyms_dir,
        image_acronyms_expansion_dir,
        context_summary_processed_dir,
        context_summary_expanded_dir,
    ]:
        os.makedirs(d, exist_ok=True)

    # Step 1: Build abbreviation table from Markdown files
    construct_abbr_table(
        input_dir=markdown_dir,
        output_dir=abbreviations_table_dir,
    )

    # Step 2: Extract abbreviations from images
    image_abbr_extraction(
        image_dir=images_dir,
        output_dir=image_acronyms_dir,
        image_format="jpeg",
        file_extension=".jpg",
    )

    # Step 3: Expand image abbreviations using the abbreviation table
    image_abbr_expansion(
        image_acronyms_dir=image_acronyms_dir,
        abbreviations_table_dir=abbreviations_table_dir,
        output_dir=image_acronyms_expansion_dir,
    )

    # Step 4: Expand context summaries with abbreviations from context text
    context_abbr_expansion(
        input_dir=context_summary_dir,
        output_dir=context_summary_processed_dir,
        abbreviations_folder=abbreviations_table_dir,
    )

    # Step 5: Add expanded image abbreviations to the processed context summaries
    add_image_abbr(
        image_acronyms_path=image_acronyms_expansion_dir,
        context_summary_path=context_summary_processed_dir,
        output_path=context_summary_expanded_dir,
    )


if __name__ == "__main__":
    main()
