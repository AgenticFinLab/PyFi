"""
Image Context Extraction and Analysis Pipeline

This module processes book reports to extract image-related context from Markdown files,
analyze image classifications (normal, abnormal, extreme abnormal), and generate structured
JSON outputs for downstream tasks.

The pipeline executes the following sequence:
1.  Discovers book resources by scanning the input directory for co-located Markdown, PDF, and image assets.
2.  Preprocesses Markdown files by removing interfering content (e.g., figure directories, HTML tag).
3.  Extracts image captions and references via rule-based parsing of Markdown image tags and adjacent textual context.
4.  Resolves in-text citations by identifying textual references that semantically correspond to extracted captions.
5.  Enriches image metadata with contextual expansions of captions and their citation anchors.
6.  Classifies images using caption semantics and positional features (e.g., chapter proximity), serializing results to structured JSON.
7.  Provides diagnostic utilities for statistical analysis of classification outcomes and targeted inspection of anomalous cases.

Image Classification Rules:
Expanded search strategy: Starting from current image tag, search in expanding ranges:
n=1 (immediate lines), n=2, ..., until n=x where no captions found, then search range [x+1, x+N].

Classification scenarios:
- Caption search (A): A-0 (no match), A-1 (one match), A-2 (multiple matches)
- Image search (B): B-0 (no other images), B-1 (other images present)

Normal: A-1 + B-0
Abnormal: A-1 + B-1, A-2  
Extreme abnormal: A-0

Input Directory Structure:
    <input_dir>/
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

Output Directory Structure:
    <input_dir>/context/{book_id}.json

NOTE: For the detailed pipeline, parameters, and examples, see:
   docs/progress_record/image_context_extraction.md

"""

import os
import re
import json
import time
import random
import shutil
import argparse
from typing import Tuple, List, Dict, Any, Union, Optional


# Post Check Functions
def abnormal_context_sample(input_dir: str, sample_percentage: float = 1.0) -> None:
    """Randomly sample JSON files containing abnormal images and copy them to abnormal_sample folder.

    This function reads JSON files from the context directory, finds all files
    containing abnormal images, randomly samples a percentage of them, and copies
    the JSON files to the abnormal_sample directory.

    Args:
        input_dir: The root directory containing the output/context folder.
            Expected structure: {input_dir}/output/context/{book_id}.json
        sample_percentage: Percentage of files containing abnormal images to sample (default: 1.0 for 1%)

    Returns:
        None
    """
    context_dir = os.path.join(input_dir, "context")
    sample_dir = os.path.join(input_dir, "abnormal_sample")

    # Create sample directory if it doesn't exist
    os.makedirs(sample_dir, exist_ok=True)

    # Check if context directory exists
    if not os.path.exists(context_dir):
        raise FileNotFoundError(f"Context directory not found: {context_dir}")

    # Collect all JSON files that contain abnormal images
    files_with_abnormal = []

    # Iterate through all JSON files in the context directory
    for filename in os.listdir(context_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(context_dir, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    image_data_list = json.load(f)

                # Check if this file contains any abnormal images
                has_abnormal = False
                abnormal_count = 0

                for image_data in image_data_list:
                    classification = image_data.get("classification", "").lower()
                    if classification == "abnormal":
                        has_abnormal = True
                        abnormal_count += 1

                # If file contains abnormal images, add it to our list
                if has_abnormal:
                    files_with_abnormal.append(
                        {
                            "filename": filename,
                            "file_path": file_path,
                            "abnormal_count": abnormal_count,
                        }
                    )

            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not process file {filename}: {e}")
                continue

    # Calculate sample size
    total_files_with_abnormal = len(files_with_abnormal)
    sample_size = max(1, int(total_files_with_abnormal * sample_percentage / 100))

    print(f"Total JSON files containing abnormal images: {total_files_with_abnormal}")
    print(f"Sampling {sample_size} files ({sample_percentage}%)")

    # Randomly sample files
    sampled_files = random.sample(
        files_with_abnormal, min(sample_size, total_files_with_abnormal)
    )

    # Copy sampled JSON files to sample directory
    copied_count = 0
    total_abnormal_in_sample = 0

    for sampled_file in sampled_files:
        source_file_path = sampled_file["file_path"]
        filename = sampled_file["filename"]
        abnormal_count = sampled_file["abnormal_count"]

        destination_path = os.path.join(sample_dir, filename)

        # If destination file already exists, add a suffix to avoid overwriting
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(destination_path):
            new_filename = f"{base_name}_{counter}{ext}"
            destination_path = os.path.join(sample_dir, new_filename)
            counter += 1

        try:
            shutil.copy2(source_file_path, destination_path)
            copied_count += 1
            total_abnormal_in_sample += abnormal_count
            print(f"Copied {filename} (contains {abnormal_count} abnormal images)")
        except IOError as e:
            print(f"Warning: Could not copy file {filename}: {e}")

    print(f"Successfully copied {copied_count} JSON files to {sample_dir}")
    print(f"Total abnormal images in sampled files: {total_abnormal_in_sample}")

    # Save sampled file information to a summary JSON file
    summary_info = {
        "sample_percentage": sample_percentage,
        "total_files_with_abnormal": total_files_with_abnormal,
        "sampled_files_count": copied_count,
        "total_abnormal_in_sample": total_abnormal_in_sample,
        "sampled_files": sampled_files,
    }

    summary_path = os.path.join(sample_dir, "sample_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_info, f, indent=2, ensure_ascii=False)

    print(f"Sample summary saved to {summary_path}")


def classification_statistics(input_dir: str) -> Dict[str, int]:
    """Count the statistics of image classifications across all books.

    This function reads JSON files from the context directory and counts
    occurrences of each classification type: normal, abnormal, extreme abnormal.

    Args:
        input_dir: The root directory containing the output/context folder.
            Expected structure: {input_dir}/output/context/{book_id}.json

    Returns:
        A dictionary with classification counts:
        {
            'normal': int,
            'abnormal': int,
            'extreme_abnormal': int
        }

    """
    context_dir = os.path.join(input_dir, "context")
    classification_counts = {"normal": 0, "abnormal": 0, "extreme_abnormal": 0}

    # Check if context directory exists
    if not os.path.exists(context_dir):
        raise FileNotFoundError(f"Context directory not found: {context_dir}")

    # Iterate through all JSON files in the context directory
    for filename in os.listdir(context_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(context_dir, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    image_data_list = json.load(f)

                # Process each image entry in the JSON file
                for image_data in image_data_list:
                    classification = image_data.get("classification", "").lower()

                    # Map classification to our standardized categories
                    if classification == "normal":
                        classification_counts["normal"] += 1
                    elif classification == "abnormal":
                        classification_counts["abnormal"] += 1
                    elif classification == "extreme abnormal":
                        classification_counts["extreme_abnormal"] += 1
                    # Ignore unknown classifications

            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not process file {filename}: {e}")
                continue

    return classification_counts


# vital tool functions used in context extraction
def clean_useless_text(context: str) -> str:
    """Remove HTML table tags and attributes while preserving book structure.

    This function removes HTML table-related tags and their attributes,
    while preserving paragraph boundaries and book structure by replacing
    table elements with appropriate whitespace.

    Args:
        context: A string containing HTML content with table elements.

    Returns:
        A cleaned string with table elements removed and whitespace normalized,
        while preserving original paragraph structure.
    """
    context = re.sub(
        r"<(t[dh])(?=[0-9. ])",
        r"<\1>",  # fix <td>
        context,
        flags=re.IGNORECASE,
    )
    # Replace table cell tags (td, th) with newlines to preserve paragraph structure
    cell_pattern = re.compile(r"</?(td|th)[^>]*>", re.IGNORECASE)
    cleaned = cell_pattern.sub("\n", context)

    # Remove other table structure tags (table, tr, tbody, thead, tfoot)
    structure_pattern = re.compile(
        r"</?(table|tr|tbody|thead|tfoot)[^>]*>", re.IGNORECASE
    )
    cleaned = structure_pattern.sub("", cleaned)

    # Remove common table attributes from remaining elements
    attr_pattern = re.compile(
        r"\s*(rowspan|colspan|style|class|width|height|align|valign|border|"
        r'cellpadding|cellspacing)\s*=\s*"[^"]*"',
        re.IGNORECASE,
    )
    cleaned = attr_pattern.sub("", cleaned)

    # Remove single-quoted table attributes
    standalone_attr_pattern = re.compile(
        r"\s*(rowspan|colspan|style|class|width|height|align|valign|border|"
        r"cellpadding|cellspacing)\s*=\s*'[^']*'",
        re.IGNORECASE,
    )
    cleaned = standalone_attr_pattern.sub("", cleaned)

    # Replace multiple spaces/tabs with single space
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # Normalize multiple consecutive newlines to double newlines (paragraph breaks)
    cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned)

    cleaned = cleaned.strip()

    return cleaned


def split_into_paragraphs(content: str) -> List[Dict[str, Any]]:
    """Split content into paragraphs and track their line ranges.

    Args:
        content (str): The input text content to be split into paragraphs

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each containing:
            - 'content': The paragraph text (stripped of leading/trailing whitespace)
            - 'start_line': The starting line number of the paragraph (1-indexed)
            - 'end_line': The ending line number of the paragraph (1-indexed)
            - 'lines': A list of individual lines that make up the paragraph
    """
    # Split the content by double newlines to get raw paragraphs
    raw_paragraphs = content.split("\n\n")
    paragraphs_info = []
    current_line = 1

    for raw_paragraph in raw_paragraphs:
        # Remove leading and trailing whitespace from the paragraph
        stripped_paragraph = raw_paragraph.strip()
        if stripped_paragraph:
            # Split the paragraph into individual lines
            paragraph_lines = stripped_paragraph.split("\n")
            # Record the starting line number for this paragraph
            start_line = current_line
            # Calculate the ending line number (start + number of lines - 1)
            end_line = current_line + len(paragraph_lines) - 1

            # Add paragraph information to the result list
            paragraphs_info.append(
                {
                    "content": stripped_paragraph,
                    "start_line": start_line,
                    "end_line": end_line,
                    "lines": paragraph_lines,
                }
            )

            # Update current line position (end_line + 2 accounts for the "\n\n" separator)
            current_line = end_line + 2
        else:
            # If the paragraph is empty (after stripping), just increment by 1 line
            current_line += 1

    return paragraphs_info


def ensure_minimum_context(
    md_content: str,
    k: int,
    text: str,
) -> str:
    """Ensure the text has minimum k characters with complete paragraphs context.

    Args:
        md_content: The full markdown content of the book/report.
        k: Minimum required character count.
        text: The text to be processed (must exist in md_content).

    Returns:
        Processed text with at least k characters and complete paragraph boundaries.
    """
    # Preprocess: Split document into paragraphs using the provided function
    paragraphs_info = split_into_paragraphs(md_content)

    # Handle empty document case
    if not paragraphs_info:
        return text

    # Extract paragraph contents
    paragraphs = [para_info["content"] for para_info in paragraphs_info]

    # Find actual positions by searching in the original content
    para_positions = []
    search_pos = 0
    for para in paragraphs:
        found_pos = md_content.find(para, search_pos)
        if found_pos != -1:
            para_positions.append(found_pos)
            search_pos = found_pos + len(para) + 2  # Move past paragraph and \n\n
        else:
            return text

    # Find the position of the target text in md_content
    pos = md_content.find(text)
    if pos == -1:
        return text  # text not found in md_content

    # Find the paragraph indices containing the target text
    text_end_pos = pos + len(text)
    start_para_idx = None
    end_para_idx = None

    for i, start_pos in enumerate(para_positions):
        para = paragraphs[i]
        para_end = start_pos + len(para)
        if start_pos <= pos < para_end:
            start_para_idx = i
        if start_pos < text_end_pos <= para_end:
            end_para_idx = i
            break

    # Fallback to original text if paragraphs cannot be located
    if (
        start_para_idx is None
        or end_para_idx is None
        or not (0 <= start_para_idx < len(paragraphs))
        or not (0 <= end_para_idx < len(paragraphs))
    ):
        return text

    # Expand context
    current_start_idx = start_para_idx
    current_end_idx = end_para_idx

    # Calculate required characters for each side
    required_each_side = k // 2

    # Expand backwards
    prev_chars = 0
    temp_start_idx = current_start_idx
    while temp_start_idx > 0 and prev_chars < required_each_side:
        temp_start_idx -= 1
        prev_chars += len(paragraphs[temp_start_idx]) + 2
    current_start_idx = max(0, temp_start_idx)

    # Expand forwards
    next_chars = 0
    temp_end_idx = current_end_idx
    while temp_end_idx < len(paragraphs) - 1 and next_chars < required_each_side:
        temp_end_idx += 1
        next_chars += len(paragraphs[temp_end_idx]) + 2
    current_end_idx = min(len(paragraphs) - 1, temp_end_idx)

    # Validate final range
    if current_start_idx > current_end_idx:
        return text

    # Join paragraphs
    try:
        result = "\n\n".join(paragraphs[current_start_idx : current_end_idx + 1])
        return result
    except Exception:
        return text


def find_elements_in_range(
    lines: List[str],
    target_line_num: int,
    element_pattern: Union[str, re.Pattern],
    max_range: int = 5,
) -> List[dict]:
    """Find elements (captions or images) in expanding ranges around a target line.

    The search logic:
    1. Start with distance=1 (line immediately above/below)
    2. If elements are found at current distance, increase distance by 1 and repeat
    3. When no elements found at distance=X, then search from X to X+max_range
    4. Return all found elements and a flag indicating if elements were found in inner range

    Args:
        lines: List of lines to search in.
        target_line_num: The line number to search around (1-based index).
        element_pattern: Regex pattern to match the elements (string or compiled pattern).
        max_range: Maximum range to search (default 6).

    Returns:
        List of found elements (each as dict with keys: 'line_num', 'content', 'distance', 'pos')
    """
    # Initialize variables
    found_elements = []
    checked_lines = set()  # Track checked lines to avoid duplicates
    break_distance = None  # Distance where we stopped finding elements

    # Handle both string and compiled pattern
    if isinstance(element_pattern, str):
        pattern = re.compile(element_pattern, re.IGNORECASE)
    else:
        pattern = element_pattern

    # Step 1: Expand gradually until we find no elements at a distance
    current_distance = 1
    while current_distance <= max_range:
        lines_to_check = []

        # Get lines at current distance (above and below)
        target_index = target_line_num - 1
        above_line = target_index - current_distance
        below_line = target_index + current_distance

        if 0 <= above_line < len(lines):
            lines_to_check.append(above_line)
        if 0 <= below_line < len(lines):
            lines_to_check.append(below_line)

        found_at_current_distance = False

        # Check lines at this distance
        for line_num in lines_to_check:
            if line_num in checked_lines:
                continue

            checked_lines.add(line_num)
            line_content = lines[line_num].strip()

            # Skip empty lines
            if not line_content:
                continue

            # Check if line matches the pattern
            if pattern.search(line_content):
                # Calculate position in full content
                # Find the start position of this line in the full markdown_content
                target_line_content = lines[line_num]
                # Calculate the position up to the start of this line
                pos = (
                    sum(len(lines[i]) + 1 for i in range(line_num))
                    if line_num > 0
                    else 0
                )
                # Find the exact position of the match within this line
                line_start_pos = pos
                match = pattern.search(target_line_content)
                if match:
                    pos = line_start_pos + match.start()

                element_data = {
                    "line_num": line_num,
                    "content": line_content,
                    "distance": current_distance,
                    "pos": pos,
                }
                found_elements.append(element_data)
                found_at_current_distance = True

        # If found elements at this distance, continue to next distance
        if found_at_current_distance:
            current_distance += 1
        else:
            break_distance = current_distance
            break

    # If we didn't break in the loop, set break_distance to max_range+1
    if break_distance is None:
        break_distance = max_range + 1

    # Step 2: Search extended range from break_distance to break_distance + max_range
    if break_distance <= max_range:
        start_distance = break_distance
        end_distance = min(
            break_distance + max_range, len(lines) // 2
        )  # Avoid excessive search
        end_distance = max(
            end_distance, max_range
        )  # Ensure we search at least max_range

        for distance in range(start_distance, end_distance + 1):
            lines_to_check = []

            # Get lines at current distance
            target_index = target_line_num - 1

            above_line = target_index - distance
            below_line = target_index + distance

            if above_line >= 0:
                lines_to_check.append(above_line)
            if below_line < len(lines):
                lines_to_check.append(below_line)

            # Check lines at this distance
            for line_num in lines_to_check:
                if line_num in checked_lines:
                    continue

                checked_lines.add(line_num)
                line_content = lines[line_num].strip()

                # Skip empty lines
                if not line_content:
                    continue

                # Check if line matches the pattern
                if pattern.search(line_content):
                    # Calculate position in full content
                    # Find the start position of this line in the full markdown_content
                    target_line_content = lines[line_num]
                    # Calculate the position up to the start of this line
                    pos = (
                        sum(len(lines[i]) + 1 for i in range(line_num))
                        if line_num > 0
                        else 0
                    )
                    # Find the exact position of the match within this line
                    line_start_pos = pos
                    match = pattern.search(target_line_content)
                    if match:
                        pos = line_start_pos + match.start()

                    element_data = {
                        "line_num": line_num,
                        "content": line_content,
                        "distance": distance,
                        "pos": pos,
                    }
                    found_elements.append(element_data)

    return found_elements


def extract_figure_identifier(text: str) -> Optional[re.Match]:
    """Extract figure identifier from text using detailed regex pattern."""
    figure_pattern = re.compile(
        r"(图\s*([a-zA-Z]?)\s*(\d+(?:[.-]\d+)*\d*)|Figure\s*(\d+(?:[.-]\d+)*\d*)|Fig\.?\s*(\d+(?:[.-]\d+)*\d*))",
        re.IGNORECASE,
    )
    return figure_pattern.search(text)


def extract_image_info(markdown_content: str, book_id: str) -> List[Dict[str, Any]]:
    """Extract image information and their captions from markdown content.

    This function finds all image tags in the markdown content and extracts
    their corresponding captions according to the specified rules.

    Args:
        markdown_content: The markdown content as a string.
        book_id: The book identifier (e.g., '000001').

    Returns:
        A list of dictionaries containing image information and classification data.
    """
    # Split the markdown content into paragraphs to track line numbers and content
    paragraphs_info = split_into_paragraphs(markdown_content)

    # Define regex pattern to match image tags in markdown format ![alt_text](../images/folder/filename)
    image_pattern = re.compile(r"!\[.*?]\(\.\./images/[^/]+/([^)]+)\)")
    image_matches = []

    # Find all image matches with their positions in the original content
    for match in image_pattern.finditer(markdown_content):
        # Calculate the line number where the image tag appears (1-based line number)
        match_start_pos = match.start()
        line_num = (
            markdown_content[:match_start_pos].count("\n") + 1
        )  # 1-based line number

        # Find which paragraph contains this line
        paragraph_index = None
        for idx, para in enumerate(paragraphs_info):
            if para["start_line"] <= line_num <= para["end_line"]:
                paragraph_index = idx
                break

        # Store image match information if found within a paragraph
        if paragraph_index is not None:
            image_matches.append(
                {
                    "line_num": line_num,
                    "paragraph_index": paragraph_index,
                    "image_filename": match.group(
                        1
                    ),  # Extract filename from regex group
                    "line_content": markdown_content.split("\n")[
                        line_num - 1
                    ].strip(),  # Get the actual line content
                }
            )

    # Split all content into lines for global lookup (preserving empty lines and original layout)
    all_lines = markdown_content.split(
        "\n"
    )  # This preserves all lines including empty ones

    # Initialize list to store extracted image information
    image_info_list = []

    # Process each found image match
    for i, image_match in enumerate(image_matches):
        line_num = image_match["line_num"]
        image_filename = image_match["image_filename"]
        line_content = image_match["line_content"]
        para_index = image_match["paragraph_index"]

        # Get the paragraph containing the image
        paragraph = paragraphs_info[para_index]
        raw_context = paragraph["content"]

        # Get surrounding context around the image (4000 characters radius)
        image_surround_text = ensure_minimum_context(
            md_content=markdown_content, k=4000, text=raw_context
        )

        # Define regex pattern to match various caption formats (Chinese "图", English "Figure/Fig")
        caption_pattern = re.compile(
            r"(?:"
            r"图\s*[a-zA-Z]?(?:\d+(?:[.\-]\d+)*)+|"  # Chinese: 图 followed by optional letter and numbers
            r"Figure\s*(?:\d+(?:[.\-]\d+)*)+|"  # English: Figure followed by numbers
            r"Fig\.?\s*(?:\d+(?:[.\-]\d+)*)+"  # English: Fig. or Fig followed by numbers
            r")",
            re.IGNORECASE,
        )

        # Set search range for finding captions (5 lines upward from image)
        upper_bound = 5
        # Search for captions above the image line
        captions_found = find_elements_in_range(
            all_lines, line_num - 1, caption_pattern, upper_bound
        )

        # Filter captions: must start with figure identifier at beginning of line/paragraph
        filtered_captions = []
        # Pattern to match the beginning of figure identifiers
        figure_start_pattern = re.compile(
            r"^\s*(图|fig|Fig|Figure|Figura)", re.IGNORECASE
        )

        # Validate each found caption
        for caption in captions_found:
            caption_line = all_lines[caption["line_num"]]
            if figure_start_pattern.match(caption_line):
                # Caption starts with figure identifier on the same line
                filtered_captions.append(caption)
            else:
                # Check if this is part of a paragraph that starts with figure identifier
                caption_line_num_1based = caption["line_num"] + 1
                # Find which paragraph this caption line belongs to
                caption_para_idx = None
                for idx, para in enumerate(paragraphs_info):
                    if (
                        para["start_line"]
                        <= caption_line_num_1based
                        <= para["end_line"]
                    ):
                        caption_para_idx = idx
                        break

                if caption_para_idx is not None:
                    caption_para = paragraphs_info[caption_para_idx]
                    # Check if the paragraph starts with a figure identifier
                    if figure_start_pattern.match(caption_para["lines"][0]):
                        filtered_captions.append(caption)

        # Update captions_found with filtered results
        captions_found = filtered_captions

        # Find other images near the current image (within the same search range)
        other_images_found = find_elements_in_range(
            all_lines, line_num - 1, image_pattern, upper_bound
        )

        # Filter out the current image itself from other images list
        other_images_found = [
            img for img in other_images_found if img["line_num"] + 1 != line_num
        ]

        # Sort captions by distance to image (closest first)
        captions_found.sort(key=lambda x: x["distance"])

        # Classify the sample based on rules:
        # A-0: No captions found
        # A-1: One caption found
        # A-2: Multiple captions found
        # B-0: No other images nearby
        # B-1: Other images nearby
        caption_count = len(captions_found)

        if caption_count == 0:
            classification = "extreme abnormal"  # A-0: No captions
            caption_text = ""
        elif caption_count == 1:
            if not other_images_found:
                classification = "normal"  # A-1 + B-0: One caption, no other images
            else:
                classification = (
                    "abnormal"  # A-1 + B-1: One caption, other images present
                )
            caption_text = captions_found[0]["content"]
        else:
            classification = "abnormal"  # A-2: Multiple captions
            caption_text = captions_found[0]["content"]

        # Create detailed information about other images found nearby
        other_images_info = {
            "count": len(other_images_found),  # Count of other images
            "images": [
                {
                    "line_number": img["line_num"],  # 1-based indexing
                    "content": img["content"],
                    "distance": img["distance"],  # Distance from current image
                }
                for img in other_images_found
            ],
        }

        # Create comprehensive image information dictionary
        image_info = {
            "classification": classification,  # Classification based on rules
            "book_id": book_id,  # Book identifier
            "image_filename": image_filename,  # Extracted filename
            "image_tag_line_number": line_num,  # Line number where image appears (1-based)
            "image_surround_text": image_surround_text,  # Context around the image
            "other_images_nearby": other_images_info,  # Information about nearby images
            "caption_count": caption_count,  # Total number of captions found
            "captions_found": [  # Detailed information about each found caption
                {
                    "content": cap["content"],  # Caption text
                    "content_paragraph": ensure_minimum_context(
                        markdown_content, 500, cap["content"]
                    ),  # Paragraph context around caption
                    "line_number": cap["line_num"]
                    + 1,  # Line number of caption (1-based)
                    "distance": abs(
                        cap["line_num"] - line_num + 1
                    ),  # Distance from image
                }
                for cap in captions_found
            ],
            "nearest_caption": caption_text,  # The closest caption text to the image
        }

        # Add the processed image information to the result list
        image_info_list.append(image_info)

    # Return the list of all extracted image information
    return image_info_list


def process_image_reference(
    markdown_content: str, image_info_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Process image references and associate them with corresponding captions.

    This function analyzes markdown content to find references to images within paragraphs
    and associates them with their corresponding captions. It handles various reference
    patterns and attempts to correct figure numbers when necessary.

    Args:
        markdown_content: The cleaned markdown content containing images and text.
        image_info_list: List of dictionaries containing image metadata including captions.

    Returns:
        A list of image information dictionaries with added reference data grouped by caption.
    """

    # Split the markdown content into paragraphs for easier processing
    paragraph_mapping = split_into_paragraphs(markdown_content)

    # Initialize the results list to store processed image information
    processed_results = []

    # Process each image in the provided image information list
    for image_info in image_info_list:
        # Extract captions found for this image
        captions = image_info["captions_found"]

        # Get the line number where the image tag appears in the markdown
        image_line_num = image_info["image_tag_line_number"]

        # Get the image filename for reference purposes
        index = image_info["image_filename"]

        # Track processed captions and figure numbers to avoid duplicates
        seen_captions = set()
        processed_figures = set()

        # Each caption will have its own list of references
        caption_references = []
        expanded_content = ""

        # Process each caption associated with this image
        for caption in captions:
            # Extract the caption content, handling both string and dictionary formats
            caption_content = (
                caption["content"] if isinstance(caption, dict) else caption
            )

            # Skip duplicate captions to avoid processing the same caption multiple times
            if caption_content in seen_captions:
                continue
            seen_captions.add(caption_content)

            # Extract figure identifier part from caption (e.g., "图1" from "图1经济增长率")
            # This helps identify which figure the caption is referring to
            figure_match = extract_figure_identifier(caption_content)
            if not figure_match:
                continue

            # Extract the figure number from the match (e.g., "图1")
            figure_number = figure_match.group(1)

            # Skip duplicate figure numbers to avoid processing the same figure multiple times
            if figure_number in processed_figures:
                continue
            processed_figures.add(figure_number)

            # Initialize variables to store reference information
            ref_text = ""
            references = []

            # Get the line number where this caption appears
            caption_line_number = caption["line_number"]

            # Track exact match and non-exact match counts for early termination logic
            exact_match_count = 0
            non_exact_match_count = 0
            max_non_exact_matches = 2  # Maximum number of non-exact matches to process
            found_exact_match = False  # Flag to indicate if an exact match was found

            # Iterate through each paragraph in the markdown content
            for paragraph_info in paragraph_mapping:
                # Extract the paragraph content and line boundaries
                paragraph_content = paragraph_info["content"]
                start_line = paragraph_info["start_line"]
                end_line = paragraph_info["end_line"]

                # Find the position of this paragraph in the overall markdown content
                pos = markdown_content.find(paragraph_content)
                if pos != -1:
                    # Ensure we have enough context around the paragraph for analysis
                    expanded_content = ensure_minimum_context(
                        md_content=markdown_content,
                        k=1000,  # Minimum context length of 1000 characters
                        text=paragraph_content,
                    )
                else:
                    # If paragraph not found, mark as null
                    expanded_content = "null"

                # Skip the paragraph containing the image to avoid self-referencing
                if start_line <= image_line_num <= end_line:
                    continue

                # Remove the caption line from paragraph if it exists in this paragraph
                # This prevents the caption itself from being treated as a reference
                if start_line <= caption_line_number <= end_line:
                    lines = paragraph_content.split("\n")
                    relative_line_index = caption_line_number - start_line
                    if 0 <= relative_line_index < len(lines):
                        lines.pop(relative_line_index)
                        paragraph_info["content"] = "\n".join(lines)
                        paragraph_info["end_line"] -= 1

                # Find all references of the figure identifier in this paragraph
                # Use case-insensitive matching to catch variations
                reference_pattern = re.compile(re.escape(figure_number), re.IGNORECASE)
                potential_matches = reference_pattern.finditer(paragraph_content)

                # Process each potential match found in the paragraph
                for match_obj in potential_matches:
                    # Get the character position where the match starts
                    char_start = match_obj.start()

                    # Define a comprehensive pattern to match various figure reference formats
                    # This includes Chinese "图", English "Figure" and "Fig.", with various number formats
                    pattern = (
                        r"(图\s*([a-zA-Z]?)\s*(\d+(?:[.-]\d+)*)|Figure\s*(\d+(?:[.-]\d+)*)|Fig\.?\s*(\d+(?:["
                        r".-]\d+)*))"
                    )

                    # Determine which line contains the match by calculating cumulative lengths
                    cumulative_length = 0
                    matching_line_info = None

                    # Iterate through each line in the paragraph to find the matching line
                    for idx, line in enumerate(paragraph_info["lines"]):
                        line_length = len(line) + 1  # +1 for newline character
                        if (
                            cumulative_length
                            <= char_start
                            < cumulative_length + line_length
                        ):
                            # Calculate the actual line number in the document
                            current_line_number = start_line + idx

                            # Skip if this is the caption line (already handled)
                            if current_line_number != caption_line_number:
                                # Create detailed information about the matching line
                                matching_line_info = {
                                    "line_number": current_line_number,
                                    "content": line.strip(),
                                    "char_position_in_paragraph": char_start,
                                }

                                # Find all reference text matches in the current line
                                ref_text_matches = re.finditer(
                                    pattern,
                                    matching_line_info["content"],
                                    re.IGNORECASE,
                                )
                                ref_text = [
                                    match.group(0) for match in ref_text_matches
                                ]
                                break
                        cumulative_length += line_length

                    # If a matching line was found, process the reference
                    if matching_line_info:
                        # Determine if this is an exact match (case-insensitive comparison)
                        is_exact = any(
                            figure_number.lower() == ref_text_item.lower()
                            for ref_text_item in ref_text
                        )

                        # Update counters based on match type for early termination logic
                        if is_exact:
                            exact_match_count += 1
                            found_exact_match = True
                        else:
                            non_exact_match_count += 1

                        # Add the reference information to the references list
                        references.append(
                            {
                                "reference_text": ref_text,
                                "is_exact_match": is_exact,
                                "match_line_info": matching_line_info,
                                "reference_paragraph": paragraph_content,
                                "reference_paragraph_extension": expanded_content,
                                "total_lines_in_paragraph": len(
                                    paragraph_info["lines"]
                                ),
                            }
                        )

                        # Early exit condition: at least one exact match AND at least two non-exact matches
                        # This prevents excessive processing when sufficient references are found
                        if (
                            found_exact_match
                            and non_exact_match_count >= max_non_exact_matches
                        ):
                            break  # Break inner loop over matches

                # Check again after processing paragraph to decide whether to break outer loop
                # This allows for early termination based on accumulated matches across paragraphs
                if found_exact_match and non_exact_match_count >= max_non_exact_matches:
                    break  # Break outer loop over paragraphs

            # Create a comprehensive entry for this caption with all its references
            caption_entry = {
                "caption": caption_content,
                "figure_number": figure_number,
                "reference_count": len(references),
                "references": references,
            }

            # Only append entries that have actual references to avoid empty duplicates
            if references:
                caption_references.append(caption_entry)

        # Handle cases like "图22015-2016" when no references found
        # This section attempts to correct malformed figure numbers by trimming characters
        for cr in caption_references:
            # Only process captions with no references but with a figure number
            if cr["reference_count"] == 0 and cr["figure_number"]:

                figure_number = cr["figure_number"]
                has_three_or_more_consecutive_digits = False

                # Check if the figure number contains 3 or more consecutive digits
                # This indicates a potentially malformed figure number that needs correction
                consecutive_digit_count = 0
                for char in figure_number:
                    if char.isdigit():
                        consecutive_digit_count += 1
                        if consecutive_digit_count >= 3:
                            has_three_or_more_consecutive_digits = True
                            break
                    else:
                        consecutive_digit_count = 0

                # Skip if there are fewer than 3 consecutive digits (likely correct format)
                if not has_three_or_more_consecutive_digits:
                    continue
                else:
                    # Extract the original figure number for processing
                    original_figure_number = cr["figure_number"]

                    # List to store candidate-reference pairs found during correction
                    candidate_references_pairs = []

                    # Start with the original figure number and progressively trim characters
                    current_candidate = original_figure_number

                    # Reduce characters from right to left to find valid figure references
                    while len(current_candidate) > 1:
                        # Remove the last character to create a new candidate
                        current_candidate = current_candidate[:-1]

                        # Stop if candidate string becomes too short to be meaningful
                        if len(current_candidate) <= 1:
                            break

                        # Stop if candidate no longer contains digits (not a figure number)
                        if not any(char.isdigit() for char in current_candidate):
                            break

                        # Search for references using the trimmed candidate string
                        corrected_references = []

                        # Iterate through all paragraphs to find references to the candidate
                        for paragraph_info in paragraph_mapping:
                            paragraph_content = paragraph_info["content"]
                            start_line = paragraph_info["start_line"]
                            end_line = paragraph_info["end_line"]

                            # Skip the paragraph containing the image
                            if start_line <= image_line_num <= end_line:
                                continue

                            # Create pattern to match candidate string as whole word
                            # Use case-insensitive matching to catch variations
                            pattern = re.compile(
                                re.escape(current_candidate), re.IGNORECASE
                            )
                            potential_matches = pattern.finditer(paragraph_content)

                            # Process each potential match found for the candidate
                            for match_obj in potential_matches:
                                char_start = match_obj.start()

                                # Define a comprehensive pattern to match various figure reference formats
                                # This includes Chinese "图", English "Figure" and "Fig." with various number formats
                                caption_pattern = r"((图\s*([a-zA-Z]?)\s*(\d+(\s*[.\-]\s*\d+)*\s*)|Figure\s*(\d+(\s*[.\-]\s*\d+\s*)*)|Fig\.?\s*(\s*\d+(?:\s*[.\-]\s*\d+\s*)*)))"
                                try:
                                    # Search for the pattern in a limited context around the match
                                    caption_match = re.search(
                                        caption_pattern,
                                        paragraph_content[
                                            char_start : char_start + 100
                                        ],
                                        re.IGNORECASE,
                                    )
                                except re.error as e:
                                    # Handle regex errors gracefully and continue processing
                                    print(f"Regex error: {e}")
                                    print(f"Pattern: {caption_pattern}")
                                    continue

                                # If a caption match is found, process the reference
                                if caption_match:
                                    ref_text = caption_match.group(0)

                                    # Locate the matching line within the paragraph
                                    cumulative_length = 0
                                    matching_line_info = None
                                    for idx, line in enumerate(paragraph_info["lines"]):
                                        line_length = len(line) + 1
                                        if (
                                            cumulative_length
                                            <= char_start
                                            < cumulative_length + line_length
                                        ):
                                            # Create detailed information about the matching line
                                            matching_line_info = {
                                                "line_number": start_line + idx,
                                                "content": line.strip(),
                                                "char_position_in_paragraph": char_start,
                                            }
                                            break
                                        cumulative_length += line_length

                                    # If a matching line was found, add the reference to corrected references
                                    if matching_line_info:
                                        corrected_references.append(
                                            {
                                                "reference_text": ref_text,
                                                "is_exact_match": current_candidate
                                                == ref_text,
                                                "match_line_info": matching_line_info,
                                                "paragraph_content": paragraph_content,
                                                "reference_paragraph_extension": expanded_content,
                                                "total_lines_in_paragraph": len(
                                                    paragraph_info["lines"]
                                                ),
                                            }
                                        )

                        # If references were found for this candidate, save the pair
                        if corrected_references:
                            candidate_references_pairs.append(
                                {
                                    "candidate": current_candidate,
                                    "references": corrected_references,
                                }
                            )

                    # Select the best pair from all candidates based on similarity to image index
                    if candidate_references_pairs:
                        # Extract digits from the image index for comparison
                        index_digits = "".join(filter(str.isdigit, index))
                        index_number = int(index_digits) if index_digits else 0

                        # Initialize variables to track the best matching candidate
                        best_pair = None
                        best_similarity = float("inf")

                        # Evaluate each candidate-reference pair
                        for pair in candidate_references_pairs:
                            candidate = pair["candidate"]
                            # Extract the numbers in candidate for comparison
                            candidate_digits = "".join(filter(str.isdigit, candidate))
                            candidate_number = (
                                int(candidate_digits) if candidate_digits else 0
                            )

                            # Calculate the absolute difference between candidate and index numbers
                            # Smaller differences indicate better matches
                            difference = abs(candidate_number - index_number)

                            # Update the best pair if this one has better similarity
                            if difference < best_similarity:
                                best_similarity = difference
                                best_pair = pair

                        # Use the best pair to update the caption reference information
                        if best_pair:
                            cr["figure_number"] = best_pair["candidate"]
                            cr["references"] = best_pair["references"]
                            cr["reference_count"] = len(best_pair["references"])

        # Update the total reference count for this image
        image_info["caption_references"] = caption_references
        image_info["total_reference_count"] = sum(
            cr["reference_count"] for cr in caption_references
        )

    # Return the updated list of image information with reference data
    return image_info_list


# main process
def discover_books(input_dir: str) -> List[Tuple[str, str, str]]:
    """Discovers books by looking for corresponding files in subdirectories.

    Args:
        input_dir: The base input directory containing 'images', 'markdown', 'pdf'.

    Returns:
        A list of tuples (book_id, md_path, pdf_path).
    """
    images_dir = os.path.join(input_dir, "images")
    markdown_dir = os.path.join(input_dir, "markdown")
    pdf_dir = os.path.join(input_dir, "pdf")

    if not os.path.isdir(images_dir):
        raise FileNotFoundError(f"'images' directory not found at {images_dir}")
    if not os.path.isdir(markdown_dir):
        raise FileNotFoundError(f"'markdown' directory not found at {markdown_dir}")

    # Get all markdown files that conform to the naming pattern
    md_files = [
        f
        for f in os.listdir(markdown_dir)
        if f.endswith(".md") and len(f) == 9 and f[:6].isdigit()
    ]
    books_info = []
    for md_file in md_files:
        # Filename is like '000001.md'
        book_id = md_file[:-3]
        # Check if corresponding image directory exists
        book_images_dir = os.path.join(images_dir, book_id)
        if not os.path.isdir(book_images_dir):
            print(
                f"Image directory for book ID {book_id} not found at {book_images_dir}. Skipping."
            )
            continue
        md_path = os.path.join(markdown_dir, md_file)
        # Check for corresponding PDF
        pdf_filename = f"{book_id}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        if not os.path.exists(pdf_path):
            pdf_path = ""
        books_info.append((book_id, md_path, pdf_path))

    # Sort by book_id for consistent processing order
    books_info.sort(key=lambda x: x[0])
    return books_info


def read_markdown_file(file_path: str) -> str:
    """Reads the content of a Markdown file and deletes the '图目录' section if present.

    Args:
        file_path: Path to the Markdown file.

    Returns:
        The remaining content of the Markdown file with the figure section removed.

    Raises:
        IOError: If the file cannot be read or written.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        raise

    # Define patterns for figure directory headers
    fig_dir_patterns = [
        # Chinese - Figure related to "图目录"
        r"#\s*图目录",
        r"#\s*图表目录",
        r"#\s*插图目录",
        r"#\s*图形目录",
        r"#\s*图片目录",
        r"#\s*图索引",
        r"#\s*图表索引",
        r"#\s*插图索引",
        r"#\s*图形索引",
        r"#\s*图\s*目\s*录",
        r"#\s*图\s*索\s*引",
        r"#\s*目录\s*图",
        r"#\s*索引\s*图",
        r"#\s*图\s*表\s*目\s*录",
        r"#\s*插\s*图\s*目\s*录",
        # English - Figure related directories
        r"#\s*Figure\s*Directory",
        r"#\s*Table\s*of\s*Figures",
        r"#\s*Figures\s*List",
        r"#\s*List(\s*of)?\s*Figures",
        r"#\s*Index\s*of\s*Figures",
        r"#\s*Figure\s*Index",
        r"#\s*Contents\s*of\s*Figures",
        r"#\s*Figures\s*Contents",
        r"#\s*Figure\s*Catalog",
        r"#\s*Catalog\s*of\s*Figures",
        # English - Illustrations related directories
        r"#\s*List\s*of\s*Illustrations",
        r"#\s*Illustrations\s*List",
        r"#\s*Index\s*of\s*Illustrations",
        r"#\s*Illustrations\s*Index",
        r"#\s*Table\s*of\s*Illustrations",
        r"#\s*Illustrations\s*Directory",
        r"#\s*Illustrations\s*Catalog",
        r"#\s*Catalog\s*of\s*Illustrations",
        # English - Mixed content directories (graphs, tables, figures)
        r"#\s*List\s*of\s*Tables\s*and\s*Figures",
        r"#\s*Tables\s*and\s*Figures\s*List",
        r"#\s*Index\s*of\s*Tables\s*and\s*Figures",
        r"#\s*Table\s*of\s*Contents\s*Figures",
        r"#\s*List\s*of\s*Figures\s*and\s*Tables",
        r"#\s*Figures\s*and\s*Tables\s*List",
        # English - Charts and Graphs directories
        r"#\s*List\s*of\s*Charts",
        r"#\s*Charts\s*List",
        r"#\s*Index\s*of\s*Charts",
        r"#\s*Chart\s*Index",
        r"#\s*Table\s*of\s*Charts",
        r"#\s*List\s*of\s*Graphs",
        r"#\s*Graphs\s*List",
        r"#\s*Index\s*of\s*Graphs",
        r"#\s*Graph\s*Index",
        r"#\s*Table\s*of\s*Graphs",
        # English - General content directories that may contain figures
        r"#\s*List\s*of\s*Contents",
        r"#\s*Contents\s*List",
        r"#\s*Index\s*of\s*Contents",
        # English - Academic/Technical report sections that often contain figure directories
        r"#\s*\d+\s*LESSONS\s*AND\s*RECOMMENDATIONS",
        r"#\s*LESSONS\s*AND\s*RECOMMENDATIONS",
        r"#\s*\d+\s*CONCLUSIONS",
        r"#\s*CONCLUSIONS",
        r"#\s*\d+\s*SUMMARY",
        r"#\s*SUMMARY",
        r"#\s*\d+\s*RESULTS?\s*AND\s*DISCUSSION",
        r"#\s*RESULTS?\s*AND\s*DISCUSSION",
        r"#\s*\d+\s*FINDINGS",
        r"#\s*FINDINGS",
        r"#\s*\d+\s*ANALYSIS",
        r"#\s*ANALYSIS",
        r"#\s*\d+\s*RESULTS?",
        r"#\s*RESULTS?",
    ]

    # Compile patterns for better performance
    compiled_patterns = [
        re.compile(pattern, re.IGNORECASE) for pattern in fig_dir_patterns
    ]

    # Find the first matching pattern
    fig_dir_match = None
    for pattern in compiled_patterns:
        match = pattern.search(content)
        if match:
            fig_dir_match = match
            break

    if fig_dir_match is None:
        return content

    # Get the start and end positions of the figure directory section
    start_index = fig_dir_match.start()

    # Find the next main heading to determine the end of the section
    next_heading_pattern = re.compile(r"\n#", re.MULTILINE)
    next_heading_match = next_heading_pattern.search(
        content, start_index + len(fig_dir_match.group())
    )

    if next_heading_match:
        end_index = next_heading_match.start()
    else:
        end_index = len(content)

    # Remove the figure directory section from the content
    modified_content = (content[:start_index] + content[end_index:]).strip()
    final_content = clean_useless_text(modified_content)

    result = re.sub(r"([Ff]igure\s*\d+)o", r"\g<1>0", final_content)
    result = re.sub(r"([Ff]ig\.?\s*\d+)o", r"\g<1>0", result)
    result = re.sub(r"(图\s*\d+)o", r"\g<1>0", result, flags=re.IGNORECASE)
    result = re.sub(r"([Ff]igure\s*\d+)O", r"\g<1>0", result)
    result = re.sub(r"([Ff]ig\.?\s*\d+)O", r"\g<1>0", result)
    result = re.sub(r"(图\s*\d+)O", r"\g<1>0", result)
    result = re.sub(r"(?<=\d)一(?=\d)", "-", result)
    pattern = re.compile(r"([Ff](?:igure|ig\.?)|图)\s*(\d+)[oO]", re.IGNORECASE)
    result = pattern.sub(r"\g<1>\g<2>0", result)

    return result


def process_markdown_file(md_file_path: str, context_dir: str, book_id: str) -> None:
    """Processes a Markdown file and generates a JSON output for a single book."""
    print(f"Processing book ID: {book_id}")
    # Read Markdown file
    try:
        md_content = read_markdown_file(md_file_path)
    except Exception as e:
        print(f"Error reading Markdown file {md_file_path}: {e}")
        return

    # Extract the surrounding info of each picture
    all_image_info = extract_image_info(md_content, book_id)

    processed_data = []

    # Only process if classification is 'normal'
    # for image_info in all_image_info:
    #     classification = image_info.get("classification", "")
    #     if classification == "normal":
    #         # Only process if classification is 'normal'
    #         processed_item = process_image_reference(md_content, [image_info])
    #         processed_data.extend(
    #             processed_item
    #         )  # assuming process_image_reference returns a list
    #     else:
    #         # Skip processing and add raw image_info directly
    #         processed_data.append(image_info)

    # extract reference for all classification (normal/abnormal/extreme abnormal)
    processed_data = process_image_reference(md_content, all_image_info)

    # Define output JSON path for this book
    output_json_path = os.path.join(context_dir, f"{book_id}.json")
    # Write processed data to JSON file
    try:
        with open(output_json_path, "w", encoding="utf-8") as jsonfile:
            json.dump(processed_data, jsonfile, ensure_ascii=False, indent=2)
        print(
            f"Finished processing book ID {book_id}. Context saved to {output_json_path}"
        )
    except Exception as e:
        print(f"Error writing JSON file for book ID {book_id}: {e}")


def extract_context(input_dir: str = "input") -> None:
    """Process books in the specified directory."""
    if not os.path.isdir(input_dir):
        print(f"The directory '{input_dir}' does not exist.")
        return
    try:
        books_to_process = discover_books(input_dir)
    except FileNotFoundError as e:
        print(f"Error discovering books: {e}")
        return

    if not books_to_process:
        print("No books found to process in the specified directory structure.")
        return

    print(f"Found {len(books_to_process)} financial docs to process.")
    # Create the context output directory
    context_dir = os.path.join(input_dir, "context")
    os.makedirs(context_dir, exist_ok=True)
    print(f"Context files will be saved to: {context_dir}")

    # Process each book
    for i, (book_id, md_path, pdf_path) in enumerate(books_to_process):
        output_json_path = os.path.join(context_dir, f"{book_id}.json")

        # skip the processed book
        if os.path.exists(output_json_path) and os.path.getsize(output_json_path) > 0:
            print(f"Skipping already processed book ID: {book_id} (JSON exists)")
            continue

        start_time = time.time()
        try:
            # process the markdown file for each book
            process_markdown_file(md_path, context_dir, book_id)

            end_time = time.time()
            print(f"Total time for book {book_id}: {end_time - start_time:.2f}s")

        except Exception as e:
            print(f"Failed to process book ID {book_id}: {e}")
            # Continue with the next book


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract context information from markdown files"
    )
    parser.add_argument(
        "--input_dir",
        "-i",
        type=str,
        default="D:\GitHub\\fttracer\\examples\\data_preprocess\\Question_example",
        help="Input directory path containing markdown files",
    )
    parser.add_argument(
        "--sample_rate",
        type=float,
        default=1.0,
        help="Sample rate for abnormal context files (percentage)",
    )

    args = parser.parse_args()

    start_time = time.time()

    # Extract context information
    extract_context(input_dir=args.input_dir)

    # Record end time and calculate duration
    end_time = time.time()
    print(f"duration: {end_time-start_time}(s)\n")

    # Print classification statistics
    print(classification_statistics(args.input_dir))

    # Sample abnormal context files
    abnormal_context_sample(args.input_dir, args.sample_rate)
