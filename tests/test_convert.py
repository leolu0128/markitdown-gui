"""convert_one() 的單元測試（用 .txt 當來源，markitdown 內建支援）。"""
from pathlib import Path

from gui import convert_one


def test_output_uses_source_stem(tmp_path: Path):
    src = tmp_path / "年度報告.txt"
    src.write_text("hello markitdown", encoding="utf-8")
    out_dir = tmp_path / "out"

    ok, msg = convert_one(src, out_dir)

    assert ok, msg
    dest = out_dir / "年度報告.md"
    assert dest.exists()
    assert "hello markitdown" in dest.read_text(encoding="utf-8")
    assert msg == str(dest)


def test_overwrites_existing_md(tmp_path: Path):
    src = tmp_path / "a.txt"
    src.write_text("new content", encoding="utf-8")
    dest = tmp_path / "a.md"
    dest.write_text("old content", encoding="utf-8")

    ok, _ = convert_one(src, tmp_path)

    assert ok
    assert "new content" in dest.read_text(encoding="utf-8")


def test_failure_returns_message_not_exception(tmp_path: Path):
    ok, msg = convert_one(tmp_path / "不存在.docx", tmp_path)

    assert not ok
    assert msg  # 有錯誤訊息
