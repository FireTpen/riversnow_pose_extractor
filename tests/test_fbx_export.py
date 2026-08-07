# -*- coding: utf-8 -*-
"""Blender FBX 导出通路验证（需本机已安装 Blender）。"""
import json
import os
import tempfile

from src.fbx_export import export_fbx, find_blender


def point(x=0.0, y=0.0, z=0.0):
    return {"x": x, "y": y, "z": z, "visibility": 1.0}


if not find_blender():
    print("SKIPPED: Blender is not installed")
    raise SystemExit(0)

# Pose world landmarks: enough non-degenerate joints to exercise every body chain.
pose = [point() for _ in range(33)]
for index, value in {
    0: point(0, -1.7, 0),
    11: point(0.25, -1.45, 0), 12: point(-0.25, -1.45, 0),
    13: point(0.52, -1.28, 0), 14: point(-0.52, -1.28, 0),
    15: point(0.72, -1.12, 0), 16: point(-0.72, -1.12, 0),
    23: point(0.16, -0.95, 0), 24: point(-0.16, -0.95, 0),
    25: point(0.18, -0.52, 0), 26: point(-0.18, -0.52, 0),
    27: point(0.18, -0.10, 0), 28: point(-0.18, -0.10, 0),
    31: point(0.18, -0.05, -0.18), 32: point(-0.18, -0.05, -0.18),
}.items():
    pose[index] = value

data = {
    "fps": 30,
    "frames": [
        {"frame_index": 0, "landmarks": {
            "pose_world": pose, "left_hand_world": None, "right_hand_world": None,
        }},
        {"frame_index": 1, "landmarks": {
            "pose_world": pose, "left_hand_world": None, "right_hand_world": None,
        }},
    ],
}

tmp = tempfile.mkdtemp(prefix="pose_fbx_test_")
keypoints = os.path.join(tmp, "keypoints.json")
out_fbx = os.path.join(tmp, "animation.fbx")
with open(keypoints, "w", encoding="utf-8") as f:
    json.dump(data, f)

result = export_fbx(keypoints, out_fbx)
assert result == out_fbx and os.path.getsize(out_fbx) > 1024
print("FBX EXPORT TEST PASSED:", out_fbx, os.path.getsize(out_fbx), "bytes")
