# PoseExtractor

**English** | **[中文](README.zh-CN.md)**

Convert a dance/motion video of a person into a **black-background skeleton video** (ControlNet OpenPose style, ready for AI video generation) plus the **raw keypoints JSON**. The engine combines MediaPipe Pose (33 body landmarks) and Hands (21 finger landmarks per hand), wrapped as a standalone module (`src/pose_engine.py`) so other engines (e.g. DWPose) can be added later.

> Experimental: after processing, export the keypoints JSON as an **animation-only FBX**. The exporter solves a Mixamo-style named armature from body/hand world landmarks; retarget the animation to your character in Unity, Unreal, or Blender.

Runs locally with a Gradio web UI (Chinese/English, switchable in the top-right corner).

## Windows x64

The project includes a native Windows packaging script. On Windows 10/11 with Python 3.10 or 3.11, run `packaging\\build_windows.ps1`; see [packaging/README.windows.md](packaging/README.windows.md) for the complete build and validation process. FBX export on Windows requires a separate Blender installation; the app discovers its default installation path, or you can set `BLENDER_BIN`.

## Download (DMG installer)

Download the latest `PoseExtractor.dmg` from [**GitHub Releases**](https://github.com/FireTpen/riversnow_pose_extractor/releases). Open the DMG and drag `PoseExtractor.app` into **Applications**. The app bundles its own Python and all dependencies — nothing else is required (Apple Silicon / arm64 only). To build it yourself, see `packaging/README.md`.

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
        "pose": [{"x": 0.5, "y": 0.3, "z": 0.0, "visibility": 0.99}],
        "left_hand": [{"x": 0.5, "y": 0.3, "z": 0.0, "visibility": 1.0}],
        "right_hand": null
      }
    }
  ]
}
```

Coordinates are normalized (0–1, relative to the output resolution). `pose` has 33 body points and each hand contains 21 points; an undetected hand is `null`, as is `landmarks` if no body or hand is detected.

## Known Limitations

- Hand tracking may drop or jitter when hands are small, motion-blurred, occluded, or fingers overlap. Keep hands sharp and relatively large in frame for best finger motion capture.
- model_complexity=2 is slow on long 1080p videos — clip a short segment first to test.
- The output mp4 is H.264 (transcoded via imageio-ffmpeg); transcode with ffmpeg afterwards if you need H.265.
- Building/running requires the arm64 architecture (Apple Silicon); Intel Macs are untested.

## License

See [LICENSE](LICENSE).
