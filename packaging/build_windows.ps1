# 构建 Windows 便携版（必须在 Windows x64 上执行）。
# 用法：powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectDir
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$AppName = "PoseExtractor"

if (-not (Test-Path $Python)) {
    throw "未找到 .venv\\Scripts\\python.exe。请先按 packaging\\README.windows.md 创建 Windows 虚拟环境。"
}

Write-Host "==> 1/3 PyInstaller 打包（Windows x64）"
& $Python -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name $AppName `
    --collect-all mediapipe `
    --collect-all gradio `
    --collect-all gradio_client `
    --collect-all imageio_ffmpeg `
    --paths . `
    --runtime-hook packaging\pyi_runtime_hook.py `
    --collect-submodules src `
    packaging\entry.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller 构建失败。" }

Write-Host "==> 2/3 整理便携版目录"
$PortableDir = Join-Path $ProjectDir "dist\$AppName-windows-x64"
Remove-Item -Recurse -Force $PortableDir -ErrorAction SilentlyContinue
Copy-Item -Recurse (Join-Path $ProjectDir "dist\$AppName") $PortableDir

Write-Host "==> 3/3 打包 ZIP"
$ZipPath = Join-Path $ProjectDir "dist\$AppName-windows-x64.zip"
Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
Compress-Archive -Path $PortableDir -DestinationPath $ZipPath
Write-Host "完成：$ZipPath"
