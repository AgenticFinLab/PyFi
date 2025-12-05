# webpage: https://help.aliyun.com/zh/model-studio/vision?spm=a2c4g.11186623.0.0.78d84823eude4r#d987f8de5395x

"""
Aliyun Model Studio Vision API Wrapper

This module provides a Python interface to Aliyun's Model Studio vision models,
including Qwen-VL series and QVQ series models. It's designed for easy integration
and modular usage.

Features:
- Support for all Qwen-VL and QVQ model variants
- Proper parameterization for all API options
- Consistent naming conventions
- Comprehensive error handling
- Detailed docstrings for each function

Usage:
    from aliyun_vision import qwen_vl_max_latest

    messages = [
        {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
            {"type": "text", "text": "Describe this image"}
        ]}
    ]
    response = qwen_vl_max_latest(messages)
"""

from openai import OpenAI
import os
from typing import List, Dict, Union, Optional
import base64

# Initialize the client
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def _make_api_call(model: str, messages: List[Dict], stream: bool = False,
                   vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Internal function to make the API call to Aliyun's model studio.

    Args:
        model: The model name to use
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Whether to enable high resolution image processing

    Returns:
        The model's response content or the full response object if streaming
    """
    try:
        if vl_high_resolution_images:
            import dashscope
            response = dashscope.MultiModalConversation.call(
                api_key=os.getenv('DASHSCOPE_API_KEY'),
                model=model,
                messages=messages,
                vl_high_resolution_images=True
            )
            return response.output.choices[0].message.content[0]["text"]
        else:
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


# Qwen-VL Model Functions
def qwen_vl_max(messages: List[Dict], stream: bool = False,
                vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Max model with general visual understanding capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-max", messages, stream, vl_high_resolution_images)


def qwen_vl_max_latest(messages: List[Dict], stream: bool = False,
                       vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Latest version of Qwen-VL Max model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-max-latest", messages, stream, vl_high_resolution_images)


def qwen_vl_max_2025_04_02(messages: List[Dict], stream: bool = False,
                           vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Max model snapshot from 2025-04-02.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-max-2025-04-02", messages, stream, vl_high_resolution_images)


def qwen_vl_max_2025_01_25(messages: List[Dict], stream: bool = False,
                           vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Max model snapshot from 2025-01-25.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-max-2025-01-25", messages, stream, vl_high_resolution_images)


def qwen_vl_max_2024_12_30(messages: List[Dict], stream: bool = False,
                           vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Max model snapshot from 2024-12-30.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-max-2024-12-30", messages, stream, vl_high_resolution_images)


def qwen_vl_max_2024_10_30(messages: List[Dict], stream: bool = False,
                           vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Max model snapshot from 2024-10-30.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-max-2024-10-30", messages, stream, vl_high_resolution_images)


def qwen_vl_max_2024_08_09(messages: List[Dict], stream: bool = False,
                           vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Max model snapshot from 2024-08-09.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-max-2024-08-09", messages, stream, vl_high_resolution_images)


def qwen_vl_plus(messages: List[Dict], stream: bool = False,
                 vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Plus model with balanced performance and cost.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-plus", messages, stream, vl_high_resolution_images)


def qwen_vl_plus_latest(messages: List[Dict], stream: bool = False,
                        vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Latest version of Qwen-VL Plus model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-plus-latest", messages, stream, vl_high_resolution_images)


def qwen_vl_plus_2025_05_07(messages: List[Dict], stream: bool = False,
                            vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Plus model snapshot from 2025-05-07.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-plus-2025-05-07", messages, stream, vl_high_resolution_images)


def qwen_vl_plus_2025_01_25(messages: List[Dict], stream: bool = False,
                            vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Plus model snapshot from 2025-01-25.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-plus-2025-01-25", messages, stream, vl_high_resolution_images)


def qwen_vl_plus_2025_01_02(messages: List[Dict], stream: bool = False,
                            vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Plus model snapshot from 2025-01-02.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-plus-2025-01-02", messages, stream, vl_high_resolution_images)


def qwen_vl_plus_2024_08_09(messages: List[Dict], stream: bool = False,
                            vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Qwen-VL Plus model snapshot from 2024-08-09.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen-vl-plus-2024-08-09", messages, stream, vl_high_resolution_images)


# QVQ Model Functions
def qvq_max(messages: List[Dict], stream: bool = False,
            vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    QVQ Max model with strong visual reasoning capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qvq-max", messages, stream, vl_high_resolution_images)


def qvq_max_latest(messages: List[Dict], stream: bool = False,
                   vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Latest version of QVQ Max model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qvq-max-latest", messages, stream, vl_high_resolution_images)


def qvq_max_2025_05_15(messages: List[Dict], stream: bool = False,
                       vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    QVQ Max model snapshot from 2025-05-15.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qvq-max-2025-05-15", messages, stream, vl_high_resolution_images)


def qvq_max_2025_03_25(messages: List[Dict], stream: bool = False,
                       vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    QVQ Max model snapshot from 2025-03-25.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qvq-max-2025-03-25", messages, stream, vl_high_resolution_images)


def qvq_plus(messages: List[Dict], stream: bool = False,
             vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    QVQ Plus model with balanced visual reasoning capabilities.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qvq-plus", messages, stream, vl_high_resolution_images)


def qvq_plus_latest(messages: List[Dict], stream: bool = False,
                    vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    Latest version of QVQ Plus model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qvq-plus-latest", messages, stream, vl_high_resolution_images)


def qvq_plus_2025_05_15(messages: List[Dict], stream: bool = False,
                        vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    QVQ Plus model snapshot from 2025-05-15.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qvq-plus-2025-05-15", messages, stream, vl_high_resolution_images)


# Qwen2.5-VL Open Source Model Functions
def qwen2_5_vl_72b_instruct(messages: List[Dict], stream: bool = False,
                            vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    72B parameter version of Qwen2.5-VL open source model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen2.5-vl-72b-instruct", messages, stream, vl_high_resolution_images)


def qwen2_5_vl_32b_instruct(messages: List[Dict], stream: bool = False,
                            vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    32B parameter version of Qwen2.5-VL open source model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen2.5-vl-32b-instruct", messages, stream, vl_high_resolution_images)


def qwen2_5_vl_7b_instruct(messages: List[Dict], stream: bool = False,
                           vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    7B parameter version of Qwen2.5-VL open source model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen2.5-vl-7b-instruct", messages, stream, vl_high_resolution_images)


def qwen2_5_vl_3b_instruct(messages: List[Dict], stream: bool = False,
                           vl_high_resolution_images: bool = False) -> Union[str, Dict]:
    """
    3B parameter version of Qwen2.5-VL open source model.

    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        vl_high_resolution_images: Enable high resolution image processing

    Returns:
        Model response content or stream object
    """
    return _make_api_call("qwen2.5-vl-3b-instruct", messages, stream, vl_high_resolution_images)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple image description
    example_messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant."}]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"
                    },
                },
                {"type": "text", "text": "图中描绘的是什么景象？"},
            ],
        }
    ]

    print("Qwen-VL Max Latest response:")
    print(qwen_vl_max_latest(example_messages))

    # Example 2: Using local image file
    try:
        local_image_messages = [
            {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {"role": "user", "content": create_message_content(
                image_path=r"D:\Documents\GitHub\AgenticFinLab\fttracer\fttracer\images\000001.png",
                text="Describe this image"
            )}
        ]
        print("\nLocal image response:")
        print(qwen_vl_plus(local_image_messages))
    except Exception as e:
        print(f"Local image example failed: {str(e)}")

# assistant_message = completion.choices[0].message
# messages.append(assistant_message.model_dump())
# messages.append({
#         "role": "user",
#         "content": [
#         {
#             "type": "text",
#             "text": "做一首诗描述这个场景"
#         }
#         ]
#     })
# completion = client.chat.completions.create(
#     model="qwen-vl-max-latest",
#     messages=messages,
#     )




"""

# 多图像输入

import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-vl-max-latest", # 此处以qwen-vl-max-latest为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
    messages=[
       {"role":"system","content":[{"type": "text", "text": "You are a helpful assistant."}]},
       {"role": "user","content": [
           # 第一张图像url，如果传入本地文件，请将url的值替换为图像的Base64编码格式
           {"type": "image_url","image_url": {"url": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},},
           # 第二张图像url，如果传入本地文件，请将url的值替换为图像的Base64编码格式
           {"type": "image_url","image_url": {"url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/tiger.png"},},
           {"type": "text", "text": "这些图描绘了什么内容？"},
            ],
        }
    ],
    stream=True
)

print(completion.choices[0].message.content)


# 高分辨率图像理解

import os
import dashscope

messages = [
    {
        "role": "user",
        "content": [
            {"image": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250212/earbrt/vcg_VCG211286867973_RF.jpg"},
            {"text": "这张图表现了什么内容?"}
        ]
    }
]

response = dashscope.MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    model='qwen-vl-max-latest',  # 此处以qwen-vl-max-latest为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
    messages=messages,
    vl_high_resolution_images=True
)

print("大模型的回复:\n ",response.output.choices[0].message.content[0]["text"])
print("Token用量情况：","输入总Token：",response.usage["input_tokens"] , "，输入图像Token：" , response.usage["image_tokens"])



# 多图像输入

import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-vl-max-latest", # 此处以qwen-vl-max-latest为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
    messages=[
       {"role":"system","content":[{"type": "text", "text": "You are a helpful assistant."}]},
       {"role": "user","content": [
           # 第一张图像url，如果传入本地文件，请将url的值替换为图像的Base64编码格式
           {"type": "image_url","image_url": {"url": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"},},
           # 第二张图像url，如果传入本地文件，请将url的值替换为图像的Base64编码格式
           {"type": "image_url","image_url": {"url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/tiger.png"},},
           {"type": "text", "text": "这些图描绘了什么内容？"},
            ],
        }
    ],
)
print(completion.choices[0].message.content)



# 传入本地文件

from openai import OpenAI
import os
import base64

#  base 64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# 将xxxx/eagle.png替换为你本地图像的绝对路径
base64_image = encode_image("xxx/eagle.png")

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-vl-max-latest", # 此处以qwen-vl-max-latest为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
    messages=[
    	{
    	    "role": "system",
            "content": [{"type":"text","text": "You are a helpful assistant."}]},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    # 需要注意，传入Base64，图像格式（即image/{format}）需要与支持的图片列表中的Content Type保持一致。"f"是字符串格式化的方法。
                    # PNG图像：  f"data:image/png;base64,{base64_image}"
                    # JPEG图像： f"data:image/jpeg;base64,{base64_image}"
                    # WEBP图像： f"data:image/webp;base64,{base64_image}"
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}, 
                },
                {"type": "text", "text": "图中描绘的是什么景象?"},
            ],
        }
    ],
)
print(completion.choices[0].message.content)

"""