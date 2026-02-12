#!/bin/bash
# 打包脚本 - 将应用打包为 macOS .app 文件（使用项目虚拟环境）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "开始打包单词卡片应用..."

# 使用当前项目的虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "使用虚拟环境: $SCRIPT_DIR/venv"
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    echo "使用虚拟环境: $SCRIPT_DIR/.venv"
    source .venv/bin/activate
else
    echo "错误: 未找到项目虚拟环境。"
    echo "请先创建并激活虚拟环境，例如："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 检查是否安装了 PyInstaller
if ! python -m pyinstaller --version &>/dev/null; then
    echo "正在安装 PyInstaller..."
    pip install pyinstaller
fi

# 清理之前的构建（保留 .spec 文件）
echo "清理之前的构建文件..."
rm -rf build dist
[ -d __pycache__ ] && rm -rf __pycache__

# 使用 PyInstaller 打包
echo "正在打包应用..."
python -m PyInstaller word_card_app.spec --clean

# 检查是否成功创建 .app 文件
if [ -d "dist/单词卡片.app" ]; then
    echo ""
    echo "✓ 打包成功！"
    echo "应用位置: $(pwd)/dist/单词卡片.app"
    echo ""
    echo "你可以："
    echo "1. 双击 dist/单词卡片.app 来运行应用"
    echo "2. 将 dist/单词卡片.app 拖拽到应用程序文件夹"
    echo ""
else
    echo "✗ 打包失败，请检查错误信息"
    exit 1
fi
