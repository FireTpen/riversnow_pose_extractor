# PoseExtractor 骨架提取工具

**[English](README.md)** | **中文**

把人物舞蹈/动作视频转换为「纯黑底骨架视频」（ControlNet OpenPose 风格，可用于 AI 视频生成）+ 原始关键点 JSON 数据。姿态引擎为 MediaPipe Pose（33 个关键点），引擎已封装为独立模块（`src/pose_engine.py`），以后可扩展 DWPose。

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

- **骨架视频 mp4**：纯黑底，彩色骨架连线（MediaPipe POSE_CONNECTIONS）+ 白色关节点，不叠加原画面。
- **关键点 JSON**：

```json
{
  "fps": 30.0,
  "width": 512,
  "height": 512,
  "frame_count": 100,
  "frames": [
    {
      "frame_index": 0,
      "time_sec": 0.0,
      "landmarks": [{"x": 0.5, "y": 0.3, "z": 0.0, "visibility": 0.99}]  // 33 个；未检出人体时为 null
    }
  ]
}
```

坐标为归一化值（0~1，相对于输出分辨率）。

## 已知限制

- MediaPipe Pose 对快速舞蹈动作、遮挡、宽松衣物可能丢点或抖动（对应帧 landmarks 为 null 或关键点跳变）。
- model_complexity=2 在 1080p 长视频上处理较慢，建议先裁剪片段试跑。
- 输出 mp4 使用 H.264 编码（imageio-ffmpeg 转码）；如需 H.265 可后期用 ffmpeg 再转码。
- 打包/运行需 arm64 架构（Apple Silicon）；Intel Mac 未经测试。
