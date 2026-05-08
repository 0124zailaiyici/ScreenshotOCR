# ScreenshotOCR

一个 Windows 截图工具，支持**截图选区后三选一操作**：钉住到屏幕、OCR 识别文字、复制图片。常驻系统托盘，全局热键触发，无需联网。

## 功能

| 功能 | 说明 |
|------|------|
| 截图选区 | `Ctrl+Shift+A` 全局热键，任意应用中触发 |
| 钉住 | 截图浮在屏幕最上层，滚轮缩放，拖拽移动，Esc 关闭 |
| 识字 (OCR) | 识别截图中英文文字，弹出窗口自由选择复制 |
| 复制图片 | 一键复制截图到剪贴板 |

## 界面预览

```
按 Ctrl+Shift+A → 拖拽选区 → 松开鼠标 → 浮动工具栏

    ┌─────────────┐
    │  钉住  识字  复制 │    ← 选区旁的浮动按钮
    └─────────────┘

钉住：截图浮窗，滚轮缩放，无边框
识字：OCR 文字窗口，选中后 Ctrl+C 复制
复制：直接复制图片到剪贴板
```

## 快速开始

### 方式一：下载 exe（推荐）

从 [Releases](https://github.com/0124zailaiyici/ScreenshotOCR/releases) 下载 `ScreenshotOCR.exe`，双击运行，托盘出现图标即可使用。

### 方式二：从源码运行

**环境要求**：Python 3.10+

```bash
# 1. 克隆仓库
git clone https://github.com/0124zailaiyici/ScreenshotOCR.git
cd ScreenshotOCR

# 2. 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行
python main.py
```

## OCR 识字功能配置

识字功能需要安装 **Tesseract-OCR**（开源 OCR 引擎）：

### 安装 Tesseract

1. 下载安装包：[Tesseract-OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
2. 运行安装程序，记下安装路径（默认 `C:\Program Files\Tesseract-OCR\`）
3. 下载中文语言包：[chi_sim.traineddata](https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata)
4. 将 `chi_sim.traineddata` 放到 Tesseract 安装目录的 `tessdata` 文件夹中

### 配置 Tesseract 路径

如果 Tesseract 安装在非默认路径（如 `D:\develop\tesseract\`），需要在配置文件中指定。

配置文件位置：`C:\Users\<用户名>\.screenshot_ocr_config.json`

```json
{
    "hotkey": "<ctrl>+<shift>+a",
    "ocr_backend": "tesseract",
    "ocr_lang": "chi_sim+eng",
    "tesseract_path": "D:/develop/tesseract/tesseract.exe",
    "notification_enabled": true
}
```

## 配置文件说明

首次运行后自动生成 `~/.screenshot_ocr_config.json`：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `hotkey` | `<ctrl>+<shift>+a` | 全局快捷键，格式如 `<ctrl>+<shift>+x` |
| `ocr_backend` | `tesseract` | OCR 引擎，目前仅支持 tesseract |
| `ocr_lang` | `chi_sim+eng` | OCR 语言，`eng` 仅英文，`chi_sim+eng` 中英混合 |
| `tesseract_path` | `""` | Tesseract 安装路径，留空自动查找 |
| `notification_enabled` | `true` | 是否显示托盘通知气泡 |

## 依赖

### Python 包

```
pynput>=1.7.6        # 全局热键
pystray>=0.19.5      # 系统托盘
pytesseract>=0.3.10  # OCR Python 绑定
Pillow>=10.0.0       # 图像处理
pywin32>=306         # Windows API（剪贴板等）
```

### 外部依赖

| 软件 | 用途 | 必需 |
|------|------|------|
| Tesseract-OCR 5.x | OCR 文字识别 | 仅识字功能需要 |

## 打包为 exe

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name "ScreenshotOCR" \
  --hidden-import pystray --hidden-import pynput \
  --hidden-import pytesseract --hidden-import win32clipboard \
  --add-data "ocr_backends;ocr_backends" main.py
```

输出在 `dist/ScreenshotOCR.exe`。

## 项目结构

```
.
├── main.py                 # 入口：托盘 + 热键 + 流程调度
├── screenshot_overlay.py   # 全屏选区覆盖层 + 浮动工具栏
├── pin_window.py           # 钉住浮窗（无边框、滚轮缩放）
├── ocr_window.py           # OCR 文字识别窗口
├── ocr_engine.py           # OCR 引擎工厂
├── ocr_backends/           # OCR 后端实现
│   ├── base.py             #   抽象基类
│   └── tesseract_backend.py#   Tesseract 后端
├── clipboard_manager.py    # 剪贴板管理（图片/文字）
├── hotkey_listener.py      # 全局热键监听（pynput）
├── tray_app.py             # 系统托盘（pystray）
├── config.py               # 配置文件管理
└── requirements.txt        # Python 依赖清单
```

## 许可证

MIT
