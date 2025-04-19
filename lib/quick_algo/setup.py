from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize

ext_modules = [
    Extension(
        "quick_algo.di_graph.di_graph",
        sources=[
            "quick_algo/di_graph/di_graph.pyx",
        ],
        include_dirs=["quick_algo/di_graph/cpp"],
        extra_compile_args=["-std=c++11"],
        language="c++",
    ),
    Extension(
        "quick_algo.pagerank.pagerank",
        sources=[
            "quick_algo/pagerank/pagerank.pyx",
        ],
        include_dirs=["quick_algo/pagerank/cpp", "quick_algo/di_graph/cpp"],
        extra_compile_args=["-std=c++11"],
        language="c++",
    ),
]

if __name__ == "__main__":
    setup(
        name="quick_algo",
        version="0.1.0",
        packages=find_packages(),
        ext_modules=cythonize(ext_modules),
    )
