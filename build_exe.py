import os, sys, subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

EXCLUDES = ["tensorflow","torch","torchvision","scipy","pandas","numpy","matplotlib",
            "pyarrow","sympy","PIL","lxml","cryptography","bcrypt","pygments","fsspec",
            "psutil","keras","skimage","cv2","pygame","pytest","nose","bokeh","plotly",
            "flask","django","selenium","bs4"]

cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed",
       "--name", "PDFToolbox", "--add-data", "core.py;.",
       "--clean", "--noconfirm", "--log-level", "WARN"]
for mod in EXCLUDES:
    cmd.extend(["--exclude-module", mod])
if os.path.exists("icon.png"):
    cmd.extend(["--icon", "icon.png"])
cmd.append("main.py")

subprocess.run(cmd, check=True)
exe = os.path.abspath("dist/PDFToolbox.exe")
print(f"\n✅ {exe}  ({os.path.getsize(exe)/1024/1024:.1f} MB)")
