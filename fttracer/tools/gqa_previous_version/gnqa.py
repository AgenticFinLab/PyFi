import os
import json
import math
import random
from typing import List, Dict, Union, Optional, Tuple
import base64
from openai import OpenAI

# Initialize the client
client = OpenAI(
    api_key=os.getenv("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

# Constants
CAPABILITIES = [
    "visual recognition",
    "data extraction",
    "calculation and analysis",
    "trend analysis",
    "logical reasoning",
    "decision support"
]

# Exploration constant for UCB formula
C = math.sqrt(2)

# Maximum number of nodes to generate
MAX_NODES = 100

# Maximum depth for any chain
MAX_DEPTH = 6

# Number of first layer nodes (similar to 361 in Go)
FIRST_LAYER_NODES = 20


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


def load_final_questions(json_path: str) -> List[Dict]:
    """Load final questions from JSON file"""
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_nodes(nodes: List[Dict], json_path: str):
    """Save all nodes to JSON file"""
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)


def generate_node_answer(image_path: str, node_data: Dict) -> str:
    """Generate answer for a node using the vision model"""
    question_prompt = f"""Given the following financial trend image question, provide the correct answer:

Question: {node_data['question']}
Options: {json.dumps(node_data['choices'], ensure_ascii=False)}

Rules:
1. Answer must be one of the provided options (just the letter)
2. Must be objectively correct based on the image
3. For multiple correct answers, provide all letters separated by commas
4. If true/false, answer with 'T' or 'F'

Output only the answer letter(s) with no other text or formatting."""

    messages = [
        {"role": "user", "content": create_message_content(
            image_path=image_path,
            text=question_prompt
        )}
    ]

    try:
        answer = doubao_1_5_thinking_vision_pro(messages).strip()
        # Validate answer format
        if ',' in answer:
            # For multiple choice, validate each option exists
            parts = [p.strip() for p in answer.split(',')]
            for p in parts:
                if p not in node_data['choices']:
                    return random.choice(list(node_data['choices'].keys()))
            return answer
        elif answer in node_data['choices'] or answer in ['T', 'F']:
            return answer
        else:
            return random.choice(list(node_data['choices'].keys()))
    except Exception:
        return random.choice(list(node_data['choices'].keys()))


def generate_new_node(image_path: str, parent_node: Optional[Dict], chain_nodes: List[Dict],
                      final_question: Dict) -> Dict:
    """Generate a new node in the QA chain"""
    prompt = """Generate a new question-answer pair for financial trend image analysis that logically follows from previous nodes and moves toward answering the final question.

Requirements:
1. The question must be objective (single-choice, multi-choice, or true/false)
2. Answer must be unambiguous and verifiable from the image
3. Must build upon previous nodes in the chain
4. Must help progress toward answering the final question
5. Must cover one of these capability dimensions:
   - visual recognition
   - data extraction
   - calculation and analysis
   - trend analysis
   - logical reasoning
   - decision support

Final Question:
{final_question}

Existing Chain (most recent first):
{existing_chain}

Output format (JSON):
{{
  "instruction": "context for the question",
  "question": "the actual question",
  "choices": {{"A": "option1", "B": "option2", ...}},
  "capability": "one of the 6 capabilities",
  "can_answer_finalq": true/false
}}""".format(
        final_question=json.dumps(final_question, ensure_ascii=False, indent=2),
        existing_chain=json.dumps(chain_nodes, ensure_ascii=False,
                                  indent=2)
    )

    messages = [
        {"role": "user", "content": create_message_content(
            image_path=image_path,
            text=prompt
        )}
    ]

    try:
        response = doubao_1_5_thinking_vision_pro(messages)
        node_data = json.loads(response)

        # Validate required fields
        if not all(key in node_data for key in ['instruction', 'question', 'choices', 'capability']):
            raise ValueError("Missing required fields in generated node")

        if node_data['capability'] not in CAPABILITIES:
            node_data['capability'] = random.choice(CAPABILITIES)

        # Ensure can_answer_finalq is boolean
        node_data['can_answer_finalq'] = node_data.get('can_answer_finalq', False)

        return node_data
    except Exception as e:
        print(f"Error generating node: {str(e)}")
        # Return a simple fallback node if generation fails
        return {
            "instruction": "Identify the main trend line in the image",
            "question": "Is the primary trend line increasing or decreasing?",
            "choices": {
                "A": "Increasing",
                "B": "Decreasing",
                "C": "No clear trend"
            },
            "capability": "visual recognition",
            "can_answer_finalq": False
        }


def calculate_ucb(node: Dict, parent_visit_count: int) -> float:
    """Calculate UCB value for node selection"""
    if node['visit_count'] == 0:
        return float('inf')

    # Ensure parent_visit_count is at least 1 to avoid math domain errors
    safe_parent_count = max(1, parent_visit_count)


    exploitation = node['victory_count'] / node['visit_count']
    exploration = math.sqrt(math.log(safe_parent_count) / node['visit_count'])
    return exploitation + C * exploration


def select_node(nodes: List[Dict], parent_visit_count: int) -> Dict:
    """Select node using UCB formula"""
    max_ucb = -1
    selected_node = None

    # Ensure parent_visit_count is at least 1
    safe_parent_count = max(1, parent_visit_count)

    for node in nodes:
        if node['visit_count'] == 0:
            return node
        try:
            ucb = calculate_ucb(node, safe_parent_count)
            if ucb > max_ucb:
                max_ucb = ucb
                selected_node = node
        except:
            # Fallback to random selection if calculation fails
            return random.choice(nodes)

    return selected_node if selected_node is not None else random.choice(nodes)


def can_answer_final_question(chain: List[Dict], final_question: Dict) -> bool:
    """Check if current chain can answer the final question"""
    if not chain:
        return False

    # Check if any node in chain claims it can answer
    for node in chain:
        if node.get('can_answer_finalq', False):
            return True

    return False


def answer_final_question(image_path: str, chain: List[Dict], final_question: Dict) -> str:
    """Attempt to answer the final question using the chain"""
    prompt = f"""Based on the following chain of reasoning from the financial trend image, answer the final question:

Chain of Reasoning:
{json.dumps(chain, ensure_ascii=False, indent=2)}

Final Question:
{final_question['question']}
Options: {json.dumps(final_question['choices'], ensure_ascii=False)}

Rules:
1. Answer must be one of the provided options (just the letter)
2. Must be based on the chain of reasoning
3. Output only the answer letter with no other text"""

    messages = [
        {"role": "user", "content": create_message_content(
            image_path=image_path,
            text=prompt
        )}
    ]

    try:
        answer = doubao_1_5_thinking_vision_pro(messages).strip()
        if answer in final_question['choices'] or answer in ['T', 'F']:
            return answer
        return random.choice(list(final_question['choices'].keys()))
    except Exception:
        return random.choice(list(final_question['choices'].keys()))


def backpropagate(nodes: List[Dict], chain: List[Dict], is_correct: bool):
    """Update visit and victory counts for nodes in the chain"""
    for node in chain:
        # Find the node in the full nodes list
        for n in nodes:
            if n['node'] == node['node']:
                n['visit_count'] += 1
                if is_correct:
                    n['victory_count'] += 1
                break


def process_final_question(image_path: str, final_question: Dict, nodes: List[Dict]) -> List[Dict]:
    """Process a single final question to build QA chains"""
    # Initialize first layer nodes if needed
    first_layer_nodes = [n for n in nodes if n['parent'] == 0 and n['finalqano'] == final_question['no']]

    if len(first_layer_nodes) < FIRST_LAYER_NODES:
        # Generate first layer nodes
        for i in range(FIRST_LAYER_NODES - len(first_layer_nodes)):
            new_node_data = generate_new_node(image_path, None, [], final_question)

            new_node = {
                "picture_name": final_question['picture_name'],
                "finalqano": final_question['no'],
                "node": len(nodes) + 1,
                "parent": 0,
                "instruction": new_node_data['instruction'],
                "question": new_node_data['question'],
                "choices": new_node_data['choices'],
                "answer": "",
                "capability": new_node_data['capability'],
                "can_answer_finalq": new_node_data['can_answer_finalq'],
                "visit_count": 0,
                "victory_count": 0
            }

            # Get answer from vision model
            new_node['answer'] = generate_node_answer(image_path, new_node)

            nodes.append(new_node)
            print(f"Generated first layer node {new_node['node']}")

    # Perform MCTS iterations
    while len(nodes) < MAX_NODES:
        # Select a chain to explore
        current_chain = []
        current_node = select_node([n for n in nodes if n['parent'] == 0 and n['finalqano'] == final_question['no']],
                                   max(1,
                                       sum(n['visit_count'] for n in nodes if n['finalqano'] == final_question['no'])))

        if current_node is None:
            break

        current_chain.append(current_node)

        # Traverse down the tree
        while True:
            children = [n for n in nodes if
                        n['parent'] == current_node['node'] and n['finalqano'] == final_question['no']]

            if not children:
                # Need to expand this node
                break

            current_node = select_node(children, current_node['visit_count'])
            current_chain.append(current_node)

            # Check if we can answer the final question
            if can_answer_final_question(current_chain, final_question):
                break

            # Prevent infinite loops
            if len(current_chain) >= MAX_DEPTH:
                break

        # Check if we can answer the final question
        if can_answer_final_question(current_chain, final_question):
            # Attempt to answer
            model_answer = answer_final_question(image_path, current_chain, final_question)
            is_correct = model_answer == final_question['answer']

            # Create final question node
            final_node = {
                "picture_name": final_question['picture_name'],
                "finalqano": final_question['no'],
                "node": len(nodes) + 1,
                "parent": current_node['node'],
                "instruction": final_question['instruction'],
                "question": final_question['question'],
                "choices": final_question['choices'],
                "answer": model_answer,
                "capability": final_question['capability'],
                "can_answer_finalq": True,
                "visit_count": -1,
                "victory_count": -1
            }
            nodes.append(final_node)

            # Backpropagate results
            backpropagate(nodes, current_chain, is_correct)

            print(f"Chain completed with {'correct' if is_correct else 'incorrect'} answer")
            continue

        # Generate new child node
        new_node_data = generate_new_node(image_path, current_node, current_chain, final_question)

        new_node = {
            "picture_name": final_question['picture_name'],
            "finalqano": final_question['no'],
            "node": len(nodes) + 1,
            "parent": current_node['node'],
            "instruction": new_node_data['instruction'],
            "question": new_node_data['question'],
            "choices": new_node_data['choices'],
            "answer": "",
            "capability": new_node_data['capability'],
            "can_answer_finalq": new_node_data['can_answer_finalq'],
            "visit_count": 0,
            "victory_count": 0
        }

        # Get answer from vision model
        new_node['answer'] = generate_node_answer(image_path, new_node)

        nodes.append(new_node)
        print(f"Generated new node {new_node['node']} under parent {current_node['node']}")

        # If this new node can answer, try to answer
        if new_node['can_answer_finalq']:
            model_answer = answer_final_question(image_path, current_chain + [new_node], final_question)
            is_correct = model_answer == final_question['answer']

            # Create final question node
            final_node = {
                "picture_name": final_question['picture_name'],
                "finalqano": final_question['no'],
                "node": len(nodes) + 1,
                "parent": new_node['node'],
                "instruction": final_question['instruction'],
                "question": final_question['question'],
                "choices": final_question['choices'],
                "answer": model_answer,
                "capability": final_question['capability'],
                "can_answer_finalq": True,
                "visit_count": -1,
                "victory_count": -1
            }
            nodes.append(final_node)

            # Backpropagate results
            backpropagate(nodes, current_chain + [new_node], is_correct)

            print(f"Chain completed with {'correct' if is_correct else 'incorrect'} answer")

    return nodes


def main():
    # Configuration
    finalqa_path = "finalqa_example.json"
    nodes_path = "nodeqa_example.json"
    image_dir = "images"  # Directory containing financial trend images

    # Load final questions
    final_questions = load_final_questions(finalqa_path)
    if not final_questions:
        print("No final questions found in finalqa.json")
        return

    # Load existing nodes or initialize
    if os.path.exists(nodes_path):
        with open(nodes_path, 'r', encoding='utf-8') as f:
            nodes = json.load(f)
    else:
        nodes = []

    # Get list of image files
    image_files = {}
    for fq in final_questions:
        img_path = os.path.join(image_dir, fq['picture_name'])
        if os.path.exists(img_path):
            image_files[fq['no']] = img_path

    if not image_files:
        print("No valid image files found for the final questions")
        return

    # Process each final question
    for fq in final_questions:
        if fq['no'] not in image_files:
            continue

        print(f"\nProcessing final question {fq['no']}")
        nodes = process_final_question(image_files[fq['no']], fq, nodes)

        # Save progress after each question
        save_nodes(nodes, nodes_path)

    print(f"\nCompleted processing. Saved {len(nodes)} nodes to {nodes_path}")


if __name__ == "__main__":
    main()

