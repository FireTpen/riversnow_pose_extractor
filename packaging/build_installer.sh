#!/bin/bash
# 构建独立 PoseExtractor.app（PyInstaller onedir + windowed）并打成 DMG。
# 用法：packaging/build_installer.sh
# 产物：dist/PoseExtractor.app、dist/PoseExtractor.dmg
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

PY=".venv/bin/python"
APP_NAME="PoseExtractor"
# windowed 模式下 BUNDLE 直接把 .app 放在 dist/ 根（dist/PoseExtractor/ 是同内容 onedir 目录）
APP="dist/$APP_NAME.app"
DMG="dist/$APP_NAME.dmg"
STAGING="dist/dmg_staging"

echo "==> 1/4 PyInstaller 打包（onedir + windowed, arm64）"
"$PY" -m PyInstaller --noconfirm --clean --windowed \
    --name "$APP_NAME" \
    --target-arch arm64 \
    --collect-all mediapipe \
    --collect-all gradio \
    --collect-all gradio_client \
    --collect-all imageio_ffmpeg \
    --paths . \
    --runtime-hook packaging/pyi_runtime_hook.py \
    --collect-submodules src \
    packaging/entry.py

echo "==> 2/4 ad-hoc 签名"
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP"

echo "==> 3/4 生成 DMG（.app + /Applications 符号链接）"
rm -rf "$STAGING" "$DMG"
mkdir -p "$STAGING"
cp -R "dist/$APP_NAME.app" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" -ov -format UDZO "$DMG"
rm -rf "$STAGING"

echo "完成：$DMG"
