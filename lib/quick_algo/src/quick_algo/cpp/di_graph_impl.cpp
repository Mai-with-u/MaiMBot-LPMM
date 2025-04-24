#define __USE_MINGW_ANSI_STDIO 1
#include <stdio.h>
#include <exception>
#include <stdlib.h>
#include "di_graph.hpp"

CDiNode::CDiNode(long long id)
{
    this->id = id;               // 节点ID
    this->first_in_edge = NULL;  // 第一条入边
    this->num_in_edges = 0;      // 入边数量
    this->first_out_edge = NULL; // 第一条出边
    this->num_out_edges = 0;     // 出边数量
}

CDiNode::~CDiNode()
{
}

CDiEdge::CDiEdge(long long src, long long dst, double weight)
{
    this->src = src;            // 起始节点
    this->dst = dst;            // 结束节点
    this->weight = weight;      // 权重
    this->next_same_src = NULL; // 同起始节点的下一条边
    this->prev_same_src = NULL; // 同起始节点的上一条边
    this->next_same_dst = NULL; // 同结束节点的下一条边
    this->prev_same_dst = NULL; // 同结束节点的上一条边
}

CDiEdge::~CDiEdge()
{
}

CDiGraph::CDiGraph(long long size)
{
    this->num_nodes = 0;                        // 节点数量
    this->num_edges = 0;                        // 边数量
    this->nodes = new std::vector<CDiNode *>(); // 节点数组指针
    this->reusable_node_id = new std::queue<long long>();
    if (this->nodes == NULL || this->reusable_node_id == NULL)
        throw std::bad_alloc(); // 抛出异常
}

CDiGraph::~CDiGraph()
{
    // 释放节点数据结构
    for (long long i = 0; i < this->num_nodes; i++)
    {
        if (this->nodes->at(i) != NULL)
        {
            // 释放节点的边数据结构（只需处理出边即可，入边会在其它节点的出边列表中处理）
            CDiEdge *edge = this->nodes->at(i)->first_out_edge;
            CDiEdge *next_edge;
            this->nodes->at(i)->first_out_edge = NULL; // 清除出边指针，避免野指针
            this->nodes->at(i)->first_in_edge = NULL;  // 清除节点入边指针，避免野指针
            while (edge != NULL)
            {
                next_edge = edge->next_same_src;
                delete edge;
                edge = next_edge;
            }
            delete this->nodes->at(i); // 释放节点
        }
    }

    // 释放图节点数组
    delete this->nodes;

    // 释放可重用节点数组
    delete this->reusable_node_id;
}

/**
 * @brief 添加节点
 *
 * @return long long 节点ID
 */
long long CDiGraph::add_node()
{
    // 创建新节点
    CDiNode *new_node = new CDiNode(this->num_nodes);
    if (new_node == NULL)
        throw std::bad_alloc(); // 抛出异常

    long long id;

    if (this->reusable_node_id->empty())
    {
        // 如果可重用节点ID数组为空，则直接添加新节点
        id = this->num_nodes;
        new_node->id = id;
        this->nodes->push_back(new_node);
    }
    else
    {
        // 有可重用节点ID，取用
        id = this->reusable_node_id->front();
        new_node->id = id;
        this->reusable_node_id->pop();
        if (this->nodes->at(id) == NULL)
            this->nodes->at(id) = new_node;
        else
        {
            // 异常：可重用ID位置已被占用
            delete new_node;
            return -1;
        }
    }

    this->num_nodes++; // 节点数量加1

    return id;
}

/**
 * @brief 添加边
 *
 * @param src 源节点ID
 * @param dst 目标节点ID
 * @param weight 边权重
 *
 * @return int 返回0表示成功，-1表示失败
 */
int CDiGraph::add_edge(long long src, long long dst, double weight)
{
    // 检查源节点和目标节点是否存在
    CDiNode *src_node = this->get_node(src); // 源节点
    CDiNode *dst_node = this->get_node(dst); // 目标节点
    if (src_node == NULL || dst_node == NULL)
        return -1; // 返回错误代码

    // 创建新边
    CDiEdge *new_edge = new CDiEdge(src, dst, weight);
    if (new_edge == NULL)
        throw std::bad_alloc(); // 抛出异常

    // 将新边添加到源节点的出边列表中（按目标节点ID升序插入）
    if (src_node->first_out_edge == NULL)
    {
        // 如果源节点的出边列表为空，则直接添加
        src_node->first_out_edge = new_edge; // 更新首边指针
    }
    else if (src_node->first_out_edge->dst > dst)
    {
        // 如果首边的目标节点ID大于新边的目标节点ID，则插入到首边之前
        new_edge->next_same_src = src_node->first_out_edge; // 更新新边的同源后继指针
        src_node->first_out_edge->prev_same_src = new_edge; // 更新首边的同源前驱指针
        src_node->first_out_edge = new_edge;                // 更新首边指针
    }
    else
    {
        // 否则按升序插入到出边列表中
        CDiEdge *edge = src_node->first_out_edge;
        while (edge->next_same_src != NULL && edge->next_same_src->dst < dst)
            edge = edge->next_same_src;
        // 此时，edge是新边的前驱边（最后一个dst小于new_dst的边）

        new_edge->next_same_src = edge->next_same_src;     // 更新新边的同源后继指针
        if (edge->next_same_src != NULL)                   //
            edge->next_same_src->prev_same_src = new_edge; // 如果有后继边，则更新后继边的同源前驱指针
        edge->next_same_src = new_edge;                    // 更新当前边的同源后继指针
        new_edge->prev_same_src = edge;                    // 更新新边的同源前驱指针
    }
    src_node->num_out_edges++; // 源节点的出边数量加1

    // 将新边添加到目标节点的入边列表中
    if (dst_node->first_in_edge == NULL)
    {
        // 如果目标节点的入边列表为空，则直接添加
        dst_node->first_in_edge = new_edge; // 更新首边指针
    }
    else if (dst_node->first_in_edge->src > src)
    {
        // 如果首边的源节点ID大于新边的源节点ID，则插入到首边之前
        new_edge->next_same_dst = dst_node->first_in_edge; // 更新新边的同目标后继指针
        dst_node->first_in_edge->prev_same_dst = new_edge; // 更新首边的同目标前驱指针
        dst_node->first_in_edge = new_edge;                // 更新首边指针
    }
    else
    {
        // 否则按升序插入到入边列表中
        CDiEdge *edge = dst_node->first_in_edge;
        while (edge->next_same_dst != NULL && edge->next_same_dst->src < src)
            edge = edge->next_same_dst;
        // 此时，edge是新边的前驱边（最后一个src小于new_src的边）

        new_edge->next_same_dst = edge->next_same_dst;     // 更新新边的同目标后继指针
        if (edge->next_same_dst != NULL)                   //
            edge->next_same_dst->prev_same_dst = new_edge; // 如果有后继边，则更新后继边的同目标前驱指针
        edge->next_same_dst = new_edge;                    // 更新当前边的同目标后继指针
        new_edge->prev_same_dst = edge;                    // 更新新边的同目标前驱指针
    }
    dst_node->num_in_edges++; // 目标节点的入边数量加1

    num_edges++; // 边数量加1

    return 0;
}

int CDiGraph::remove_node(long long id)
{
    // 检查节点ID是否有效
    CDiNode *node = this->get_node(id); // 节点指针
    if (node == NULL)
        return -1; // 返回错误代码

    CDiEdge *edge;
    CDiEdge *next_edge;
    // 删除节点的出边
    edge = node->first_out_edge;
    node->first_out_edge = NULL; // 清除出边指针，避免野指针
    while (edge != NULL)
    {
        next_edge = edge->next_same_src; // 保存下一条边
        // 无需处理同源边之间的关系，因为都会被移除。
        // 只需处理同目标边之间的关系
        if (edge->prev_same_dst != NULL) // 如果有同目标前驱边，更新前驱边的同目标后继指针
            edge->prev_same_dst->next_same_dst = edge->next_same_dst;
        else // 如果是首边，更新首边指针
            this->nodes->at(edge->dst)->first_in_edge = edge->next_same_dst;
        if (edge->next_same_dst != NULL) // 如果有同目标后继边，更新后继边的同目标前驱指针
            edge->next_same_dst->prev_same_dst = edge->prev_same_dst;
        delete edge;      // 删除边
        edge = next_edge; // 更新当前边为下一条边
    }

    // 删除节点的入边
    edge = node->first_in_edge;
    node->first_in_edge = NULL; // 清除入边指针，避免野指针
    while (edge != NULL)
    {
        next_edge = edge->next_same_dst;
        // 无需处理同目标边之间的关系，因为都会被移除。
        // 只需处理同源边之间的关系
        if (edge->prev_same_src != NULL) // 如果有同源前驱边，更新前驱边的同源后继指针
            edge->prev_same_src->next_same_src = edge->next_same_src;
        else // 如果是首边，更新首边指针
            this->nodes->at(edge->src)->first_out_edge = edge->next_same_src;
        if (edge->next_same_src != NULL) // 如果有同源后继边，更新后继边的同源前驱指针
            edge->next_same_src->prev_same_src = edge->prev_same_src;
        delete edge;      // 删除边
        edge = next_edge; // 更新当前边为下一条边
    }

    // 释放节点内存
    delete node;
    this->nodes->at(id) = NULL;       // 清除节点指针，避免野指针
    this->reusable_node_id->push(id); // 将节点ID放入可重用节点ID数组

    this->num_nodes--; // 节点数量减1

    return 0; // 返回成功代码
}

int CDiGraph::remove_edge(long long src, long long dst)
{
    CDiEdge *edge = this->get_edge(src, dst); // 检查源节点和目标节点是否存在
    if (edge == NULL)
        return -1; // 返回错误代码

    // 更新同源边之间的关系
    if (edge->prev_same_dst != NULL) // 如果有同目标前驱边，更新前驱边的同目标后继指针
        edge->prev_same_dst->next_same_dst = edge->next_same_dst;
    else // 如果是首边，更新首边指针
        this->nodes->at(edge->dst)->first_in_edge = edge->next_same_dst;
    if (edge->next_same_dst != NULL) // 如果有同目标后继边，更新后继边的同目标前驱指针
        edge->next_same_dst->prev_same_dst = edge->prev_same_dst;
    this->nodes->at(src)->num_out_edges--; // 源节点的出边数量减1

    // 更新同目标边之间的关系
    if (edge->prev_same_src != NULL) // 如果有同源前驱边，更新前驱边的同源后继指针
        edge->prev_same_src->next_same_src = edge->next_same_src;
    else // 如果是首边，更新首边指针
        this->nodes->at(edge->src)->first_out_edge = edge->next_same_src;
    if (edge->next_same_src != NULL) // 如果有同源后继边，更新后继边的同源前驱指针
        edge->next_same_src->prev_same_src = edge->prev_same_src;
    this->nodes->at(dst)->num_in_edges--; // 目标节点的入边数量减1

    delete edge;       // 删除边
    this->num_edges--; // 边数量减1

    return 0; // 返回成功代码
}

int CDiGraph::clear()
{
    // 释放节点数据结构
    for (long long i = 0; i < this->num_nodes; i++)
    {
        CDiNode *node = this->nodes->at(i); // 节点指针
        if (node != NULL)
        {
            // 释放节点的边数据结构（只需处理出边即可，入边会在其它节点的出边列表中处理）
            CDiEdge *edge = node->first_out_edge;
            CDiEdge *next_edge;
            node->first_out_edge = NULL; // 清除出边指针，避免野指针
            node->first_in_edge = NULL;  // 清除节点入边指针，避免野指针
            while (edge != NULL)
            {
                next_edge = edge->next_same_src;
                delete edge;
                edge = next_edge;
            }
            delete node; // 释放节点
        }
    }

    this->num_nodes = 0; // 节点数量清零
    num_edges = 0;       // 边数量清零

    // 重置图节点数组
    this->nodes->clear(); // 清空节点数组
    while (!this->reusable_node_id->empty())
    {
        // 清空可重用节点ID数组
        this->reusable_node_id->pop();
    }

    return 0; // 返回成功代码
}

int CDiGraph::compact_nodes()
{
    // 整理节点数组的内存占用（当前节点数组中有空指针时）
    long long new_id = 0; // 新节点ID
    for (long long i = 0; i < this->nodes->size(); i++)
    {
        CDiNode *node = this->nodes->at(i); // 节点指针
        if (node != NULL)
        {
            if (node->id != new_id)
            {
                // 如果节点ID与新ID不匹配（前面有NULL），则将其移动到新位置
                this->nodes->at(new_id) = node; // 将节点移动到新位置
                this->nodes->at(i) = NULL;      // 清除旧位置处的指针
                node->id = new_id;              // 更新节点ID

                // 更新该节点出入边中对应的节点ID
                CDiEdge *edge = node->first_out_edge;
                while (edge != NULL)
                {
                    edge->src = new_id;
                    edge = edge->next_same_src;
                }
                edge = node->first_in_edge;
                while (edge != NULL)
                {
                    edge->dst = new_id;
                    edge = edge->next_same_dst;
                }
            }
            new_id++;
        }
    }

    this->nodes->resize(new_id);  // 调整节点数组大小
    this->nodes->shrink_to_fit(); // 收缩节点数组的内存占用

    while (!this->reusable_node_id->empty())
    {
        // 清空可重用节点ID数组
        this->reusable_node_id->pop();
    }

    return 0; // 返回成功代码
}

CDiNode *CDiGraph::get_node(long long id)
{
    // 检查节点ID是否有效
    if (id < 0 || id >= this->nodes->size())
    {
        printf("Invalid index: %lld\n", id);
        return NULL; // 返回空指针
    }
    else if (this->nodes->at(id) == NULL)
    {
        printf("Node %lld is NULL\n", id);
        return NULL; // 返回空指针
    }

    return this->nodes->at(id); // 返回节点指针
}

CDiEdge *CDiGraph::get_edge(long long src, long long dst)
{
    // 检查源节点和目标节点是否存在
    if (src < 0 || src >= this->nodes->size())
    {
        printf("Invalid src index: %lld\n", src);
        return NULL; // 返回空指针
    }
    else if (this->nodes->at(src) == NULL)
    {
        printf("Src node %lld is NULL\n", src);
        return NULL; // 返回空指针
    }
    if (dst < 0 || dst >= this->nodes->size())
    {
        printf("Invalid dst index: %lld\n", dst);
        return NULL; // 返回空指针
    }
    else if (this->nodes->at(dst) == NULL)
    {
        printf("Dst node %lld is NULL\n", dst);
        return NULL; // 返回空指针
    }

    // 查找边结构体
    CDiEdge *edge;
    if (this->nodes->at(src)->num_out_edges < this->nodes->at(dst)->num_in_edges)
    {
        edge = this->nodes->at(src)->first_out_edge; // 从源节点的出边列表开始查找
        while (edge != NULL && edge->dst != dst)
        {
            if (edge->dst > dst)
                return NULL;            // 如果源节点的出边列表中没有目标节点，返回空指针
            edge = edge->next_same_src; // 否则继续遍历同源边
        }
    }
    else
    {
        edge = this->nodes->at(dst)->first_in_edge; // 从目标节点的入边列表开始查找
        while (edge != NULL && edge->src != src)
        {
            if (edge->src > src)
                return NULL;            // 如果目标节点的入边列表中没有源节点，返回空指针
            edge = edge->next_same_dst; // 遍历同目标边
        }
    }

    return edge; // 返回找到的边结构体指针
}