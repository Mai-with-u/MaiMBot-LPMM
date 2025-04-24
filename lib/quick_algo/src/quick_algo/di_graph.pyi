__all__ = ["DiGraph", "DiEdge", "DiNode", "save_to_file", "load_from_file"]

class DiNode:
    """
    有向图节点类
    """
    
    name: str
    attr: dict[str, str | int | float]

    def __init__(self, name: str, attr: None | dict = None):
        """
        有向图节点类
        :param name: 节点名称
        :param attr: 节点属性
        """
        ...

    def __getitem__(self, item: str) -> str | int | float:
        ...

    def __setitem__(self, key: str, value: str | int | float):
        ...

    def __contains__(self, item: str) -> bool:
        ...

class DiEdge:
    """
    有向图边类
    """
    
    src: str
    dst: str
    attr: dict[str, str | int | float]

    def __init__(self, src: str, dst: str, attr: None | dict = None):
        """
        有向图边类
        :param src: 边的起始节点名称
        :param dst: 边的结束节点名称
        :param attr: 边的属性
        """
        ...

    def __getitem__(self, item: str) -> str | int | float:
        ...

    def __setitem__(self, key: str, value: str | int | float):
        ...

    def __contains__(self, item: str) -> bool:
        ...

class DiGraph:
    """
    有向图
    """
    node_name2idx_map: dict[str, int]
    
    def __init__(self):
        """
        有向图类
        """
        ...

    def __getitem__(self, item: str | tuple) -> DiNode | DiEdge:
        ...

    def __delitem__(self, key):
        ...

    def __contains__(self, item: str | tuple) -> bool:
        ...

    def add_edge(self, edge: DiEdge):
        """
        添加边
        :param edge: 边对象 
        """
        ...

    def add_edges_from(self, edges: list[DiEdge]):
        """
        批量添加边
        :param edges: 边对象列表 `[DiEdge, DiEdge, ...]`
        """
        ...

    def update_edge(self, edge: DiEdge):
        """
        更新边
        :param edge: 边对象 
        """
        ...

    def remove_edge(self, edge: tuple[str, str]):
        """
        删除边
        :param edge: 边的起始节点和结束节点名称元组 `(src, dst)`
        """
        ...

    def add_node(self, node: DiNode):
        """
        添加节点
        :param node: 节点对象
        """
        ...

    def add_nodes_from(self, nodes: list[DiNode]):
        """
        批量添加节点
        :param nodes: 节点对象列表 `[DiNode, DiNode, ...]`
        """
        ...

    def update_node(self, node: DiNode):
        """
        更新节点
        :param node: 节点对象 
        """
        ...

    def remove_node(self, node_name: str):
        """
        删除节点
        :param node_name: 节点名称
        """
        ...

    def get_node_list(self) -> list[str]:
        """
        获取节点列表
        :return: 节点名称列表 `[node_name, node_name, ...]`
        """
        ...

    def get_edge_list(self) -> list[tuple[str, str]]:
        """
        获取边列表
        :return: 边的起始节点和结束节点名称元组列表 `[(src, dst), (src, dst), ...]`
        """
        ...

    def get_node(self, node_name: str) -> DiNode:
        """
        获取节点
        :param node_name: 节点名称 
        """
        ...

    def get_edge(self, edge_key: tuple[str, str]) -> DiEdge:
        """
        获取边
        :param edge_key: 边的起始节点和结束节点名称元组 `(src, dst)`
        :return:
        """
        ...

    def compact_node_array(self):
        """
        压缩节点数组
        """
        ...

    def clear(self):
        """
        清空图
        """
        ...

def save_to_file(graph: DiGraph, filename: str, enable_zip: bool = False):
    """
    保存图到文件
    :param graph: 图对象
    :param filename: 文件名
    :param enable_zip: 是否启用压缩
    """
    ...

def load_from_file(filename: str) -> DiGraph:
    """
    从文件加载图
    :param filename: 文件名
    :return: 图对象
    """
    ...