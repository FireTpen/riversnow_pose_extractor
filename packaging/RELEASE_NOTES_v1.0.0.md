# PoseExtractor v1.0.0

Extract human pose from motion/dance videos → black-background skeleton video (H.264) + keypoints JSON. Designed for AI video generation workflows (ControlNet OpenPose style).

从人物动作/舞蹈视频提取骨骼姿态 → 黑底骨架视频（H.264）+ 关键点 JSON，适用于 AI 视频生成（ControlNet OpenPose 风格）。

## Download / 下载

**`PoseExtractor.dmg`** — standalone macOS installer (Apple Silicon / arm64 only). Bundles Python and all dependencies; nothing else to install.

独立 macOS 安装包（仅 Apple Silicon / arm64），内置 Python 与全部依赖，开箱即用。

> First launch: the app is ad-hoc signed (not notarized). **Right-click → Open** to bypass Gatekeeper.
> 首次打开：应用为 ad-hoc 签名（未公证），请**右键 → 打开**。

## Features / 功能

- Black-background skeleton video + keypoints JSON (MediaPipe Pose, 33 landmarks)
- 黑底骨架视频 + 关键点 JSON（MediaPipe Pose，33 个关键点）
- Adjustable output resolution and clip range, with risk warnings
- 输出分辨率、时长裁剪可调，带风险提示
- Chinese / English UI switch / 中英文界面切换
- Auto-converts HEVC and other browser-unfriendly formats for preview
- HEVC 等格式自动转码预览
- Handles phone videos with rotation metadata correctly
- 正确处理手机视频的旋转元数据

## Source install / 源码安装

See README: `pip install -r requirements.txt`, then `./run_app.sh`.
