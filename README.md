# 📄 PDF 萬能工具箱

> **純本地 PDF 處理桌面工具** — 合併、壓縮、浮水印、轉圖片，全部在您自己的電腦上完成，無需上傳任何檔案。

![Python](https://img.shields.io/badge/Python-3.11-blue)
![GUI](https://img.shields.io/badge/GUI-tkinter-green)
![PDF Engine](https://img.shields.io/badge/PDF%20Engine-PyMuPDF-red)
![Build](https://img.shields.io/badge/Build-PyInstaller-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 📄 **合併 PDF** | 將多個 PDF 檔案依序合併為單一文件 |
| 📦 **壓縮 PDF** | 最佳化 PDF 大小，可調整壓縮程度 |
| 💧 **新增浮水印** | 自訂文字浮水印（字型、顏色、透明度、旋轉、位置、平鋪） |
| 🖼️ **轉換圖片** | PDF 每頁轉為 PNG / JPEG / WebP，可調整縮放與品質 |

### 為什麼選擇 PDF 萬能工具箱？

- 🔒 **100% 離線處理** — 所有操作在本機完成，檔案絕不外洩
- 🎯 **輕量快速** — 單一 EXE 約 30MB，免安裝即開即用
- 🖥️ **直覺介面** — 繁體中文，操作簡單
- 🆓 **完全免費** — MIT 開源授權

---

## 🚀 快速開始

### 方法一：直接執行（免安裝）

下載 [`PDFToolbox.exe`](dist/PDFToolbox.exe) 後直接雙擊開啟。

> **系統需求：** Windows 10 / 11，64 位元

### 方法二：原始碼執行

```bash
# 1. 安裝 Python 3.11+
# 2. 安裝依賴
pip install PyMuPDF

# 3. 執行程式
python main.py
```

### 方法三：自行打包

```bash
pip install PyMuPDF pyinstaller
python build_exe.py
```

---

## 📖 使用教學

### 基本流程

1. **新增檔案** — 點擊「🗁 新增檔案」選擇 PDF
2. **選擇工具** — 點擊四個功能按鈕之一
3. **設定參數** — 調整選項面板中的參數
4. **開始處理** — 點擊「▶ 開始處理」
5. **儲存結果** — 選擇輸出位置，完成！

### 各功能詳細說明

#### 合併 PDF
- 需至少選擇 2 個 PDF 檔案
- 依照檔案列表順序合併
- 支援大量檔案同時合併

#### 壓縮 PDF
- 滑桿往左 = 檔案更小（壓縮率更高）
- 滑桿往右 = 保留更高品質
- 建議值：0.6（推薦平衡）

#### 新增浮水印
- **文字**：輸入自訂浮水印內容
- **字型大小**：12px ~ 120px
- **透明度**：0.05（幾乎透明）~ 1.0（完全不透明）
- **旋轉角度**：-180° ~ 180°（建議 -30°）
- **顏色**：點擊選色器自訂
- **位置**：居中 / 左上 / 右上 / 左下 / 右下 / 平鋪

#### 轉換圖片
- **格式**：PNG（無損） / JPEG（較小） / WebP（現代格式）
- **縮放**：1x (72 DPI) / 2x (144 DPI) / 3x (216 DPI) / 4x (288 DPI)
- **品質**：僅 JPEG 與 WebP 可調整（10% ~ 100%）

---

## 📁 專案結構

```
pdf-toolbox-python/
├── main.py              # GUI 主程式（tkinter）
├── core.py              # PDF 核心處理模組（PyMuPDF）
├── build_exe.py         # 一鍵打包腳本（PyInstaller）
├── requirements.txt     # Python 依賴
├── icon.png             # 應用程式圖示
├── dist/
│   └── PDFToolbox.exe   # 可執行檔案
├── README.md            # 本文件
├── CHANGELOG.md         # 更新日誌
├── LICENSE              # MIT 授權條款
└── .gitignore
```

---

## 🧰 技術棧

| 項目 | 技術 |
|------|------|
| 程式語言 | Python 3.11 |
| GUI 框架 | tkinter / ttk |
| PDF 引擎 | PyMuPDF (fitz) |
| 打包工具 | PyInstaller |
| 授權 | MIT |

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

### 開發方向
- [ ] 支援更多 PDF 操作（分割、旋轉、簽名等）
- [ ] 圖片模式壓縮（降低圖片解析度）
- [ ] 批次處理多個檔案
- [ ] 深色模式
- [ ] 拖曳上傳支援
- [ ] 多語言介面

---

## 📜 更新日誌

請參閱 [CHANGELOG.md](CHANGELOG.md)

---

## 🙏 致謝

- [Stirling PDF](https://github.com/Stirling-Tools/Stirling-PDF) — 專案靈感來源
- [PyMuPDF](https://pypi.org/project/PyMuPDF/) — 強大的 PDF 處理引擎
- [PyInstaller](https://pyinstaller.org/) — 打包工具

---

<p align="center">Made with ❤️ for the open-source community</p>
