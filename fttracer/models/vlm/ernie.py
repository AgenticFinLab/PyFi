"""
Aliyun Qianfan Vision API Wrapper

This module provides a Python interface to Baidu's Qianfan vision models,
including ERNIE series and other vision models. It's designed for easy integration
and modular usage.

Features:
- Support for all Qianfan vision model variants
- Proper parameterization for all API options
- Consistent naming conventions
- Comprehensive error handling
- Detailed docstrings for each function

Usage:
    from aliyun_vision import ernie_4_5_turbo_vl_preview

    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": "分别使用1句话描述以下3张图片的内容"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image1.jpg"}},
            {"type": "image_url", "image_url": {"url": "https://example.com/image2.jpg"}},
            {"type": "image_url", "image_url": {"url": "https://example.com/image3.jpg"}}
        ]}
    ]
    response = ernie_4_5_turbo_vl_preview(messages)
"""

import os
import json
import base64
import requests
from typing import List, Dict, Union, Optional

# Base API configuration
QIANFAN_API_BASE = "https://qianfan.baidubce.com/v2/chat/completions"


def _make_api_call(model: str, messages: List[Dict], stream: bool = False,
                   temperature: Optional[float] = None, top_p: Optional[float] = None,
                   penalty_score: Optional[float] = None, max_tokens: Optional[int] = None,
                   enable_thinking: Optional[bool] = None, seed: Optional[int] = None,
                   stop: Optional[List[str]] = None, user: Optional[str] = None,
                   web_search: Optional[Dict] = None, response_format: Optional[Dict] = None,
                   metadata: Optional[Dict] = None, detail: Optional[str] = None) -> Union[str, Dict]:
    """
    Internal function to make the API call to Qianfan's model studio.

    Args:
        model: The model name to use
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        penalty_score: Penalty for repeated tokens (1.0-2.0)
        max_tokens: Maximum number of tokens to generate
        enable_thinking: Whether to enable deep thinking mode
        seed: Random seed for deterministic sampling
        stop: List of stop sequences
        user: User identifier for tracking
        web_search: Web search enhancement options
        response_format: Format of the response
        metadata: Additional metadata
        detail: Image processing detail level ('low', 'high', 'auto')

    Returns:
        The model's response content or the full response object if streaming
    """
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("QIANFAN_API_KEY")}'
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }

    # Add optional parameters if provided
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if penalty_score is not None:
        payload["penalty_score"] = penalty_score
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if enable_thinking is not None:
        payload["enable_thinking"] = enable_thinking
    if seed is not None:
        payload["seed"] = seed
    if stop is not None:
        payload["stop"] = stop
    if user is not None:
        payload["user"] = user
    if web_search is not None:
        payload["web_search"] = web_search
    if response_format is not None:
        payload["response_format"] = response_format
    if metadata is not None:
        payload["metadata"] = metadata

    # Handle image detail parameter
    if detail is not None:
        for message in messages:
            if "content" in message:
                for content in message["content"]:
                    if content.get("type") == "image_url" and "image_url" in content:
                        content["image_url"]["detail"] = detail

    try:
        response = requests.post(QIANFAN_API_BASE, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
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
                           text: Optional[str] = None,
                           detail: Optional[str] = None) -> List[Dict]:
    """
    Create properly formatted message content for vision models.

    Args:
        image_url: URL of the image (remote)
        image_path: Path to local image file
        text: Accompanying text prompt
        detail: Image processing detail level ('low', 'high', 'auto')

    Returns:
        List of content items for the message
    """
    content = []

    if image_url:
        image_content = {
            "type": "image_url",
            "image_url": {"url": image_url}
        }
        if detail:
            image_content["image_url"]["detail"] = detail
        content.append(image_content)
    elif image_path:
        base64_image = encode_image_file(image_path)
        # Determine image format from file extension
        ext = image_path.split('.')[-1].lower()
        if ext not in ['png', 'jpeg', 'jpg', 'bmp']:
            raise ValueError("Unsupported image format. Use PNG, JPEG, or BMP.")
        mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
        }
        if detail:
            image_content["image_url"]["detail"] = detail
        content.append(image_content)

    if text:
        content.append({"type": "text", "text": text})

    return content


# ERNIE Model Functions
def ernie_4_5_turbo_vl_preview(messages: List[Dict], stream: bool = False,
                               temperature: Optional[float] = None, top_p: Optional[float] = None,
                               max_tokens: Optional[int] = None, detail: Optional[str] = None) -> Union[str, Dict]:
    """
    ERNIE 4.5 Turbo VL Preview model with visual understanding capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate
        detail: Image processing detail level ('low', 'high', 'auto')

    Returns:
        Model response content or stream object
    """
    return _make_api_call("ernie-4.5-turbo-vl-preview", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens,
                          detail=detail)


def ernie_4_5_turbo_vl_32k(messages: List[Dict], stream: bool = False,
                           temperature: Optional[float] = None, top_p: Optional[float] = None,
                           max_tokens: Optional[int] = None, detail: Optional[str] = None) -> Union[str, Dict]:
    """
    ERNIE 4.5 Turbo VL 32K model with extended context window.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate
        detail: Image processing detail level ('low', 'high', 'auto')

    Returns:
        Model response content or stream object
    """
    return _make_api_call("ernie-4.5-turbo-vl-32k", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens,
                          detail=detail)


def ernie_4_5_turbo_vl_32k_preview(messages: List[Dict], stream: bool = False,
                                   temperature: Optional[float] = None, top_p: Optional[float] = None,
                                   max_tokens: Optional[int] = None, detail: Optional[str] = None) -> Union[str, Dict]:
    """
    ERNIE 4.5 Turbo VL 32K Preview model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate
        detail: Image processing detail level ('low', 'high', 'auto')

    Returns:
        Model response content or stream object
    """
    return _make_api_call("ernie-4.5-turbo-vl-32k-preview", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens,
                          detail=detail)


def ernie_4_5_8k_preview(messages: List[Dict], stream: bool = False,
                         temperature: Optional[float] = None, top_p: Optional[float] = None,
                         max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    ERNIE 4.5 8K Preview model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("ernie-4.5-8k-preview", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def ernie_4_5_vl_28b_a3b(messages: List[Dict], stream: bool = False,
                         temperature: Optional[float] = None, top_p: Optional[float] = None,
                         max_tokens: Optional[int] = None, enable_thinking: Optional[bool] = None) -> Union[str, Dict]:
    """
    ERNIE 4.5 VL 28B A3B model with deep thinking capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate
        enable_thinking: Whether to enable deep thinking mode

    Returns:
        Model response content or stream object
    """
    return _make_api_call("ernie-4.5-vl-28b-a3b", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens,
                          enable_thinking=enable_thinking)


# Other Vision Models
def internvl3_38b(messages: List[Dict], stream: bool = False,
                  temperature: Optional[float] = None, top_p: Optional[float] = None,
                  max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    InternVL3 38B model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("internvl3-38b", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def internvl3_14b(messages: List[Dict], stream: bool = False,
                  temperature: Optional[float] = None, top_p: Optional[float] = None,
                  max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    InternVL3 14B model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("internvl3-14b", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def internvl3_1b(messages: List[Dict], stream: bool = False,
                 temperature: Optional[float] = None, top_p: Optional[float] = None,
                 max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    InternVL3 1B model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("internvl3-1b", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def internvl2_5_38b_mpo(messages: List[Dict], stream: bool = False,
                        temperature: Optional[float] = None, top_p: Optional[float] = None,
                        max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    InternVL2.5 38B MPO model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("internvl2.5-38b-mpo", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def qwen2_5_vl_32b_instruct(messages: List[Dict], stream: bool = False,
                            temperature: Optional[float] = None, top_p: Optional[float] = None,
                            max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    Qwen2.5 VL 32B Instruct model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen2.5-vl-32b-instruct", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def qwen2_5_vl_7b_instruct(messages: List[Dict], stream: bool = False,
                           temperature: Optional[float] = None, top_p: Optional[float] = None,
                           max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    Qwen2.5 VL 7B Instruct model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen2.5-vl-7b-instruct", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def deepseek_vl2(messages: List[Dict], stream: bool = False,
                 temperature: Optional[float] = None, top_p: Optional[float] = None,
                 max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    DeepSeek VL2 model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("deepseek-vl2", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


def deepseek_vl2_small(messages: List[Dict], stream: bool = False,
                       temperature: Optional[float] = None, top_p: Optional[float] = None,
                       max_tokens: Optional[int] = None) -> Union[str, Dict]:
    """
    DeepSeek VL2 Small model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        temperature: Controls randomness (higher = more random)
        top_p: Controls diversity via nucleus sampling
        max_tokens: Maximum number of tokens to generate

    Returns:
        Model response content or stream object
    """
    return _make_api_call("deepseek-vl2-small", messages, stream,
                          temperature=temperature, top_p=top_p, max_tokens=max_tokens)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple image description
    example_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "分别使用1句话描述以下3张图片的内容"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://qcloudimg.tencent-cloud.cn/raw/42c198dbc0b57ae490e57f89aa01ec23.png"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://qcloudimg.tencent-cloud.cn/raw/42c198dbc0b57ae490e57f89aa01ec23.png"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://qcloudimg.tencent-cloud.cn/raw/42c198dbc0b57ae490e57f89aa01ec23.png"
                    }
                }
            ]
        }
    ]

    print("ERNIE 4.5 Turbo VL Preview response:")
    print(ernie_4_5_turbo_vl_preview(example_messages))

    # Example 2: Using local image file with detail setting
    try:
        local_image_messages = [
            {"role": "user", "content": create_message_content(
                image_path=r"C:\Users\XT\Pictures\1659492198(1).jpg",
                text="Describe this image in detail",
                detail="high"
            )}
        ]
        print("\nLocal image with high detail response:")
        print(ernie_4_5_turbo_vl_32k(local_image_messages))
    except Exception as e:
        print(f"Local image example failed: {str(e)}")