from typing import Dict, List
from .gqa import ImageQASystem
from .utils import plot_tree


class TreeBuilder:
    STRATEGIES = ['uct', 'dfs', 'bfs']

    def __init__(self, qa_system: ImageQASystem):
        self.system = qa_system

    def build(self, strategy: str = 'uct', max_depth: int = 10):
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy. Available: {self.STRATEGIES}")

        if strategy == 'uct':
            self._build_with_uct(max_depth)
        elif strategy == 'dfs':
            self._build_with_dfs(max_depth)
        else:
            self._build_with_bfs(max_depth)

    def _build_with_uct(self, max_depth: int):
        current_depth = 0
        while (not self.system.can_answer_fq_judge() and
               current_depth < max_depth):
            if not self.system.child_num_is_zero():
                if self.system.sigmoid_sampling_judge():
                    self.system.node_selection()
                else:
                    self.system.node_expansion()
            else:
                self.system.node_expansion()
            self.system.node_action()
            current_depth += 1

    def _build_with_dfs(self, max_depth: int):
        # 深度优先实现
        pass

    def _build_with_bfs(self, max_depth: int):
        # 广度优先实现
        pass

    def visualize(self, save_path: str):
        """可视化当前树结构"""
        plot_tree(self.system.current_image_fq_tree, save_path)