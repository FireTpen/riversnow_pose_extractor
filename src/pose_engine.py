# -*- coding: utf-8 -*-
"""姿态引擎封装。

当前实现：MediaPipe Pose（33 个关键点）+ Hands（每只手 21 个关键点）。
以后如需接入 DWPose 等引擎，实现同样的接口即可：
    - num_landmarks 属性
    - detect(bgr_image) -> {"pose", "left_hand", "right_hand"} 或 None
    - draw(canvas, landmarks) -> 画好骨架的黑底图
    - close()
landmark 元素为 dict: {"x", "y", "z", "visibility"}，坐标为归一化值。
"""
import cv2
import mediapipe as mp

# MediaPipe Pose 的连接定义（33 点）
POSE_CONNECTIONS = mp.solutions.pose.POSE_CONNECTIONS
HAND_CONNECTIONS = mp.solutions.hands.HAND_CONNECTIONS

# 每个关键点的颜色（BGR），让骨架更易区分
_POINT_COLOR = (255, 255, 255)
_LINE_COLORS = [
    (255, 255, 255), (0, 255, 255), (255, 0, 255), (0, 255, 0),
    (255, 128, 0), (0, 128, 255), (200, 200, 0), (0, 200, 200),
]


class MediaPipePoseEngine:
    """MediaPipe Pose + Hands 封装：逐帧提关键点 + 黑底画骨架。"""

    num_landmarks = 33
    num_hand_landmarks = 21

    def __init__(self, model_complexity=1, min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=int(model_complexity),
            enable_segmentation=False,
            min_detection_confidence=float(min_detection_confidence),
            min_tracking_confidence=float(min_tracking_confidence),
        )
        # Pose 只有手腕、拇指/食指/小指的少数点；Hands 才提供完整的
        # 21 个手部关节（腕、4 根手指各 4 节）。两套模型并行运行，
        # 既保留原来的身体骨架，也能读取手指动作。
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=float(min_detection_confidence),
            min_tracking_confidence=float(min_tracking_confidence),
        )

    @staticmethod
    def _to_landmarks(landmarks, use_landmark_visibility=True):
        """把 MediaPipe landmarks 转为可 JSON 序列化的统一格式。

        Pose 的 ``visibility`` 是模型输出的有效置信度；Hands 虽然 protobuf
        对象也暴露该字段，但其值始终是未填充的 0，不能据此过滤已识别的手指。
        """
        return [
            {
                "x": float(lm.x),
                "y": float(lm.y),
                "z": float(lm.z),
                "visibility": (float(lm.visibility) if use_landmark_visibility
                               else 1.0),
            }
            for lm in landmarks
        ]

    def detect(self, bgr_image):
        """输入 BGR 图像，返回身体和双手关键点；三者皆未检出时返回 None。

        返回值结构固定为 ``pose``（33 点）、``left_hand``/``right_hand``（各 21
        点或 ``None``）。这避免把身体点和手指点混在一个无法辨别含义的数组中。
        """
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        pose_result = self._pose.process(rgb)
        hands_result = self._hands.process(rgb)

        pose = (self._to_landmarks(pose_result.pose_landmarks.landmark)
                if pose_result.pose_landmarks else None)
        hands = {"left_hand": None, "right_hand": None}
        if hands_result.multi_hand_landmarks:
            # multi_handedness 与 multi_hand_landmarks 一一对应；正常情况下每侧
            # 最多一只手。
            for hand_lms, handedness in zip(
                    hands_result.multi_hand_landmarks,
                    hands_result.multi_handedness or []):
                label = handedness.classification[0].label.lower()
                key = "%s_hand" % label
                if key in hands:
                    # Hands 的 protobuf visibility 默认恒为 0；该手既然已被
                    # 模型检出，21 个关节应全部参与绘制。
                    hands[key] = self._to_landmarks(hand_lms.landmark,
                                                     use_landmark_visibility=False)

        if pose is None and not any(hands.values()):
            return None
        return {"pose": pose, **hands}

    def draw(self, canvas, landmarks):
        """在 canvas（应为黑底图）上画骨架连线和关节点，返回 canvas。"""
        h, w = canvas.shape[:2]
        thickness = max(1, round(min(w, h) / 256))
        radius = max(2, round(min(w, h) / 160))

        def draw_part(part, connections, colors, point_color):
            if not part:
                return
            pts = []
            for lm in part:
                x = int(lm["x"] * w)
                y = int(lm["y"] * h)
                vis = lm.get("visibility", 1.0)
                pts.append((x, y, vis))
            for i, (a, b) in enumerate(connections):
                xa, ya, va = pts[a]
                xb, yb, vb = pts[b]
                if va < 0.3 or vb < 0.3:
                    continue
                cv2.line(canvas, (xa, ya), (xb, yb), colors[i % len(colors)],
                         thickness, cv2.LINE_AA)
            for x, y, vis in pts:
                if vis >= 0.3:
                    cv2.circle(canvas, (x, y), radius, point_color, -1, cv2.LINE_AA)

        draw_part(landmarks.get("pose"), POSE_CONNECTIONS, _LINE_COLORS, _POINT_COLOR)
        draw_part(landmarks.get("left_hand"), HAND_CONNECTIONS,
                  [(255, 220, 0), (255, 140, 0)], (255, 255, 0))
        draw_part(landmarks.get("right_hand"), HAND_CONNECTIONS,
                  [(255, 0, 255), (180, 0, 180)], (255, 0, 255))
        return canvas

    def close(self):
        self._pose.close()
        self._hands.close()


def create_engine(name="mediapipe", **kwargs):
    """引擎工厂。以后加 DWPose 时在这里分支。"""
    if name == "mediapipe":
        return MediaPipePoseEngine(**kwargs)
    raise ValueError("未知姿态引擎: %s" % name)
