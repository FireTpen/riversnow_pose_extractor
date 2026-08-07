# -*- coding: utf-8 -*-
"""将包含 MediaPipe world landmarks 的 JSON 导出为动画专用 FBX。"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_blender():
    """返回 Blender 可执行文件，支持 macOS、Windows 与 Linux。"""
    candidates = [
        os.environ.get("BLENDER_BIN"),
        "/Applications/Blender.app/Contents/MacOS/Blender",
        shutil.which("blender"),
        shutil.which("blender.exe"),
    ]
    if os.name == "nt":
        for root in filter(None, (
            os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMW6432"),
            os.environ.get("PROGRAMFILES(X86)"),
        )):
            blender_root = Path(root) / "Blender Foundation"
            if blender_root.is_dir():
                candidates.extend(
                    str(version_dir / "blender.exe")
                    for version_dir in sorted(blender_root.glob("Blender *"), reverse=True)
                )
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def export_fbx(keypoints_path, out_fbx_path, root_motion=False):
    """后台启动 Blender，生成 Mixamo 命名风格的 animation-only FBX。"""
    blender = find_blender()
    if not blender:
        raise RuntimeError(
            "未找到 Blender。请安装 Blender，或设置环境变量 BLENDER_BIN 指向 Blender 可执行文件。")
    if not os.path.isfile(keypoints_path):
        raise ValueError("关键点 JSON 不存在: %s" % keypoints_path)
    script = os.path.join(os.path.dirname(__file__), "blender_fbx.py")
    out_fbx_path = os.path.abspath(out_fbx_path)
    os.makedirs(os.path.dirname(out_fbx_path), exist_ok=True)
    cmd = [blender, "--background", "--python", script, "--",
           os.path.abspath(keypoints_path), out_fbx_path,
           "--root-motion" if root_motion else "--in-place"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not os.path.isfile(out_fbx_path):
        detail = (proc.stderr or proc.stdout or "未知 Blender 错误")[-2000:]
        raise RuntimeError("FBX 导出失败：%s" % detail)
    return out_fbx_path
