import os
import re
import shutil


def process_markdown_images(md_file_path, output_dir='images_copy'):
    """
    处理Markdown文件中的图片引用，按顺序重命名图片并保存到指定目录

    :param md_file_path: Markdown文件路径
    :param output_dir: 输出目录，默认为'images_copy'
    """
    # 获取Markdown文件所在目录
    md_dir = os.path.dirname(md_file_path)

    # 创建输出目录
    output_path = os.path.join(md_dir, output_dir)
    os.makedirs(output_path, exist_ok=True)

    # 读取Markdown文件内容
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配图片引用格式 ![](images/xxx.jpg)
    pattern = r'!\[\]\((images/[^)]+)\)'
    matches = re.findall(pattern, content)

    if not matches:
        print("未找到图片引用")
        return

    print(f"共找到 {len(matches)} 张图片引用")

    # 初始化计数器
    counter = 1

    # 处理每张图片
    for img_rel_path in matches:
        # 原始图片路径（相对于Markdown文件所在目录）
        original_path = os.path.join(md_dir, img_rel_path)

        if not os.path.exists(original_path):
            print(f"警告: 图片文件不存在 - {original_path}")
            continue

        # 生成新文件名
        ext = os.path.splitext(original_path)[1]
        new_filename = f"{counter:06d}{ext}"
        new_path = os.path.join(output_path, new_filename)

        # 复制并重命名文件
        shutil.copy2(original_path, new_path)
        print(f"已复制: {original_path} -> {new_path}")

        # 更新Markdown内容中的图片引用
        new_img_ref = f"![]({output_dir}/{new_filename})"
        content = content.replace(f"![]({img_rel_path})", new_img_ref)

        counter += 1

    # 保存修改后的Markdown文件
    new_md_path = os.path.join(md_dir, os.path.splitext(os.path.basename(md_file_path))[0] + '_processed.md')
    with open(new_md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"处理完成! 修改后的Markdown文件已保存为: {new_md_path}")


# 使用示例
if __name__ == '__main__':
    md_file = input("请输入Markdown文件路径: ")
    if md_file.startswith("\"") and md_file.endswith("\""):
        md_file=md_file[1:-1]
    process_markdown_images(md_file)