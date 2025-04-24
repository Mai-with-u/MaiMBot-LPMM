#define __USE_MINGW_ANSI_STDIO 1
#include <stdio.h>
#include <stdexcept>
#include <stdlib.h>
#include <math.h>

#include "pagerank.hpp"

#ifdef __AVX2__
#include <immintrin.h> // SIMD指令集头文件
#endif

/**
 * @brief 释放内存
 *
 * @param graph
 * @param weight_matrix
 * @param score
 */
void clean_up(CDiGraph *graph, EdgeList *weight_matrix, double *out_weight_sum, double *score)
{
    if (graph != NULL && weight_matrix != NULL)
    {
        for (long long i = 0; i < graph->nodes->size(); i++)
        {
            if (weight_matrix[i].edges != NULL)
            {
                free(weight_matrix[i].edges); // 释放边权重列表
            }
        }
        free(weight_matrix); // 释放权重矩阵指针
    }

    if (out_weight_sum != NULL)
        free(out_weight_sum); // 释放出边权重和数组

    if (score != NULL)
        free(score); // 释放Score向量
}

/**
 * 个性化PageRank算法
 */
double *pagerank(
    CDiGraph *graph,             // 图对象
    double *init_score_vec,      // 初始节点分数向量（已概率归一化）
    double *personalization_vec, // 个性化向量（已概率归一化）
    double *dangling_weight_vec, // 悬挂节点权重向量（已概率归一化）
    double alpha,                // 阻尼系数
    int max_iter,                // 最大迭代次数
    double tol                   // 收敛阈值
)
{
    long long node_array_size = graph->nodes->size(); // 节点数量

    EdgeList *weight_matrix = (EdgeList *)calloc(node_array_size, sizeof(EdgeList)); // 同目标边权重矩阵
    if (weight_matrix == NULL)
    {
        // 内存分配失败，释放已分配的内存并返回NULL
        printf("[Err] Memory allocation failed for weight_matrix array\n");
        clean_up(graph, NULL, NULL, NULL);
        throw std::bad_alloc(); // 抛出异常
    }
    double *out_weight_sum = (double *)calloc(node_array_size, sizeof(double)); // 出边权重和
    if (out_weight_sum == NULL)
    {
        // 内存分配失败，释放已分配的内存并返回NULL
        printf("[Err] Memory allocation failed for out_weight_sum array\n");
        clean_up(graph, weight_matrix, NULL, NULL);
        throw std::bad_alloc(); // 抛出异常
    }

    {
        for (long long i = 0; i < node_array_size; i++)
        {
            if (graph->nodes->at(i) == NULL)
            {
                weight_matrix[i].edge_num = -1; // 边数量为-1（表示无效）
                weight_matrix[i].edges = NULL;  // 如果节点为空，则边权重列表也为空
                out_weight_sum[i] = 0.0L;       // 出边权重和为0
            }
            else
            {
                {
                    // 计算当前节点的出边权重之和
                    CDiEdge *edge = graph->nodes->at(i)->first_out_edge; // 获取节点的第一条出边
                    while (edge != NULL)
                    {
                        out_weight_sum[i] += edge->weight; // 累加出边权重
                        edge = edge->next_same_src;        // 移动到下一条同源边
                    }
                    if (out_weight_sum[i] < 0)
                    {
                        // 出边权重和小于零，异常退出
                        printf("[Err] Sum of out weights is negative for node %lld\n", i);
                        clean_up(graph, weight_matrix, out_weight_sum, NULL);
                        throw std::runtime_error("Sum of out weights is negative"); // 抛出异常
                    }
                }

                weight_matrix[i].edge_num = graph->nodes->at(i)->num_in_edges;                                // 获取入边数量
                weight_matrix[i].edges = (EdgeWeight *)calloc(weight_matrix[i].edge_num, sizeof(EdgeWeight)); // 分配内存
                if (weight_matrix[i].edges == NULL)
                {
                    // 内存分配失败，释放已分配的内存并返回NULL
                    printf("[Err] Memory allocation failed for weight_matrix[%lld]->edges\n", i);
                    clean_up(graph, weight_matrix, out_weight_sum, NULL);
                    throw std::bad_alloc(); // 抛出异常
                }
            }
        }

        // 填充权重矩阵
        for (long long i = 0; i < node_array_size; i++)
        {
            if (weight_matrix[i].edge_num < 0)
                continue;                                       // 跳过无效节点
            CDiEdge *edge = graph->nodes->at(i)->first_in_edge; // 获取节点的第一条入边
            long long j = 0;
            while (edge != NULL && j < weight_matrix[i].edge_num)
            {
                weight_matrix[i].edges[j].src = edge->src;                                   // 源节点ID
                weight_matrix[i].edges[j].weight = edge->weight / out_weight_sum[edge->src]; // 权重归一化
                edge = edge->next_same_dst;                                                  // 移动到下一条同目标边
                j++;
            }
        }
    }

    // 初始化Score向量
    double *score = (double *)calloc(node_array_size, sizeof(double)); // 初始化Score向量为0
    if (score == NULL)
    {
        // 内存分配失败，释放已分配的内存并返回NULL
        printf("[Err] Memory allocation failed for score\n");
        clean_up(graph, weight_matrix, out_weight_sum, NULL);
        throw std::bad_alloc(); // 抛出异常
    }
    for (long long i = 0; i < node_array_size; i++)
    {
        score[i] = init_score_vec[i]; // 使用init_score_vec初始化Score向量
    }

    // 迭代计算PageRank
    for (int iter = 0; iter < max_iter; iter++)
    {
        double *last_score = score;                                // 保存上一次的Score向量
        score = (double *)calloc(node_array_size, sizeof(double)); // 分配新的Score向量
        if (score == NULL)
        {
            // 内存分配失败，释放已分配的内存并返回NULL
            printf("[Err] Memory allocation failed for new_score\n");
            clean_up(graph, weight_matrix, out_weight_sum, last_score);
            throw std::bad_alloc(); // 抛出异常
        }

        // 统计悬挂节点贡献的总量
        double dangling_sum = 0.0L; // 悬挂节点贡献的总量
        for (long long i = 0; i < node_array_size; i++)
        {
            if (weight_matrix[i].edge_num < 0)
                continue; // 跳过无效节点

            if (out_weight_sum[i] == 0.0L)
            {
                dangling_sum += last_score[i]; // 累加悬挂节点的Score
            }
        }
        dangling_sum = alpha * dangling_sum; // 计算悬挂节点的贡献

#ifdef __AVX2__
        // 使用AVX2加速运算
        // 1. 计算悬挂节点贡献和个性化向量贡献
        {
            long long i;
            {
                __m256d dangling_sum_vec = _mm256_set1_pd(dangling_sum); // 设置悬挂节点贡献向量
                __m256d n_alpha_vec = _mm256_set1_pd(1.0 - alpha);       // 设置个性化向量系数
                for (i = 0; i < node_array_size - 4; i += 4)
                {
                    __m256d score_vec = _mm256_loadu_pd(&score[i]); // 加载当前Score向量
                    {
                        // 使用SIMD指令计算悬挂节点贡献
                        __m256d dangling_weight_vec_vec = _mm256_loadu_pd(&dangling_weight_vec[i]);      // 加载悬挂节点权重向量
                        __m256d dangling_vec = _mm256_mul_pd(dangling_sum_vec, dangling_weight_vec_vec); // 计算悬挂节点贡献
                        score_vec = _mm256_add_pd(score_vec, dangling_vec);                              // 累加悬挂节点贡献
                    }
                    {
                        // 使用SIMD指令计算个性化向量贡献
                        __m256d personalization_vec_vec = _mm256_loadu_pd(&personalization_vec[i]);             // 加载个性化向量
                        __m256d personalization_vec_vec3 = _mm256_mul_pd(personalization_vec_vec, n_alpha_vec); // 计算个性化向量贡献
                        score_vec = _mm256_add_pd(score_vec, personalization_vec_vec3);                         // 累加个性化向量贡献
                    }
                    _mm256_storeu_pd(&score[i], score_vec); // 存储结果
                }
            }
            for (; i < node_array_size; ++i)
            {
                if (weight_matrix[i].edge_num < 0)
                    continue; // 跳过无效节点

                // 计算悬挂节点贡献和个性化向量贡献
                score[i] += dangling_sum * dangling_weight_vec[i];  // 悬挂节点贡献
                score[i] += (1.0 - alpha) * personalization_vec[i]; // 个性化向量贡献
            }
        }
        // 2. 计算节点间传播贡献
        {
            for (long long i = 0; i < node_array_size; ++i)
            {
                if (weight_matrix[i].edge_num < 0)
                    continue; // 跳过无效节点

                double sum_propagation = 0.0L; // 节点间传播贡献
                // 遍历所有入边
                for (long long j = 0; j < weight_matrix[i].edge_num; j++)
                    sum_propagation += last_score[weight_matrix[i].edges[j].src] * weight_matrix[i].edges[j].weight;
                score[i] += sum_propagation * alpha; // 节点间传播贡献
            }
        }
#else
        // 使用普通循环计算
        for (long long i = 0; i < node_array_size; i++)
        {
            if (weight_matrix[i].edge_num < 0)
                continue; // 跳过无效节点

            // 计算新的Score向量：1. 计算悬挂节点贡献和个性化向量贡献
            score[i] += dangling_sum * dangling_weight_vec[i];  // 悬挂节点贡献
            score[i] += (1.0 - alpha) * personalization_vec[i]; // 个性化向量贡献

            // 计算新的Score向量：2. 计算节点间传播贡献
            double sum_propagation = 0.0L; // 节点间传播贡献
            // 遍历所有入边
            for (long long j = 0; j < weight_matrix[i].edge_num; j++)
                sum_propagation += last_score[weight_matrix[i].edges[j].src] * weight_matrix[i].edges[j].weight;
            score[i] += sum_propagation * alpha; // 节点间传播贡献
        }
#endif

        // 检查收敛
        double diff = 0.0L;
        for (long long i = 0; i < node_array_size; i++)
            diff += fabs(score[i] - last_score[i]);

        // 释放上一次的Score向量
        free(last_score); // 释放上一次的Score向量

        if (diff < graph->num_nodes * tol)
            break;
    }

    clean_up(graph, weight_matrix, out_weight_sum, NULL); // 释放临时Score向量

    return score;
}