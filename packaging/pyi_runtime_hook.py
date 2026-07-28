# -*- coding: utf-8 -*-
"""PyInstaller runtime hook：预加载 cv2 原生扩展。

冻结后 sys.path[0] 指向 Resources（base_library.zip 所在目录），
cv2 自带 bootstrap 把扩展目录插到 sys.path[1]，重新 import "cv2" 时
又被 Resources 里的 cv2 包截获，报 "recursion is detected during
loading of cv2 binary extensions"。这里直接用扩展加载器把
cv2.abi3.so 装进 sys.modules['cv2']，绕开 bootstrap。
"""
import importlib.util
import os
import sys

if getattr(sys, "frozen", False):
    _cv2_dir = os.path.join(sys._MEIPASS, "cv2")
    _so = os.path.join(_cv2_dir, "cv2.abi3.so")
    if os.path.exists(_so):
        _spec = importlib.util.spec_from_file_location("cv2", _so)
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["cv2"] = _mod
        _spec.loader.exec_module(_mod)
        # cv2/data（haarcascades 等）路径
        _mod.__path__ = [_cv2_dir]
