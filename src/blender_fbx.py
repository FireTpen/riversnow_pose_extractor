"""Blender 后台脚本：MediaPipe world landmarks -> Mixamo 命名风格骨架动画 FBX。

由 src.fbx_export 启动；此文件只应在 Blender 内运行（需要 bpy/mathutils）。
"""
import json
import os
import sys

import bpy
from mathutils import Vector


PREFIX = "mixamorig:"

# name, parent, rest head, rest tail, target start/end keys
BONES = [
    ("Hips", None, (0, 0, 1.0), (0, 0, 1.15), "hips", "spine"),
    ("Spine", "Hips", (0, 0, 1.15), (0, 0, 1.35), "spine", "chest"),
    ("Spine1", "Spine", (0, 0, 1.35), (0, 0, 1.52), "chest", "neck"),
    ("Neck", "Spine1", (0, 0, 1.52), (0, 0, 1.68), "neck", "head"),
    ("Head", "Neck", (0, 0, 1.68), (0, 0, 1.88), "head", "head_top"),
    ("LeftShoulder", "Spine1", (0, 0, 1.48), (0.16, 0, 1.48), "chest", "l_shoulder"),
    ("LeftArm", "LeftShoulder", (0.16, 0, 1.48), (0.43, 0, 1.43), "l_shoulder", "l_elbow"),
    ("LeftForeArm", "LeftArm", (0.43, 0, 1.43), (0.66, 0, 1.36), "l_elbow", "l_wrist"),
    ("LeftHand", "LeftForeArm", (0.66, 0, 1.36), (0.75, 0, 1.36), "l_wrist", "l_hand_tip"),
    ("RightShoulder", "Spine1", (0, 0, 1.48), (-0.16, 0, 1.48), "chest", "r_shoulder"),
    ("RightArm", "RightShoulder", (-0.16, 0, 1.48), (-0.43, 0, 1.43), "r_shoulder", "r_elbow"),
    ("RightForeArm", "RightArm", (-0.43, 0, 1.43), (-0.66, 0, 1.36), "r_elbow", "r_wrist"),
    ("RightHand", "RightForeArm", (-0.66, 0, 1.36), (-0.75, 0, 1.36), "r_wrist", "r_hand_tip"),
    ("LeftUpLeg", "Hips", (0.09, 0, 1.0), (0.10, 0, 0.56), "l_hip", "l_knee"),
    ("LeftLeg", "LeftUpLeg", (0.10, 0, 0.56), (0.10, 0, 0.12), "l_knee", "l_ankle"),
    ("LeftFoot", "LeftLeg", (0.10, 0, 0.12), (0.10, -0.17, 0.02), "l_ankle", "l_foot"),
    ("RightUpLeg", "Hips", (-0.09, 0, 1.0), (-0.10, 0, 0.56), "r_hip", "r_knee"),
    ("RightLeg", "RightUpLeg", (-0.10, 0, 0.56), (-0.10, 0, 0.12), "r_knee", "r_ankle"),
    ("RightFoot", "RightLeg", (-0.10, 0, 0.12), (-0.10, -0.17, 0.02), "r_ankle", "r_foot"),
]

FINGERS = (("Thumb", (1, 2, 3, 4)), ("Index", (5, 6, 7, 8)),
           ("Middle", (9, 10, 11, 12)), ("Ring", (13, 14, 15, 16)),
           ("Pinky", (17, 18, 19, 20)))
for side in ("Left", "Right"):
    for finger, ids in FINGERS:
        parent = side + "Hand"
        for i in range(3):
            name = side + "Hand" + finger + str(i + 1)
            # 手指 rest pose 只决定初始骨长/朝向；动画由每帧 landmark 向量驱动。
            offset = (i + 1) * 0.045
            sign = 1 if side == "Left" else -1
            BONE_START = (sign * (0.75 + offset), 0.02 * (ids[0] % 4), 1.36)
            BONE_END = (sign * (0.75 + offset + 0.035), 0.02 * (ids[0] % 4), 1.36)
            BONES.append((name, parent, BONE_START, BONE_END,
                          "%s_%d" % (side.lower(), ids[i]),
                          "%s_%d" % (side.lower(), ids[i + 1])))
            parent = name


def mp_to_blender(point):
    """MediaPipe x-right/y-down/z-forward -> Blender x-right/y-back/z-up。"""
    return Vector((point["x"], -point["z"], -point["y"]))


def midpoint(a, b):
    return (a + b) * 0.5


def points_for_frame(frame):
    lms = frame.get("landmarks") or {}
    pose = lms.get("pose_world")
    if not pose:
        return None
    # 被遮挡关节的 world 值可能突然跳到身体另一侧；这一帧不参与解算，
    # 后续平滑器会保持最近可靠姿态。
    required = (0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 31, 32)
    if any(float(pose[index].get("visibility", 1.0)) < 0.45 for index in required):
        return None
    p = [mp_to_blender(x) for x in pose]
    hips = midpoint(p[23], p[24])
    chest = midpoint(p[11], p[12])
    neck = chest.lerp(p[0], 0.22)
    out = {
        "hips": hips, "spine": hips.lerp(chest, 0.35), "chest": chest,
        "neck": neck, "head": p[0], "head_top": p[0] + (p[0] - neck) * 0.55,
        "l_shoulder": p[11], "l_elbow": p[13], "l_wrist": p[15],
        "r_shoulder": p[12], "r_elbow": p[14], "r_wrist": p[16],
        "l_hip": p[23], "l_knee": p[25], "l_ankle": p[27], "l_foot": p[31],
        "r_hip": p[24], "r_knee": p[26], "r_ankle": p[28], "r_foot": p[32],
    }
    for side, wrist_key in (("left", "l_wrist"), ("right", "r_wrist")):
        hand = lms.get(side + "_hand_world")
        if not hand:
            out[("l" if side == "left" else "r") + "_hand_tip"] = out[wrist_key]
            continue
        # 手部世界点以手自身中心为原点；只把相对向量附着到 Pose 的手腕位置。
        hand_pts = [mp_to_blender(x) for x in hand]
        wrist = out[wrist_key]
        local = [q - hand_pts[0] for q in hand_pts]
        prefix = "left" if side == "left" else "right"
        for index, q in enumerate(local):
            out["%s_%d" % (prefix, index)] = wrist + q
        out[("l" if side == "left" else "r") + "_hand_tip"] = wrist + local[9]
    return out


def smooth_targets(data, position_alpha=0.24):
    """指数平滑世界点，并在短暂遮挡时保持上一帧的有效关节。

    直接使用逐帧 MediaPipe 估计会把毫米级点抖动放大成明显的骨骼角度跳变；
    这里优先稳定性。位置 alpha 越小，越平滑但反应越慢。
    """
    previous = {}
    result = []
    fps = float(data.get("fps") or 30.0)
    # 约 4.5 m/s 的单帧位移已远超普通人体关节在该采样率下的合理变化；
    # 这类值通常是单目深度估计/遮挡导致的离群点。手部允许更快运动。
    max_body_step = 4.5 / fps
    max_hand_step = 6.0 / fps
    for frame in data["frames"]:
        current = points_for_frame(frame)
        if current:
            for key, value in current.items():
                if key in previous:
                    max_step = max_hand_step if key.startswith(("left_", "right_")) else max_body_step
                    if (value - previous[key]).length > max_step:
                        # 不让单帧离群值进入滤波器，否则会污染后续多帧。
                        continue
                    previous[key] = previous[key].lerp(value, position_alpha)
                else:
                    previous[key] = value.copy()
        result.append({key: value.copy() for key, value in previous.items()})
    return result


def create_armature(rest_targets):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    arm_data = bpy.data.armatures.new("MediaPipeMixamoRig")
    arm_obj = bpy.data.objects.new("MediaPipeMixamoRig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for name, _, head, tail, start_key, end_key in BONES:
        bone = arm_data.edit_bones.new(PREFIX + name)
        target_head = rest_targets.get(start_key, Vector(head))
        target_tail = rest_targets.get(end_key, Vector(tail))
        # 初始帧可能没有检测到手；这种骨骼保留默认 rest pose，稍后检测到时再动画化。
        if (target_tail - target_head).length < 1e-4:
            target_head, target_tail = Vector(head), Vector(tail)
        bone.head, bone.tail = target_head, target_tail
    for name, parent, _, _, _, _ in BONES:
        if parent:
            arm_data.edit_bones[PREFIX + name].parent = arm_data.edit_bones[PREFIX + parent]
    bpy.ops.object.mode_set(mode="POSE")
    for bone in arm_obj.pose.bones:
        bone.rotation_mode = "QUATERNION"
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def bake_animation(arm_obj, data, root_motion):
    fps = float(data.get("fps") or 30.0)
    bpy.context.scene.render.fps = round(fps)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = max(1, len(data["frames"]))
    targets_by_frame = smooth_targets(data)
    initial = next((x for x in targets_by_frame if x), None)
    if not initial:
        raise RuntimeError("没有可用的身体 world landmarks。")
    # rest_rot 是 Blender 编辑骨骼在 armature 空间中的朝向。动画属性必须是
    # 相对 rest pose 和父骨骼的局部旋转，不能把世界坐标直接写到子骨骼位置。
    rest_rot = {
        name: arm_obj.data.bones[PREFIX + name].matrix_local.to_quaternion()
        for name, _, _, _, _, _ in BONES
    }
    rest_dir = {name: (rest_rot[name] @ Vector((0, 1, 0))).normalized()
                for name, _, _, _, _, _ in BONES}
    # 每根骨骼保存上一帧的全局旋转。Quaternion q 与 -q 表示同一姿态，但若不
    # 统一符号，插值会产生 180° 抖动。
    previous_global_rotation = {}
    reference_hips = initial["hips"].copy()
    for frame_no, targets in enumerate(targets_by_frame, 1):
        if not targets:
            continue
        global_rotation = {}
        for name, parent, _, _, start_key, end_key in BONES:
            start, end = targets.get(start_key), targets.get(end_key)
            if start is None or end is None or (end - start).length < 1e-5:
                continue
            # 从 rest 骨骼方向到目标方向的最短旋转；保留 rest pose 的 roll，
            # 不会因全局 up-axis 在近竖直姿态时翻面。
            rotation = rest_dir[name].rotation_difference((end - start).normalized()) @ rest_rot[name]
            old_rotation = previous_global_rotation.get(name)
            if old_rotation:
                if old_rotation.dot(rotation) < 0:
                    rotation.negate()
                rotation = old_rotation.slerp(rotation, 0.28)
            previous_global_rotation[name] = rotation.copy()
            global_rotation[name] = rotation
            bone = arm_obj.pose.bones[PREFIX + name]
            # R_current = R_parent_current * R_parent_rest^-1 * R_bone_rest * R_local
            # 解得局部旋转。这样子骨骼始终跟随父级，不会出现散架。
            if parent and parent in global_rotation:
                local_rotation = (rest_rot[name].inverted() @ rest_rot[parent]
                                  @ global_rotation[parent].inverted() @ rotation)
            else:
                local_rotation = rest_rot[name].inverted() @ rotation
            bone.rotation_quaternion = local_rotation
            bone.keyframe_insert(data_path="rotation_quaternion", frame=frame_no)
        if root_motion:
            hips = arm_obj.pose.bones[PREFIX + "Hips"]
            hips.location = targets["hips"] - reference_hips
            hips.keyframe_insert(data_path="location", frame=frame_no)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) < 2:
        raise RuntimeError("Usage: blender_fbx.py -- keypoints.json animation.fbx [--root-motion]")
    keypoints_path, out_path = args[0], args[1]
    with open(keypoints_path, encoding="utf-8") as f:
        data = json.load(f)
    if not any((f.get("landmarks") or {}).get("pose_world") for f in data.get("frames", [])):
        raise RuntimeError("JSON 不含 pose_world。请使用新版应用重新处理视频后再导出 FBX。")
    initial_targets = next((x for x in smooth_targets(data) if x), None)
    arm = create_armature(initial_targets)
    bake_animation(arm, data, "--root-motion" in args)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.abspath(out_path), use_selection=True,
        object_types={"ARMATURE"}, add_leaf_bones=False,
        bake_anim=True, bake_anim_use_all_bones=True,
        bake_anim_simplify_factor=0.0)
    print("EXPORTED_FBX=" + os.path.abspath(out_path))


if __name__ == "__main__":
    main()
