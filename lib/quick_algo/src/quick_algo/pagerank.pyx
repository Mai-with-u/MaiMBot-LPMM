# distutils: language=c++

from libc.stdlib cimport free, malloc

from .di_graph cimport DiGraph

__all__ = ["run_pagerank"]

def run_pagerank(
        graph: DiGraph,
        init_score: None | dict[str, float] = None,
        personalization: None | dict[str, float] = None,
        dangling_weight: None | dict[str, float] = None,
        alpha: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-6
):
    """
    运行PageRank算法
    :param graph: 有向图
    :param init_score: 初始分数
    :param personalization: 节点的个性化向量
    :param dangling_weight: 悬空节点的权重
    :param alpha: 阻尼系数
    :param max_iter: 最大迭代次数
    :param tol: 收敛阈值
    :return: PageRank值列表
    """
    node_array_size = graph.graph.nodes.size()
    num_nodes = graph.graph.num_nodes

    cdef double *init_score_array = <double *> malloc(node_array_size * sizeof(double))
    cdef double *personalization_array = <double *> malloc(node_array_size * sizeof(double))
    cdef double *dangling_weight_array = <double *> malloc(node_array_size * sizeof(double))

    for i in range(node_array_size):
        init_score_array[i] = 0
        personalization_array[i] = 0
        dangling_weight_array[i] = 0

    if init_score is not None:
        sum_init_score = sum(init_score.values())
    if personalization is not None:
        sum_personalization = sum(personalization.values())
    if dangling_weight is not None:
        sum_dangling_weight = sum(dangling_weight.values())

    for node_name, idx in graph.node_name2idx_map.items():
        if init_score is not None:
            init_score_array[idx] = init_score.get(node_name, 0.0) / sum_init_score
        else:
            init_score_array[idx] = 1.0 / num_nodes

        if personalization is not None:
            personalization_array[idx] = personalization.get(node_name, 0.0) / sum_personalization
        else:
            personalization_array[idx] = 1.0 / num_nodes

        if dangling_weight is not None:
            dangling_weight_array[idx] = dangling_weight.get(node_name, 0.0) / sum_dangling_weight
        else:
            dangling_weight_array[idx] = personalization_array[idx]

    cdef double *rank_result = pagerank(
        graph.graph,
        init_score_array,
        personalization_array,
        dangling_weight_array,
        alpha,
        max_iter,
        tol
    )

    free(init_score_array)
    free(personalization_array)
    free(dangling_weight_array)
    
    result = dict()
    for node_name, idx in graph.node_name2idx_map.items():
        result[node_name] = rank_result[idx]

    free(rank_result)

    return result