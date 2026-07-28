# -*- coding: utf-8 -*-
"""pose_engine 单图姿态检测验证。"""
import sys

import cv2

from src.pose_engine import create_engine

img_path = sys.argv[1]
img = cv2.imread(img_path)
assert img is not None, "读图失败: %s" % img_path

engine = create_engine("mediapipe", model_complexity=1)
lms = engine.detect(img)
assert lms is not None, "未检出人体姿态"
assert len(lms) == 33, len(lms)
for lm in lms:
    assert set(lm.keys()) == {"x", "y", "z", "visibility"}
canvas = engine.draw(__import__("numpy").zeros(img.shape, dtype="uint8"), lms)
assert canvas.sum() > 0, "骨架画布为空"
engine.close()
print("POSE ENGINE TEST PASSED: 检出 33 个关键点, visibility 均值 %.3f"
      % (sum(l["visibility"] for l in lms) / 33))
