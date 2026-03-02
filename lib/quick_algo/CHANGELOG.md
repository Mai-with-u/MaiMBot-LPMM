# v0.1.1
 - 仅打包 .cpp & .hpp 源码文件，不再打包 .pyx & .pxd ，用户安装包体时不再需要安装Cython

# v0.1.2
 - 停用OpenMP，避免Linux分发中PageRank的运行错误（且考虑到OpenMP带来的提升并不明显，故暂时不启用）
 - 添加Wheel包，支持Python 3.10-3.13（Windows、Linux）

# v0.1.3
 - 取消OpenMP需求
 - SIMD优化
 - 构建脚本优化

# v0.1.4
 - 修复macOS安装时的构建崩溃问题（去除对 `cpuinfo['flags']` 的硬依赖）
 - 安装构建流程支持在缺失预生成 `.cpp` 时自动回退到 `.pyx`（无需手动预编译）
 - 新增macOS wheel构建与发布流程，覆盖Intel（x86_64）和Apple Silicon（arm64）
