# -*- coding: utf-8 -*-
"""PyInstaller 打包入口（macOS / Windows）。"""
import os
import sys

if getattr(sys, "frozen", False):
    if sys.platform == "darwin":
        log_path = os.path.expanduser("~/Library/Logs/PoseExtractor.log")
    elif os.name == "nt":
        log_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                                "PoseExtractor", "PoseExtractor.log")
    else:
        log_path = os.path.expanduser("~/.local/state/PoseExtractor/PoseExtractor.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_file = open(log_path, "a", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file

    # launch_counter 会往 gradio 包目录写 launches.json，
    # 冻结后该目录在已签名的 .app 内，写入会破坏 codesign seal，这里禁掉。
    import gradio.utils
    gradio.utils.launch_counter = lambda: None

from src.main import main

main()
