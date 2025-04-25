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
    is_arm_platform = False
    if "arch_string_raw" in cpu_info:
        arch_raw = cpu_info["arch_string_raw"].lower()
        is_arm_platform = any(arm_arch in arch_raw for arm_arch in ["aarch64", "arm64", "armv8", "arm"])
    
    # 备用检测方法
    if not is_arm_platform and "arch" in cpu_info:
        arch = cpu_info["arch"].lower()
        is_arm_platform = any(arm_arch in arch for arm_arch in ["aarch64", "arm64", "armv8", "arm"])
    
    # 将ARM信息保存到platform_info中
    platform_info["is_arm"] = is_arm_platform
    
    print(f"cpu info:{cpu_info}")
    if "flags" in cpu_info:
        print(f"CPU Flags: {cpu_info['flags']}")
    print(f"Detected Platform: {'ARM' if is_arm_platform else 'x86'}")
    
    if not build_args["no-simd"]:
        if is_arm_platform:
            # ARM平台上启用NEON，明确设置AVX2为False
            platform_info["avx2"] = False
            
            # AArch64 处理器均支持NEON
            if any(arm_arch in cpu_info.get("arch_string_raw", "").lower() 
                  for arm_arch in ["aarch64", "arm64", "armv8"]):
                platform_info["neon"] = True
                print("Enabled ARM NEON support (AArch64)")
            # 对于ARMv7，需要检查flags中是否有neon标志
            elif "neon" in cpu_info.get("flags", []):
                platform_info["neon"] = True
                print("Enabled ARM NEON support (ARMv7)")
        else:
            # 非ARM平台上检查AVX2支持
            platform_info["neon"] = False
            if "avx2" in cpu_info.get("flags", []):
                platform_info["avx2"] = True

# 生成构建参数
def get_compile_and_link_args():
    get_platform_info()

    compile_args = []
    
    print(f"Generating Compilation Parameters - Platform Detection: {'ARM' if platform_info['is_arm'] else 'x86'}")
    print(f"SIMD support: AVX2={platform_info['avx2']}, NEON={platform_info['neon']}")

    if platform_info["is_arm"]:
        # 在ARM平台上只使用NEON指令集，不添加AVX2相关参数
        if platform_info["neon"]:
            # 对于AArch64，NEON是默认的，不需要额外的编译选项
            # 但是我们添加宏定义，以便在代码中检测NEON支持
            compile_args.append("-D__ARM_NEON__")
            print("Enabled NEON support")
    else:
        # 非ARM平台才考虑使用AVX2
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