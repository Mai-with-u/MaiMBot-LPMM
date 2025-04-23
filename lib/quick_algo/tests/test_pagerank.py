import os
import random
import time

import networkx
from quick_algo.pagerank import run_pagerank
from quick_algo.di_graph import DiGraph, DiEdge



def generate_rand_data(node_num: int, edge_num: int):
    edge_list = dict()
    for i in range(node_num):
        # 对每个节点，至少有一条出边或入边
        if random.random() < 0.5:
            # 生成出边
            while True:
                j = random.randint(0, node_num - 1)
                if i != j and (i, j) not in edge_list:
                    break
            edge_list[(i, j)] = random.random()
        else:
            # 生成入边
            while True:
                j = random.randint(0, node_num - 1)
                if i != j and (j, i) not in edge_list:
                    break
            edge_list[(j, i)] = random.random()
    # 再随机生成剩余的边
    for i in range(edge_num - node_num):
        while True:
            j = random.randint(0, node_num - 1)
            k = random.randint(0, node_num - 1)
            if j != k and (j, k) not in edge_list:
                break
        edge_list[(j, k)] = random.random()

    personalization = dict()
    for i in range(node_num // 10):
        while True:
            j = random.randint(0, node_num)
            if j not in personalization:
                break
        personalization[str(j)] = random.random()

    return edge_list, personalization


class TestPageRank:
    def test_pagerank(self):
        print("Running TestPageRank - 1")
        graph = DiGraph()
        nx_graph = networkx.DiGraph()

        # 测试数据
        print("TestPageRank - 1 - CP1")

        edge_list, personalization = generate_rand_data(100, 1000)

        graph.add_edges_from(
            [
                DiEdge(str(src), str(dst), {"weight": weight})
                for (src, dst), weight in edge_list.items()
            ]
        )
        nx_graph.add_edges_from(
            [
                (str(src), str(dst), {"weight": weight})
                for (src, dst), weight in edge_list.items()
            ]
        )

        # 随机生成个性化向量


        alpha = 0.85
        max_iter = 100
        tol = 1e-6

        # 调用PageRank算法
        print("TestPageRank - 1 - CP2")
        timer = time.perf_counter()
        result = run_pagerank(
            graph,
            personalization=personalization,
            alpha=alpha,
            max_iter=max_iter,
            tol=tol
        )
        print(f"QuickAlgo PPR Time taken: {time.perf_counter() - timer:.8f}s")

        timer = time.perf_counter()
        nx_result = networkx.pagerank(
            nx_graph,
            personalization=personalization,
            alpha=alpha,
            max_iter=max_iter,
            tol=tol,
        )
        print(f"NetworkX PPR Time taken: {time.perf_counter() - timer:.8f}s")

        # 检查结果
        print("TestPageRank - 1 - CP3")
        for node in nx_result:
            assert abs(result[node] - nx_result[node]) < 1e-6, f"Test failed for node {node}"


    def test_pr_speed(self):
        print("Running TestPageRank - 2")

        time_cost_qa = []
        time_cost_nx = []

        alpha = 0.85
        max_iter = 100
        tol = 1e-6

        # 加载测试数据
        if not os.path.exists("test_data.txt"):
            print("Generating test data...")
            edge_list, personalization = generate_rand_data(20000, 100000)
            with open("test_data.txt", "w") as f:
                f.write(f"{len(edge_list)} {len(personalization)}\n")
                for (src, dst), weight in edge_list.items():
                    f.write(f"{src} {dst} {weight}\n")
                for node, weight in personalization.items():
                    f.write(f"{node} {weight}\n")
                print("Test data generated and saved.")
        else:
            print("Loading test data...")
            with open("test_data.txt", "r") as f:
                lines = f.readlines()
                num_edges, num_personalization = map(int, lines[0].split())
                edge_list = dict()
                for i in range(1, num_edges + 1):
                    src, dst, weight = lines[i].split()
                    edge_list[(int(src), int(dst))] = float(weight)
                personalization = dict()
                for i in range(num_edges + 1, num_edges + num_personalization + 1):
                    node, weight = lines[i].split()
                    personalization[node] = float(weight)
                print("Test data loaded.")            

        for i in range(25):
            # 构造图
            graph = DiGraph()
            nx_graph = networkx.DiGraph()

            graph.add_edges_from(
                [
                    DiEdge(str(src), str(dst), {"weight": weight})
                    for (src, dst), weight in edge_list.items()
                ]
            )
            nx_graph.add_edges_from(
                [
                    (str(src), str(dst), {"weight": weight})
                    for (src, dst), weight in edge_list.items()
                ]
            )

            # 调用PageRank算法
            timer = time.perf_counter()
            result = run_pagerank(
                graph,
                personalization=personalization,
                alpha=alpha,
                max_iter=max_iter,
                tol=tol,
            )
            time_cost_qa.append(time.perf_counter() - timer)

            timer = time.perf_counter()
            nx_result = networkx.pagerank(
                nx_graph,
                personalization=personalization,
                alpha=alpha,
                max_iter=max_iter,
                tol=tol,
            )
            time_cost_nx.append(time.perf_counter() - timer)

        print("QuickAlgo PPR Time taken:")
        print(f"Avg: {sum(time_cost_qa) / len(time_cost_qa):.8f}s Min: {min(time_cost_qa):.8f}s Max: {max(time_cost_qa):.8f}s")
        print("NetworkX PPR Time taken:")
        print(f"Avg: {sum(time_cost_nx) / len(time_cost_nx):.8f}s Min: {min(time_cost_nx):.8f}s Max: {max(time_cost_nx):.8f}s")