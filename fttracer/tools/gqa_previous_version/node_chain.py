import json
from collections import defaultdict


def process_json_data(input_file, chain_output_file, ordered_json_output_file):
    # 读取JSON数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 创建节点字典，方便查找
    nodes = {item['node']: item for item in data}

    # 构建子节点映射
    children = defaultdict(list)
    for item in data:
        children[item['parent']].append(item['node'])

    # 找出所有最终节点（没有子节点的节点）
    all_parents = set()
    all_nodes = set()

    for item in data:
        all_nodes.add(item['node'])
        all_parents.add(item['parent'])

    leaf_nodes = list(all_nodes - all_parents)

    # 从每个叶子节点回溯到根节点(0)
    chains = []
    for leaf in leaf_nodes:
        chain = []
        current = leaf
        while current != 0 and current in nodes:
            chain.append(current)
            current = nodes[current]['parent']
        chain.append(0)  # 添加根节点
        chain.reverse()  # 反转使顺序从根到叶
        chains.append(chain)

    # 写入节点链文件
    with open(chain_output_file, 'w', encoding='utf-8') as f:
        for chain in chains:
            f.write('->'.join(map(str, chain)) + '\n')

    print(f"共找到 {len(chains)} 条节点链，已保存到 {chain_output_file}")

    # 按照链的顺序重新组织节点
    # 首先收集所有唯一节点（保持顺序）
    ordered_nodes = []
    seen_nodes = set()

    for chain in chains:
        for node in chain:
            if node not in seen_nodes:
                seen_nodes.add(node)
                ordered_nodes.append(node)

    # 构建新的有序JSON数据
    ordered_data = []
    for node in ordered_nodes:
        if node in nodes:
            ordered_data.append(nodes[node])

    # 添加可能遗漏的节点（如果有）
    for node in all_nodes:
        if node not in seen_nodes:
            ordered_data.append(nodes[node])

    # 保存有序JSON文件
    with open(ordered_json_output_file, 'w', encoding='utf-8') as f:
        json.dump(ordered_data, f, indent=2, ensure_ascii=False)

    print(f"已按照节点链顺序重新整理JSON数据，保存到 {ordered_json_output_file}")


# 使用示例
input_json = 'nodeqa_example.json'
chain_output = 'node_chain.txt'
ordered_json = 'nodeqa_obc_example.json' # nodeqa ordered by chain

process_json_data(input_json, chain_output, ordered_json)