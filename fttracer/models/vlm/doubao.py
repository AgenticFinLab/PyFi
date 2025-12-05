
#模型列表 https://www.volcengine.com/docs/82379/1330310
#快速入门 https://www.volcengine.com/docs/82379/1399008
#教程 https://www.volcengine.com/docs/82379/1362931


"""
Volcengine Doubao API Wrapper

This module provides a Python interface to Volcengine's Doubao vision models,
including Seed series and Vision Pro models. It's designed for easy integration
and modular usage.

Features:
- Support for all Doubao model variants
- Proper parameterization for all API options
- Consistent naming conventions
- Comprehensive error handling
- Detailed docstrings for each function

Usage:
    from doubao import doubao_seed_1_6

    messages = [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
            {"type": "text", "text": "Describe this image"}
        ]}
    ]
    response = doubao_seed_1_6(messages)
"""

import os
from openai import OpenAI
from typing import List, Dict, Union, Optional
import base64

# Initialize the client
client = OpenAI(
    api_key=os.getenv("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)



def _make_api_call(model: str, messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Internal function to make the API call to Volcengine's Doubao models.

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


# Seed 1.6 Model Series
def doubao_seed_1_6(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Doubao Seed 1.6 model with general visual understanding capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("doubao-seed-1-6-250615", messages, stream)


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


def doubao_seed_1_6_thinking(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Doubao Seed 1.6 Thinking model with enhanced reasoning capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("doubao-seed-1-6-thinking-250715", messages, stream)


# Vision Pro Model
def doubao_1_5_thinking_vision_pro(messages: List[Dict], stream: bool = False) -> Union[str, Dict]:
    """
    Doubao 1.5 Thinking Vision Pro model with advanced visual processing.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response

    Returns:
        Model response content or stream object
    """
    return _make_api_call("doubao-1-5-thinking-vision-pro-250428", messages, stream)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple image description
    # example_messages = [
    #     {
    #         "role": "user",
    #         "content": [
    #             {
    #                 "type": "image_url",
    #                 "image_url": {
    #                     "url": "https://ark-project.tos-cn-beijing.ivolces.com/images/view.jpeg"
    #                 },
    #             },
    #             {"type": "text", "text": "这是哪里？"},
    #         ],
    #     }
    # ]
    #
    # print("Doubao Seed 1.6 response:")
    # print(doubao_seed_1_6(example_messages))

    # Example 2: Using local image file
    try:
        import time

        local_image_messages = [
            {"role": "user", "content": create_message_content(
                image_path=r"D:\Documents\GitHub\AgenticFinLab\fttracer\fttracer\images\000001.png",
                text="请描述这张图的信息！"
            )}
        ]
        print("\nLocal image response:")

        start=time.time()
        info=doubao_seed_1_6_flash(local_image_messages)
        print(type(info))
        print(info)
        end=time.time()

        print(f"{end-start}s")

    except Exception as e:
        print(f"Local image example failed: {str(e)}")
