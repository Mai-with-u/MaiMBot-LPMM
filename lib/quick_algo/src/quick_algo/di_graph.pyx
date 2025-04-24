# distutils: language=c++

import os
import xml.etree.ElementTree as et
from xml.dom import minidom

__all__ = ["DiGraph", "DiEdge", "DiNode", "save_to_file", "load_from_file"]

cdef class DiNode:
    """
    有向图节点的Python封装
    """

    def __init__(self, name: str, attr: None | dict = None):
        """
        A class representing a node in a directed graph.
        :param name: Node name
        :param attr: Node attributes
        """
        self.name = name
        self.attr = {} if attr is None else attr

    def __getitem__(self, item):
        """
        Get the attribute of the node.
        :param item: Attribute name
        :return: Attribute value
        """
        if item in self.attr:
            return self.attr[item]
        else:
            raise KeyError(f"Attribute \"{item}\" not found in node \"{self.name}\".")

    def __setitem__(self, key, value):
        """
        Set the attribute of the node.
        :param key: Attribute name
        :param value: Attribute value
        """
        self.attr[key] = value

    def __contains__(self, item):
        """
        Check if the node contains the attribute.
        :param item: Attribute name
        :return: True if the attribute exists, False otherwise
        """
        return item in self.attr


cdef class DiEdge:
    """
    有向图边的Python封装
    """

    def __init__(self, src: str, dst: str, attr: None | dict = None):
        """
        A class representing an edge in a directed graph.
        :param src: Source node name
        :param dst: Destination node name
        :param attr: Edge attributes
        """
        self.src = src
        self.dst = dst

        if attr is not None:
            attr_dict = attr
            if "weight" not in attr_dict:
                attr_dict["weight"] = 0.0
            else:
                attr_dict["weight"] = float(attr_dict["weight"])
        else:
            attr_dict = {"weight": 0.0}
        self.attr = attr_dict

    def __getitem__(self, item):
        """
        Get the attribute of the edge.
        :param item: Attribute name
        :return: Attribute value
        """
        if item in self.attr:
            return self.attr[item]
        else:
            raise KeyError(f"Attribute \"{item}\" not found in edge \"{self.src}->{self.dst}\".")

    def __setitem__(self, key, value):
        """
        Set the attribute of the edge.
        :param key: Attribute name
        :param value: Attribute value
        """
        self.attr[key] = value

    def __contains__(self, item):
        """
        Check if the edge contains the attribute.
        :param item: Attribute name
        :return: True if the attribute exists, False otherwise
        """
        return item in self.attr

cdef class DiGraph:
    """
    A class representing a directed graph.
    """
    def __init__(self, int num_nodes = 10):
        """"""
        # C++ directed graph对象
        self.graph = new CDiGraph(num_nodes)

        # 节点名到索引的映射
        self.node_name2idx_map = dict()
        # 边名到索引的映射（仅用来确定边存在，暂无它用）
        self.edge_name2idx_map = dict()
        # 节点名/边名到属性的映射
        self.name2attr_map = dict()

    def __dealloc__(self):
        """
        Destructor to free the C++ graph object.
        """
        if self.graph is not NULL:
            del self.graph
            self.graph = NULL

    def __getitem__(self, item: str | tuple):
        if isinstance(item, str):
            return self.get_node(item)
        elif isinstance(item, tuple) and len(item) == 2:
            return self.get_edge(item)
        else:
            raise TypeError("Invalid key type. Use node name or edge (src, dst) tuple.")

    def __delitem__(self, key):
        if isinstance(key, str):
            self.remove_node(key)
        elif isinstance(key, tuple) and len(key) == 2:
            self.remove_edge(key)
        else:
            raise TypeError("Invalid key type. Use node name or edge (src, dst) tuple.")

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.node_name2idx_map
        elif isinstance(item, tuple) and len(item) == 2:
            return item in self.edge_name2idx_map
        else:
            raise TypeError("Invalid key type. Use node name or edge (src, dst) tuple.")

    def _direct_add_edge(self, edge: DiEdge):
        """
        直接添加一条边到图中
        :param edge: (src, dst, weight, attr)
        """
        # 起止节点索引
        src_idx = self.node_name2idx_map[edge.src]
        dst_idx = self.node_name2idx_map[edge.dst]

        # 添加边
        res = self.graph.add_edge(src_idx, dst_idx, edge.attr["weight"])
        if res != 0:
            raise RuntimeError(f"Failed to add edge {edge.src}->{edge.dst} to the C-graph.")

        # 更新边属性
        key = (edge.src, edge.dst)
        self.name2attr_map[key] = edge.attr
        self.edge_name2idx_map[key] = 0

    def add_edge(self, edge: DiEdge):
        """
        添加一条边到图中
        :param edge: (src, dst, weight, attr)
        """
        # 检查边是否已经存在
        if (edge.src, edge.dst) in self.edge_name2idx_map:
            raise KeyError(f"Edge {edge.src}->{edge.dst} already exists in the graph.")

        # 收集节点
        new_nodes = set()
        if edge.src not in self.node_name2idx_map:
            new_nodes.add(edge.src)
        if edge.dst not in self.node_name2idx_map:
            new_nodes.add(edge.dst)

        # 添加节点
        self.add_nodes_from([
            DiNode(node)
            for node in new_nodes
        ])

        self._direct_add_edge(edge)

    def add_edges_from(self, edges: list[DiEdge]):
        """
        添加一组边到图中
        :param edges: [DiEdge, ...]
        """
        # 遍历所有边，收集节点
        new_nodes = set()
        for edge in edges:
            # 检查边是否已经存在
            if (edge.src, edge.dst) in self.edge_name2idx_map:
                raise KeyError(f"Edge {edge.src}->{edge.dst} already exists in the graph.")
            if edge.src not in self.node_name2idx_map:
                new_nodes.add(edge.src)
            if edge.dst not in self.node_name2idx_map:
                new_nodes.add(edge.dst)

        # 添加节点
        self.add_nodes_from([
            DiNode(node)
            for node in new_nodes
        ])

        for edge in edges:
            self._direct_add_edge(edge)

    def update_edge(self, edge: DiEdge):
        """
        更新边的属性
        :param edge: (src, dst, weight, attr)
        """
        # 检查边是否存在
        if (edge.src, edge.dst) not in self.edge_name2idx_map:
            raise KeyError(f"Edge {edge.src}->{edge.dst} does not exist in the graph.")
        # 获取索引
        src_idx = self.node_name2idx_map[edge.src]
        dst_idx = self.node_name2idx_map[edge.dst]
        # 获取边结构体指针
        cdef CDiEdge *edge_ptr = self.graph.get_edge(src_idx, dst_idx)
        if edge_ptr is NULL:
            raise RuntimeError(f"Edge {edge.src}->{edge.dst} does not exist in the C-graph.")
        # 更新权重
        edge_ptr.weight = edge.attr["weight"]
        # 更新边属性
        key = (edge.src, edge.dst)
        self.name2attr_map[key] = edge.attr

    def remove_edge(self, edge: tuple[str, str]):
        """
        删除一条边
        :param edge: (src, dst)
        """
        # 检查边是否存在
        src, dst = edge
        if (src, dst) not in self.edge_name2idx_map:
            raise KeyError(f"Edge {src}->{dst} does not exist in the graph.")

        # 获取索引
        src_idx = self.node_name2idx_map[src]
        dst_idx = self.node_name2idx_map[dst]
        # 删除边
        if self.graph.remove_edge(src_idx, dst_idx) != 0:
            raise RuntimeError(f"Failed to remove edge {src}->{dst} from the C-graph.")

        # 删除边属性
        key = (src, dst)
        if key in self.name2attr_map:
            del self.name2attr_map[key]
        # 删除边索引映射
        del self.edge_name2idx_map[key]

    def add_node(self, node: DiNode):
        """
        添加节点到图中
        :param node: (node_name, attr)
        :return:
        """
        if node.name in self.node_name2idx_map:
            raise KeyError(f"Node {node.name} already exists in the graph.")

        # 创建节点
        cdef long long idx = self.graph.add_node()
        if idx < 0:
            raise RuntimeError(f"Failed to add node {node.name} to the C-graph.")
        # 更新索引映射&属性映射
        self.node_name2idx_map[node.name] = idx
        self.name2attr_map[node.name] = node.attr

    def add_nodes_from(self, nodes: list[DiNode]):
        """
        添加节点到图中
        :param nodes: [(node_name, attr), ...]
        :return:
        """
        # 检查节点是否已经存在
        for node in nodes:
            if node.name in self.node_name2idx_map:
                raise KeyError(f"Node {node.name} already exists in the graph.")

        cdef long long idx
        for node in nodes:
            # 创建节点
            idx = self.graph.add_node()
            if idx < 0:
                raise RuntimeError(f"Failed to add node {node.name} to the C-graph.")
            # 更新索引映射&属性映射
            self.node_name2idx_map[node.name] = idx
            self.name2attr_map[node.name] = node.attr

    def update_node(self, node: DiNode):
        """
        更新节点的属性
        :param node: (node_name, attr)
        :return:
        """
        # 检查节点是否存在
        if node.name not in self.node_name2idx_map:
            raise KeyError(f"Node \"{node.name}\" does not exist in the graph.")
        # 获取索引
        #idx = self.node_name2idx_map[node.name]
        # 更新节点属性
        self.name2attr_map[node.name] = node.attr

    def remove_node(self, node_name: str):
        """
        删除节点
        :param node_name: node name
        :return:
        """
        # 检查节点是否存在
        if node_name not in self.node_name2idx_map:
            raise KeyError(f"Node \"{node_name}\" does not exist in the graph.")
        # 获取索引
        idx = self.node_name2idx_map[node_name]
        # 删除节点
        if self.graph.remove_node(idx) != 0:
            raise RuntimeError(f"Failed to remove node {node_name} from the C-graph.")

        # 删除节点属性
        del self.name2attr_map[node_name]
        # 删除节点索引映射
        del self.node_name2idx_map[node_name]

        # 删除相关的边对应的属性和索引
        for edge in list(self.edge_name2idx_map.keys()):
            if edge[0] == node_name or edge[1] == node_name:
                del self.edge_name2idx_map[edge]
                del self.name2attr_map[edge]

    def get_node_list(self) -> list[str]:
        """
        获取所有节点
        :return: 节点列表
        """
        return list(self.node_name2idx_map.keys())

    def get_edge_list(self) -> list[tuple[str, str]]:
        """
        获取所有边
        :return: 边列表
        """
        return list(self.edge_name2idx_map.keys())

    def get_node(self, node: str) -> DiNode:
        """
        获取节点
        :param node: 节点名
        :return: 节点属性
        """
        if node in self.node_name2idx_map:
            return DiNode(node, self.name2attr_map.get(node, None))
        else:
            raise KeyError(f"Node \"{node}\" does not exist in the graph.")

    def get_edge(self, edge: tuple[str, str]) -> DiEdge:
        """
        获取边的属性
        :param edge: (src, dst)
        :return: 边属性
        """
        src, dst = edge
        if (src, dst) in self.name2attr_map:
            return DiEdge(src, dst, self.name2attr_map.get((src, dst), None))
        else:
            raise KeyError(f"Edge \"{src}->{dst}\" does not exist in the graph.")

    def compact_node_array(self):
        """
        压缩节点数组
        :return:
        """
        # 若果节点数组已经压缩，则不需要再压缩
        if self.graph.num_nodes == self.graph.nodes.size():
            return

        # 压缩节点数组
        self.graph.compact_nodes()

        # 更新索引映射
        node_list = [
            (node_name, idx)
            for node_name, idx in self.node_name2idx_map.items()
        ]

        node_list = sorted(node_list, key=lambda x: x[1]) # 按照索引排序

        # 重建索引映射
        count = 0
        for node_name, _ in node_list:
            self.node_name2idx_map[node_name] = count
            count += 1

    def clear(self):
        """
        清空图
        :return:
        """
        self.graph.clear()
        self.node_name2idx_map.clear()
        self.edge_name2idx_map.clear()
        self.name2attr_map.clear()

def save_to_file(graph: DiGraph, file_path: str, enable_zip: bool = False):
    """
    保存图到文件
    :param graph: 图对象
    :param file_path: 文件路径
    :param enable_zip: 是否压缩
    :return:
    """
    # 创建XML根节点
    root = et.Element("graphml")
    # 添加头信息
    root.set("xmlns", "http://graphml.graphdrawing.org/xmlns")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:schemaLocation", "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd")

    graph_element = et.Element("graph")
    graph_element.set("edgedefault", "directed")

    # 收集属性标头
    keys = {}
    nodes = []
    edges = []

    for node_name in graph.node_name2idx_map.keys():
        node = et.SubElement(graph_element, "node")
        node.set("id", node_name)
        for key, value in graph.name2attr_map[node_name].items():
            if key not in keys:
                # 创建属性标头
                key_element = et.SubElement(root, "key")
                key_element.set("id", f"d{len(keys)}")
                key_element.set("for", "node")
                key_element.set("attr.name", key)
                key_element.set("attr.type", type(value).__name__)
                keys[key] = key_element
            key_id = keys[key].get("id")
            data = et.SubElement(node, "data")
            data.set("key", key_id)
            data.text = str(value)
        nodes.append(node)

    for edge_key in graph.edge_name2idx_map.keys():
        edge = et.SubElement(graph_element, "edge")
        edge.set("source", edge_key[0])
        edge.set("target", edge_key[1])
        for key, value in graph.name2attr_map[edge_key].items():
            if key not in keys:
                # 创建属性标头
                key_element = et.SubElement(root, "key")
                key_element.set("id", f"d{len(keys)}")
                key_element.set("for", "edge")
                key_element.set("attr.name", key)
                key_element.set("attr.type", type(value).__name__)
                keys[key] = key_element
            key_id = keys[key].get("id")
            data = et.SubElement(edge, "data")
            data.set("key", key_id)
            data.text = str(value)
        edges.append(edge)

    root.append(graph_element)

    # 转化为字符串
    tree = et.ElementTree(root)
    rough_str = et.tostring(root, 'utf-8')
    # 格式化
    reparsed = minidom.parseString(rough_str)
    new_str = reparsed.toprettyxml(indent='\t')

    if enable_zip:
        # 保存为graphmlz
        import gzip
        if not file_path.endswith(".graphmlz"):
            raise ValueError("You must use .graphmlz format when enable_zip is True.")
        with gzip.open(file_path, 'wb') as f:
            f.write(new_str.encode('utf-8'))
    else:
        # 保存为graphml
        if not file_path.endswith(".graphml"):
            raise ValueError("You must use .graphml format when enable_zip is False.")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_str)


def load_from_file(file_path: str) -> DiGraph:
    """
    从文件加载图
    :param file_path: 文件路径
    :return: DiGraph对象
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")

    content: str

    if file_path.endswith(".graphmlz"):
        # 解压缩
        import gzip
        with gzip.open(file_path, 'rb') as f:
            content = f.read().decode(encoding="utf-8")
    elif file_path.endswith(".graphml"):
        # 读取文件
        with open(file_path, 'rb') as f:
            content = f.read().decode(encoding="utf-8")
    else:
        raise ValueError("Unsupported file format. Please use .graphml or .graphmlz format.")

    # 解析XML文件
    root = et.fromstring(content)
    xmlns = "{http://graphml.graphdrawing.org/xmlns}"
    if root.tag != f"{xmlns}graphml":
        raise ValueError("Invalid file format. Please use .graphml or .graphmlz format.")

    # 读取所有属性标头
    keys = {}
    for key in root.findall(f"{xmlns}key"):
        key_id = key.get("id")
        attr_name = key.get("attr.name")
        attr_type = key.get("attr.type")
        keys[key_id] = (attr_name, attr_type)

    nodes = root.findall(f"{xmlns}graph/{xmlns}node")
    edges = root.findall(f"{xmlns}graph/{xmlns}edge")

    # 创建图对象
    graph = DiGraph(len(nodes))

    # 添加节点
    for node in nodes:
        node_id = node.get("id")
        node_attr = {}
        for data in node.findall(f"{xmlns}data"):
            key_id = data.get("key")
            attr_name, attr_type = keys[key_id]
            if attr_type == "int":
                node_attr[attr_name] = int(data.text)
            elif attr_type == "float":
                node_attr[attr_name] = float(data.text)
            else:
                node_attr[attr_name] = data.text
        graph.add_node(DiNode(node_id, node_attr))

    # 添加边
    for edge in edges:
        src = edge.get("source")
        dst = edge.get("target")
        edge_attr = {}
        for data in edge.findall(f"{xmlns}data"):
            key_id = data.get("key")
            attr_name, attr_type = keys[key_id]
            if attr_type == "int":
                edge_attr[attr_name] = int(data.text)
            elif attr_type == "float":
                edge_attr[attr_name] = float(data.text)
            else:
                edge_attr[attr_name] = data.text
        graph.add_edge(DiEdge(src, dst, edge_attr))

    return graph