import os
import asyncio
from typing import List, Dict, Union, Optional
import base64
from openai import OpenAI
from dotenv import load_dotenv
from volcenginesdkarkruntime import AsyncArk  # Client for batch inference


# --------------------------
# Client Initialization (Retrieve API key from environment variables uniformly)
# --------------------------

def get_openai_client() -> OpenAI:
    """Get OpenAI-compatible client for normal (non-batch) inference"""
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise ValueError(
            "Please set the environment variable ARK_API_KEY (Volcengine API key) first"
        )
    return OpenAI(
        api_key=api_key,
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )


def get_ark_batch_client() -> AsyncArk:
    """Get AsyncArk client dedicated for batch inference"""
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise ValueError(
            "Please set the environment variable ARK_API_KEY (Volcengine API key) first"
        )
    return AsyncArk(
        api_key=api_key,
        timeout=24
        * 3600,  # Keep consistent timeout setting with official batch inference examples
    )


# --------------------------
# Core Utility Functions (Preserve original functionality)
# --------------------------
def encode_image_file(image_path: str) -> str:
    """
    Encode a local image file to base64 format.

    Args:
        image_path: File path to the local image

    Returns:
        Base64-encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_message_content(
    image_url: Optional[str] = None,
    image_path: Optional[str] = None,
    text: Optional[str] = None,
) -> List[Dict]:
    """
    Create properly formatted message content for vision models.

    Args:
        image_url: URL of a remote image
        image_path: File path to a local image
        text: Accompanying text prompt

    Returns:
        List of content items conforming to the API message format
    """
    content = []

    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    elif image_path:
        base64_image = encode_image_file(image_path)
        # Determine image MIME type from file extension
        ext = image_path.split(".")[-1].lower()
        if ext not in ["png", "jpeg", "jpg", "webp"]:
            raise ValueError("Unsupported image format. Use PNG, JPEG, or WEBP.")
        mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
            }
        )

    if text:
        content.append({"type": "text", "text": text})

    return content


# --------------------------
# Core Function for Normal (Non-Batch) Inference
# --------------------------
def _make_api_call(
    model: str, messages: List[Dict], stream: bool = False
) -> Union[str, Dict]:
    """
    Internal function to make normal (non-batch) API calls to Volcengine's Doubao models.
    """
    client = get_openai_client()
    try:
        completion = client.chat.completions.create(
            model=model, messages=messages, stream=stream
        )

        if stream:
            return completion  # Return stream object directly for streaming responses
        return completion.choices[
            0
        ].message.content  # Return text content for non-streaming responses
    except Exception as e:
        raise Exception(f"Normal API call failed: {str(e)}")


# --------------------------
# Core Functions for Batch Inference (Async + Sync Wrapper)
# --------------------------
async def _async_batch_api_call(
    model: str, messages: List[Dict], stream: bool = False
) -> Union[str, Dict]:
    """
    Asynchronous batch inference call (adapts to Volcengine batch/chat/completions endpoint)
    """
    if stream:
        # Batch inference endpoints typically don't support streaming; explicitly throw unsupported exception
        raise NotImplementedError("Batch inference does not support stream mode")

    client = get_ark_batch_client()
    try:
        # Construct batch inference request (single request also adapts to batch interface format)
        request_params = {
            "model": model,
            "messages": messages,
        }
        # Call batch inference endpoint
        completion = await client.batch.chat.completions.create(**request_params)

        # Parse response format to be consistent with normal inference (return content text)
        if hasattr(completion, "choices") and len(completion.choices) > 0:
            return completion.choices[0].message.content
        raise ValueError("Batch API response invalid: no 'choices' field found")
    except Exception as e:
        raise Exception(f"Batch API call failed: {str(e)}")
    finally:
        await client.close()  # Close asynchronous client connection


def _make_batch_api_call(
    model: str, messages: List[Dict], stream: bool = False
) -> Union[str, Dict]:
    """
    Synchronous wrapper for batch inference calls (hides async implementation from external users,
    preserving the original synchronous interface)
    """
    try:
        # Run asynchronous batch inference function and return results
        return asyncio.run(_async_batch_api_call(model, messages, stream))
    except Exception as e:
        raise Exception(f"Batch API wrapper failed: {str(e)}")


# --------------------------
# Model Interface Functions (Only doubao_seed_1_6_flash uses batch inference)
# --------------------------
def doubao_seed_1_6(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Doubao Seed 1.6 model with general visual understanding capabilities.

    Args:
        messages: List of message dictionaries conforming to API format
        stream: Whether to enable streaming response

    Returns:
        Model response content (string) or stream object (if stream=True)
    """
    return _make_api_call("doubao-seed-1-6-250615", messages, stream)


def doubao_seed_1_6_flash(
    messages: List[Dict], stream: bool = False
) -> Union[str, Dict]:
    """
    Doubao Seed 1.6 Flash model optimized for faster responses (uses batch inference endpoint).

    Args:
        messages: List of message dictionaries conforming to API format
        stream: Whether to enable streaming response (NOT supported for batch inference)

    Returns:
        Model response content (stream mode is not supported)
    """
    # Call batch inference endpoint, keeping the same model name as original function
    # return _make_batch_api_call("ep-bi-20250918150137-fljck", messages, stream)
    return _make_api_call("doubao-seed-1-6-flash-250828", messages, stream)


def doubao_seed_1_6_thinking(
    messages: List[Dict], stream: bool = False
) -> Union[str, Dict]:
    """
    Doubao Seed 1.6 Thinking model with enhanced reasoning capabilities.

    Args:
        messages: List of message dictionaries conforming to API format
        stream: Whether to enable streaming response

    Returns:
        Model response content (string) or stream object (if stream=True)
    """
    return _make_api_call("doubao-seed-1-6-thinking-250715", messages, stream)


def doubao_1_5_thinking_vision_pro(
    messages: List[Dict], stream: bool = False
) -> Union[str, Dict]:
    """
    Doubao 1.5 Thinking Vision Pro model with advanced visual processing capabilities.

    Args:
        messages: List of message dictionaries conforming to API format
        stream: Whether to enable streaming response

    Returns:
        Model response content (string) or stream object (if stream=True)
    """
    return _make_api_call("doubao-1-5-thinking-vision-pro-250428", messages, stream)


def doubao_seed_1_6_vision_250815(
    messages: List[Dict], stream: bool = False
) -> Union[str, Dict]:
    """
    Doubao Seed 1.6 Vision model with advanced visual processing capabilities.

    Args:
        messages: List of message dictionaries conforming to API format
        stream: Whether to enable streaming response

    Returns:
        Model response content (string) or stream object (if stream=True)
    """
    return _make_api_call("doubao-seed-1-6-vision-250815", messages, stream)


# --------------------------
# Example Calls (Preserve original logic)
# --------------------------
if __name__ == "__main__":
    # Example 1: Remote image inference (using batch inference Flash model)
    load_dotenv()  # Load environment variables from .env file
    remote_image_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://ark-project.tos-cn-beijing.ivolces.com/images/view.jpeg"
                    },
                },
                {
                    "type": "text",
                    "text": "Where is this place? Describe it in one sentence.",
                },
            ],
        }
    ]
    try:
        print("=== Remote Image Inference (Batch Endpoint) ===")
        response = doubao_seed_1_6_flash(remote_image_messages)
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Remote image inference failed: {str(e)}\n")

    # # Example 2: Local image inference (using batch inference Flash model)
    # local_image_path = r"D:\Documents\GitHub\AgenticFinLab\fttracer\data_server_001\data_shell_011\images\000212\000056.jpg"  # Replace with your local image path
    # local_image_messages = [
    #     {
    #         "role": "user",
    #         "content": create_message_content(
    #             image_path=local_image_path,
    #             text='Are there any abbreviations in the image? If so, list them all. Output format: {"abbreviations": ["abbrev1", ...]}',
    #         ),
    #     }
    # ]
    # try:
    #     print("=== Local Image Inference (Batch Endpoint) ===")
    #     import time

    #     start_time = time.time()
    #     response = doubao_seed_1_6_flash(local_image_messages)
    #     end_time = time.time()
    #     print(f"Response: {response}")
    #     print(f"Time elapsed: {end_time - start_time:.2f} seconds\n")
    # except Exception as e:
    #     print(f"Local image inference failed: {str(e)}\n")

    # Example 3: Text-only inference (using batch inference Flash model)
    text_messages = [
        {
            "role": "user",
            "content": create_message_content(
                text="What are some common Brassicaceae plants?"
            ),
        }
    ]
    try:
        print("=== Text-Only Inference (Batch Endpoint) ===")
        response = doubao_seed_1_6_flash(text_messages)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Text-only inference failed: {str(e)}")
