#!/bin/bash
# 命令行直接启动 PoseExtractor
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "未找到 .venv，请先运行: /usr/bin/python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt"
  exit 1
fi
source .venv/bin/activate
exec python -m src.main
