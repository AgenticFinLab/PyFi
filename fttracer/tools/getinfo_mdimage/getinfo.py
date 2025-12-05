import re
import csv
import os
from openai import OpenAI
from typing import List, Dict, Optional
from pathlib import Path

# 配置DeepSeek API
DEEPSEEK_API_KEY = ""  # 替换为你的API Key
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def read_markdown_file(file_path: str) -> str:
    """读取Markdown文件内容"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def split_text(text: str, chunk_size: int = 10000) -> List[str]:
    """将文本分割成指定大小的块"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


def extract_image_info(text: str) -> List[Dict[str, str]]:
    """从Markdown文本中提取图片信息"""
    # 匹配Markdown图片语法 ![](path)
    image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
    images = image_pattern.findall(text)

    # 获取每个图片附近的上下文
    image_info = []
    for i, image_path in enumerate(images):
        # 查找图片前后的内容
        start_pos = text.find(f'![]({image_path})')
        if start_pos == -1:
            continue

        # 获取图片前后的段落
        context_start = max(0, start_pos - 2000)
        context_end = min(len(text), start_pos + 2000)
        context = text[context_start:context_end]

        image_info.append({
            "No": i + 1,
            "Path": image_path,
            "Context": context
        })

    return image_info


def analyze_image_with_deepseek(book_name: str, image_info: Dict[str, str], text_chunk: str) -> Dict[str, str]:
    """使用DeepSeek API分析图片信息"""
    prompt = f"""
    你是一个专业的金融教科书内容分析助手。请根据提供的金融教科书内容和图片上下文信息，完成以下任务：

    图书名称: {book_name}
    图片路径: {image_info["Path"]}
    图片序号: {image_info["No"]}
    图片上下文: {image_info["Context"]}

    请提供以下信息:
    1. ChartTitle: 图片的标题或名称，一般出现在图的前后，如果有序号比如图x-x等则必须完整带上序号；
    2. Theme: 图片的主题，来源于章节标题，采用三级结构，例如xxxx-xxxx-xxxx；
    3. Content: 原文中关于这张图片的段落内容，必须完全是原文，且包含上文段落、提及图片的段落和下文段落，不要有任何其他新的文字信息；
    4. Note: 关于这张图片的简短分析，像专业金融分析师一样直接陈述分析内容；
    5. VLM_Instruction: 用于视觉理解模型训练的instruction提示词，介绍这张图的背景信息等，体现专业金融分析师的素养；
    6. VLM_QA: 用于评估视觉理解模型金融图像理解能力的问答对，可以是单选题、多选题或者判断题，格式为[{{"input":"","output":""}},{{"input":"","output":""}},...]的字符串，必须基于这张图和原文描述，且体现专业金融分析师的素养；
    7. Other_Info: 其他需要补充的信息。

    输出的语言要基于原文语言（原文是中文就输出中文，原文是英文就输出英文）。请严格以JSON格式返回结果，包含以下字段: ChartTitle, Theme, Content, Note, VLM_Instruction, VLM_QA, Other_Info
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional financial book content analyst."},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content
        return eval(result)
    except Exception as e:
        print(f"Error analyzing image {image_info['No']}: {str(e)}")
        return {
            "ChartTitle": "",
            "Theme": "",
            "Content": image_info["Context"],
            "Note": "",
            "VLM_Instruction": "",
            "VLM_QA": "[]",
            "Other_Info": f"Error: {str(e)}"
        }


def process_markdown_file(md_file_path: str, book_name: str, output_csv: str):
    """处理Markdown文件并生成CSV"""
    # 读取Markdown文件
    md_content = read_markdown_file(md_file_path)

    # 分割文本以适应上下文长度限制
    text_chunks = split_text(md_content)

    # 提取所有图片信息
    all_image_info = extract_image_info(md_content)

    # 准备CSV文件
    csv_header = [
        "No", "Book_Name", "ChartTitle", "Path",
        "Theme", "Content", "Note",
        "VLM_Instruction", "VLM_QA", "Other_Info"
    ]

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_header)
        writer.writeheader()

        # 处理每张图片
        for image_info in all_image_info:
            # 使用DeepSeek分析图片信息
            analysis = analyze_image_with_deepseek(book_name, image_info, md_content)

            # 准备CSV行数据
            row = {
                "No": image_info["No"],
                "Book_Name": book_name,
                "ChartTitle": analysis.get("ChartTitle", ""),
                "Path": image_info["Path"],
                "Theme": analysis.get("Theme", ""),
                "Content": analysis.get("Content", ""),
                "Note": analysis.get("Note", ""),
                "VLM_Instruction": analysis.get("VLM_Instruction", ""),
                "VLM_QA": analysis.get("VLM_QA", "[]"),
                "Other_Info": analysis.get("Other_Info", "")
            }

            writer.writerow(row)
            print(f"Processed image {image_info['No']}/{len(all_image_info)}")


def main():
    # 用户输入
    md_file_path = input("请输入Markdown文件路径: ")
    if(md_file_path.startswith("\"") and md_file_path.endswith("\"")):
        md_file_path=md_file_path[1:-1]

    print(md_file_path)
    book_name = input("请输入书名: ")
    output_csv = input("请输入输出CSV文件路径(默认为output.csv): ") or "output.csv"

    # 处理文件
    process_markdown_file(md_file_path, book_name, output_csv)
    print(f"处理完成，结果已保存到 {output_csv}")


if __name__ == "__main__":
    main()