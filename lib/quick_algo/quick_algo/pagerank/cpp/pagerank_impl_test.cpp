#include <stdio.h>
#include <stdlib.h>

#include "pagerank.hpp"
#include <sys/time.h>

int main()
{
    // 测试代码
    CDiGraph *graph = new CDiGraph();

    for (int i = 0; i < 5; i++)
    {
        graph->add_node();
    }

    graph->add_edge(0, 1, 0.5);
    graph->add_edge(1, 2, 0.3);
    graph->add_edge(2, 0, 0.2);
    graph->add_edge(1, 3, 0.4);
    graph->add_edge(3, 4, 0.6);
    graph->add_edge(4, 1, 0.7);

    double init_score_vec[5] = {0.2, 0.2, 0.2, 0.2, 0.2};
    double personalization_vec[5] = {1.0, 0.0, 0.0, 0.0, 0.0};
    double dangling_weight_vec[5] = {1.0, 0.0, 0.0, 0.0, 0.0};

    double alpha = 0.85;
    int max_iter = 100;
    double tol = 1e-6;

    timeval start, end;

    gettimeofday(&start, NULL); // 获取当前时间

    double *result = pagerank(graph, init_score_vec, personalization_vec, dangling_weight_vec, alpha, max_iter, tol);

    gettimeofday(&end, NULL); // 获取当前时间

    double elapsed_time = (end.tv_sec - start.tv_sec) + (end.tv_usec - start.tv_usec) / 1000000.0; // 计算耗时
    printf("Elapsed time: %f seconds\n", elapsed_time);

    for (int i = 0; i < 5; i++)
    {
        printf("Node %d: %f\n", i, result[i]);
    }

    delete graph; // 释放图对象
    free(result); // 释放结果数组
}