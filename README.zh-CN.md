# PoseExtractor 骨架提取工具

**[English](README.md)** | **中文**

把人物舞蹈/动作视频转换为「纯黑底骨架视频」（ControlNet OpenPose 风格，可用于 AI 视频生成）+ 原始关键点 JSON 数据。姿态引擎使用 MediaPipe Pose（33 个身体关键点）+ Hands（每只手 21 个手指关键点）；引擎已封装为独立模块（`src/pose_engine.py`），以后可扩展 DWPose。

> 实验功能：处理完成后可将关键点 JSON 导出为 **animation-only FBX**。导出器使用身体/手部 world landmarks 解算 Mixamo 命名风格的骨架旋转；建议导入 Unity、Unreal 或 Blender 后重定向到你的角色骨架。

## Windows 版本

项目已提供 Windows x64 的原生构建脚本。请在 Windows 10/11、Python 3.10/3.11 环境执行 `packaging\\build_windows.ps1`；完整构建、测试和日志位置见 [packaging/README.windows.md](packaging/README.windows.md)。Windows 的 FBX 导出需单独安装 Blender，程序会自动搜索默认安装路径，也可设置 `BLENDER_BIN`。

## 下载安装（DMG 安装包）

从 [**GitHub Releases**](https://github.com/FireTpen/riversnow_pose_extractor/releases) 下载最新的 `PoseExtractor.dmg`：打开 DMG，把 `PoseExtractor.app` 拖进「应用程序」即可。应用内置 Python 解释器和全部依赖，目标机器零依赖（仅支持 Apple Silicon / arm64）。自行构建见 `packaging/README.md`。

应用为 ad-hoc 签名（未公证），首次打开需**右键 → 打开**并确认，以绕过 Gatekeeper。

## 环境要求

- macOS（Apple Silicon 已验证）
- 系统 Python 3.9+（/usr/bin/python3），无需 Homebrew Python

## 安装

```bash
cd /Users/fengjiahao/mycode_project/riversnow/pose_extractor
/usr/bin/python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## 启动

- 命令行：`./run_app.sh`
- Mac 应用：先运行 `./build_app.sh` 生成 `PoseExtractor.app`，双击即可（自动打开浏览器）。

启动后访问 http://127.0.0.1:7860

界面右上角可切换 中文 / English。

## 用法

1. 上传视频（mp4/mov 等），界面显示源视频分辨率/帧率/时长。
2. 调整参数：
   - 输出分辨率：默认与源一致，可选 512x512 / 768x768 / 1024x1024 或自定义宽高。
   - 时长裁剪：起止秒（结束秒填 0 表示全长）。
   - model_complexity：0/1/2，越大越准越慢。
3. 风险提示区会动态提示：分辨率放大、总像素超 1024x1024、时长超 60 秒（附预计帧数）；裁剪区间非法会报错并阻止处理。
4. 点击「开始处理」，完成后预览骨架视频并下载 JSON。预览默认缩略显示，可用「缩略 / 宽屏 / 全屏」按钮切换大小。

## 输出说明

- **骨架视频 mp4**：纯黑底，身体骨架加上双手的完整手指连线，不叠加原画面。
- **关键点 JSON**：

```json
{
  "landmark_format": {"pose": 33, "left_hand": 21, "right_hand": 21},
  "fps": 30.0,
  "width": 512,
  "height": 512,
  "frame_count": 100,
  "frames": [
    {
      "frame_index": 0,
      "time_sec": 0.0,
      "landmarks": {
        "pose": [{"x": 0.5, "y": 0.3, "z": 0.0, "visibility": 0.99}], // 33 个或 null
        "left_hand": [{"x": 0.5, "y": 0.3, "z": 0.0, "visibility": 1.0}], // 21 个或 null
        "right_hand": null
      }
    }
  ]
}
```

坐标为归一化值（0~1，相对于输出分辨率）。`pose` 是身体 33 点，`left_hand` 和 `right_hand` 各为完整手部 21 点；某只手未识别到时为 `null`。三组均未识别到时，整帧 `landmarks` 为 `null`。

新版 JSON 还包含 `pose_world`、`left_hand_world`、`right_hand_world`：单位为米的 MediaPipe 估计世界坐标。身体坐标以髋部为中心；手部坐标以手自身为中心，因此 FBX 导出器将手部 world landmarks 仅用于局部手指旋转，并把手腕挂接到身体骨架。

## FBX 导出

1. 按正常流程处理视频，先生成关键点 JSON。
2. 点击右侧的「导出 FBX 动画（实验）」。首次导出会启动本机 Blender，耗时略长。
3. 下载 `animation.fbx`，在 Unity/Unreal/Blender 中重定向到目标角色。

需要安装 Blender（macOS 默认查找 `/Applications/Blender.app`；也可设置 `BLENDER_BIN`）。该功能会做基础骨骼旋转解算，但单目视频无法保证真实根位移、遮挡处姿态或完全无脚滑；高质量成片仍建议后续编辑或使用双机位输入。

## 已知限制

- 手部在画面中太小、运动模糊、被遮挡或手指相互重叠时，Hands 可能丢失该手或产生抖动；请让手部清晰、尽量占画面较大区域。
- model_complexity=2 在 1080p 长视频上处理较慢，建议先裁剪片段试跑。
- 输出 mp4 使用 H.264 编码（imageio-ffmpeg 转码）；如需 H.265 可后期用 ffmpeg 再转码。
- 打包/运行需 arm64 架构（Apple Silicon）；Intel Mac 未经测试。
