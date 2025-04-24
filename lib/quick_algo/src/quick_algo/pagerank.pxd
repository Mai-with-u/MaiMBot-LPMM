# distutils: language=c++

from .di_graph cimport CDiGraph

cdef extern from "cpp/pagerank.hpp":
    double *pagerank(
            CDiGraph *graph,
            double *init_score_vec,
            double *personalization_vec,
            double *dangling_weight_vec,
            double alpha,
            int max_iter,
            double tol
    )