# 打包独立安装包（PyInstaller）

当前目录包含两种原生构建脚本：

- macOS（Apple Silicon）：`build_installer.sh`，产出 `.app` 和 `.dmg`。
- Windows x64：`build_windows.ps1`，产出便携版 `.zip`。详见 [README.windows.md](README.windows.md)。

> PyInstaller 不能可靠交叉构建：Windows `.exe` 必须在 Windows x64 机器上构建与测试，macOS `.app` 必须在 macOS 上构建。

把应用打成**零依赖**的 `PoseExtractor.app`（内置 Python 解释器和全部依赖，仅 arm64），
ad-hoc 签名后生成拖放式 DMG 安装包。

## 构建

```bash
./.venv/bin/pip install -r requirements-dev.txt   # 首次，安装 pyinstaller
packaging/build_installer.sh
```

产物：

- `dist/PoseExtractor.app` —— 独立应用（onedir + windowed）
- `dist/PoseExtractor.dmg` —— 安装包（内含 .app + /Applications 符号链接）

## 文件说明

- `entry.py`：打包入口。冻结运行时把 stdout/stderr 追加到
  `~/Library/Logs/PoseExtractor.log`（windowed 无控制台），再调用 `src.main.main()`。
- `pyi_runtime_hook.py`：runtime hook，预加载 `cv2.abi3.so`。
  否则 cv2 自带 bootstrap 在冻结环境下 sys.path 顺序变化导致
  "recursion is detected during loading of cv2 binary extensions"。
- `build_installer.sh`：PyInstaller 打包 → codesign ad-hoc → hdiutil 生成 DMG。

## 验证（模拟无开发环境的机器）

```bash
pkill -f "src.main"          # 释放 7860 端口
mv .venv .venv_bak           # 临时藏起开发环境
open dist/PoseExtractor.app
curl http://localhost:7860   # 应返回 200
# 还可用 Gradio API（POST /upload + /api/process）跑一个短视频验证处理流程
mv .venv_bak .venv           # 验证完恢复
```

排错看 `~/Library/Logs/PoseExtractor.log`。

## 注意

- 仅 arm64（Apple Silicon）；未公证，其他 Mac 首次打开需右键 → 打开。
- 若以后新增带数据文件的依赖而运行报缺文件，给 `build_installer.sh`
  补 `--collect-all <pkg>` 或 `--add-data`。
