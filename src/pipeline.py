# -*- coding: utf-8 -*-
"""视频处理流水线：读取/裁剪/缩放/逐帧身体与手部提取/写 mp4 + json。"""
import json
import os
import re
import subprocess

import cv2
import numpy as np

from .pose_engine import create_engine


def get_video_codec(video_path):
    """返回视频编码名（小写，如 h264/hevc），探测失败返回 None。"""
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    err = subprocess.run([exe, "-i", video_path],
                         capture_output=True, text=True).stderr
    m = re.search(r"Video:\s*([a-z0-9]+)", err, re.I)
    return m.group(1).lower() if m else None


def ensure_browser_playable(video_path):
    """确保视频能被浏览器播放（用于预览）。

    返回 (路径, 是否做了转换)。H.264/VP8/VP9/AV1 且容器合适时原样返回；
    否则（如 iPhone 录屏的 HEVC .mov）转码为 H.264 mp4 副本——
    转码时 ffmpeg 会自动应用旋转元数据，副本方向也被归一化。
    副本写在上传文件所在目录（Gradio 上传缓存目录，/file= 路由可服务）。
    """
    codec = get_video_codec(video_path)
    ext = os.path.splitext(video_path)[1].lower()
    if codec in ("h264", "vp8", "vp9", "av1") and ext in (".mp4", ".m4v", ".webm"):
        return video_path, False
    base = os.path.splitext(os.path.basename(video_path))[0]
    dst = os.path.join(os.path.dirname(video_path), base + "_h264.mp4")
    _transcode_to_h264(video_path, dst)
    return dst, True


def _transcode_to_h264(src_path, dst_path):
    """用 imageio-ffmpeg 自带的 ffmpeg 把视频转成 H.264（浏览器可预览）。"""
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [exe, "-y", "-i", src_path,
           "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-movflags", "+faststart", dst_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError("H.264 transcode failed: %s" % (proc.stderr or "")[-500:])


def _open_capture(video_path):
    """打开视频并启用自动旋转（手机视频常带 rotate=90 元数据，不处理会把横屏读成竖屏）。"""
    cap = cv2.VideoCapture(video_path)
    if cap.isOpened():
        # OpenCV >= 4.5 支持；不支持的版本静默忽略
        cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
    return cap


def probe_video(video_path):
    """返回源视频信息 dict: width, height, fps, frame_count, duration_sec。"""
    cap = _open_capture(video_path)
    if not cap.isOpened():
        raise ValueError("Cannot open video file: %s" % video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    # 读一帧取真实画面尺寸（CAP_PROP_FRAME_WIDTH/HEIGHT 不含旋转修正，不可靠）
    ok, frame = cap.read()
    if not ok:
        cap.release()
        raise ValueError("No readable frames in video: %s" % video_path)
    h, w = frame.shape[:2]
    info = {
        "width": w,
        "height": h,
        "fps": float(fps),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duration_sec": float(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps),
    }
    cap.release()
    return info


def process_video(video_path, out_video_path, out_json_path,
                  out_width=None, out_height=None,
                  start_sec=0.0, end_sec=None,
                  model_complexity=1, engine_name="mediapipe",
                  progress_cb=None):
    """处理视频，输出黑底骨架 mp4 和关键点 json。

    progress_cb(done_frames, total_frames) 每帧回调（可为 None）。
    返回结果 dict（含实际输出参数与统计）。
    """
    info = probe_video(video_path)
    src_w, src_h, fps = info["width"], info["height"], info["fps"]
    duration = info["duration_sec"]

    out_width = int(out_width) if out_width else src_w
    out_height = int(out_height) if out_height else src_h
    # H.264 yuv420p 要求偶数宽高；奇数会被 cv2/ffmpeg 静默改尺寸，导致
    # 实际视频与 JSON 里的 width/height 不一致。这里统一下取偶。
    out_width = max(2, out_width - out_width % 2)
    out_height = max(2, out_height - out_height % 2)

    start_sec = max(0.0, float(start_sec or 0.0))
    end_sec = duration if end_sec in (None, "", 0) else min(float(end_sec), duration)
    if end_sec <= start_sec:
        raise ValueError(
            "Invalid clip range: end (%.2fs) must be greater than start (%.2fs) "
            "and within duration (%.2fs)"
            % (end_sec, start_sec, duration))

    start_frame = int(round(start_sec * fps))
    end_frame = min(int(round(end_sec * fps)), info["frame_count"])
    total_frames = max(0, end_frame - start_frame)
    if total_frames == 0:
        raise ValueError("No frames to process in the clip range.")

    engine = create_engine(engine_name, model_complexity=model_complexity)

    cap = _open_capture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    # 先写 mp4v 临时文件，结束后转码 H.264（浏览器不支持 mp4v 预览）
    tmp_video_path = out_video_path + ".tmp.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_video_path, fourcc, fps, (out_width, out_height))
    if not writer.isOpened():
        cap.release()
        engine.close()
        raise RuntimeError("Cannot create output video: %s" % tmp_video_path)

    frames_json = []
    detected = 0
    try:
        for i in range(total_frames):
            ok, frame = cap.read()
            if not ok:
                break
            if (frame.shape[1], frame.shape[0]) != (out_width, out_height):
                frame = cv2.resize(frame, (out_width, out_height),
                                   interpolation=cv2.INTER_AREA)
            landmarks = engine.detect(frame)
            canvas = np.zeros((out_height, out_width, 3), dtype=np.uint8)
            if landmarks is not None:
                engine.draw(canvas, landmarks)
                detected += 1
            writer.write(canvas)
            frames_json.append({
                "frame_index": start_frame + i,
                "time_sec": round((start_frame + i) / fps, 6),
                "landmarks": landmarks,
            })
            if progress_cb:
                progress_cb(i + 1, total_frames)
    finally:
        cap.release()
        writer.release()
        engine.close()

    try:
        _transcode_to_h264(tmp_video_path, out_video_path)
    finally:
        if os.path.exists(tmp_video_path):
            os.remove(tmp_video_path)

    data = {
        "landmark_format": {
            "pose": 33,
            "pose_world": 33,
            "left_hand": 21,
            "right_hand": 21,
            "left_hand_world": 21,
            "right_hand_world": 21,
        },
        "world_landmarks_note": (
            "MediaPipe estimated world coordinates in meters. Pose is hip-centered; "
            "each hand is hand-centered and should be used for local finger rotations."),
        "fps": fps,
        "width": out_width,
        "height": out_height,
        "frame_count": len(frames_json),
        "frames": frames_json,
    }
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return {
        "out_video": os.path.abspath(out_video_path),
        "out_json": os.path.abspath(out_json_path),
        "fps": fps,
        "width": out_width,
        "height": out_height,
        "frames_written": len(frames_json),
        "frames_detected": detected,
        "start_sec": start_sec,
        "end_sec": end_sec,
    }
