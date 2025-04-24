#ifndef DI_GRAPH_H
#define DI_GRAPH_H

#include <vector>
#include <queue>

static const long long DEFAULT_NODE_ARRAY_SIZE = 8; // 默认节点数组大小

class CDiEdge;
class CDiNode;

/**
 * @brief 有向图 结构体
 *
 */
class CDiGraph
{
public:
    std::vector<CDiNode *> *nodes;           // 节点数组指针
    std::queue<long long> *reusable_node_id; // 可重用节点ID数组指针

    long long num_nodes; // 节点数量
    long long num_edges; // 边数量

    CDiGraph(long long size = DEFAULT_NODE_ARRAY_SIZE);
    ~CDiGraph();

    // 添加节点
    long long add_node();
    // 添加边
    int add_edge(long long src, long long dst, double weight);
    // 删除节点
    int remove_node(long long id);
    // 删除边
    int remove_edge(long long src, long long dst);
    // 清空图
    int clear();
    // 整理节点数组的内存占用
    int compact_nodes();
    // 获取节点
    CDiNode *get_node(long long id);
    // 获取边
    CDiEdge *get_edge(long long src, long long dst);
};

/**
 * @brief 有向图节点 结构体
 *
 */
class CDiNode
{
public:
    long long id; // 节点ID

    CDiEdge *first_in_edge;  // 第一条入边
    long long num_in_edges;  // 入边数量
    CDiEdge *first_out_edge; // 第一条出边
    long long num_out_edges; // 出边数量

    CDiNode(long long id);
    ~CDiNode();
};

/**
 * @brief 有向图边 结构体
 *
 */
class CDiEdge
{
public:
    long long src; // 起始节点
    long long dst; // 结束节点

    double weight; // 权重

    CDiEdge *next_same_src; // 同起始节点的下一条边
    CDiEdge *prev_same_src; // 同起始节点的上一条边
    CDiEdge *next_same_dst; // 同结束节点的下一条边
    CDiEdge *prev_same_dst; // 同结束节点的上一条边

    CDiEdge(long long src = -1, long long dst = -1, double weight = 0.0L);
    ~CDiEdge();
};

#endif // DI_GRAPH_H