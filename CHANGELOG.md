# 独轮车 DL Cart - 更新日志

## Unreleased (2026-04-20)

### 🎉 新增功能

#### 打包与运行环境
- ✅ **Playwright 依赖补齐** - `build.bat` 和 GitHub Actions 现会显式安装 `playwright`，避免在干净环境里执行 `python -m playwright install chromium` 时失败
- ✅ **设置项补全** - 设置窗口新增 `Proxy URL` 和 `Cookie Browser`，可以显式配置或清空代理与浏览器 Cookie 来源

#### 文档与说明
- ✅ **README 对齐真实行为** - 中英文 README 已补充源码运行/构建步骤、代理行为、Cookie 降级逻辑和新增设置项说明
- ✅ **故障排查增强** - 中英文 README 已增加代理错误和浏览器 Cookie 读取失败的排查说明

### 🐛 Bug修复

1. 修复了 `build.bat` / CI 未安装 `playwright` 就尝试安装 Chromium 的问题
2. 修复了浏览器兜底下载路径无法取消、且取消后可能残留半成品文件的问题
3. 修复了后台下载线程直接更新 Tk 状态栏的线程安全隐患
4. 修复了应用默认受 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量干扰，导致在损坏代理下下载失败的问题
5. 修复了浏览器 Cookie 数据库不可访问时，普通下载会直接失败的问题；现在会自动无 Cookie 重试
6. 修复了直接调用 `download_video()` 时任务仍留在队列中，导致同一下载被重复启动的问题
7. 清理了重复和误导性的下载阶段日志，使完成态与真实行为更一致

### ✅ 实际验证

- 已验证 GUI 可正常启动和关闭
- 已验证 Playwright Chromium 可 headless 启动
- 已验证在禁用损坏代理后，`yt-dlp` 可完成真实在线提取
- 已验证 `DownloadManager` 可真实下载公开 MP4 文件
- 已验证浏览器 Cookie 读取失败后，会自动降级并成功完成下载
- 已验证下载结束后状态正确落为 `completed`

## v2.0 (2026-04-02)

### 🎉 新增功能

#### UI改进
- ✅ **右键菜单支持** - URL输入框右键菜单（粘贴、清空、全选）
- ✅ **高级选项面板** - 可折叠的高级设置面板
- ✅ **格式选择对话框** - 可视化查看和选择视频格式
- ✅ **增强错误显示** - 状态栏错误提示 + 详细错误对话框

#### 下载功能增强
- ✅ **字幕下载** - 支持多语言字幕下载（中文、英文、日文、韩文等）
- ✅ **代理支持** - HTTP/HTTPS代理配置，支持认证代理
- ✅ **自定义格式** - 手动选择特定格式ID下载
- ✅ **输出模板** - 自定义输出文件名模板

#### 系统优化
- ✅ **FFmpeg自动检测** - 启动时检测FFmpeg，缺失时显示警告
- ✅ **增强错误处理** - 详细错误信息和解决方案
- ✅ **浏览器集成** - 支持通过命令行参数传入URL

### 🐛 Bug修复

1. 修复了错误信息不显示的问题
2. 修复了尝试/异常处理，提供更详细的错误描述
3. 修复了多线程下载的稳定性问题
4. 修复了队列管理的并发问题

### 📦 文件清单

- `ytdlp_gui.py` (45KB) - 主程序，包含所有新功能
- `start.bat` - 增强启动脚本，检查FFmpeg
- `setup.bat` - 安装脚本，支持FFmpeg安装提示
- `test_installation.py` - 完整测试脚本
- `FEATURES.md` - 功能说明文档

### ⚠️ 重要提示

#### FFmpeg是必需的！
由于YouTube、Bilibili等网站使用分离的音频/视频流，FFmpeg用于合并它们。

**安装方法**：
```bash
# 使用winget（推荐）
winget install FFmpeg

# 或手动下载
# https://www.ffmpeg.org/download.html
```

### 🎯 快速开始

1. **解压** `yt-dlp-gui-windows.zip`
2. **双击** `start.bat`
3. **复制** 视频URL
4. **粘贴** 到应用（Ctrl+V或右键）
5. **选择** 字幕语言（如需要）
6. **点击** "Download"

### 🚀 高级使用

#### 使用代理
```
1. 勾选 Advanced Options
2. 输入 Proxy URL: http://proxy:8080
3. 点击 Download
```

#### 选择特定格式
```
1. 输入URL
2. 点击 Advanced Options
3. 点击 "View Available Formats"
4. 选择格式并点击 "Use This Format"
5. 点击 Download
```

#### 下载字幕
```
1. 粘贴URL
2. 在 Subtitles 下拉菜单中选择语言
3. 点击 Download
```

#### 从命令行启动并传入URL
```bash
python ytdlp_gui.py "https://youtube.com/watch?v=xxxxx"
```

## v1.0 (2026-04-02)

### 🎉 初始版本

#### 核心功能
- ✅ 基本的视频下载功能
- ✅ 6种质量预设（Best/4K/1080p/720p/480p/Audio）
- ✅ 多线程下载队列
- ✅ 实时进度跟踪

#### UI特性
- ✅ 简洁的Tkinter界面
- ✅ 暗色/亮色主题
- ✅ 基本错误处理
- ✅ 设置对话框

#### 文件清单
- `ytdlp_gui.py` - 基础版本
- `start.bat` - 基本启动脚本
- `setup.bat` - 安装脚本
- `test_installation.py` - 测试脚本
- `RUN.md` - 用户指南

### ⚠️ 已知问题

1. 错误信息不显示在GUI上
2. 缺少FFmpeg检测
3. 没有右键菜单
4. 不支持字幕下载
5. 无代理支持
6. 无格式选择对话框

这些问题在v2.0中已全部修复！
