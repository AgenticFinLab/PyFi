from fttracer.mcts.gqa import *
import os
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process financial images with context"
    )
    parser.add_argument(
        "--base",
        "-b",
        type=str,
        required=True,
        help="Base directory path containing images and context folders",
    )

    args = parser.parse_args()
    base = args.base

    base_image_pdfs_path = os.path.join(base, "images")
    context_base_path = os.path.join(base, "context")

    if not os.path.exists(base_image_pdfs_path):
        print(f"Error: Images directory not found at {base_image_pdfs_path}")
        exit(1)

    if not os.path.exists(context_base_path):
        print(f"Warning: Context directory not found at {context_base_path}")

    image_pdfs = os.listdir(base_image_pdfs_path)
    for image_pdf_i in range(len(image_pdfs)):
        base_image_path = os.path.join(base_image_pdfs_path, image_pdfs[image_pdf_i])
        images_name = os.listdir(base_image_path)
        for image_name in images_name:
            if image_name.endswith(".jpg") or image_name.endswith(".png"):
                images_path = os.path.join(base_image_path, image_name)
                print("Processing image:", images_path)
                system = ImageQASystem()
                system.main(image_path=images_path, context_base_path=context_base_path)
