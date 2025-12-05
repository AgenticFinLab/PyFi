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
from dataclasses import dataclass
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


### extract captions for each image


@dataclass
class ImageMatch:
    """Data class to store image match information."""

    line_num: int
    paragraph_index: int
    image_filename: str
    line_content: str


@dataclass
class CaptionInfo:
    """Data class to store caption information."""

    content: str
    line_num: int
    distance: int


@dataclass
class ImageInfo:
    """Data class to store comprehensive image information."""

    classification: str
    book_id: str
    image_filename: str
    image_tag_line_number: int
    image_surround_text: str
    other_images_nearby: Dict[str, Any]
    caption_count: int
    captions_found: List[Dict[str, Any]]
    nearest_caption: str


def extract_image_info(markdown_content: str, book_id: str) -> List[Dict[str, Any]]:
    """
    Extract image information and their captions from markdown content.

    This function processes markdown content to find all image tags and their corresponding
    captions according to specified rules, then classifies each image based on the findings.

    Args:
        markdown_content: The markdown content as a string
        book_id: The book identifier (e.g., '000001')

    Returns:
        A list of dictionaries containing image information and classification data
    """
    # Split markdown content into paragraphs for line tracking
    paragraphs_info = split_into_paragraphs(markdown_content)

    # Extract all image matches from the content
    image_matches = _extract_image_matches(markdown_content, paragraphs_info)

    # Process each image match to extract complete information
    image_info_list = []
    all_lines = markdown_content.split("\n")

    for image_match in image_matches:
        image_info = _process_single_image(
            image_match=image_match,
            all_lines=all_lines,
            paragraphs_info=paragraphs_info,
            markdown_content=markdown_content,
            book_id=book_id,
        )
        image_info_list.append(image_info)

    return image_info_list


def _extract_image_matches(
    markdown_content: str, paragraphs_info: List[Dict]
) -> List[ImageMatch]:
    """
    Extract all image matches from markdown content with their position information.

    Args:
        markdown_content: The markdown content as a string
        paragraphs_info: List of paragraph information with line ranges

    Returns:
        List of ImageMatch objects containing image information
    """
    # Define regex pattern to match image tags in markdown format ![alt_text](../images/folder/filename)
    image_pattern = re.compile(r"!\[.*?]\(\.\./images/[^/]+/([^)]+)\)")
    image_matches = []

    # Find all image matches with their positions in the original content
    for match in image_pattern.finditer(markdown_content):
        match_start_pos = match.start()
        # Calculate 1-based line number where the image tag appears
        line_num = markdown_content[:match_start_pos].count("\n") + 1

        # Find which paragraph contains this line
        paragraph_index = _find_paragraph_index(paragraphs_info, line_num)

        if paragraph_index is not None:
            image_matches.append(
                ImageMatch(
                    line_num=line_num,
                    paragraph_index=paragraph_index,
                    image_filename=match.group(1),  # Extract filename from regex group
                    line_content=markdown_content.split("\n")[line_num - 1].strip(),
                )
            )

    return image_matches


def _find_paragraph_index(paragraphs_info: List[Dict], line_num: int) -> Optional[int]:
    """
    Find the paragraph index that contains the given line number.

    Args:
        paragraphs_info: List of paragraph information with line ranges
        line_num: The line number to search for

    Returns:
        The paragraph index if found, None otherwise
    """
    for idx, para in enumerate(paragraphs_info):
        if para["start_line"] <= line_num <= para["end_line"]:
            return idx
    return None


def _process_single_image(
    image_match: ImageMatch,
    all_lines: List[str],
    paragraphs_info: List[Dict],
    markdown_content: str,
    book_id: str,
) -> ImageInfo:
    """
    Process a single image match to extract complete information including captions and classification.

    Args:
        image_match: The ImageMatch object containing basic image information
        all_lines: List of all lines in the markdown content
        paragraphs_info: List of paragraph information
        markdown_content: The original markdown content
        book_id: The book identifier

    Returns:
        An ImageInfo object containing comprehensive image information
    """
    line_num = image_match.line_num
    image_filename = image_match.image_filename
    para_index = image_match.paragraph_index

    # Get the paragraph containing the image and surrounding context
    paragraph = paragraphs_info[para_index]
    raw_context = paragraph["content"]
    image_surround_text = ensure_minimum_context(
        md_content=markdown_content, k=4000, text=raw_context
    )

    # Find captions and other images near the current image
    captions_found = _find_captions_near_image(all_lines, line_num)
    other_images_found = _find_other_images_near_image(
        all_lines, line_num, image_match.line_content
    )

    # Classify the image based on found captions and nearby images
    classification, nearest_caption = _classify_image(
        len(captions_found), other_images_found
    )

    # Prepare information about other images nearby
    other_images_info = _prepare_other_images_info(other_images_found)

    # Prepare detailed caption information
    captions_detail = _prepare_caption_details(
        captions_found, markdown_content, line_num
    )

    # Create comprehensive image information
    return ImageInfo(
        classification=classification,
        book_id=book_id,
        image_filename=image_filename,
        image_tag_line_number=line_num,
        image_surround_text=image_surround_text,
        other_images_nearby=other_images_info,
        caption_count=len(captions_found),
        captions_found=captions_detail,
        nearest_caption=nearest_caption,
    )


def _find_captions_near_image(all_lines: List[str], line_num: int) -> List[CaptionInfo]:
    """
    Find captions near the given image line number.

    Args:
        all_lines: List of all lines in the markdown content
        line_num: The line number where the image appears

    Returns:
        List of CaptionInfo objects containing found captions
    """
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
    return _filter_valid_captions(captions_found, all_lines, line_num)


def _filter_valid_captions(
    captions_found: List[Dict], all_lines: List[str], line_num: int
) -> List[CaptionInfo]:
    """
    Filter captions to ensure they start with proper figure identifiers.

    Args:
        captions_found: List of raw caption matches
        all_lines: List of all lines in the markdown content
        line_num: The line number where the image appears

    Returns:
        List of valid CaptionInfo objects
    """
    # Pattern to match the beginning of figure identifiers
    figure_start_pattern = re.compile(r"^\s*(图|fig|Fig|Figure|Figura)", re.IGNORECASE)

    filtered_captions = []

    for caption in captions_found:
        caption_line = all_lines[caption["line_num"]]
        if figure_start_pattern.match(caption_line):
            # Caption starts with figure identifier on the same line
            filtered_captions.append(
                CaptionInfo(
                    content=caption["content"],
                    line_num=caption["line_num"],
                    distance=caption["distance"],
                )
            )
        else:
            # Check if this is part of a paragraph that starts with figure identifier
            caption_line_num_1based = caption["line_num"] + 1
            paragraphs_info = split_into_paragraphs("\n".join(all_lines))
            caption_para_idx = _find_paragraph_index(
                paragraphs_info, caption_line_num_1based
            )

            if caption_para_idx is not None:
                caption_para = paragraphs_info[caption_para_idx]
                # Check if the paragraph starts with a figure identifier
                if figure_start_pattern.match(caption_para["lines"][0]):
                    filtered_captions.append(
                        CaptionInfo(
                            content=caption["content"],
                            line_num=caption["line_num"],
                            distance=caption["distance"],
                        )
                    )

    # Sort captions by distance to image (closest first)
    filtered_captions.sort(key=lambda x: x.distance)
    return filtered_captions


def _find_other_images_near_image(
    all_lines: List[str], line_num: int, current_image_line: str
) -> List[Dict]:
    """
    Find other images near the current image (excluding the current image itself).

    Args:
        all_lines: List of all lines in the markdown content
        line_num: The line number where the current image appears
        current_image_line: The content of the line containing the current image

    Returns:
        List of other images found near the current image
    """
    # Define regex pattern for image matching
    image_pattern = re.compile(r"!\[.*?]\(\.\./images/[^/]+/([^)]+)\)")

    # Set search range (5 lines upward from image)
    upper_bound = 5
    # Find other images in the specified range
    other_images_found = find_elements_in_range(
        all_lines, line_num - 1, image_pattern, upper_bound
    )

    # Filter out the current image itself from other images list
    other_images_found = [
        img
        for img in other_images_found
        if img["line_num"] + 1 != line_num or img["content"] != current_image_line
    ]

    return other_images_found


def _classify_image(
    caption_count: int, other_images_found: List[Dict]
) -> Tuple[str, str]:
    """
    Classify the image based on caption count and presence of other nearby images.

    Classification rules:
    - extreme abnormal: No captions found
    - normal: One caption found and no other images nearby
    - abnormal: Other cases (one caption + other images, or multiple captions)

    Args:
        caption_count: Number of captions found near the image
        other_images_found: List of other images found nearby

    Returns:
        Tuple of (classification, nearest_caption_text)
    """
    if caption_count == 0:
        return "extreme abnormal", ""  # A-0: No captions
    elif caption_count == 1:
        if not other_images_found:
            return "normal", ""  # A-1 + B-0: One caption, no other images
        else:
            return "abnormal", ""  # A-1 + B-1: One caption, other images present
    else:
        return "abnormal", ""  # A-2: Multiple captions


def _prepare_other_images_info(other_images_found: List[Dict]) -> Dict[str, Any]:
    """
    Prepare structured information about other images found near the current image.

    Args:
        other_images_found: List of other images found nearby

    Returns:
        Dictionary containing count and details of other images
    """
    return {
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


### extract references for each image


def _prepare_caption_details(
    captions_found: List[CaptionInfo], markdown_content: str, image_line_num: int
) -> List[Dict[str, Any]]:
    """
    Prepare detailed information about each found caption.

    Args:
        captions_found: List of CaptionInfo objects
        markdown_content: The original markdown content
        image_line_num: The line number of the current image

    Returns:
        List of dictionaries containing detailed caption information
    """
    return [
        {
            "content": cap.content,  # Caption text
            "content_paragraph": ensure_minimum_context(
                markdown_content, 500, cap.content
            ),  # Paragraph context around caption
            "line_number": cap.line_num + 1,  # Line number of caption (1-based)
            "distance": abs(cap.line_num - image_line_num + 1),  # Distance from image
        }
        for cap in captions_found
    ]


def process_image_reference(
    markdown_content: str, image_info_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Process image references and associate them with corresponding captions.

    This function analyzes markdown content to find references to images within paragraphs,
    matching figure identifiers in captions with their corresponding references in the text.

    Args:
        markdown_content: The cleaned markdown content to analyze
        image_info_list: List of dictionaries containing image metadata including captions

    Returns:
        A list of image information dictionaries with added reference data grouped by caption
    """
    # Split the markdown content into paragraphs for reference searching
    paragraph_mapping = split_into_paragraphs(markdown_content)

    # Process each image in the provided list
    for image_info in image_info_list:
        _process_single_image_reference(image_info, markdown_content, paragraph_mapping)

    return image_info_list


def _process_single_image_reference(
    image_info: Dict[str, Any],
    markdown_content: str,
    paragraph_mapping: List[Dict[str, Any]],
) -> None:
    """Process a single image to find its references in the markdown content.

    Args:
        image_info: Dictionary containing image metadata and captions
        markdown_content: The full markdown content
        paragraph_mapping: List of paragraph information for reference searching
    """
    captions = image_info["captions_found"]
    image_line_num = image_info["image_tag_line_number"]
    image_filename = image_info["image_filename"]

    # Track processed captions and figure numbers to avoid duplicates
    seen_captions = set()
    processed_figures = set()

    # Each caption will have its own list of references
    caption_references = []

    # Process each caption associated with the current image
    for caption in captions:
        caption_content = caption["content"] if isinstance(caption, dict) else caption

        # Skip duplicate captions
        if caption_content in seen_captions:
            continue
        seen_captions.add(caption_content)

        # Extract figure identifier part from caption (e.g., "图1" from "图1经济增长率")
        figure_match = extract_figure_identifier(caption_content)
        if not figure_match:
            continue

        figure_number = figure_match.group(1)  # e.g., "图1"

        # Skip duplicate figure numbers
        if figure_number in processed_figures:
            continue
        processed_figures.add(figure_number)

        # Find all references to this figure number in the content
        references = _find_figure_references(
            figure_number, caption, image_line_num, paragraph_mapping, markdown_content
        )

        # Create caption entry and only add if there are actual references
        caption_entry = {
            "caption": caption_content,
            "figure_number": figure_number,
            "reference_count": len(references),
            "references": references,
        }

        # Only append entries that have actual references to avoid empty duplicates
        if references:
            caption_references.append(caption_entry)

    # Handle special cases where no references were found initially
    _handle_no_reference_cases(
        caption_references, image_filename, paragraph_mapping, image_line_num
    )

    # Update the image info with processed results
    image_info["caption_references"] = caption_references
    image_info["total_reference_count"] = sum(
        cr["reference_count"] for cr in caption_references
    )


def _find_figure_references(
    figure_number: str,
    caption: Dict[str, Any],
    image_line_num: int,
    paragraph_mapping: List[Dict[str, Any]],
    markdown_content: str,
) -> List[Dict[str, Any]]:
    """Find all references to a specific figure number in the markdown content.

    Args:
        figure_number: The figure identifier to search for (e.g., "图1")
        caption: The caption dictionary containing line number information
        image_line_num: The line number where the image tag appears
        paragraph_mapping: List of paragraph information for reference searching
        markdown_content: The full markdown content

    Returns:
        List of reference information dictionaries
    """
    references = []
    caption_line_number = caption["line_number"]

    # Track exact match and non-exact match counts for early termination
    exact_match_count = 0
    non_exact_match_count = 0
    max_non_exact_matches = 2
    found_exact_match = False

    # Search for references in all paragraphs
    for paragraph_info in paragraph_mapping:
        paragraph_content = paragraph_info["content"]
        start_line = paragraph_info["start_line"]
        end_line = paragraph_info["end_line"]

        # Get expanded content around the paragraph for context
        expanded_content = _get_expanded_content(markdown_content, paragraph_content)

        # Skip the paragraph containing the image
        if start_line <= image_line_num <= end_line:
            continue

        # Remove the caption line from paragraph if it exists in this paragraph
        paragraph_info = _remove_caption_line_from_paragraph(
            paragraph_info, caption_line_number, start_line
        )

        # Find all references of the figure identifier in this paragraph
        paragraph_references, exact_found, non_exact_count = (
            _search_paragraph_for_references(
                paragraph_info, figure_number, caption_line_number
            )
        )

        # Update counters and references list
        references.extend(paragraph_references)

        for ref in paragraph_references:
            if ref["is_exact_match"]:
                exact_match_count += 1
                found_exact_match = True
            else:
                non_exact_match_count += 1

        # Early termination condition: at least one exact match AND at least two non-exact matches
        if found_exact_match and non_exact_match_count >= max_non_exact_matches:
            break

    return references


def _get_expanded_content(markdown_content: str, paragraph_content: str) -> str:
    """Get expanded content around a paragraph for context.

    Args:
        markdown_content: The full markdown content
        paragraph_content: The content of the current paragraph

    Returns:
        Expanded content string or "null" if not found
    """
    pos = markdown_content.find(paragraph_content)
    if pos != -1:
        return ensure_minimum_context(
            md_content=markdown_content,
            k=1000,
            text=paragraph_content,
        )
    else:
        return "null"


def _remove_caption_line_from_paragraph(
    paragraph_info: Dict[str, Any], caption_line_number: int, start_line: int
) -> Dict[str, Any]:
    """Remove the caption line from a paragraph if it exists in that paragraph.

    Args:
        paragraph_info: Dictionary containing paragraph information
        caption_line_number: The line number of the caption
        start_line: The starting line number of the paragraph

    Returns:
        Updated paragraph_info dictionary
    """
    paragraph_content = paragraph_info["content"]
    start_line = paragraph_info["start_line"]
    end_line = paragraph_info["end_line"]

    if start_line <= caption_line_number <= end_line:
        lines = paragraph_content.split("\n")
        relative_line_index = caption_line_number - start_line
        if 0 <= relative_line_index < len(lines):
            lines.pop(relative_line_index)
            paragraph_info["content"] = "\n".join(lines)
            paragraph_info["end_line"] -= 1
            paragraph_info["lines"] = lines  # Update the lines list as well

    return paragraph_info


def _search_paragraph_for_references(
    paragraph_info: Dict[str, Any], figure_number: str, caption_line_number: int
) -> Tuple[List[Dict[str, Any]], bool, int]:
    """Search a paragraph for references to a figure number.

    Args:
        paragraph_info: Dictionary containing paragraph information
        figure_number: The figure identifier to search for
        caption_line_number: The line number of the caption (to avoid

    Returns:
        Tuple of (references list, exact match found, non-exact count)
    """
    paragraph_content = paragraph_info["content"]
    start_line = paragraph_info["start_line"]
    end_line = paragraph_info["end_line"]

    references = []
    exact_match_found = False
    non_exact_count = 0

    # Find all references of the figure identifier in this paragraph
    reference_pattern = re.compile(re.escape(figure_number), re.IGNORECASE)
    potential_matches = reference_pattern.finditer(paragraph_content)

    for match_obj in potential_matches:
        char_start = match_obj.start()

        # Define pattern for figure references (Chinese: 图, English: Figure/Fig)
        pattern = r"(图\s*([a-zA-Z]?)\s*(\d+(?:[.-]\d+)*)|Figure\s*(\d+(?:[.-]\d+)*)|Fig\.?\s*(\d+(?:[.-]\d+)*))"

        # Find the line that contains the match
        matching_line_info = _find_matching_line_info(
            paragraph_info, char_start, start_line, caption_line_number
        )

        if matching_line_info:
            # Find all figure reference patterns in the matching line
            ref_text_matches = re.finditer(
                pattern,
                matching_line_info["content"],
                re.IGNORECASE,
            )
            ref_text = [match.group(0) for match in ref_text_matches]

            # Check if this is an exact match
            is_exact = any(
                figure_number.lower() == ref_text_item.lower()
                for ref_text_item in ref_text
            )

            if is_exact:
                exact_match_found = True
            else:
                non_exact_count += 1

            # Create reference entry
            reference_entry = {
                "reference_text": ref_text,
                "is_exact_match": is_exact,
                "match_line_info": matching_line_info,
                "reference_paragraph": paragraph_content,
                "reference_paragraph_extension": ensure_minimum_context(
                    md_content=paragraph_content,
                    k=1000,
                    text=paragraph_content,
                ),
                "total_lines_in_paragraph": len(paragraph_info["lines"]),
            }
            references.append(reference_entry)

    return references, exact_match_found, non_exact_count


def _find_matching_line_info(
    paragraph_info: Dict[str, Any],
    char_start: int,
    start_line: int,
    caption_line_number: int,
) -> Optional[Dict[str, Any]]:
    """Find the line information for a character position in a paragraph.

    Args:
        paragraph_info: Dictionary containing paragraph information
        char_start: The character position where the match starts
        start_line: The starting line number of the paragraph
        caption_line_number: The line number of the caption (to avoid)

    Returns:
        Dictionary containing line information or None if not found
    """
    paragraph_content = paragraph_info["content"]
    lines = paragraph_info["lines"]

    # Calculate cumulative length to find which line contains the match
    cumulative_length = 0
    for idx, line in enumerate(lines):
        line_length = len(line) + 1  # +1 for newline character
        if cumulative_length <= char_start < cumulative_length + line_length:
            current_line_number = start_line + idx

            # Skip if this is the caption line
            if current_line_number != caption_line_number:
                return {
                    "line_number": current_line_number,
                    "content": line.strip(),
                    "char_position_in_paragraph": char_start,
                }
            break
        cumulative_length += line_length

    return None


def _handle_no_reference_cases(
    caption_references: List[Dict[str, Any]],
    image_filename: str,
    paragraph_mapping: List[Dict[str, Any]],
    image_line_num: int,
) -> None:
    """Handle cases where no references were found for a figure number.

    This function attempts to find alternative figure numbers by shortening the original
    figure number and searching for similar references.

    Args:
        caption_references: List of caption reference entries to process
        image_filename: The filename of the image (used for similarity matching)
        paragraph_mapping: List of paragraph information for reference searching
        image_line_num: The line number where the image tag appears
    """
    for cr in caption_references:
        # Only process entries with no references and a figure number
        if cr["reference_count"] == 0 and cr["figure_number"]:
            figure_number = cr["figure_number"]

            # Check if there are 3 or more consecutive digits in the figure number
            has_three_or_more_consecutive_digits = _has_three_consecutive_digits(
                figure_number
            )

            if not has_three_or_more_consecutive_digits:
                continue

            # Try to find alternative figure number candidates by shortening the original
            best_candidate = _find_best_figure_candidate(
                cr["figure_number"], paragraph_mapping, image_line_num, image_filename
            )

            # Update the caption reference with the best candidate if found
            if best_candidate:
                cr["figure_number"] = best_candidate["candidate"]
                cr["references"] = best_candidate["references"]
                cr["reference_count"] = len(best_candidate["references"])


def _has_three_consecutive_digits(text: str) -> bool:
    """Check if a string has 3 or more consecutive digits.

    Args:
        text: The string to check

    Returns:
        True if there are 3 or more consecutive digits, False otherwise
    """
    consecutive_digit_count = 0
    for char in text:
        if char.isdigit():
            consecutive_digit_count += 1
            if consecutive_digit_count >= 3:
                return True
        else:
            consecutive_digit_count = 0
    return False


def _find_best_figure_candidate(
    original_figure_number: str,
    paragraph_mapping: List[Dict[str, Any]],
    image_line_num: int,
    image_filename: str,
) -> Optional[Dict[str, Any]]:
    """Find the best figure number candidate by shortening the original figure number.

    Args:
        original_figure_number: The original figure number to shorten
        paragraph_mapping: List of paragraph information for reference searching
        image_line_num: The line number where the image tag appears
        image_filename: The filename of the image (used for similarity matching)

    Returns:
        Best candidate information dictionary or None if no candidates found
    """
    candidate_references_pairs = []
    current_candidate = original_figure_number

    # Reduce characters from right to left to find shorter figure number candidates
    while len(current_candidate) > 1:
        # Remove the last character
        current_candidate = current_candidate[:-1]

        # Stop if candidate string becomes too short
        if len(current_candidate) <= 1:
            break

        # Stop if candidate no longer contains digits
        if not any(char.isdigit() for char in current_candidate):
            break

        # Search for references using the trimmed candidate string
        corrected_references = _search_for_candidate_references(
            current_candidate, paragraph_mapping, image_line_num
        )

        # If references found, save the candidate
        if corrected_references:
            candidate_references_pairs.append(
                {
                    "candidate": current_candidate,
                    "references": corrected_references,
                }
            )

    # Select the best pair among all candidates based on number similarity
    if candidate_references_pairs:
        # Extract the number from image filename for similarity comparison
        index_digits = "".join(filter(str.isdigit, image_filename))
        index_number = int(index_digits) if index_digits else 0

        best_pair = None
        best_similarity = float("inf")

        # Find the candidate with the closest number to the image index
        for pair in candidate_references_pairs:
            candidate = pair["candidate"]
            # Extract the numbers in candidate
            candidate_digits = "".join(filter(str.isdigit, candidate))
            candidate_number = int(candidate_digits) if candidate_digits else 0

            # Calculate the difference
            difference = abs(candidate_number - index_number)

            if difference < best_similarity:
                best_similarity = difference
                best_pair = pair

        return best_pair

    return None


def _search_for_candidate_references(
    candidate: str, paragraph_mapping: List[Dict[str, Any]], image_line_num: int
) -> List[Dict[str, Any]]:
    """Search for references to a candidate figure number.

    Args:
        candidate: The candidate figure number to search for
        paragraph_mapping: List of paragraph information for reference searching
        image_line_num: The line number where the image tag appears

    Returns:
        List of reference information dictionaries
    """
    corrected_references = []
    expanded_content = ""

    # Search in all paragraphs
    for paragraph_info in paragraph_mapping:
        paragraph_content = paragraph_info["content"]
        start_line = paragraph_info["start_line"]
        end_line = paragraph_info["end_line"]

        # Skip the paragraph containing the image
        if start_line <= image_line_num <= end_line:
            continue

        # Create pattern to match candidate string as whole word
        pattern = re.compile(re.escape(candidate), re.IGNORECASE)
        potential_matches = pattern.finditer(paragraph_content)

        for match_obj in potential_matches:
            char_start = match_obj.start()

            # Pattern to match figure references
            caption_pattern = r"((图\s*([a-zA-Z]?)\s*(\d+(\s*[.\-]\s*\d+)*\s*)|Figure\s*(\d+(\s*[.\-]\s*\d+\s*)*)|Fig\.?\s*(\s*\d+(?:\s*[.\-]\s*\d+\s*)*)))"

            try:
                caption_match = re.search(
                    caption_pattern,
                    paragraph_content[char_start : char_start + 100],
                    re.IGNORECASE,
                )
            except re.error as e:
                print(f"Regex error: {e}")
                print(f"Pattern: {caption_pattern}")
                continue

            if caption_match:
                ref_text = caption_match.group(0)

                # Locate the matching line
                cumulative_length = 0
                matching_line_info = None
                for idx, line in enumerate(paragraph_info["lines"]):
                    line_length = len(line) + 1
                    if (
                        cumulative_length
                        <= char_start
                        < cumulative_length + line_length
                    ):
                        matching_line_info = {
                            "line_number": start_line + idx,
                            "content": line.strip(),
                            "char_position_in_paragraph": char_start,
                        }
                        break
                    cumulative_length += line_length

                if matching_line_info:
                    corrected_references.append(
                        {
                            "reference_text": ref_text,
                            "is_exact_match": candidate == ref_text,
                            "match_line_info": matching_line_info,
                            "paragraph_content": paragraph_content,
                            "reference_paragraph_extension": expanded_content,
                            "total_lines_in_paragraph": len(paragraph_info["lines"]),
                        }
                    )

    return corrected_references


# Main Process Function


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
