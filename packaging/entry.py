# -*- coding: utf-8 -*-
"""PyInstaller 打包入口。

冻结运行（python -m PyInstaller 产出的 .app）时没有控制台，
把 stdout/stderr 追加到 ~/Library/Logs/PoseExtractor.log 便于排错。
"""
import os
import sys

if getattr(sys, "frozen", False):
    log_path = os.path.expanduser("~/Library/Logs/PoseExtractor.log")
    log_file = open(log_path, "a", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file

    # launch_counter 会往 gradio 包目录写 launches.json，
    # 冻结后该目录在已签名的 .app 内，写入会破坏 codesign seal，这里禁掉。
    import gradio.utils
    gradio.utils.launch_counter = lambda: None

from src.main import main

main()
