"""
Moonshot AI Vision API Wrapper

This module provides a Python interface to Moonshot AI's vision models,
including the moonshot-v1 series and Kimi models. It's designed for easy integration
and modular usage.

Features:
- Support for all Moonshot vision model variants
- Proper parameterization for all API options
- Consistent naming conventions
- Comprehensive error handling
- Detailed docstrings for each function

Usage:
    from moonshot_vision import moonshot_v1_8k_vision_preview

    messages = [
        {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
            {"type": "text", "text": "Describe this image"}
        ]}
    ]
    response = moonshot_v1_8k_vision_preview(messages)
"""

import os
import base64
from typing import List, Dict, Union, Optional
from openai import OpenAI

# Initialize the client
client = OpenAI(
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1"
)


def _make_api_call(model: str, messages: List[Dict], stream: bool = False,
                  temperature: float = 0.3) -> Union[str, Dict]:
    """
    Internal function to make the API call to Moonshot AI's model studio.

    Args:
        model: The model name to use
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Sampling temperature (0-1)

    Returns:
        The model's response content or the full response object if streaming
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            temperature=temperature
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
        Base64 encoded string of the image with proper MIME type
    """
    with open(image_path, "rb") as image_file:
        # Determine image format from file extension
        ext = image_path.split('.')[-1].lower()
        if ext not in ['png', 'jpeg', 'jpg', 'webp']:
            raise ValueError("Unsupported image format. Use PNG, JPEG, or WEBP.")
        mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
        return f"data:{mime_type};base64,{base64.b64encode(image_file.read()).decode('utf-8')}"


def create_message_content(image_url: Optional[str] = None,
                          image_path: Optional[str] = None,
                          text: Optional[str] = None) -> List[Dict]:
    """
    Create properly formatted message content for vision models.

    Args:
        image_url: URL of the image (remote) - currently not supported by Moonshot
        image_path: Path to local image file
        text: Accompanying text prompt

    Returns:
        List of content items for the message

    Note: Moonshot currently only supports base64 encoded images, not URLs
    """
    content = []

    if image_url:
        raise ValueError("Moonshot Vision models currently only support base64 encoded images, not URLs")
    elif image_path:
        base64_image = encode_image_file(image_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": base64_image}
        })

    if text:
        content.append({"type": "text", "text": text})

    return content


# Moonshot Vision Model Functions
def moonshot_v1_8k_vision_preview(messages: List[Dict], stream: bool = False,
                                 temperature: float = 0.3) -> Union[str, Dict]:
    """
    Moonshot v1 8k context vision preview model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Sampling temperature (0-1)

    Returns:
        Model response content or stream object
    """
    return _make_api_call("moonshot-v1-8k-vision-preview", messages, stream, temperature)


def moonshot_v1_32k_vision_preview(messages: List[Dict], stream: bool = False,
                                  temperature: float = 0.3) -> Union[str, Dict]:
    """
    Moonshot v1 32k context vision preview model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Sampling temperature (0-1)

    Returns:
        Model response content or stream object
    """
    return _make_api_call("moonshot-v1-32k-vision-preview", messages, stream, temperature)


def moonshot_v1_128k_vision_preview(messages: List[Dict], stream: bool = False,
                                   temperature: float = 0.3) -> Union[str, Dict]:
    """
    Moonshot v1 128k context vision preview model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Sampling temperature (0-1)

    Returns:
        Model response content or stream object
    """
    return _make_api_call("moonshot-v1-128k-vision-preview", messages, stream, temperature)


# Kimi Model Functions
def kimi_latest(messages: List[Dict], stream: bool = False,
               temperature: float = 0.3) -> Union[str, Dict]:
    """
    Latest version of Kimi model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Sampling temperature (0-1)

    Returns:
        Model response content or stream object
    """
    return _make_api_call("kimi-latest", messages, stream, temperature)


def kimi_thinking_preview(messages: List[Dict], stream: bool = False,
                         temperature: float = 0.3) -> Union[str, Dict]:
    """
    Kimi thinking preview model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Sampling temperature (0-1)

    Returns:
        Model response content or stream object
    """
    return _make_api_call("kimi-thinking-preview", messages, stream, temperature)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple image description
    try:
        example_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": create_message_content(
                    image_path=r"C:\Users\XT\Pictures\paperbackground.jpeg",
                    text="请描述这个图片"
                )
            }
        ]

        print("Moonshot 8k Vision Preview response:")
        print(moonshot_v1_8k_vision_preview(example_messages))

        # Example 2: Streaming response
        print("\nStreaming response example:")
        stream = moonshot_v1_32k_vision_preview(example_messages, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="")

    except Exception as e:
        print(f"Example failed: {str(e)}")