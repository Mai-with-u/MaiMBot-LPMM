#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import cpuinfo

from setuptools import find_packages, setup, Extension

platform_info = {
    "os": "Unknown",  # 操作系统
    "avx2": False,      # 是否支持AVX2指令集
    "neon": False,      # 是否支持ARM NEON指令集
}

build_args = {
    "no-simd": os.getenv("QUICK_ALGO_NO_SIMD") == "1"
}

# 获取平台信息
def get_platform_info():
    # 获取操作系统信息
    if sys.platform.startswith("linux"):
        platform_info["os"] = "Linux"
    elif sys.platform.startswith("win"):
        platform_info["os"] = "Windows"
    elif sys.platform.startswith("darwin"):
        platform_info["os"] = "macOS"

    # 获取CPU信息
    cpu_info = cpuinfo.get_cpu_info()
    
    # 检查是否为ARM架构
    is_arm_platform = cpu_info["arch"].lower() in ["aarch64", "arm64", "armv8", "arm"]
    
    if not build_args["no-simd"]:
        if is_arm_platform:
            # ARM平台上启用NEON，禁用AVX2
            # AArch64 处理器均支持NEON
            if cpu_info["arch"].lower() in ["aarch64", "arm64", "armv8"]:
                platform_info["neon"] = True
            # 对于ARMv7，需要检查flags中是否有neon标志
            elif "neon" in cpu_info.get("flags", []):
                platform_info["neon"] = True
        else:
            # 非ARM平台上检查AVX2支持
            if "avx2" in cpu_info["flags"]:
                platform_info["avx2"] = True

# 生成构建参数
def get_compile_and_link_args():
    get_platform_info()

    compile_args = []

    # 根据CPU架构确定使用的SIMD指令集
    cpu_info = cpuinfo.get_cpu_info()
    is_arm_platform = cpu_info["arch"].lower() in ["aarch64", "arm64", "armv8", "arm"]

    if is_arm_platform:
        # 在ARM平台上只使用NEON指令集
        if platform_info["neon"]:
            # 对于AArch64，NEON是默认的，不需要额外的编译选项
            # 但是我们添加宏定义，以便在代码中检测NEON支持
            compile_args.append("-D__ARM_NEON__")
            print("Enabled ARM NEON support")
    else:
        # 非ARM平台使用AVX2（如果支持）
        if platform_info["os"] == "Linux" or platform_info["os"] == "macOS":
            if platform_info["avx2"]:
                compile_args.append("-mavx2")
                compile_args.append("-D__AVX2__")
                print("Enabled AVX2 support")
        elif platform_info["os"] == "Windows":
            if platform_info["avx2"]:
                compile_args.append("/arch:AVX2")
                compile_args.append("-D__AVX2__")
                print("Enabled AVX2 support")
    
    link_args = []

    return compile_args, link_args

# 获取扩展模块
def get_ext_modules():
    compile_args, link_args = get_compile_and_link_args()
    ext_modules = [
        Extension(
            "quick_algo.di_graph",
            sources=[
                "src/quick_algo/di_graph.cpp",
                "src/quick_algo/cpp/di_graph_impl.cpp",
            ],
            include_dirs=[
                "src/quick_algo"
            ],
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language="c++",
        ),
        Extension(
            "quick_algo.pagerank",
            sources=[
                "src/quick_algo/pagerank.cpp",
                "src/quick_algo/cpp/pagerank_impl.cpp",
            ],
            include_dirs=[
                "src/quick_algo",
            ],
            extra_compile_args=compile_args,
            extra_link_args=link_args,
            language="c++",
        ),
    ]

    return ext_modules

setup(
    ext_modules=get_ext_modules(),
    packages=find_packages(where="src", exclude=["tests", "*.tests", "*.tests.*", "tests.*", "*/cpp*"]),
    include_package_data=True,
)
