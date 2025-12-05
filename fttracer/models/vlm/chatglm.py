"""
Aliyun Model Studio GLM Vision API Wrapper

This module provides a Python interface to Aliyun's Model Studio GLM vision models,
including GLM-4.1V-Thinking series models. It's designed for easy integration
and modular usage.

Features:
- Support for all GLM-4.1V-Thinking model variants
- Proper parameterization for all API options
- Consistent naming conventions
- Comprehensive error handling
- Detailed docstrings for each function

Usage:
    from chatglm import glm_4v_plus_0111

    messages = [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
            {"type": "text", "text": "Describe this image"}
        ]}
    ]
    response = glm_4v_plus_0111(messages)
"""

from openai import OpenAI
import os
from typing import List, Dict, Union, Optional
import base64

# Initialize the client
client = OpenAI(
    api_key=os.getenv("ZHIPUAI_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)


def _make_api_call(model: str, messages: List[Dict], stream: bool = False,
                   top_p: float = 0.7, temperature: float = 0.9, max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    Internal function to make the API call to GLM's model studio.

    Args:
        model: The model name to use
        messages: List of message dictionaries
        stream: Whether to stream the response
        top_p: Nucleus sampling parameter (0.0-1.0)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum number of tokens to generate

    Returns:
        The model's response content or the full response object if streaming
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            top_p=top_p,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if stream:
            return completion
        return completion.choices[0].message
    except Exception as e:
        raise Exception(f"API call failed: {str(e)}")


def encode_image_file(image_path: str) -> str:
    """
    Encode a local image file to base64.

    Args:
        image_path: Path to the local image file

    Returns:
        Base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def create_message_content(image_url: Optional[str] = None,
                           image_path: Optional[str] = None,
                           video_url: Optional[str] = None,
                           text: Optional[str] = None) -> List[Dict]:
    """
    Create properly formatted message content for GLM vision models.

    Args:
        image_url: URL of the image (remote)
        image_path: Path to local image file
        video_url: URL of the video (remote)
        text: Accompanying text prompt

    Returns:
        List of content items for the message

    Raises:
        ValueError: If neither image nor video is provided, or if both are provided
    """
    content = []

    if image_url and video_url:
        raise ValueError("Cannot provide both image and video in the same message")

    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    elif image_path:
        base64_image = encode_image_file(image_path)
        # Determine image format from file extension
        ext = image_path.split('.')[-1].lower()
        if ext not in ['png', 'jpeg', 'jpg']:
            raise ValueError("Unsupported image format. Use PNG or JPEG.")
        mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
        })
    elif video_url:
        content.append({
            "type": "video_url",
            "video_url": {"url": video_url}
        })

    if text:
        content.append({"type": "text", "text": text})

    return content


# GLM-4.1V-Thinking Model Functions
def glm_4v_thinking_flash(messages: List[Dict], stream: bool = False,
                          top_p: float = 0.7, temperature: float = 0.9,
                          max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    GLM-4.1V-Thinking-Flash model with strong visual reasoning capabilities.
    Free version with basic concurrency guarantees.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        top_p: Nucleus sampling parameter (0.0-1.0)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("glm-4.1v-thinking-flash", messages, stream,
                          top_p, temperature, max_tokens)


def glm_4v_thinking_flashx(messages: List[Dict], stream: bool = False,
                           top_p: float = 0.7, temperature: float = 0.9,
                           max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    GLM-4.1V-Thinking-FlashX model with strong visual reasoning capabilities.
    Supports high concurrency and faster response times.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        top_p: Nucleus sampling parameter (0.0-1.0)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("glm-4.1v-thinking-flashx", messages, stream,
                          top_p, temperature, max_tokens)


# GLM-4V Model Functions
def glm_4v_plus_0111(messages: List[Dict], stream: bool = False,
                     top_p: float = 0.7, temperature: float = 0.9,
                     max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    GLM-4V-Plus-0111 model with balanced visual reasoning capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        top_p: Nucleus sampling parameter (0.0-1.0)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("glm-4v-plus-0111", messages, stream,
                          top_p, temperature, max_tokens)


def glm_4v_flash(messages: List[Dict], stream: bool = False,
                 top_p: float = 0.7, temperature: float = 0.9,
                 max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    GLM-4V-Flash model optimized for faster response times.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        top_p: Nucleus sampling parameter (0.0-1.0)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("glm-4v-flash", messages, stream,
                          top_p, temperature, max_tokens)


def glm_4v(messages: List[Dict], stream: bool = False,
           top_p: float = 0.7, temperature: float = 0.9,
           max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    Base GLM-4V model with general visual understanding capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        top_p: Nucleus sampling parameter (0.0-1.0)
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("glm-4v", messages, stream,
                          top_p, temperature, max_tokens)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple image description
    example_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg"
                    }
                },
                {
                    "type": "text",
                    "text": "图中描绘的是什么景象？"
                }
            ]
        }
    ]

    print("GLM-4.1V-Thinking-Flash response:")
    print(glm_4v_thinking_flash(example_messages))

    # Example 2: Using local image file
    try:
        local_image_messages = [
            {
                "role": "user",
                "content": create_message_content(
                    image_path="path/to/your/local/image.jpg",
                    text="Describe this image"
                )
            }
        ]
        print("\nLocal image response:")
        print(glm_4v_plus_0111(local_image_messages))
    except Exception as e:
        print(f"Local image example failed: {str(e)}")

    # Example 3: Video understanding
    try:
        video_messages = [
            {
                "role": "user",
                "content": create_message_content(
                    video_url="https://example.com/video.mp4",
                    text="请仔细描述这个视频"
                )
            }
        ]
        print("\nVideo understanding response:")
        print(glm_4v_thinking_flashx(video_messages))
    except Exception as e:
        print(f"Video example failed: {str(e)}")