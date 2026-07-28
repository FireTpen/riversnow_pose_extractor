# -*- coding: utf-8 -*-
"""启动入口：python -m src.main"""
import os
import sys

# 本机开了系统代理时，Python 会把对 127.0.0.1 的自检请求也发给代理，
# 导致 Gradio 误判 localhost 不可达。这里彻底绕过代理（应用只监听本机）。
import urllib.request
urllib.request.getproxies = lambda: {}
for _var in ("http_proxy", "https_proxy", "all_proxy", "no_proxy",
             "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
    os.environ.pop(_var, None)

# 保证从任意目录启动时都能 import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui import build_ui


def main():
    demo = build_ui()
    # 不用 inbrowser=True（会打开 127.0.0.1）。改用 localhost 域名打开：
    # 多数代理工具和浏览器对 "localhost" 默认直连，而 127.0.0.1 可能被代理，
    # 导致上传请求 fetch 失败（"Connection errored out"）。
    url = "http://localhost:7860"
    import tempfile
    import threading
    import webbrowser
    threading.Timer(1.5, webbrowser.open, args=(url,)).start()
    # allowed_paths 放开系统临时目录：转码副本等临时产物需要能被 /file= 路由服务，
    # 否则浏览器加载 403，播放器时长显示 NaN:NaN（本机单人应用，安全影响可接受）。
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=False,
                show_error=True, allowed_paths=[tempfile.gettempdir()])


if __name__ == "__main__":
    main()
