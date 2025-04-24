# QuickAlgo
这是一个快速算法库，旨在为LPMM（Long-term and Persistent Memory）模块提供Graph数据结构和一些复杂算法的Cpp+Cython高效实现。

## 目录结构

```text

─ quick_algo - 项目目录  
 ├─ src - 源码目录
 │ └─ quick_algo - 纯C/C++代码目录
 │   ├─ cpp - 纯C/C++代码目录
 │   │ │ ├─ di_graph.hpp - 有向图头文件
 │   │ │ └─ di_graph_impl.cpp - 有向图实现
 │   │ ├─ cpp - 纯C/C++代码目录
 │   │ │ ├─ pagerank.hpp - 有向图头文件
 │   │ │ └─ pagerank_impl.cpp - 有向图实现
 │   │ ├─ __init__.py - Python包初始化文件
 │   │ ├─ di_graph.pxd - Cython头文件
 │   │ ├─ di_graph.pyi - di_graph类型声明文件
 │   │ └─ di_graph.pyx - Cython实现
 │   │ ├─ pagerank.pxd - Cython头文件
 │   │ ├─ pagerank.pyi - pagerank类型声明文件
 │   │ └─ pagerank.pyx - Cython实现
 │   └─ __init__.py - Python包初始化文件
 ├─ tests - 测试代码目录
 ├─ build_lib.py - 构建脚本
 ├─ pyproject.toml - Python项目配置文件
 ├─ setup.py - buildtools安装脚本
 ├─ LICENSE.txt - 许可证
 └─ README.md - 本文档
```


## 构建脚本
请在项目目录下执行`build_lib.py`并添加相应的任务，这将自动化构建过程。

该脚本支持以下任务：
- `--cleanup`：清理构建目录和临时文件
- `--cythonize`：编译Cython代码（要求依赖`cython`）
- `--force_cythonize`: 强制重新编译Cython代码（要求依赖`cython`）
- `--build_dist`：构建Python包（要求依赖`setuptools`）
- `--build_wheel`：构建Python wheel包（要求依赖`setuptools`, 要求C/Cpp编译环境）
- `--install`：安装Python包（要求依赖`setuptools`, 要求C/Cpp编译环境）

## 安装
您可以直接使用`pip install quick_algo`进行安装：
```bash
pip install quick_algo
```
> 注：PyPI上提供的二进制包默认不开启SIMD优化，您可以通过编译源码分发包来启用该特性

您也可以在clone本仓库之后通过前述构建脚本于本地进行编译安装。

在编译安装之前，请确保您装有以下依赖：
- `setuptools`: Python包管理工具
- `Cython`: Cython编译器
- `py-cpuinfo`: CPU信息获取库
- `MSVC/GCC/Clang`: C/Cpp编译环境

要使用脚本编译安装，请在项目目录下执行以下命令：
```bash
python build_lib.py --cleanup --cythonize --install
```

## 测试
本项目的测试代码位于tests目录下，使用`pytest`进行测试。

在测试之前，请确保您装有以下依赖：
- `pytest`：测试框架
- `networkx`: 图算法库
- `numpy`: 数值计算库(由networkx要求)
- `scipy`: 数值计算库(由networkx要求)

要运行测试，请在项目目录下执行以下命令：
```bash
pytest ./tests -s
```