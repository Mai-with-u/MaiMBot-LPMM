# -*- coding: utf-8 -*-
import argparse
import os
import logging
import subprocess
import sys
import shutil


pyx_modules = [
    "src/quick_algo/di_graph.pyx",
    "src/quick_algo/pagerank.pyx",
]

include_dirs = [
    "src/quick_algo/cpp",
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def init_logger():
    # 初始化logger
    console_logging_handler = logging.StreamHandler()
    console_logging_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    console_logging_handler.setLevel(logging.INFO)
    logger.addHandler(console_logging_handler)

def clean_up(args):
    # 清理构建内容
    logger.warning("Cleaning up build directory...")
    build_dirs=["build", "dist", "src/quick_algo.egg-info"]

    for dir_to_del in build_dirs:
        if os.path.exists(dir_to_del):
            shutil.rmtree(dir_to_del)
            logger.info(f"Removed {dir_to_del} directory.")

    for pyx_file in pyx_modules:
        # 删除生成的cpp文件
        cythonize_source = pyx_file.replace(".pyx", ".cpp")
        if os.path.exists(cythonize_source):
            os.remove(cythonize_source)
            logger.info(f"Removed {cythonize_source} file.")


def run_cythonize(args):
    logger.info("Cythonizing source files...")

    # 检查是否安装了Cython
    try:
        from Cython.Build import cythonize
    except ImportError:
        logger.fatal("Cython is not installed. Please install Cython to run cythonize.")
        sys.exit(1)

    cythonize(
        pyx_modules,
        compiler_directives={"language_level": 3},
        include_path=include_dirs,
        force=args.force_cythonize,
    )

    logger.info("Cythonize completed successfully.")

def run_build_sdist(args):
    logger.info("Building distribution package...")
    # 构建源码分发包
    exec_args=[sys.executable, "-m", "build", "--sdist"]
    if args.compile_no_simd:
        # 添加临时环境变量
        os.environ["QUICK_ALGO_NO_SIMD"] = "1"

    try:
        result = subprocess.run(
            exec_args,
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        logger.info("Build distribution package successfully. Output:\n%s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while building distribution package. Details:\n%s", e.stderr)
        logger.error(e.stderr)
        sys.exit(1)

def run_build_wheel(args):
    logger.info("Building wheel distribution package...")
    # 构建wheel二进制分发包
    exec_args = [sys.executable, "-m", "build", "--wheel"]
    if args.compile_no_simd:
        # 添加临时环境变量
        os.environ["QUICK_ALGO_NO_SIMD"] = "1"

    try:
        result = subprocess.run(
            exec_args,
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        logger.info("Build wheel distribution package successfully. Output:\n%s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while building wheel distribution package. Details:\n%s", e.stderr)
        logger.error(e.stderr)
        sys.exit(1)

def run_install(args):
    logger.info("Installing package...")
    # 直接安装库
    exec_args = [sys.executable, "-m", "pip", "install", "."]
    if args.compile_no_simd:
        # 添加临时环境变量
        os.environ["QUICK_ALGO_NO_SIMD"] = "1"

    try:
        result = subprocess.run(
            exec_args,
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        logger.info("Install package successfully. Output:\n%s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while installing package. Details:\n%s", e.stderr)
        logger.error(e.stderr)
        sys.exit(1)


def main(args):
    # 若配置了清理任务，则清理构建目录
    if args.cleanup:
        clean_up(args)

    # 若配置了编译Cython任务，则编译Cython源文件
    if args.cythonize or args.force_cythonize:
        run_cythonize(args)

    # 若配置了构建源码分发包任务，则构建源码分发包
    if args.build_sdist:
        # 执行setup.py构建分发包
        run_build_sdist(args)

    # 若配置了构建wheel分发包任务，则构建wheel分发包
    if args.build_wheel:
        # 执行setup.py构建wheel分发包
        run_build_wheel(args)

    # 若配置了直接安装任务，则直接安装
    if args.install:
        # 执行setup.py安装
        run_install(args)

if __name__ == "__main__":
    init_logger()

    # 检查是否在正确的目录下运行
    if not os.path.exists("./setup.py"):
        logger.fatal("Please run this script from the 'lib/quick_algo' directory.")
        sys.exit(1)

    # 检查Python版本
    if sys.version_info < (3, 10):
        logger.fatal("Python version 3.10 or higher is required.")
        sys.exit(1)

    arg_parser = argparse.ArgumentParser("Build QuickAlgo", description="A script to build QuickAlgo library.")
    arg_parser.add_argument("--cleanup", action="store_true", default=False, help="Cleanup the build directory")
    arg_parser.add_argument("--cythonize", action="store_true", default=False, help="Cythonize the source files")
    arg_parser.add_argument("--force_cythonize", action="store_true", default=False, help="Force Cythonize, even if the file is not changed")
    arg_parser.add_argument("--build_sdist", action="store_true", default=False, help="Build the source code distribution")
    arg_parser.add_argument("--build_wheel", action="store_true", default=False, help="Build the wheel distribution")
    arg_parser.add_argument("--install", action="store_true", default=False, help="Directly install the package")
    arg_parser.add_argument("--compile_no_simd", action="store_true", default=False, help="Compile without SIMD optimization")
    args = arg_parser.parse_args()

    main(args)