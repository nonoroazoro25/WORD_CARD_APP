# 打包说明

## 如何打包应用为可执行程序

### 方法一：使用打包脚本（推荐）

```bash
./build_app.sh
```

### 方法二：手动打包

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 使用 PyInstaller 打包：
```bash
pyinstaller word_card_app.spec --clean
```

## 打包结果

打包完成后，会在 `dist/` 目录下生成 `单词卡片.app` 文件。

## 使用方法

1. **直接运行**：双击 `dist/单词卡片.app` 即可运行应用
2. **安装到应用程序**：将 `单词卡片.app` 拖拽到 `/Applications` 文件夹

## 注意事项

- 首次运行时，macOS 可能会提示"无法验证开发者"，需要在"系统偏好设置 > 安全性与隐私"中允许运行
- 应用的数据文件（数据库、日志等）会保存在应用所在目录
- 如果需要自定义图标，可以创建 `icon.icns` 文件并更新 `word_card_app.spec` 中的 `icon` 参数
