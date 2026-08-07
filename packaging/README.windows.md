# Windows 版本：构建与测试

Windows 版是 x64 便携应用：解压后运行 `PoseExtractor.exe`，浏览器会自动打开
`http://localhost:7860`。它不需要用户另装 Python。

## 构建环境

- Windows 10/11 x64
- Python 3.10 或 3.11 x64（MediaPipe 0.10.14 不建议使用 Python 3.12+）
- PowerShell 5+
- 如需 FBX 导出：另装 [Blender](https://www.blender.org/download/)。默认安装路径会被自动识别；也可以设置 `BLENDER_BIN` 为 `blender.exe` 的完整路径。

在项目根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

产物：`dist\PoseExtractor-windows-x64.zip`。

## 运行源码验证

```powershell
$env:PYTHONPATH = "."
python -m src.main
```

上传短 MP4，确认可下载骨架视频、JSON；若装了 Blender，再确认可导出 FBX。

## 测试已打包程序

解压 ZIP，在 `PoseExtractor-windows-x64` 文件夹中双击 `PoseExtractor.exe`。
日志在：`%LOCALAPPDATA%\PoseExtractor\PoseExtractor.log`。

如果 Windows Defender SmartScreen 出现提示，原因是当前包未购买代码签名证书。应先核对发布者/哈希或通过企业签名流程发布；不要关闭系统防护。

## VIBE GPU Worker

桌面包仅包含当前 MediaPipe 功能。VIBE 应作为 NVIDIA Windows/Linux GPU 主机上的独立 Worker 部署；确认 VIBE/SMPL 非商业许可后，再接入 UI 的任务调用。
