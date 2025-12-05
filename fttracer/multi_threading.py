import concurrent.futures
import logging
from typing import List
from mcts.gqa import ImageQASystem
from config import Config
from mcts.utils import ensure_dir


class BatchProcessor:
    def __init__(self, max_workers: int = 4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers)
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger("BatchProcessor")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(Config.OUTPUT_DIR / "batch_process.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def process_image(self, image_path: str):
        try:
            system = ImageQASystem()
            result = system.process(image_path)
            return {"status": "success", "image": image_path, "result": result}
        except Exception as e:
            self.logger.error(f"Failed to process {image_path}: {str(e)}")
            return {"status": "failed", "image": image_path, "error": str(e)}

    def process_batch(self, image_dir: str) -> List[dict]:
        import glob
        image_paths = glob.glob(f"{image_dir}/*.jpg") + glob.glob(f"{image_dir}/*.png")

        futures = []
        for img_path in image_paths:
            futures.append(self.executor.submit(self.process_image, img_path))

        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

        # 保存批量处理结果
        output_file = Config.OUTPUT_DIR / "batch_results.json"
        save_json(results, str(output_file))

        return results