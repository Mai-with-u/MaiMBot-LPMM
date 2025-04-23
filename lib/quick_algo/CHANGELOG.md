# v0.1.1
 - 仅打包 .cpp & .hpp 源码文件，不再打包 .pyx & .pxd ，用户安装包体时不再需要安装Cython

# v0.1.2
 - 停用OpenMP，避免Linux分发中PageRank的运行错误（且考虑到OpenMP带来的提升并不明显，故暂时不启用）
 - 添加Wheel包，支持Python 3.10-3.13（Windows、Linux）

# v0.1.3
 - 取消OpenMP需求
 - SIMD优化
 - 构建脚本优化