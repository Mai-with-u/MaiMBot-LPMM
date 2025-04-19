#!/usr/bin/env sh
# 该脚本用于自动构建和安装 QuickAlgo 库

# 检查是否在正确的目录下运行
if [ ! -f "lib/quick_algo/build_lib.sh" ]; then
    echo "Please run this script from the root directory of the lib."
    exit 1
fi

# 检查环境
# 检查python和pip
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install it first."
    exit 1
fi
if ! command -v pip &> /dev/null; then
    echo "Pip 3 is not installed. Please install it first."
    exit 1
fi

# 检查Cython相关依赖
if ! pip show Cython &> /dev/null; then
    echo "Cython is not installed. Installing it now..."
    pip install Cython
fi

# 构建
echo "Building QuickAlgo..."
python setup.py build_ext --inplace --force
if [ $? -ne 0 ]; then
    echo "Build failed. Please check the error messages above."
    exit 1
fi
echo "Build completed successfully."

# 安装
echo "Installing QuickAlgo..."
python setup.py install --force
if [ $? -ne 0 ]; then
    echo "Installation failed. Please check the error messages above."
    exit 1
fi
echo "Installation completed successfully."



