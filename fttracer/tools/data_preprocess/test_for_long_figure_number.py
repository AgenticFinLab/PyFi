"""Caption reference correction module.

This module provides functionality to correct and validate figure caption references
by finding matching references in the document content.
"""

import re
from typing import Dict, List, Any, Tuple


def correct_caption_references(
    cr: Dict[str, Any], 
    index: str, 
    paragraph_mapping: List[Dict[str, Any]], 
    image_line_num: int
) -> None:
    """Correct caption references by finding matching references in document content.

    This function analyzes caption parts and searches for corresponding references
    in the document paragraphs, trimming the caption part until valid matches are found.

    Args:
        cr: Caption reference dictionary containing caption_part, reference_count, and references.
        index: Image index string (e.g., '000001.jpg').
        paragraph_mapping: List of paragraph information dictionaries.
        image_line_num: Line number where the image is located.
    """
    if cr["reference_count"] == 0 and cr["caption_part"]:
        # Check if caption_part contains 3 or more consecutive digits
        caption_part = cr["caption_part"]
        has_three_or_more_consecutive_digits = False

        # Find consecutive digits
        consecutive_digit_count = 0
        for char in caption_part:
            if char.isdigit():
                consecutive_digit_count += 1
                if consecutive_digit_count >= 3:
                    has_three_or_more_consecutive_digits = True
                    break
            else:
                consecutive_digit_count = 0

        if has_three_or_more_consecutive_digits:
            original_caption_part = cr["caption_part"]
            print(f"Original caption part: {original_caption_part}")

            # Store all found candidate-reference pairs
            candidate_references_pairs = []

            # Start trimming from right to left
            current_candidate = original_caption_part

            # Reduce characters from right to left
            while len(current_candidate) > 1:
                # Remove the last character
                current_candidate = current_candidate[:-1]
                print(f"current_candidate: {current_candidate}")

                # Stop if candidate string becomes too short
                if len(current_candidate) <= 1:
                    break

                # Stop if candidate no longer contains digits
                if not any(char.isdigit() for char in current_candidate):
                    break

                # Search for references using the trimmed candidate string
                corrected_references = []

                for paragraph_info in paragraph_mapping:
                    paragraph_content = paragraph_info["content"]
                    start_line = paragraph_info["start_line"]
                    end_line = paragraph_info["end_line"]

                    # Skip paragraphs that contain the image
                    if start_line <= image_line_num <= end_line:
                        continue

                    # Create pattern to match candidate string as whole word
                    pattern = re.compile(re.escape(current_candidate), re.IGNORECASE)
                    potential_matches = pattern.finditer(paragraph_content)

                    for match_obj in potential_matches:
                        char_start = match_obj.start()
                        # Verify if it's a valid figure caption format
                        caption_pattern = (
                            r"((图\s*([a-zA-Z]?)\s*(\d+(\s*[.\-]\s*\d+)*\s*)|"
                            r"Figure\s*(\d+(\s*[.\-]\s*\d+\s*)*)|"
                            r"Fig\.?\s*(\s*\d+(?:\s*[.\-]\s*\d+\s*)*)))"
                        )
                        
                        try:
                            caption_match = re.search(
                                caption_pattern,
                                paragraph_content[char_start: char_start + 20],
                                re.IGNORECASE,
                            )
                        except re.error as e:
                            print(f"Regex error: {e}")
                            print(f"Pattern: {caption_pattern}")
                            continue

                        if caption_match:
                            ref_text = caption_match.group(0)

                            # Locate matching line
                            cumulative_length = 0
                            matching_line_info = None
                            
                            for idx, line in enumerate(paragraph_info["lines"]):
                                line_length = len(line) + 1
                                if (cumulative_length <= char_start < 
                                    cumulative_length + line_length):
                                    matching_line_info = {
                                        "line_number": start_line + idx,
                                        "content": line.strip(),
                                        "char_position_in_paragraph": char_start,
                                    }
                                    break
                                cumulative_length += line_length

                            if matching_line_info:
                                corrected_references.append({
                                    "reference_text": ref_text,
                                    "is_exact_match": current_candidate == ref_text,
                                    "match_line_info": matching_line_info,
                                    "paragraph_content": paragraph_content,
                                    "total_lines_in_paragraph": len(
                                        paragraph_info["lines"]
                                    ),
                                })

                # If references found, save this candidate pair but continue looping
                if corrected_references:
                    candidate_references_pairs.append({
                        'candidate': current_candidate,
                        'references': corrected_references
                    })
                    print(f"Found references for {current_candidate}, continuing...")

            # After loop, select best match from all candidate pairs
            if candidate_references_pairs:
                # Extract digits from index (remove leading zeros)
                index_digits = ''.join(filter(str.isdigit, index))
                index_number = int(index_digits) if index_digits else 0

                best_pair = None
                best_similarity = float('inf')

                for pair in candidate_references_pairs:
                    candidate = pair['candidate']
                    # Extract digits from candidate
                    candidate_digits = ''.join(filter(str.isdigit, candidate))
                    candidate_number = int(candidate_digits) if candidate_digits else 0

                    # Calculate numeric difference
                    difference = abs(candidate_number - index_number)

                    if difference < best_similarity:
                        best_similarity = difference
                        best_pair = pair

                # Update cr with best match
                if best_pair:
                    cr["caption_part"] = best_pair['candidate']
                    cr["references"] = best_pair['references']
                    cr["reference_count"] = len(best_pair['references'])
                    print(f"Final selected caption part: {best_pair['candidate']}")


# Example usage
if __name__ == "__main__":
    # Mock data
    # 000019
    cr = {
        "caption_part": "图22015-2016",
        "reference_count": 0,
        "references": []
    }
    index = '000001.jpg'
    paragraph_mapping = [
        {
            'content': "如图6. 2所示经济持续增长",
            'start_line': 5,
            'end_line': 5,
            'lines': ["如图2所示经济持续增长"]
        },
        {
            'content': "如图2所示经济持续下降",
            'start_line': 7,
            'end_line': 7,
            'lines': ["如图2所示经济持续下降"]
        },
        {
            'content': "如图22所示经济持续增长",
            'start_line': 6,
            'end_line': 6,
            'lines': ["如图22所示经济持续增长"]
        }
    ]

    image_line_num = 3  # Assume image is on line 3

    correct_caption_references(cr, index, paragraph_mapping, image_line_num)
    print(cr["references"])