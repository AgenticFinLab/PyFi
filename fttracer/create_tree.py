"""
Summary

"""

import argparse
from mcts.gqa import ImageQASystem
from config import Config
from multi_threading import BatchProcessor
from web import start_web_server


def main():
    parser = argparse.ArgumentParser(description="FTTracer Image QA System")
    subparsers = parser.add_subparsers(dest='command')

    # 单图处理命令
    single_parser = subparsers.add_parser('single')
    single_parser.add_argument('image_path', help="Path to input image")

    # 批量处理命令
    batch_parser = subparsers.add_parser('batch')
    batch_parser.add_argument('image_dir', help="Directory containing images")
    batch_parser.add_argument('--workers', type=int, default=4, help="Number of worker threads")

    # Web服务命令
    web_parser = subparsers.add_parser('web')
    web_parser.add_argument('--port', type=int, default=8000, help="Web server port")

    args = parser.parse_args()

    if args.command == 'single':
        system = ImageQASystem()
        system.process(args.image_path)
    elif args.command == 'batch':
        processor = BatchProcessor(max_workers=args.workers)
        processor.process_batch(args.image_dir)
    elif args.command == 'web':
        start_web_server(port=args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()