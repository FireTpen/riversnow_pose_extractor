#!/bin/bash
# 生成 PoseExtractor.app（标准 .app bundle，硬编码工程绝对路径）
set -e
PROJECT_DIR="/Users/fengjiahao/mycode_project/riversnow/pose_extractor"
APP_DIR="$PROJECT_DIR/PoseExtractor.app"
MACOS="$APP_DIR/Contents/MacOS"

rm -rf "$APP_DIR"
mkdir -p "$MACOS"

cat > "$MACOS/PoseExtractor" <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
LOG="\$HOME/Library/Logs/PoseExtractor.log"
# 强制 arm64：依赖库都是 arm64 编译，双击启动时系统可能选到 x86_64 切片
exec arch -arm64 .venv/bin/python -m src.main >>"\$LOG" 2>&1
EOF
chmod +x "$MACOS/PoseExtractor"

cat > "$APP_DIR/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>PoseExtractor</string>
  <key>CFBundleIdentifier</key>
  <string>local.poseextractor.app</string>
  <key>CFBundleName</key>
  <string>PoseExtractor</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleVersion</key>
  <string>1.0</string>
</dict>
</plist>
EOF

# ad-hoc 签名，避免 Gatekeeper 拦截
codesign --force --deep --sign - "$APP_DIR" >/dev/null 2>&1 || true

echo "已生成: $APP_DIR"
