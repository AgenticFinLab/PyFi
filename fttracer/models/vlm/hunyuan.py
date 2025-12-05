# webpage: https://cloud.tencent.com/document/product/1729/104753

"""
Tencent Hunyuan Vision API Wrapper

This module provides a Python interface to Tencent's Hunyuan vision models.
It's designed for easy integration and modular usage.

Features:
- Support for all Hunyuan vision model variants
- Proper parameterization for all API options
- Consistent naming conventions
- Comprehensive error handling
- Detailed docstrings for each function

Usage:
    from hunyuan_vision import hunyuan_large_vision

    messages = [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
            {"type": "text", "text": "Describe this image"}
        ]}
    ]
    response = hunyuan_large_vision(messages)
"""

from openai import OpenAI
import os
from typing import List, Dict, Union, Optional
import base64

# Initialize the client
client = OpenAI(
    api_key=os.getenv("HUNYUAN_API_KEY"),
    base_url="https://api.hunyuan.cloud.tencent.com/v1"
)


def _make_api_call(model: str, messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Internal function to make the API call to Tencent's Hunyuan model studio.

    Args:
        model: The model name to use
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        The model's response content or the full response object if streaming
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream
        )

        if stream:
            return completion
        return completion.choices[0].message.content
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
                          text: Optional[str] = None) -> List[Dict]:
    """
    Create properly formatted message content for vision models.

    Args:
        image_url: URL of the image (remote)
        image_path: Path to local image file
        text: Accompanying text prompt

    Returns:
        List of content items for the message
    """
    content = []

    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    elif image_path:
        base64_image = encode_image_file(image_path)
        # Determine image format from file extension
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


# Hunyuan Vision Model Functions
def hunyuan_vision(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Standard Hunyuan vision model with general visual understanding capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("hunyuan-vision", messages, stream)


def hunyuan_t1_vision(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Hunyuan T1 vision model with enhanced visual capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("hunyuan-t1-vision", messages, stream)


def hunyuan_t1_vision_20250619(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Hunyuan T1 vision model snapshot from 2025-06-19.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("hunyuan-t1-vision-20250619", messages, stream)


def hunyuan_turbos_vision(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Hunyuan Turbo vision model optimized for speed and efficiency.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("hunyuan-turbos-vision", messages, stream)


def hunyuan_large_vision(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Large-scale Hunyuan vision model with advanced visual understanding.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("hunyuan-large-vision", messages, stream)


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
                        "url": "https://qcloudimg.tencent-cloud.cn/raw/42c198dbc0b57ae490e57f89aa01ec23.png"
                    }
                },
                {"type": "text", "text": "图中描绘的是什么景象？"},
            ],
        }
    ]

    print("Hunyuan Large Vision response:")
    print(hunyuan_large_vision(example_messages))

    # Example 2: Using local image file
    try:
        local_image_messages = [
            {"role": "user", "content": create_message_content(
                image_path="path/to/your/local/image.jpg",
                text="Describe this image"
            )}
        ]
        print("\nLocal image response:")
        print(hunyuan_t1_vision(local_image_messages))
    except Exception as e:
        print(f"Local image example failed: {str(e)}")