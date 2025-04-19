@REM 该脚本用于自动构建和安装 QuickAlgo 库.

@echo off
chcp 65001 >nul

setlocal ENABLEEXTENSIONS

REM 1. 检查当前目录是否是 quick_algo.
for %%F in (.) do set CurrDirName=%%~nxF
if /I not "%CurrDirName%"=="quick_algo" (
    echo 当前目录不是 "quick_algo"，请切换到正确的目录后再运行。
    goto :EOF
)

REM 2. 检查 Python 版本是否為 3.12 或以上.
set "PYTHON_CMD=python"
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul') do set PYTHON_VERSION=%%i

if not defined PYTHON_VERSION (
    echo 未找到 Python，请确保已正确安装并添加到 PATH。
    goto :EOF
)

for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set /a PY_MAJOR=%%a
    set /a PY_MINOR=%%b
)

if %PY_MAJOR% LSS 3 (
    echo Python 版本过低，至少需要 3.12。
    goto :EOF
) else if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 12 (
    echo Python 版本为 %PYTHON_VERSION%，需要 3.12 或更高版本。
    goto :EOF
)

echo Python 版本符合要求：%PYTHON_VERSION%

REM 3. 检查是否安装了 Cython.
%PYTHON_CMD% -c "import Cython" 2>nul
if errorlevel 1 (
    echo 未安装 Cython，请使用 pip install cython 安装.
    goto :EOF
) else (
    echo Cython 已安装.
)

REM 4. 构建依赖库.
echo 开始构建

%PYTHON_CMD% setup.py build_ext --inplace --force
if errorlevel 1 (
    echo 构建失败，请检查错误信息。
    goto :EOF
) else (
    echo 构建成功。
)

REM 5. 安装依赖库.
echo 开始安装

%PYTHON_CMD% setup.py install --force
if errorlevel 1 (
    echo 安装失败，请检查错误信息。
    goto :EOF
) else (
    echo 安装成功。
)