#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import Extension, find_packages, setup

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

import os
import platform
import sys


platform_info = {
    "os": "Unknown",  # 操作系统
    "machine": platform.machine().lower(),  # CPU架构
}

build_args = {
    "with-simd": os.getenv("QUICK_ALGO_SIMD") == "1"
}


if sys.platform.startswith("linux"):
    platform_info["os"] = "Linux"
elif sys.platform.startswith("win"):
    platform_info["os"] = "Windows"
elif sys.platform.startswith("darwin"):
    platform_info["os"] = "macOS"


# 检查是否为ARM架构
def is_arm_platform():
    return any(
        arm_arch in platform_info["machine"] for arm_arch in ["aarch64", "arm64", "armv8", "arm"]
    )


# 生成构建参数
def get_compile_and_link_args():
    compile_args = []
    link_args = []

    if not build_args["with-simd"]:
        return compile_args, link_args

    if is_arm_platform():
        compile_args.append("-D__ARM_NEON__")
        return compile_args, link_args

    if platform_info["os"] in ["Linux", "macOS"]:
        compile_args.extend(["-mavx2", "-D__AVX2__"])
    elif platform_info["os"] == "Windows":
        compile_args.extend(["/arch:AVX2", "/D__AVX2__"])

    return compile_args, link_args


# 解析扩展模块主源文件：优先使用预生成的cpp，缺失时回退到pyx
# 当包中包含预生成cpp时无需Cython，仅在回退pyx时才需要Cython
def resolve_source_file(cpp_source, pyx_source):
    if Path(cpp_source).exists():
        return cpp_source, False
    if Path(pyx_source).exists():
        return pyx_source, True
    raise FileNotFoundError(
        f"Cannot find extension source file, expected one of: {cpp_source}, {pyx_source}"
    )


# 获取扩展模块
def get_ext_modules():
    compile_args, link_args = get_compile_and_link_args()
    extension_targets = [
        (
            "quick_algo.di_graph",
            "src/quick_algo/di_graph.cpp",
            "src/quick_algo/di_graph.pyx",
            "src/quick_algo/cpp/di_graph_impl.cpp",
        ),
        (
            "quick_algo.pagerank",
            "src/quick_algo/pagerank.cpp",
            "src/quick_algo/pagerank.pyx",
            "src/quick_algo/cpp/pagerank_impl.cpp",
        ),
    ]

    ext_modules = []
    require_cython = False

    for module_name, cpp_source, pyx_source, cpp_impl in extension_targets:
        source_entry, use_cython = resolve_source_file(cpp_source, pyx_source)
        require_cython = require_cython or use_cython
        ext_modules.append(
            Extension(
                module_name,
                sources=[
                    source_entry,
                    cpp_impl,
                ],
                include_dirs=[
                    "src/quick_algo"
                ],
                extra_compile_args=compile_args,
                extra_link_args=link_args,
                language="c++",
            )
        )

    if require_cython:
        if cythonize is None:
            raise RuntimeError(
                "Generated C++ sources are missing. Install Cython, or run "
                "'python build_lib.py --cythonize' before building quick-algo."
            )

        return cythonize(
            ext_modules,
            compiler_directives={"language_level": 3},
        )

    return ext_modules


setup(
    ext_modules=get_ext_modules(),
    packages=find_packages(where="src", exclude=["tests", "*.tests", "*.tests.*", "tests.*", "*/cpp*"]),
    package_data={
        "quick_algo": ["*.pyi"],
    },
    include_package_data=False,
)
