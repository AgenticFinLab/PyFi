import base64
import requests
import json
import os
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = "/root/autodl-tmp/evaluation_dir/data_folder_202509191824"
SAMPLE_FILE = "./sample/tree_action_sample.json"
OUTPUT_FILE = "./sample/tree_action_sample_models_answer.json"
ERROR_FILE = "./sample/tree_action_sample_models_answer_error.json"
RETRY_ERRORS = False  # Set to False to disable retry mechanism

# Experimental group configuration (set to True for the group you want to test)
EXPERIMENT_GROUPS = {
    "image_background_only": True,  # Group 1: Only image_background
    "analysis_information_only": False,  # Group 2: Only analysis_information
    "both_contexts": False,  # Group 3: Both image_background and analysis_information
    "no_context": False,  # Group 4: No context information
}


def encode_image(image_path):

    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def callvlm(model_name, messages):
    BASE_URL = "https://www.dmxapi.cn/"
    API_ENDPOINT = BASE_URL + "v1/chat/completions"
    API_KEY = "sk-ytCdk7ShA21uyomr5DKQBcnAeNwJyKZaqXysh6uOB7otNoMT"

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.1,
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

    response = requests.post(API_ENDPOINT, headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"]


def get_context_info(image_path):
    """Get context information from corresponding context file"""
    # Convert image path to context path
    context_path = image_path.replace("/images/", "/context/").replace(".jpg", ".json")
    full_context_path = os.path.join(BASE_DIR, context_path.lstrip("./"))

    image_background = ""
    analysis_information = ""

    if os.path.exists(full_context_path):
        with open(full_context_path, "r", encoding="utf-8") as f:
            context_data = json.load(f)
            image_background = context_data.get("image_background", "")
            analysis_information = context_data.get("analysis_information", "")

    return image_background, analysis_information


def build_prompt_group1(image_background, question, options):
    """Group 1: Only image_background"""
    prompt_parts = []

    if image_background:
        prompt_parts.append(f"image_background: {image_background}\n\n\n")

    prompt_parts.append(f"question: {question}\n\n\n")

    prompt_parts.append(f"options: {json.dumps(options, ensure_ascii=False)}\n\n\n")

    # Dynamically generate option letters
    option_letters = list(options.keys())
    option_list = ", ".join(option_letters)
    prompt_parts.append(
        f"Based on the image and the provided information, select the correct option. Output ONLY the single letter corresponding to your choice ({option_list}) with no additional text, explanations, or formatting. For example, if the answer is 'A', you must only output: A."
    )

    return "\n\n".join(prompt_parts)


def build_prompt_group2(analysis_information, question, options):
    """Group 2: Only analysis_information"""
    prompt_parts = []

    if analysis_information:
        prompt_parts.append(f"analysis_information: {analysis_information}\n\n\n")

    prompt_parts.append(f"question: {question}\n\n\n")

    prompt_parts.append(f"options: {json.dumps(options, ensure_ascii=False)}\n\n\n")

    option_letters = list(options.keys())
    option_list = ", ".join(option_letters)
    prompt_parts.append(
        f"Based on the image and the provided information, select the correct option. Output ONLY the single letter corresponding to your choice ({option_list}) with no additional text, explanations, or formatting. For example, if the answer is 'A', you must only output: A."
    )

    return "\n\n".join(prompt_parts)


def build_prompt_group3(image_background, analysis_information, question, options):
    """Group 3: Both image_background and analysis_information"""
    prompt_parts = []

    if image_background:
        prompt_parts.append(f"image_background: {image_background}\n\n\n")

    if analysis_information:
        prompt_parts.append(f"analysis_information: {analysis_information}\n\n\n")

    prompt_parts.append(f"question: {question}\n\n\n")

    prompt_parts.append(f"options: {json.dumps(options, ensure_ascii=False)}\n\n\n")

    option_letters = list(options.keys())
    option_list = ", ".join(option_letters)
    prompt_parts.append(
        f"Based on the image and the provided information, select the correct option. Output ONLY the single letter corresponding to your choice ({option_list}) with no additional text, explanations, or formatting. For example, if the answer is 'A', you must only output: A."
    )

    return "\n\n".join(prompt_parts)


def build_prompt_group4(question, options):
    """Group 4: No context information"""
    prompt_parts = []

    prompt_parts.append(f"question: {question}\n\n\n")
    prompt_parts.append(f"options: {json.dumps(options, ensure_ascii=False)}\n\n\n")

    option_letters = list(options.keys())
    option_list = ", ".join(option_letters)
    prompt_parts.append(
        f"Based on the image, select the correct option. Output ONLY the single letter corresponding to your choice ({option_list}) with no additional text, explanations, or formatting. For example, if the answer is 'A', you must only output: A."
    )

    return "\n\n".join(prompt_parts)


def validate_answer(answer, valid_options):
    """Validate that the answer is a single valid option letter or error"""
    if isinstance(answer, str):
        answer = answer.strip().upper()
        if answer in valid_options:
            return answer, True
        elif "error" in answer.lower():
            return "error", True
    return answer, False


def get_experiment_group_name(group_key):
    """Get formatted experiment group name"""
    group_names = {
        "image_background_only": "image_background_only",
        "analysis_information_only": "analysis_information_only",
        "both_contexts": "both_contexts",
        "no_context": "no_context",
    }
    return group_names.get(group_key, group_key)


def get_model_field_name(group_name, model_name):
    """Get the field name for storing model results"""
    if group_name == "both_contexts":
        return model_name
    else:
        return f"{group_name}_{model_name}"


def process_experiment_group(group_key, samples, models):
    """Process a specific experiment group"""
    if not EXPERIMENT_GROUPS[group_key]:
        print(f"Skipping experiment group: {group_key}")
        return samples

    group_name = get_experiment_group_name(group_key)
    print(f"\n{'='*60}")
    print(f"Processing Experiment Group: {group_key}")
    print(f"{'='*60}")

    processed_count = 0
    error_count = 0
    error_records = []

    for i, sample in enumerate(samples):
        print(f"Processing sample {i+1}/{len(samples)}")

        # Construct full image path
        full_image_path = os.path.join(BASE_DIR, sample["image_path"].lstrip("./"))

        if not os.path.exists(full_image_path):
            print(f"Warning: Image file not found: {full_image_path}")
            continue

        # Get context information
        image_background, analysis_information = get_context_info(sample["image_path"])

        # Encode image
        try:
            image_data = encode_image(full_image_path)
        except Exception as e:
            print(f"Error encoding image: {e}")
            continue

        # Build prompt based on experiment group
        if group_key == "image_background_only":
            prompt_text = build_prompt_group1(
                image_background, sample["question"], sample["options"]
            )
        elif group_key == "analysis_information_only":
            prompt_text = build_prompt_group2(
                analysis_information, sample["question"], sample["options"]
            )
        elif group_key == "both_contexts":
            prompt_text = build_prompt_group3(
                image_background,
                analysis_information,
                sample["question"],
                sample["options"],
            )
        elif group_key == "no_context":
            prompt_text = build_prompt_group4(sample["question"], sample["options"])
        else:
            continue

        # Test each model
        valid_options = list(sample["options"].keys())

        for model_name in models:
            model_field = get_model_field_name(group_name, model_name)

            # Skip if already has a valid answer and retry is enabled
            if RETRY_ERRORS and model_field in sample:
                existing_answer = sample[model_field]
                if (
                    isinstance(existing_answer, str)
                    and existing_answer in valid_options
                ):
                    continue

            print(f"  Testing model: {model_name} in group {group_key}")

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_data}"},
                        },
                    ],
                }
            ]

            try:
                response = callvlm(model_name, messages)
                validated_answer, is_valid = validate_answer(response, valid_options)

                if is_valid:
                    sample[model_field] = validated_answer
                    print(f"    Result: {validated_answer}")
                    processed_count += 1
                else:
                    # Store error with full context
                    error_record = {
                        "timestamp": datetime.now().isoformat(),
                        "experiment_group": group_key,
                        "model_name": model_name,
                        "sample_index": i,
                        "file_path": sample.get("file_path", ""),
                        "original_answer": response,
                        "validated_answer": validated_answer,
                        "valid_options": valid_options,
                        "prompt_used": prompt_text,
                        "image_path": sample["image_path"],
                        "question": sample["question"],
                        "options": sample["options"],
                    }
                    error_records.append(error_record)

                    sample[model_field] = {
                        "answer": response,
                        "validated": validated_answer,
                        "status": "invalid_format",
                        "error_message": f"Expected one of {valid_options} or 'error', but got: {response}",
                    }
                    print(f"    Invalid answer: {response}")
                    error_count += 1

            except Exception as e:
                error_record = {
                    "timestamp": datetime.now().isoformat(),
                    "experiment_group": group_key,
                    "model_name": model_name,
                    "sample_index": i,
                    "file_path": sample.get("file_path", ""),
                    "error": str(e),
                    "image_path": sample["image_path"],
                    "question": sample["question"],
                    "options": sample["options"],
                }
                error_records.append(error_record)

                sample[model_field] = {
                    "answer": None,
                    "status": "api_error",
                    "error_message": str(e),
                }
                print(f"    Error with model {model_name}: {e}")
                error_count += 1

        print()  # Empty line for readability

    # Save error records if any
    if error_records:
        save_error_records(error_records, group_key)

    print(
        f"Group {group_key} completed: {processed_count} processed, {error_count} errors"
    )
    return samples


def save_error_records(error_records, group_key):
    """Save error records to JSON file"""
    try:
        # Load existing errors if file exists
        if os.path.exists(ERROR_FILE):
            with open(ERROR_FILE, "r", encoding="utf-8") as f:
                existing_errors = json.load(f)
        else:
            existing_errors = []

        # Add new error records
        existing_errors.extend(error_records)

        # Save updated errors
        with open(ERROR_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_errors, f, indent=2, ensure_ascii=False)

        print(
            f"Saved {len(error_records)} error records for group {group_key} to {ERROR_FILE}"
        )

    except Exception as e:
        print(f"Error saving error records: {e}")


def process_sample_data():
    """Process the sample data for all enabled experiment groups"""

    # Load sample data
    with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # Define models to test
    models = [
        # "GLM-4.1V-9B-Thinking",
        # "qvq-max-2025-03-25",
        # "qwen2.5-vl-32b-instruct",
        # "gpt-5",
        # "gpt-5-mini",
        # "gpt-5-nano",
        "gpt-4.1",
        # "gpt-4.1-2025-04-14",
        # "gpt-4.1-mini",
        # "gpt-4.1-mini-2025-04-14",
        # "claude-opus-4-1-20250805",
        # "claude-opus-4-1-20250805-thinking",
        # "gemini-2.5-flash-lite",
        # "gemini-2.5-pro",
        # "gemini-2.5-pro-thinking",
        # "grok-4",
        # "glm-4.5v",
    ]

    # Load existing results if retry mode is enabled and file exists
    if RETRY_ERRORS and os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
    else:
        existing_results = samples

    # Process each enabled experiment group
    for group_key in EXPERIMENT_GROUPS.keys():
        existing_results = process_experiment_group(group_key, existing_results, models)

    # Save final results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_results, f, indent=2, ensure_ascii=False)

    print(f"\nFinal results saved to {OUTPUT_FILE}")


def retry_errors():
    """Retry only the samples that resulted in errors"""
    if not os.path.exists(OUTPUT_FILE):
        print("No output file found. Please run process_sample_data first.")
        return

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        samples = json.load(f)

    models = [
        "GLM-4.1V-9B-Thinking",
        # Add other models as needed
    ]

    print("\nRetrying errors...")

    for group_key in EXPERIMENT_GROUPS.keys():
        if not EXPERIMENT_GROUPS[group_key]:
            continue

        group_name = get_experiment_group_name(group_key)
        error_count = 0
        retry_count = 0

        for i, sample in enumerate(samples):
            for model_name in models:
                model_field = get_model_field_name(group_name, model_name)

                if model_field in sample:
                    current_result = sample[model_field]
                    valid_options = list(sample["options"].keys())

                    # Check if this is an error case that needs retry
                    needs_retry = False
                    if isinstance(current_result, dict) and "status" in current_result:
                        needs_retry = True
                    elif current_result == "error":
                        needs_retry = True
                    elif (
                        isinstance(current_result, str)
                        and current_result not in valid_options
                    ):
                        needs_retry = True

                    if needs_retry:
                        error_count += 1
                        print(
                            f"Retrying sample {i+1} with model {model_name} in group {group_key}"
                        )

                        # Re-process this specific sample-model combination
                        full_image_path = os.path.join(
                            BASE_DIR, sample["image_path"].lstrip("./")
                        )

                        if not os.path.exists(full_image_path):
                            continue

                        # Get context information
                        image_background, analysis_information = get_context_info(
                            sample["image_path"]
                        )

                        # Encode image
                        try:
                            image_data = encode_image(full_image_path)
                        except Exception as e:
                            print(f"Error encoding image: {e}")
                            continue

                        # Build appropriate prompt
                        if group_key == "image_background_only":
                            prompt_text = build_prompt_group1(
                                image_background, sample["question"], sample["options"]
                            )
                        elif group_key == "analysis_information_only":
                            prompt_text = build_prompt_group2(
                                analysis_information,
                                sample["question"],
                                sample["options"],
                            )
                        elif group_key == "both_contexts":
                            prompt_text = build_prompt_group3(
                                image_background,
                                analysis_information,
                                sample["question"],
                                sample["options"],
                            )
                        elif group_key == "no_context":
                            prompt_text = build_prompt_group4(
                                sample["question"], sample["options"]
                            )

                        messages = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_text},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_data}"
                                        },
                                    },
                                ],
                            }
                        ]

                        try:
                            response = callvlm(model_name, messages)
                            validated_answer, is_valid = validate_answer(
                                response, valid_options
                            )

                            if is_valid and validated_answer != "error":
                                retry_count += 1
                                sample[model_field] = validated_answer
                                print(f"  New result: {validated_answer}")
                            else:
                                print(f"  Still error: {response}")

                        except Exception as e:
                            print(f"  Error: {e}")

        print(
            f"Group {group_key}: Found {error_count} errors, successfully retried {retry_count}"
        )

    # Save updated results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(ERROR_FILE), exist_ok=True)

    # Check which experiment groups are enabled
    enabled_groups = [group for group, enabled in EXPERIMENT_GROUPS.items() if enabled]
    if not enabled_groups:
        print(
            "No experiment groups enabled. Please set at least one EXPERIMENT_GROUPS value to True."
        )
    else:
        print(f"Enabled experiment groups: {', '.join(enabled_groups)}")

        # First run: process all samples for enabled groups
        process_sample_data()

        # Optional: retry errors if enabled
        if RETRY_ERRORS:
            retry_errors()
