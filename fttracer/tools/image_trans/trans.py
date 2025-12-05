from PIL import Image
import os


def png_to_jpg(input_path, output_path=None, quality=95):
    """
    将PNG图片转换为JPG格式

    参数:
        input_path (str): 输入的PNG图片路径
        output_path (str): 输出的JPG图片路径(可选)
        quality (int): 输出图片质量(1-100)，默认95
    """
    try:
        # 打开PNG图片
        img = Image.open(input_path)

        # 如果图片有透明通道(alpha)，创建一个白色背景
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])  # 使用alpha通道作为mask
            img = background

        # 设置输出路径(如果未提供)
        if output_path is None:
            base_path = os.path.splitext(input_path)[0]
            output_path = f"{base_path}.jpg"

        # 保存为JPG
        img.convert('RGB').save(output_path, 'JPEG', quality=quality)
        print(f"转换成功: {input_path} -> {output_path}")

    except Exception as e:
        print(f"转换失败: {e}")


# 使用示例
if __name__ == "__main__":
    input_image = r"D:\Documents\GitHub\AgenticFinLab\fttracer\fttracer\images\000001.png"  # 替换为你的PNG文件路径
    output_image = r"D:\Documents\GitHub\AgenticFinLab\fttracer\fttracer\images\000001.jpg"  # 可选，如果不指定则自动生成

    png_to_jpg(input_image, output_image)