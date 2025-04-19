from ..di_graph.di_graph cimport CDiGraph

cdef extern from "cpp/pagerank_impl.cpp":
    double *pagerank(
            CDiGraph *graph,
            double *init_score_vec,
            double *personalization_vec,
            double *dangling_weight_vec,
            double alpha,
            int max_iter,
            double tol
    )