# distutils: language=c++

from libcpp.vector cimport vector

cdef extern from "cpp/di_graph.hpp":
    cdef cppclass CDiNode:
        # C++ class for directed node
        long long id
        CDiEdge *first_in_edge
        long long num_in_edges
        CDiEdge *first_out_edge
        long long num_out_edges

        CDiNode(long long) except +


    cdef cppclass CDiEdge:
        # C++ class for directed edge
        long long src
        long long dst
        double weight
        CDiEdge *next_same_src
        CDiEdge *prev_same_src
        CDiEdge *next_same_dst
        CDiEdge *prev_same_dst

        CDiEdge(long long, long long, double) except +

    cdef cppclass CDiGraph:
        # C++ class for directed graph
        vector[CDiNode *] *nodes
        long long num_nodes
        long long num_edges

        CDiGraph(long long num_nodes) except +
        long long add_node()
        int add_edge(long long src, long long dst, double weight)
        int remove_node(long long id)
        int remove_edge(long long src, long long dst)
        int clear()
        int compact_nodes()
        CDiNode *get_node(long long id)
        CDiEdge *get_edge(long long src, long long dst)

cdef class DiNode:
    cdef public str name
    cdef public dict[str, str | int | float] attr

cdef class DiEdge:
    cdef public str src
    cdef public str dst
    cdef public dict[str, str | int | float] attr

cdef class DiGraph:
    cdef CDiGraph *graph  # C++ directed graph object
    cdef public dict[str, int] node_name2idx_map
    cdef dict[tuple[str, str], int] edge_name2idx_map
    cdef dict[str | tuple[str, str], dict] name2attr_map