#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
import cpuinfo

from setuptools import find_packages, setup, Extension

# Package meta-data.
NAME = "quick_algo"
DESCRIPTION = "A simple and fast Graph structure and PPR algorithm implementation based on Cpp&Cython."
URL = "https://github.com/MaiM-with-u/MaiMBot-LPMM"
EMAIL = "octautumn2002@gmail.com"
AUTHOR = "Oct Autumn"
REQUIRES_PYTHON = ">=3.10"
VERSION = "0.1.3"

# What packages are required for this module to be executed?
REQUIRED = [
    # 'requests', 'maya', 'records',
]

# What packages are optional?
EXTRAS = {
    # 'fancy feature': ['django'],
}

platform_info = {
    "avx2": False,      # 是否支持AVX2指令集
}

build_args = {
    "no-simd": False,  # 是否禁用SIMD优化
}

# 获取额外参数
def get_extra_args():
    if "--compile_no_simd" in sys.argv:
        # 禁用SIMD优化
        sys.argv.remove("--compile_no_simd")
        build_args["no-simd"] = True

# 获取平台信息
def get_platform_info():
    # 获取AVX2指令集支持情况
    cpu_info = cpuinfo.get_cpu_info()
    if "avx2" in cpu_info["flags"] and not build_args["no-simd"]:
        platform_info["avx2"] = True
    # TODO: 考虑支持ARM平台的SIMD指令集，如NEON等

# 生成构建参数
def get_compile_and_link_args():
    get_platform_info()
    compile_args = [
        "-O3"
    ]
    if platform_info["avx2"]:
        compile_args.append("-mavx2")
        compile_args.append("-D__AVX2__")
        print("Enabled AVX2 support")
    
    link_args = []

    return compile_args, link_args

# 获取扩展模块
def get_ext_modules():
    compile_args, link_args = get_compile_and_link_args()
    ext_modules = [
        Extension(
            "quick_algo.di_graph.di_graph",
            sources=[
                "quick_algo/di_graph/di_graph.cpp",
                "quick_algo/di_graph/cpp/di_graph_impl.cpp",
            ],
            include_dirs=[
                "quick_algo/di_graph"
            ],

            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language="c++",
        ),
        Extension(
            "quick_algo.pagerank.pagerank",
            sources=[
                "quick_algo/pagerank/pagerank.cpp",
                "quick_algo/pagerank/cpp/pagerank_impl.cpp",
            ],
            include_dirs=[
                "quick_algo/pagerank",
                "quick_algo/di_graph",
            ],
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language="c++",
        ),
    ]

    return ext_modules

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
    with open(os.path.join(here, project_slug, "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION

get_extra_args()    # 先于setup()函数调用，处理额外参数
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    ext_modules=get_ext_modules(),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],
    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Natural Language :: Chinese (Simplified)",
        "Programming Language :: C++",
        "Programming Language :: Cython",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
