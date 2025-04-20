# Unit tests for the DiGraph class in quick_algo
from quick_algo.di_graph import DiGraph, DiNode, DiEdge, save_to_file, load_from_file


class TestDiGraph:
    def test_node_operation(self):
        print("\nRunning TestDiGraph - 1")

        graph = DiGraph()
        # 测试空图
        print("TestDiGraph - 1 - CP1")
        assert graph.get_node_list() == []
        assert graph.get_edge_list() == []

        # 添加单个节点
        print("TestDiGraph - 1 - CP2")
        graph.add_node(DiNode("node1", {"update_time": 100}))
        assert graph.get_node_list() == ["node1"]
        assert "update_time" in graph["node1"]
        # 添加多个节点
        print("TestDiGraph - 1 - CP3")
        graph.add_nodes_from([DiNode("node2"), DiNode("node3")])
        assert "node2" in graph
        assert "node3" in graph
        assert graph["node2"].attr == {}

        # 重复添加节点
        print("TestDiGraph - 1 - CP4")
        try:
            graph.add_node(DiNode("node1", {"update_time": 200}))
            assert False  # 如果没有抛出异常，则测试失败
        except KeyError:
            pass

        # 修改节点属性
        print("TestDiGraph - 1 - CP5")
        updated_node = graph["node1"]
        assert isinstance(updated_node, DiNode)
        updated_node["update_time"] = 200
        graph.update_node(updated_node)
        assert graph["node1"]["update_time"] == 200

        # 删除节点
        print("TestDiGraph - 1 - CP6")
        del graph["node2"]
        assert "node2" not in graph
        try:
            _node = graph["node2"]
            assert False  # 如果没有抛出异常，则测试失败
        except KeyError:
            pass

        # 删除不存在的节点
        print("TestDiGraph - 1 - CP7")
        try:
            del graph["N/A"]
            assert False  # 如果没有抛出异常，则测试失败
        except KeyError:
            pass

    def test_edge_operation(self):
        print("\nRunning TestDiGraph - 2")

        graph = DiGraph()
        # 添加一条边
        print("TestDiGraph - 2 - CP1")
        graph.add_edge(DiEdge("node1", "node2", {"weight": 1.0, "update_time": 100}))
        assert "node1" in graph
        assert "node2" in graph
        assert ("node1", "node2") in graph
        assert "update_time" in graph["node1", "node2"]
        # 添加多条边
        print("TestDiGraph - 2 - CP2")
        graph.add_edges_from(
            [
                DiEdge("node2", "node3", {"weight": 2.0}),
                DiEdge("node3", "node1", {"weight": 3.0}),
            ]
        )
        assert ("node2", "node3") in graph
        assert ("node3", "node1") in graph
        assert list(graph["node2", "node3"].attr.keys()) == ["weight"]
        assert graph["node2", "node3"]["weight"] == 2.0

        # 重复添加边
        print("TestDiGraph - 2 - CP3")
        try:
            graph.add_edge(
                DiEdge("node1", "node2", {"weight": 1.0, "update_time": 200})
            )
            assert False  # 如果没有抛出异常，则测试失败
        except KeyError:
            pass

        # 修改边属性
        print("TestDiGraph - 2 - CP4")
        updated_edge = graph["node1", "node2"]
        assert isinstance(updated_edge, DiEdge)
        assert updated_edge["weight"] == 1.0
        updated_edge["update_time"] = 200
        updated_edge["weight"] += 1
        graph.update_edge(updated_edge)
        assert graph["node1", "node2"]["update_time"] == 200
        assert graph["node1", "node2"]["weight"] == 2.0

        # 删除边
        print("TestDiGraph - 2 - CP5")
        del graph["node2", "node3"]
        assert ("node2", "node3") not in graph
        try:
            _edge = graph["node2", "node3"]
            assert False  # 如果没有抛出异常，则测试失败
        except KeyError:
            pass

        # 删除节点之后的边
        print("TestDiGraph - 2 - CP6")
        assert ("node1", "node2") in graph
        assert ("node3", "node1") in graph
        del graph["node1"]
        assert ("node1", "node2") not in graph
        assert ("node3", "node1") not in graph

    def test_compact_node_array(self):
        print("\nRunning TestDiGraph - 3")

        graph = DiGraph()
        # 添加节点
        print("TestDiGraph - 3 - CP1")
        graph.add_nodes_from(
            [
                DiNode("node1"),
                DiNode("node2"),
                DiNode("node3"),
                DiNode("node4"),
                DiNode("node5"),
            ]
        )

        # 添加边
        print("TestDiGraph - 3 - CP2")
        graph.add_edges_from(
            [
                DiEdge("node1", "node2"),
                DiEdge("node3", "node5"),
            ]
        )

        # 删除节点
        print("TestDiGraph - 3 - CP3")
        del graph["node2"]
        del graph["node4"]

        # 执行压缩
        print("TestDiGraph - 3 - CP4")
        graph.compact_node_array()

        # 检查节点是否被正确压缩
        print("TestDiGraph - 3 - CP5")
        assert graph["node1"] is not None
        try:
            _node = graph["node2"]
            assert False  # 如果没有抛出异常，则测试失败
        except KeyError:
            pass
        assert graph["node3", "node5"] is not None
        try:
            _edge = graph["node1", "node2"]
            assert False  # 如果没有抛出异常，则测试失败
        except KeyError:
            pass

        # 检查压缩完整性
        print("TestDiGraph - 3 - CP6")
        assert len(graph.get_node_list()) == 3
        assert len(graph.get_edge_list()) == 1
        assert "node1" in graph
        assert "node3" in graph
        assert "node5" in graph
        assert ("node3", "node5") in graph

    def test_save_load(self):
        print("\nRunning TestDiGraph - 4")

        graph = DiGraph()
        # 添加节点和边
        print("TestDiGraph - 4 - CP1")
        graph.add_nodes_from(
            [
                DiNode("node1", {"content": "test content"}),
                DiNode("node2", {"content": "test content"}),
                DiNode("node3"),
            ]
        )
        graph.add_edges_from(
            [
                DiEdge("node1", "node2", {"weight": 1.0, "update_time": 100}),
                DiEdge("node2", "node3"),
            ]
        )

        # 保存图
        print("TestDiGraph - 4 - CP2")
        save_to_file(graph, "test_graph.graphml")
        save_to_file(graph, "test_graph.graphmlz", enable_zip=True)

        # 加载图
        print("TestDiGraph - 4 - CP3")
        loaded_graph = load_from_file("test_graph.graphml")
        # 检查加载的图是否与原图相同
        for node_name in graph.get_node_list():
            assert node_name in loaded_graph
            assert graph[node_name].attr == loaded_graph[node_name].attr
        for edge_key in graph.get_edge_list():
            assert edge_key in loaded_graph
            assert graph[edge_key].attr == loaded_graph[edge_key].attr

        print("TestDiGraph - 4 - CP4")
        # 检查加载的图是否与原图相同
        loaded_graph = load_from_file("test_graph.graphmlz")
        for node_name in graph.get_node_list():
            assert node_name in loaded_graph
            assert graph[node_name].attr == loaded_graph[node_name].attr
        for edge_key in graph.get_edge_list():
            assert edge_key in loaded_graph
            assert graph[edge_key].attr == loaded_graph[edge_key].attr

        # 清理（删除保存的文件）
        print("TestDiGraph - 4 - CP5")
        import os
        if os.path.exists("test_graph.graphml"):
            os.remove("test_graph.graphml")
        if os.path.exists("test_graph.graphmlz"):
            os.remove("test_graph.graphmlz")

    def test_clear(self):
        print("\nRunning TestDiGraph - 5")

        graph = DiGraph()
        # 添加节点和边
        print("TestDiGraph - 5 - CP1")
        graph.add_nodes_from(
            [
                DiNode("node1", {"content": "test content"}),
                DiNode("node2", {"content": "test content"}),
                DiNode("node3"),
            ]
        )
        graph.add_edges_from(
            [
                DiEdge("node1", "node2", {"weight": 1.0, "update_time": 100}),
                DiEdge("node2", "node3"),
            ]
        )

        # 清空图
        print("TestDiGraph - 5 - CP2")
        graph.clear()

        # 检查图是否为空
        print("TestDiGraph - 5 - CP3")
        assert len(graph.get_node_list()) == 0
        assert len(graph.get_edge_list()) == 0

        # 再次添加节点和边
        print("TestDiGraph - 5 - CP4")
        graph.add_nodes_from(
            [
                DiNode("node1", {"content": "test content2"}),
                DiNode("node2", {"content": "test content2"}),
                DiNode("node3"),
            ]
        )
        graph.add_edges_from(
            [
                DiEdge("node2", "node3", {"weight": 1.0, "update_time": 200}),
                DiEdge("node1", "node3"),
            ]
        )

        # 检查图是否重新添加成功
        print("TestDiGraph - 5 - CP5")
        assert len(graph.get_node_list()) == 3
        assert len(graph.get_edge_list()) == 2
        assert "node1" in graph
        assert "node2" in graph
        assert "node3" in graph
        assert ("node2", "node3") in graph
        assert ("node1", "node3") in graph
        assert graph["node2", "node3"]["weight"] == 1.0
        assert graph["node2", "node3"]["update_time"] == 200
        assert graph["node1"]["content"] == "test content2"
        assert graph["node2"]["content"] == "test content2"

