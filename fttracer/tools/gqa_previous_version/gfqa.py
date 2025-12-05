import os
import json
import random
from typing import List, Dict, Union, Optional
import base64
from openai import OpenAI
from MCTS.prompt import *

# Initialize the client
client = OpenAI(
    api_key=os.getenv("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# Constants
MIN_CHOICES = 3
MAX_CHOICES = 5
CAPABILITIES = [
    "visual recognition",
    "data extraction",
    "calculation and analysis",
    "trend analysis",
    "logical reasoning",
    "decision support"
]


def _make_api_call(model: str, messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream
        )
        if stream:
            return completion
        resp = completion.choices[0].message.content
        return resp
    except Exception as e:
        raise Exception(f"API call failed: {str(e)}")


def encode_image_file(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_message_content(image_url: Optional[str] = None,
                           image_path: Optional[str] = None,
                           text: Optional[str] = None) -> List[Dict]:
    content = []
    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    elif image_path:
        base64_image = encode_image_file(image_path)
        ext = image_path.split('.')[-1].lower()
        if ext not in ['png', 'jpeg', 'jpg', 'webp']:
            raise ValueError("Unsupported image format. Use PNG, JPEG, or WEBP.")
        mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
        })
    if text:
        content.append({"type": "text", "text": text})
    return content


def doubao_1_5_thinking_vision_pro(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    return _make_api_call("doubao-1-5-thinking-vision-pro-250428", messages, stream)


def doubao_seed_1_6_flash(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Doubao Seed 1.6 Flash model optimized for faster responses.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("doubao-seed-1-6-flash-250715", messages, stream)


def load_existing_questions(json_path: str) -> List[Dict]:
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_questions(questions: List[Dict], json_path: str):
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)


def generate_question_prompt(existing_questions: List[Dict]) -> str:
    prompt = prompt_2(contextual_information="None",existing_final_questions=json.dumps(existing_questions, ensure_ascii=False, indent=2))
    return prompt


def generate_answer_prompt(question_data: Dict) -> str:
    prompt = prompt_3(contextual_information="None",final_question=json.dumps(question_data, ensure_ascii=False, indent=2))
    return prompt


def generate_new_qa_pair(image_path: str, existing_questions: List[Dict]) -> Dict:
    # Generate question components
    question_prompt = generate_question_prompt(existing_questions)
    messages = [
        {"role": "user", "content": create_message_content(
            image_path=image_path,
            text=question_prompt
        )}
    ]

    question_temp=doubao_seed_1_6_flash(messages)
    print(question_temp)
    question_data = json.loads(question_temp)

    # Generate answer
    answer_prompt = generate_answer_prompt(question_data)
    messages = [
        {"role": "user", "content": create_message_content(
            image_path=image_path,
            text=answer_prompt
        )}
    ]


    answer_temp=doubao_seed_1_6_flash(messages)
    print(answer_temp)
    answer = json.loads(answer_temp)


    # Assemble final QA pair
    picture_name = os.path.basename(image_path)
    next_no = max([q.get('no', 0) for q in existing_questions], default=0) + 1

    return {
        "picture_name": picture_name,
        "no": next_no,
        "instruction": question_data.get("instruction", ""),
        "question": question_data.get("question", ""),
        "question_type": question_data.get("question_type", ""),
        "choices": question_data.get("choices", {}),
        "answer": answer.get("answer",""),
        "capability": question_data.get("capability", ""),
        "complexity": question_data.get("complexity", "")
    }


def main():
    # Configuration
    json_path = "finalqa-5.json"
    # image_dir = "images"  # Directory containing financial trend images
    num_iterations = 5 # Number of new QA pairs to generate

    # Load existing questions
    existing_questions = load_existing_questions(json_path)

    # Get list of image files
    # image_files = [
    #     os.path.join(image_dir, f) for f in os.listdir(image_dir)
    #     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    # ]

    # if not image_files:
    #     print("No valid image files found in the directory.")
    #     return

    # Generate new QA pairs
    new_questions = []
    for _ in range(num_iterations):
        # Select a random image
        image_path = r"D:\Documents\GitHub\AgenticFinLab\fttracer\fttracer\images\000001.png"

        try:
            import time
            start=time.time()
            new_qa = generate_new_qa_pair(image_path, existing_questions + new_questions)
            end=time.time()
            print(f"Spent {end-start}s")
            new_questions.append(new_qa)
            print(f"Generated QA pair #{new_qa['no']} for {new_qa['picture_name']}")
        except Exception as e:
            print(f"Error generating QA pair: {str(e)}")
            continue

    # Save updated questions
    if new_questions:
        updated_questions = existing_questions + new_questions
        save_questions(updated_questions, json_path)
        print(f"Saved {len(new_questions)} new QA pairs to {json_path}")
    else:
        print("No new QA pairs were generated.")


if __name__ == "__main__":
    main()