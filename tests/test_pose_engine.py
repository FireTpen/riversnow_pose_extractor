# -*- coding: utf-8 -*-
"""pose_engine 单图姿态检测验证。"""
import sys

import cv2

from src.pose_engine import MediaPipePoseEngine, create_engine


class _FakeHandLandmark:
    x = 0.5
    y = 0.5
    z = 0.0
    # MediaPipe Hands 的 protobuf 会提供默认 0，而这不代表未检出。
    visibility = 0.0


hand_point = MediaPipePoseEngine._to_landmarks(
    [_FakeHandLandmark()], use_landmark_visibility=False)[0]
assert hand_point["visibility"] == 1.0
hand_canvas = __import__("numpy").zeros((100, 100, 3), dtype="uint8")
MediaPipePoseEngine.draw(object(), hand_canvas,
                          {"pose": None, "left_hand": [hand_point] * 21,
                           "right_hand": None})
assert hand_canvas.sum() > 0, "已检出的手部点应被绘制"

img_path = sys.argv[1]
img = cv2.imread(img_path)
assert img is not None, "读图失败: %s" % img_path

engine = create_engine("mediapipe", model_complexity=1)
lms = engine.detect(img)
assert lms is not None, "未检出人体姿态"
assert set(lms) == {"pose", "pose_world", "left_hand", "right_hand",
                    "left_hand_world", "right_hand_world"}
assert lms["pose"] is not None and len(lms["pose"]) == 33, lms["pose"]
for lm in lms["pose"]:
    assert set(lm.keys()) == {"x", "y", "z", "visibility"}
canvas = engine.draw(__import__("numpy").zeros(img.shape, dtype="uint8"), lms)
assert canvas.sum() > 0, "骨架画布为空"
engine.close()
print("POSE ENGINE TEST PASSED: 身体 33 点, 左手 %s 点, 右手 %s 点, visibility 均值 %.3f"
      % (len(lms["left_hand"]) if lms["left_hand"] else 0,
         len(lms["right_hand"]) if lms["right_hand"] else 0,
         sum(l["visibility"] for l in lms["pose"]) / 33))
