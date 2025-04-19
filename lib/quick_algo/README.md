# QuickAlgo
这是一个快速算法库，旨在为LPMM（Long-term and Persistent Memory）模块提供Graph数据结构和一些复杂算法的Cpp+Cython高效实现。

## 目录结构

```text

/┬- quick_algo - 项目目录  
 ├- quick_algo - 源码目录
 | ├- di_graph - 有向图实现
 | | ├- cpp - C++头文件&实现
 | | └- ...
 | ├- pagerank - PageRank算法实现
 | | ├- cpp - C++头文件&实现
 | | └- ...
 | └- ...
 ├- tests - 测试目录
 ├- build_lib.bat - Windows下的构建脚本
 ├- build_lib.sh - Linux下的构建脚本
 ├- README.md - 本文档
 └- setup.py - Python包安装脚本
```


## 构建
请在项目目录下执行`build_lib.bat`/`build_lib.sh`，这将在本目录下构建本依赖库。

在构建之前，请确保您的电脑上装有以下依赖：

- MSVC（Windows）/GCC（Linux）
- Python 3.12
- Cython（Python包，通过pip安装）