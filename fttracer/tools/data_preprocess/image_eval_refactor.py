import os
import json
import shutil


def process_json_files(input_dir, output_dir_yes, output_dir_no):
    """
    Add the fields of book_id and image_id for the JSON files, and maintain the original directory structure

    Args:
        input_dir
        output_dir
    """

    # Check if the input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: The dir '{input_dir}' doesn't exist! ")
        return

    # Traverse all subdirectories under the input directory
    for book_id in os.listdir(input_dir):
        book_dir = os.path.join(input_dir, book_id)

        # confirm
        if not os.path.isdir(book_dir):
            continue

        # create the corresponding output dir
        output_book_dir_yes = os.path.join(output_dir_yes, book_id)
        output_book_dir_no = os.path.join(output_dir_no, book_id)
        if not os.path.exists(output_book_dir_yes):
            os.makedirs(output_book_dir_yes)
        if not os.path.exists(output_book_dir_no):
            os.makedirs(output_book_dir_no)

        # Traverse all JSON files in this directory.
        for filename in os.listdir(book_dir):
            if filename.endswith(".json"):
                image_id = filename.replace(".json", ".jpg")
                json_path = os.path.join(book_dir, filename)
                output_json_path_yes = os.path.join(output_book_dir_yes, filename)
                output_json_path_no = os.path.join(output_book_dir_no, filename)

                try:
                    # Read the file
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Add book_i and image_id fields
                    data["book_id"] = book_id
                    data["image_id"] = image_id

                    # Wrap the data in a list and save it

                    if data["is_compliant"] == "yes":
                        with open(output_json_path_yes, "w", encoding="utf-8") as f:
                            json.dump([data], f, ensure_ascii=False, indent=2)
                            print(f"Success: {json_path} -> {output_json_path_yes}")
                    else:
                        with open(output_json_path_no, "w", encoding="utf-8") as f:
                            json.dump([data], f, ensure_ascii=False, indent=2)
                            print(f"Success: {json_path} -> {output_json_path_no}")

                except Exception as e:
                    print(f"File: {json_path}  Error: {e}")

    print(f"Completed!")
