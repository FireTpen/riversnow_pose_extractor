# -*- coding: utf-8 -*-
"""姿态引擎封装。

当前实现：MediaPipe Pose（33 个关键点）。
以后如需接入 DWPose 等引擎，实现同样的接口即可：
    - num_landmarks 属性
    - detect(bgr_image) -> landmarks 列表或 None
    - draw(canvas, landmarks) -> 画好骨架的黑底图
    - close()
landmark 元素为 dict: {"x", "y", "z", "visibility"}，坐标为归一化值。
"""
import cv2
import mediapipe as mp

# MediaPipe Pose 的连接定义（33 点）
POSE_CONNECTIONS = mp.solutions.pose.POSE_CONNECTIONS

# 每个关键点的颜色（BGR），让骨架更易区分
_POINT_COLOR = (255, 255, 255)
_LINE_COLORS = [
    (255, 255, 255), (0, 255, 255), (255, 0, 255), (0, 255, 0),
    (255, 128, 0), (0, 128, 255), (200, 200, 0), (0, 200, 200),
]


class MediaPipePoseEngine:
    """MediaPipe Pose 封装：逐帧提关键点 + 黑底画骨架。"""

    num_landmarks = 33

    def __init__(self, model_complexity=1, min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=int(model_complexity),
            enable_segmentation=False,
            min_detection_confidence=float(min_detection_confidence),
            min_tracking_confidence=float(min_tracking_confidence),
        )

    def detect(self, bgr_image):
        """输入 BGR 图像，返回 33 个归一化关键点列表；未检出返回 None。"""
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._pose.process(rgb)
        if not result.pose_landmarks:
            return None
        return [
            {
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(lm.z),
                "visibility": float(lm.visibility),
            }
            for lm in result.pose_landmarks.landmark
        ]

    def draw(self, canvas, landmarks):
        """在 canvas（应为黑底图）上画骨架连线和关节点，返回 canvas。"""
        h, w = canvas.shape[:2]
        pts = []
        for lm in landmarks:
            x = int(lm["x"] * w)
            y = int(lm["y"] * h)
            vis = lm.get("visibility", 1.0)
            pts.append((x, y, vis))
        thickness = max(1, round(min(w, h) / 256))
        radius = max(2, round(min(w, h) / 160))
        # 画线（两端可见度都太低则跳过）
        for i, (a, b) in enumerate(POSE_CONNECTIONS):
            xa, ya, va = pts[a]
            xb, yb, vb = pts[b]
            if va < 0.3 or vb < 0.3:
                continue
            color = _LINE_COLORS[i % len(_LINE_COLORS)]
            cv2.line(canvas, (xa, ya), (xb, yb), color, thickness, cv2.LINE_AA)
        # 画点
        for x, y, vis in pts:
            if vis < 0.3:
                continue
            cv2.circle(canvas, (x, y), radius, _POINT_COLOR, -1, cv2.LINE_AA)
        return canvas

    def close(self):
        self._pose.close()


def create_engine(name="mediapipe", **kwargs):
    """引擎工厂。以后加 DWPose 时在这里分支。"""
    if name == "mediapipe":
        return MediaPipePoseEngine(**kwargs)
    raise ValueError("未知姿态引擎: %s" % name)
