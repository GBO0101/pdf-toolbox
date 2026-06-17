"""
PDF 萬能工具箱 - 核心處理模組
使用 PyMuPDF (fitz) 實現全部 PDF 操作
"""

import os
import fitz  # PyMuPDF
from typing import List, Tuple, Optional


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """將十六進制顏色轉為 RGB 浮點元組 (0-1)"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def blend_with_opacity(color: Tuple[float, float, float], opacity: float, bg: Tuple[float, float, float] = (1, 1, 1)) -> Tuple[float, float, float]:
    """將顏色按照透明度與背景混合"""
    r = color[0] * opacity + bg[0] * (1 - opacity)
    g = color[1] * opacity + bg[1] * (1 - opacity)
    b = color[2] * opacity + bg[2] * (1 - opacity)
    return (r, g, b)


def merge_pdfs(file_paths: List[str], output_path: str) -> str:
    """
    合併多個 PDF 文件為一個
    :param file_paths: PDF 文件路徑列表
    :param output_path: 輸出文件路徑
    :returns: 輸出文件路徑
    """
    if len(file_paths) < 2:
        raise ValueError("請至少選擇 2 個 PDF 文件")

    result = fitz.open()
    try:
        for path in file_paths:
            pdf = fitz.open(path)
            try:
                result.insert_pdf(pdf)
            finally:
                pdf.close()

        result.save(output_path, garbage=4, deflate=True)
    finally:
        result.close()

    return output_path


def compress_pdf(input_path: str, output_path: str, quality: float = 0.7) -> str:
    """
    壓縮 PDF 文件大小
    :param input_path: 輸入文件路徑
    :param output_path: 輸出文件路徑
    :param quality: 壓縮程度 (0.1-1.0)，越小壓縮越大
    :returns: 輸出文件路徑
    """
    pdf = fitz.open(input_path)
    try:
        # 清除元數據
        pdf.del_xml_metadata()
        pdf.metadata = {}

        # 根據 quality 決定壓縮參數
        if quality <= 0.3:
            # 最大壓縮：徹底清理 + 圖像縮減
            save_kwargs = {
                'garbage': 4,
                'deflate': True,
                'clean': True,
                'ascii': False,
                'linear': False,
            }
        elif quality <= 0.6:
            # 中等壓縮
            save_kwargs = {
                'garbage': 3,
                'deflate': True,
                'clean': True,
            }
        else:
            # 輕度壓縮
            save_kwargs = {
                'garbage': 1,
                'deflate': True,
            }

        pdf.save(output_path, **save_kwargs)
    finally:
        pdf.close()

    return output_path


def add_watermark(
    input_path: str,
    output_path: str,
    text: str = "CONFIDENTIAL",
    font_size: int = 48,
    color: str = "#CCCCCC",
    opacity: float = 0.4,
    rotation: int = -30,
    position: str = "center",
) -> str:
    """
    為 PDF 添加文字浮水印
    :param input_path: 輸入文件路徑
    :param output_path: 輸出文件路徑
    :param text: 浮水印文字
    :param font_size: 字號
    :param color: 顏色十六進制
    :param opacity: 不透明度 (0-1)
    :param rotation: 旋轉角度
    :param position: 位置 (center/top-left/top-right/bottom-left/bottom-right/tile)
    :returns: 輸出文件路徑
    """
    pdf = fitz.open(input_path)
    try:
        rgb_color = hex_to_rgb(color)

        for page_num in range(len(pdf)):
            page = pdf[page_num]
            rect = page.rect
            page_w, page_h = rect.width, rect.height

            # 估算文字寬度（粗略）
            text_width = len(text) * font_size * 0.6
            text_height = font_size

            if position == "tile":
                # 平鋪浮水印
                step_x = font_size * 5
                step_y = font_size * 4
                for y in range(-int(text_height), int(page_h + step_y), int(step_y)):
                    for x in range(0, int(page_w + step_x), int(step_x)):
                        page.insert_text(
                            point=(x, y),
                            text=text,
                            fontsize=font_size,
                            color=rgb_color,
                            rotate=rotation,
                            overlay=True,
                            stroke_opacity=opacity,
                            fill_opacity=opacity,
                        )
            else:
                # 單位置
                x, y = _calc_position(position, page_w, page_h, text_width, text_height, font_size)
                page.insert_text(
                    point=(x, y),
                    text=text,
                    fontsize=font_size,
                    color=rgb_color,
                    rotate=rotation,
                    overlay=True,
                    stroke_opacity=opacity,
                    fill_opacity=opacity,
                )

        pdf.save(output_path, garbage=4, deflate=True)
    finally:
        pdf.close()

    return output_path


def _calc_position(position: str, page_w: float, page_h: float, text_w: float, text_h: float, font_size: int) -> Tuple[float, float]:
    """計算浮水印位置"""
    margin = 40
    pos_map = {
        "top-left":      (margin, page_h - margin - font_size),
        "top-right":     (page_w - margin - text_w, page_h - margin - font_size),
        "bottom-left":   (margin, margin + text_h),
        "bottom-right":  (page_w - margin - text_w, margin + text_h),
        "center":        ((page_w - text_w) / 2, (page_h - text_h) / 2),
    }
    return pos_map.get(position, pos_map["center"])


def pdf_to_images(
    input_path: str,
    output_dir: str,
    format: str = "png",
    quality: int = 90,
    scale: int = 2,
    progress_callback=None,
) -> List[str]:
    """
    將 PDF 每頁轉為圖片
    :param input_path: 輸入文件路徑
    :param output_dir: 輸出目錄
    :param format: 圖片格式 (png/jpeg/webp)
    :param quality: JPEG/WebP 品質 (1-100)
    :param scale: 縮放倍數 (1-4)
    :param progress_callback: 進度回調函數(current, total)
    :returns: 生成的圖片文件路徑列表
    """
    os.makedirs(output_dir, exist_ok=True)
    pdf = fitz.open(input_path)
    total = len(pdf)
    output_paths = []

    try:
        for page_num in range(total):
            page = pdf[page_num]
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            ext = format
            if format == "jpeg":
                ext = "jpg"

            out_path = os.path.join(output_dir, f"page_{page_num + 1}.{ext}")
            pix.save(out_path)

            output_paths.append(out_path)

            if progress_callback:
                progress_callback(page_num + 1, total)
    finally:
        pdf.close()

    return output_paths


def get_pdf_page_count(file_path: str) -> int:
    """獲取 PDF 頁數"""
    try:
        pdf = fitz.open(file_path)
        count = len(pdf)
        pdf.close()
        return count
    except Exception:
        return 0


def get_file_size_str(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"


def word_to_pdf(input_path: str, output_path: str) -> str:
    """
    使用 WPS Word (或 Microsoft Word) 將 Word 文件轉換為 PDF
    :param input_path: .docx 或 .doc 檔案路徑
    :param output_path: 輸出 PDF 檔案路徑
    :returns: 輸出檔案路徑
    """
    try:
        import win32com.client
    except ImportError:
        raise RuntimeError("需要 pywin32 模組，請執行: pip install pywin32")

    # 依序嘗試 WPS 和 Microsoft Word
    prog_ids = ["Kwps.Application", "Word.Application"]
    app = None
    last_error = None
    for prog_id in prog_ids:
        try:
            app = win32com.client.Dispatch(prog_id)
            break
        except Exception as e:
            last_error = e
            continue

    if app is None:
        raise RuntimeError(
            "找不到 WPS 或 Microsoft Word，請確認已安裝 WPS Office 或 Microsoft Word"
        )

    app.Visible = False
    app.DisplayAlerts = False

    try:
        abs_in = os.path.abspath(input_path)
        abs_out = os.path.abspath(output_path)
        doc = app.Documents.Open(abs_in)
        doc.SaveAs(abs_out, FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
    except Exception as e:
        raise RuntimeError(f"轉換失敗：{e}\n請確認已安裝 WPS Office 或 Microsoft Word")
    finally:
        try:
            app.Quit()
        except Exception:
            pass

    return output_path


def is_word_file(path: str) -> bool:
    """檢查是否為 Word 檔案"""
    ext = os.path.splitext(path)[1].lower()
    return ext in ('.docx', '.doc', '.docm', '.dotx', '.dot')


def is_pdf_encrypted(path: str) -> bool:
    """
    檢查 PDF 是否有加密（需要密碼才能開啟）
    :param path: PDF 檔案路徑
    :returns: True 表示有加密
    """
    try:
        pdf = fitz.open(path)
        try:
            return pdf.is_encrypted
        finally:
            pdf.close()
    except Exception:
        return False


def unlock_pdf(input_path: str, output_path: str, password: str) -> str:
    """
    解鎖加密的 PDF（使用密碼驗證後存為無加密版本）
    :param input_path: 輸入 PDF 檔案路徑
    :param output_path: 輸出 PDF 檔案路徑（無加密）
    :param password: 使用者密碼
    :returns: 輸出檔案路徑
    :raises ValueError: 密碼錯誤或 PDF 未加密
    """
    pdf = fitz.open(input_path)
    try:
        if not pdf.is_encrypted:
            raise ValueError("此 PDF 沒有上鎖，無需解鎖")

        # 需要密碼驗證
        if pdf.needs_pass:
            auth = pdf.authenticate(password)
            if auth == 0:
                raise ValueError("密碼錯誤，請重新輸入")

        # 存為無加密版本
        pdf.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
    finally:
        pdf.close()

    return output_path
