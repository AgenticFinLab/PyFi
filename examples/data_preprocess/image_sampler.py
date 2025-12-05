"""
Analyze compliance and complexity levels from JSON files, 
extract top complex images, and filter based on chart types and content themes
"""

import argparse

from fttracer.tools.data_preprocess.image_sampler import sample_images

from fttracer.tools.data_preprocess.file_replication import copy_selected_files


def main():
    parser = argparse.ArgumentParser(
        description="Analyze compliance and complexity levels from JSON files, extract top complex images, and filter based on chart types and content themes"
    )
    parser.add_argument(
        "--base_dir",
        "-b",
        type=str,
        default="PyFi",
        help="Base directory path where evaluation and classification JSON files are stored (default: PyFi)",
    )
    parser.add_argument(
        "--compliance_thresholds",
        "-c",
        type=int,
        nargs="+",
        default=[9, 10],
        help="List of compliance levels to filter by (default: [9, 10])",
    )
    parser.add_argument(
        "--complexity_top_n",
        "-n",
        type=int,
        default=20000,
        help="Number of top complex images to extract (default: 20000)",
    )
    parser.add_argument(
        "--output_filename",
        "-o",
        type=str,
        default="sampled_images_indices.txt",
        help="Name of output file to save indices before filtering (default: sampled_images_indices.txt)",
    )
    parser.add_argument(
        "--filtered_output_filename",
        "-f",
        type=str,
        default="sampled_images_indices_filtered.txt",
        help="Name of output file to save filtered indices (default: sampled_images_indices_filtered.txt)",
    )
    parser.add_argument(
        "--keep_chart_types",
        "-k",
        type=int,
        nargs="+",
        default=[1, 2, 6, 9, 11],
        help="List of chart type IDs to keep (default: [1, 2, 6, 9, 11])",
    )
    parser.add_argument(
        "--sampling_limit_per_theme",
        "-s",
        type=int,
        default=200,
        help="Maximum number of images per content theme (default: 200)",
    )
    parser.add_argument(
        "--show_stats",
        "-v",
        action="store_true",
        help="Whether to print detailed statistics (default: False)",
    )

    args = parser.parse_args()

    # Convert keep_chart_types list to set for proper function call
    chart_types_set = (
        set(args.keep_chart_types) if args.keep_chart_types else {1, 2, 6, 9, 11}
    )

    sample_images(
        base_dir=args.base_dir,
        compliance_thresholds=args.compliance_thresholds,
        complexity_top_n=args.complexity_top_n,
        output_filename=args.output_filename,
        filtered_output_filename=args.filtered_output_filename,
        keep_chart_types=chart_types_set,
        sampling_limit_per_theme=args.sampling_limit_per_theme,
        show_stats=args.show_stats,
    )

    copy_selected_files(
        txt_path=args.filtered_output_filename,
        base_dir=args.base_dir,
        output_dir=args.base_dir + "_selected",
    )


if __name__ == "__main__":
    main()
