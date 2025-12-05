"""Remove duplicate images across subdirectories using either Qwen multimodal embeddings or perceptual hashing.

Supports two strategies:
1. Multimodal embedding and cosine similarity
2. Perceptual hashing (aHash/dHash/pHash) and Hamming distance

image_deduplicator.py
├── find_all_images()                    # Public function: Find all image paths in directory
├── mark_or_delete_duplicates()          # Public function: Handle duplicates (mark/delete)
├── compute_embedding()                  # Generate feature vector using AI model
├── compute_hash()                       # Calculate perceptual hash (pHash/dHash/aHash)
├── image_deduplication_embedding()      # Main workflow: Semantic deduplication using embeddings
├── image_deduplication_hash()           # Main workflow: Visual similarity deduplication using hashing
└── main()                               # CLI entry point, routes to deduplication strategies
"""

import os
import time
import base64
import argparse
from pathlib import Path
from http import HTTPStatus
from typing import Optional, List, Tuple

import dashscope
import imagehash
import numpy as np
from PIL import Image

# Configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
IMAGE_PATH = "parse_results"
REQUIRE_MANUAL_CONFIRMATION = 1  # 0: Auto-delete, 1: Mark for review


def find_all_images(base_path: str) -> List[Path]:
    """Finds all image paths within 'images' subdirectories."""
    base = Path(base_path)
    if not base.exists() or not base.is_dir():
        print(f"Base path '{base_path}' is invalid or not a directory.")
        return []

    image_paths = []
    for images_dir in base.rglob("images"):
        if images_dir.is_dir():
            for img_file in images_dir.iterdir():
                if img_file.is_file() and img_file.suffix.lower() in {
                    ".png",
                    ".jpg",
                    ".jpeg",
                }:
                    image_paths.append(img_file)
    return image_paths


def mark_or_delete_duplicates(
    duplicates_to_handle: List[Tuple[Path, Path]],
    valid_image_paths: List[Path],
    similarity_or_distance_list: List[float],
    require_manual_confirmation: int,
    output_format: str = "similarity",  # "similarity" or "distance"
) -> None:
    """Handles duplicate pairs: either auto-delete or mark for manual review."""
    if not duplicates_to_handle:
        print("No duplicate images found.")
        return

    print(f"\nIdentified {len(duplicates_to_handle)} potential duplicate pair(s).")

    if require_manual_confirmation == 0:
        print("\nAuto-deleting duplicates (REQUIRE_MANUAL_CONFIRMATION=0)...")
        deleted_count = 0
        errors = []
        already_deleted = set()

        for path_to_keep, path_to_delete in duplicates_to_handle:
            if path_to_delete in already_deleted:
                print(f"Skipping {path_to_delete}, already deleted.")
                continue

            try:
                os.remove(path_to_delete)
                print(f"Deleted: {path_to_delete}")
                deleted_count += 1
                already_deleted.add(path_to_delete)
            except OSError as e:
                error_msg = f"Error deleting {path_to_delete}: {e}"
                print(error_msg)
                errors.append(error_msg)

        print(f"\nAuto-delete complete. {deleted_count} files deleted.")
        if errors:
            print("--- Errors during deletion ---")
            for err in errors:
                print(err)

    else:
        print(
            "\nMarking duplicates for manual review (REQUIRE_MANUAL_CONFIRMATION=1)..."
        )
        marker_file_path = Path("duplicates_for_review.txt")

        try:
            with marker_file_path.open("w") as f:
                f.write("# Duplicate Image Pairs Found\n")
                if output_format == "similarity":
                    f.write("# Format: Similarity || Path1 || Path2\n")
                else:
                    f.write("# Format: Distance || Path1 || Path2\n")
                f.write("# Review and decide which file(s) to delete.\n\n")

                unique_pairs_written = set()

                for idx, (path_to_keep, path_to_delete) in enumerate(
                    duplicates_to_handle
                ):
                    pair_key = tuple(sorted([str(path_to_keep), str(path_to_delete)]))

                    if pair_key not in unique_pairs_written:
                        value = similarity_or_distance_list[idx]
                        f.write(f"{value:.4f} || {path_to_keep} || {path_to_delete}\n")
                        unique_pairs_written.add(pair_key)

            print(
                f"Duplicates marked in '{marker_file_path.absolute()}'. Please review and delete manually."
            )
        except IOError as e:
            print(f"Error writing marker file '{marker_file_path}': {e}")


# Embedding-based Deduplication
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def compute_embedding(image_path: str) -> Optional[list]:
    """Computes the embedding for a single image using DashScope API."""
    if not os.path.exists(image_path):
        print(f"Warning: Image path not found: {image_path}")
        return None

    base64_image = encode_image(os.path.abspath(image_path))
    image_format = "jpg"
    image_data = f"data:image/{image_format};base64,{base64_image}"
    input_data = [{"image": image_data}]

    try:
        resp = dashscope.MultiModalEmbedding.call(
            model="multimodal-embedding-v1", input=input_data
        )

        if resp.status_code == HTTPStatus.OK:
            embedding = resp.output["embeddings"][0]["embedding"]
            return embedding
        else:
            print(f"API Error for {image_path}: {resp.code}, {resp.message}")
            return None
    except Exception as e:
        print(f"Exception while processing {image_path}: {e}")
        return None


def cosine_similarity(vec1: list, vec2: list) -> float:
    """Calculates the cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)


def image_deduplication_embedding(
    image_path: str = IMAGE_PATH,
    similarity_threshold: float = 0.98,
    require_manual_confirmation: int = REQUIRE_MANUAL_CONFIRMATION,
) -> None:
    start_time = time.time()
    all_image_paths = find_all_images(image_path)
    print(f"Found {len(all_image_paths)} images.")

    if not all_image_paths:
        print("No images found to process.")
        return

    image_embeddings = []
    valid_image_paths = []
    for i, img_path in enumerate(all_image_paths):
        print(f"Processing image {i + 1}/{len(all_image_paths)}")
        embedding = compute_embedding(str(img_path))
        if embedding is not None:
            image_embeddings.append(embedding)
            valid_image_paths.append(img_path)
        else:
            print(f"Skipping image due to embedding failure: {img_path}")

    end_time = time.time()
    print(f"Successfully computed embeddings for {len(valid_image_paths)} images.")
    print(f"Total time: {end_time - start_time:.2f} seconds")

    if len(valid_image_paths) < 2:
        print("Not enough valid images to compare for duplicates.")
        return

    print("Finding duplicates...")
    duplicates_to_handle = []
    similarities = []

    for i in range(len(image_embeddings)):
        for j in range(i + 1, len(image_embeddings)):
            sim = cosine_similarity(image_embeddings[i], image_embeddings[j])

            if sim >= similarity_threshold:
                path1 = valid_image_paths[i]
                path2 = valid_image_paths[j]
                duplicates_to_handle.append((path1, path2))
                similarities.append(sim)

    mark_or_delete_duplicates(
        duplicates_to_handle=duplicates_to_handle,
        valid_image_paths=valid_image_paths,
        similarity_or_distance_list=similarities,
        require_manual_confirmation=require_manual_confirmation,
        output_format="similarity",
    )


# Hash-based Deduplication
def compute_hash(
    image_path: str, hash_type: str = "phash"
) -> Optional[imagehash.ImageHash]:
    """Computes the perceptual hash for a single image."""
    try:
        img = Image.open(image_path)
        if hash_type == "ahash":
            return imagehash.average_hash(img)
        elif hash_type == "dhash":
            return imagehash.dhash(img)
        elif hash_type == "phash":
            return imagehash.phash(img)
        else:
            raise ValueError("Unsupported hash type")
    except Exception as e:
        print(f"Exception while processing {image_path}: {e}")
        return None


def hamming_distance(hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> int:
    """Calculates the Hamming distance between two image hashes."""
    return hash1 - hash2


def image_deduplication_hash(
    image_path: str = IMAGE_PATH,
    hash_threshold: int = 5,
    require_manual_confirmation: int = REQUIRE_MANUAL_CONFIRMATION,
    hash_type: str = "ahash",
) -> None:
    start_time = time.time()
    all_image_paths = find_all_images(image_path)
    print(f"Found {len(all_image_paths)} images.")

    if not all_image_paths:
        print("No images found to process.")
        return

    image_hashes = []
    valid_image_paths = []
    for i, img_path in enumerate(all_image_paths):
        print(f"Processing image {i + 1}/{len(all_image_paths)}")
        img_hash = compute_hash(str(img_path), hash_type)
        if img_hash is not None:
            image_hashes.append(img_hash)
            valid_image_paths.append(img_path)
        else:
            print(f"Skipping image due to hash failure: {img_path}")

    end_time = time.time()
    print(f"Successfully computed hashes for {len(valid_image_paths)} images.")
    print(f"Total time: {end_time - start_time:.2f} seconds")

    if len(valid_image_paths) < 2:
        print("Not enough valid images to compare for duplicates.")
        return

    print("Finding duplicates...")
    duplicates_to_handle = []
    distances = []

    for i in range(len(image_hashes)):
        for j in range(i + 1, len(image_hashes)):
            dist = hamming_distance(image_hashes[i], image_hashes[j])

            if dist <= hash_threshold:
                path1 = valid_image_paths[i]
                path2 = valid_image_paths[j]
                duplicates_to_handle.append((path1, path2))
                distances.append(dist)

    mark_or_delete_duplicates(
        duplicates_to_handle=duplicates_to_handle,
        valid_image_paths=valid_image_paths,
        similarity_or_distance_list=distances,
        require_manual_confirmation=require_manual_confirmation,
        output_format="distance",
    )


def deduplicate_image(
    method: str = "embedding",
    image_path: str = IMAGE_PATH,
    similarity_threshold: float = 0.98,
    hash_threshold: int = 5,
    hash_type: str = "ahash",
    auto_delete: bool = False,
):
    """
    Run image deduplication using either embedding or hash-based method.

    Args:
        method (str): 'embedding' or 'hash'
        image_path (str): Path to the directory containing images
        similarity_threshold (float): For embedding method, cosine similarity threshold
        hash_threshold (int): For hash method, Hamming distance threshold
        hash_type (str): Type of hash to use ('ahash', 'dhash', 'phash')
        auto_delete (bool): If True, automatically delete duplicates; otherwise, mark for review
    """
    require_manual_confirmation = 0 if auto_delete else 1

    if method == "embedding":
        image_deduplication_embedding(
            image_path=image_path,
            similarity_threshold=similarity_threshold,
            require_manual_confirmation=require_manual_confirmation,
        )
    elif method == "hash":
        image_deduplication_hash(
            image_path=image_path,
            hash_threshold=hash_threshold,
            hash_type=hash_type,
            require_manual_confirmation=require_manual_confirmation,
        )
    else:
        raise ValueError("Invalid method. Choose 'embedding' or 'hash'.")


def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate images using embedding or hash methods."
    )
    parser.add_argument(
        "--method",
        choices=["embedding", "hash"],
        default="embedding",
        help="Choose deduplication method",
    )
    parser.add_argument(
        "--path", default=IMAGE_PATH, help="Base directory to search for images"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.98,
        help="Similarity threshold for embedding method",
    )
    parser.add_argument(
        "--hash_threshold",
        type=int,
        default=5,
        help="Hamming distance threshold for hash method",
    )
    parser.add_argument(
        "--hash_type",
        choices=["ahash", "dhash", "phash"],
        default="dhash",
        help="Type of hash to use",
    )
    parser.add_argument(
        "--auto_delete",
        action="store_true",
        help="Auto-delete duplicates without confirmation",
    )

    args = parser.parse_args()

    deduplicate_image(
        method=args.method,
        image_path=args.path,
        similarity_threshold=args.threshold,
        hash_threshold=args.hash_threshold,
        hash_type=args.hash_type,
        auto_delete=args.auto_delete,
    )


if __name__ == "__main__":
    main()

"""
test results
embedding:  520 images, Identified 20398 potential duplicate pair(s). Total time: 831.90 seconds
ahash:  520 images, Identified 144 potential duplicate pair(s). Total time: 4.22 seconds
dhash:  520 images, Identified 6 potential duplicate pair(s). Total time: 4.03 seconds
phash:  520 images, Identified 2 potential duplicate pair(s). Total time: 4.20 seconds
"""
