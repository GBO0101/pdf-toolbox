"""
PDF 萬能工具箱 - 打包腳本
使用 PyInstaller 打包為單個 EXE 檔案
"""

import os
import sys
import subprocess

# 確保在專案目錄
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 安裝依賴
print("正在安裝依賴...")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

# 定義版本資訊
VERSION = "1.0.0"

# 檔案版本資訊（Windows 屬性）
version_info = f"""
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({VERSION.replace('.', ', ')}),
    prodvers=({VERSION.replace('.', ', ')}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=1,
    subtype=0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '080404b0',
          [StringStruct('CompanyName', 'PDF Toolbox'),
           StringStruct('FileDescription', 'PDF 萬能工具箱'),
           StringStruct('FileVersion', '{VERSION}'),
           StringStruct('InternalName', 'PDFToolbox'),
           StringStruct('LegalCopyright', ''),
           StringStruct('OriginalFilename', 'PDFToolbox.exe'),
           StringStruct('ProductName', 'PDF 萬能工具箱'),
           StringStruct('ProductVersion', '{VERSION}')])
      ]),
    VarFileInfo([VarStruct('Translation', [2052, 1200])])
  ]
)
"""

with open("version_info.txt", "w", encoding="utf-8") as f:
    f.write(version_info)

print("正在打包為 EXE（排除不相關的大型套件以加快速度）...")

# PyInstaller 命令 - 排除無關的大型套件
EXCLUDES = [
    "tensorflow", "torch", "torchvision", "scipy", "pandas",
    "numpy", "matplotlib", "pyarrow", "sympy", "PIL",
    "lxml", "cryptography", "bcrypt", "pygments", "fsspec",
    "psutil", "keras", "skimage", "cv2", "pygame",
    "pytest", "nose", "bokeh", "plotly", "flask",
    "django", "selenium", "bs4",
]

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "PDFToolbox",
    "--version-file", "version_info.txt",
    "--add-data", "core.py;.",
    "--clean",
    "--noconfirm",
    "--log-level", "WARN",
]

# 加入排除模組
for mod in EXCLUDES:
    cmd.extend(["--exclude-module", mod])

if os.path.exists("icon.png"):
    cmd.extend(["--icon", "icon.png"])

cmd.append("main.py")

try:
    subprocess.run(cmd, check=True)
    exe_path = os.path.abspath("dist/PDFToolbox.exe")
    size_mb = os.path.getsize(exe_path) / 1024 / 1024
    print(f"\n✅ 打包成功！")
    print(f"📁 輸出檔案: {exe_path}")
    print(f"📏 檔案大小: {size_mb:.1f} MB")
except subprocess.CalledProcessError as e:
    print(f"\n❌ 打包失敗: {e}")
    sys.exit(1)
