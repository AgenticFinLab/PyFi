"""Summarize contextual information from JSON files using a large language model.

This script traverses a directory of JSON files containing contextual information,
extracts the text, and summarizes it using a large model API. The summarized
results are saved in a mirrored directory structure under a new root folder.

The summarization is strictly based on the provided text, without inference or
external knowledge.

Each processed file's processing time is logged to console.
"""

import os
import json
import time

from openai import OpenAI

from fttracer.tools.data_preprocess.prompt import prompt_for_context_summarization


def initialize_openai_client() -> OpenAI:
    """Initialize and return an OpenAI client using environment variables.

    This function creates an OpenAI client configured to use the DashScope API
    endpoint and retrieves the API key from the environment variable DASHSCOPE_API_KEY.

    Returns:
        OpenAI: Configured OpenAI client.
    """
    return OpenAI(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # API endpoint for DashScope
        api_key=os.environ.get(
            "DASHSCOPE_API_KEY"
        ),  # Retrieve API key from environment
    )


def context_summarizer_via_LLM(
    input_dir: str, model_name: str = "qwen3-max-preview"
) -> None:
    """Traverse directories, summarize JSON content, and save results with timing.

    This function walks through the input directory structure, processes each JSON file
    containing contextual information, generates summaries using the LLM, and saves
    the results maintaining the same directory structure in the output location.
    Processing time for each file is logged to the console.

    Args:
        input_root: Path to the root directory containing input JSON files.
        output_root: Path to the root directory where summaries will be saved.
        model_name: Name of the model used for summarization.
    """
    output_dir = os.path.join(input_dir, "context_summary_LLM")
    input_dir = os.path.join(input_dir, "context_summary_expanded")

    client = initialize_openai_client()

    # Ensure output root directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Traverse each subdirectory in the input root
    for folder_name in os.listdir(input_dir):
        folder_path = os.path.join(input_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        output_folder = os.path.join(output_dir, folder_name)
        os.makedirs(output_folder, exist_ok=True)

        # Process each JSON file in the subdirectory
        for file_name in os.listdir(folder_path):
            if not file_name.endswith(".json"):
                continue

            input_file_path = os.path.join(folder_path, file_name)
            output_file_path = os.path.join(output_folder, file_name)
            prompt_file_path = os.path.join(
                output_folder, file_name.replace(".json", "_prompt.txt")
            )

            # Skip if already processed
            if os.path.exists(output_file_path):
                print(f"Already processed: {output_file_path}")
                continue

            start_time = time.time()

            # Load the JSON content
            try:
                with open(input_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                print(f"Failed to decode JSON: {input_file_path}")
                continue

            # Extract the text to summarize
            context_text = data.get("contextual_information", "")
            if not context_text:
                print(f"Missing 'contextual_information' in: {input_file_path}")
                continue

            # Generate summary using the LLM
            try:
                summary_json, prompt = generate_summary(
                    client, model_name, context_text
                )
            except Exception as e:
                print(f"Error summarizing {input_file_path}: {e}")
                continue

            # Save the summary in a new JSON file and prompt in a separate file
            save_summary(output_file_path, summary_json)
            save_prompt(prompt_file_path, prompt)

            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[{file_name}] Processing time: {elapsed_time:.2f} seconds")


def generate_summary(client: OpenAI, model_name: str, text: str) -> tuple:
    """Generate a summary of the given text using the specified model.

    This function sends the provided text to the LLM with a structured prompt
    and system message, requesting a JSON-formatted response containing
    image background and analysis information.

    Args:
        client: OpenAI client instance.
        model_name: Name of the model to use.
        text: Text to summarize.

    Returns:
        tuple: (summary_json_dict, prompt)
    """
    prompt = prompt_for_context_summarization(text)

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are an objective summarizer that only extracts the background information and the concise analysis information. Do not add any personal thoughts, views, or opinions. Output must be in valid JSON format.",
            },  # System message defining the LLM's role
            {
                "role": "user",
                "content": prompt,
            },  # User message containing the detailed prompt
        ],
        response_format={"type": "json_object"},  # Request JSON output format
    )

    # Parse JSON response
    try:
        summary_content = completion.choices[0].message.content.strip()
        summary_json = json.loads(summary_content)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        summary_json = {"summary": summary_content}

    return summary_json, prompt


def save_summary(file_path: str, summary_json: dict) -> None:
    """Save the summary JSON directly to a file without wrapping.

    This function writes the extracted summary data directly to a JSON file,
    preserving the structure returned by the LLM.

    Args:
        file_path: Path to the output JSON file.
        summary_json: Summary content in JSON format to save directly.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, ensure_ascii=False, indent=2)
    print(f"Saved summary to: {file_path}")


def save_prompt(file_path: str, prompt: str) -> None:
    """Save the prompt to a text file.

    This function optionally saves the prompt used for generating the summary
    to a separate text file for reference or debugging.

    Args:
        file_path: Path to the output text file.
        prompt: The prompt used to generate the summary.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(prompt)
    print(f"Saved prompt to: {file_path}")


if __name__ == "__main__":
    context_summarizer_via_LLM(
        input_dir=r"PyFi",
    )
