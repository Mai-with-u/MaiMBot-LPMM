#ifndef PAGERANK_H
#define PAGERANK_H

// #define __AVX2__ // 启用AVX2优化（影响：小）

#include "di_graph.hpp"

class EdgeWeight
{
public:
    long long src; // 源节点ID
    double weight; // 权重
};

class EdgeList
{
public:
    long long edge_num; // 边数量
    EdgeWeight *edges;  // 边权重列表
};

double *pagerank(
    CDiGraph *graph,             // 图对象
    double *init_score_vec,      // 初始节点分数向量（已概率归一化）
    double *personalization_vec, // 个性化向量（已概率归一化）
    double *dangling_weight_vec, // 悬挂节点权重向量（已概率归一化）
    double alpha,                // 阻尼系数
    int max_iter,                // 最大迭代次数
    double tol                   // 收敛阈值
);

#endif // PAGERANK_H