from quick_algo.di_graph import DiGraph


def run_pagerank(
    graph: DiGraph,
    init_score: None | dict[str, float] = None,
    personalization: None | dict[str, float] = None,
    dangling_weight: None | dict[str, float] = None,
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> dict[str, float]:
    """
    Run the PageRank algorithm on a directed graph.

    Args:
        graph (DiGraph): The directed graph on which to run PageRank.
        init_score (dict[str, float], optional): Initial scores for nodes. Defaults to None.
        personalization (dict[str, float], optional): Personalization vector. Defaults to None.
        dangling_weight (dict[str, float], optional): Weights for dangling nodes. Defaults to None.
        alpha (float, optional): Damping factor. Defaults to 0.85.
        max_iter (int, optional): Maximum number of iterations. Defaults to 100.
        tol (float, optional): Tolerance for convergence. Defaults to 1e-6.

    Returns:
        dict[str, float]: A dictionary mapping node identifiers to their PageRank scores.
    """
    ...