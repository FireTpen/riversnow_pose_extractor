# PoseExtractor

**English** | **[中文](README.zh-CN.md)**

Convert a dance/motion video of a person into a **black-background skeleton video** (ControlNet OpenPose style, ready for AI video generation) plus the **raw keypoints JSON**. The pose engine is MediaPipe Pose (33 landmarks), wrapped as a standalone module (`src/pose_engine.py`) so other engines (e.g. DWPose) can be added later.

Runs locally on macOS with a Gradio web UI (Chinese/English, switchable in the top-right corner).

## Download (DMG installer)

A prebuilt standalone installer may be provided as `dist/PoseExtractor.dmg` (see `packaging/README.md` for how it is built). Open the DMG and drag `PoseExtractor.app` into **Applications**. The app bundles its own Python and all dependencies — nothing else is required (Apple Silicon / arm64 only).

The app is ad-hoc signed (not notarized), so on first launch **right-click → Open** and confirm to bypass Gatekeeper.

## Requirements

- macOS (verified on Apple Silicon / arm64)
- System Python 3.9+ (`/usr/bin/python3`); no Homebrew Python needed

## Installation

```bash
cd pose_extractor
/usr/bin/python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Usage

- CLI: `./run_app.sh`
- Mac app: run `./build_app.sh` to generate `PoseExtractor.app`, then double-click it (opens the browser automatically).

Then open http://127.0.0.1:7860

1. Upload a video (mp4/mov etc.); the UI shows source resolution / FPS / duration.
2. Adjust parameters:
   - Output resolution: same as source by default, or 512x512 / 768x768 / 1024x1024 / custom width & height.
   - Time clip: start/end seconds (end = 0 means full length).
   - model_complexity: 0/1/2 — higher is more accurate but slower.
3. The warning area dynamically flags upscaling beyond source resolution, total pixels above 1024x1024, and clips longer than 60 s (with an estimated frame count); an invalid clip range raises an error and blocks processing.
4. Click "Start Processing". When done, preview the skeleton video and download the JSON. The preview is shown as a thumbnail by default; use the Thumbnail / Wide / Fullscreen buttons to resize it.

## Output

- **Skeleton video (mp4)**: pure black background, colored skeleton connections (MediaPipe POSE_CONNECTIONS) and white joint dots; the original frame is not composited.
- **Keypoints JSON**:

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
      "landmarks": [{"x": 0.5, "y": 0.3, "z": 0.0, "visibility": 0.99}]  // 33 entries; null when no person detected
    }
  ]
}
```

Coordinates are normalized (0–1, relative to the output resolution).

## Known Limitations

- MediaPipe Pose may drop landmarks or jitter on fast dance moves, occlusion, or loose clothing (affected frames have `landmarks: null` or jumping keypoints).
- model_complexity=2 is slow on long 1080p videos — clip a short segment first to test.
- The output mp4 is H.264 (transcoded via imageio-ffmpeg); transcode with ffmpeg afterwards if you need H.265.
- Building/running requires the arm64 architecture (Apple Silicon); Intel Macs are untested.

## License

See [LICENSE](LICENSE).
