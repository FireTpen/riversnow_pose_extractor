# -*- coding: utf-8 -*-
"""pipeline 合成视频通路测试：读/裁剪/缩放/写 mp4/写 json。"""
import json
import os
import tempfile

import cv2
import numpy as np

from src.pipeline import process_video, probe_video

tmp = tempfile.mkdtemp(prefix="pose_test_")
src = os.path.join(tmp, "src.mp4")

# 生成 2 秒 640x480@20fps 的合成视频（无人体，landmarks 应为 null）
w, h, fps, n = 640, 480, 20.0, 40
wr = cv2.VideoWriter(src, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
for i in range(n):
    img = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.circle(img, (50 + i * 10, 240), 30, (0, 255, 0), -1)
    wr.write(img)
wr.release()

info = probe_video(src)
assert info["width"] == 640 and info["height"] == 480, info
print("probe 正常:", info)

out_v = os.path.join(tmp, "skel.mp4")
out_j = os.path.join(tmp, "kpts.json")
progress_calls = []
res = process_video(src, out_v, out_j, out_width=320, out_height=320,
                    start_sec=0.5, end_sec=1.5, model_complexity=0,
                    progress_cb=lambda d, t: progress_calls.append((d, t)))
print("处理结果:", res)
assert res["frames_written"] == 20, res
assert os.path.getsize(out_v) > 0

# 校验输出视频可回读且尺寸正确
cap = cv2.VideoCapture(out_v)
assert int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == 320
assert int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 320
cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()
assert cnt == 20, cnt

with open(out_j) as f:
    data = json.load(f)
assert data["width"] == 320 and data["height"] == 320
assert data["fps"] == fps
assert data["frame_count"] == 20
assert len(data["frames"]) == 20
assert data["frames"][0]["frame_index"] == 10  # 0.5s * 20fps
assert abs(data["frames"][0]["time_sec"] - 0.5) < 1e-3
# 合成画面无人体 -> landmarks 应为 null
assert all(fr["landmarks"] is None for fr in data["frames"])
assert len(progress_calls) == 20 and progress_calls[-1] == (20, 20)

# 非法裁剪区间应报错
try:
    process_video(src, out_v, out_j, start_sec=1.5, end_sec=1.0)
    raise AssertionError("应当抛出裁剪区间错误")
except ValueError as e:
    print("非法区间正确报错:", e)

print("PIPELINE TEST PASSED")
