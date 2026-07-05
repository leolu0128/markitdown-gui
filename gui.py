"""MarkitDown GUI 批次轉換工具。"""
from __future__ import annotations

from pathlib import Path

_converter = None


def _get_converter():
    """延遲建立 MarkItDown 單例（首次載入較慢，避免拖慢視窗啟動）。"""
    global _converter
    if _converter is None:
        from markitdown import MarkItDown

        _converter = MarkItDown()
    return _converter


def convert_one(src_path: str | Path, out_dir: str | Path) -> tuple[bool, str]:
    """把單一檔案轉成 Markdown。

    回傳 (成功與否, 訊息)；成功時訊息為輸出檔路徑，失敗時為錯誤原因。
    """
    try:
        src = Path(src_path)
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        result = _get_converter().convert(str(src))
        dest = out / (src.stem + ".md")
        dest.write_text(result.text_content, encoding="utf-8")
        return True, str(dest)
    except Exception as exc:  # 任何轉換錯誤都不往外拋，由呼叫端顯示
        return False, f"{type(exc).__name__}: {exc}"
