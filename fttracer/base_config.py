import os
from pathlib import Path


class Config:
    # 基础路径
    BASE_DIR = Path(__file__).parent
    OUTPUT_DIR = BASE_DIR / "output"

    # 子目录
    ERROR_DIR = OUTPUT_DIR / "error"
    TREE_DIR = OUTPUT_DIR / "tree"
    IMAGE_FQ_DIR = OUTPUT_DIR / "image_fq"

    # 模型参数
    MAX_NODE_NUM = 100
    CONTEXT_WINDOW = 300
    DEFAULT_FQ_COUNT = 5

    # 初始化目录
    @classmethod
    def init_dirs(cls):
        dirs = [cls.OUTPUT_DIR, cls.ERROR_DIR, cls.TREE_DIR, cls.IMAGE_FQ_DIR]
        for d in dirs:
            os.makedirs(d, exist_ok=True)


# 初始化配置
Config.init_dirs()