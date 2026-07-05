# MarkitDown GUI 批次轉換工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一個 Tkinter GUI，讓使用者多選檔案、選輸出資料夾，批次以 markitdown 轉成同主檔名的 .md 檔。

**Architecture:** 單檔 `gui.py` 分兩層：模組層級的 `convert_one()` 轉換函式（可獨立以 pytest 測試），與 `main()` 內的 Tkinter UI（背景執行緒 + `queue.Queue` + `root.after()` 輪詢回報進度）。另附 `.bat` 雙擊啟動檔。

**Tech Stack:** Python 3.13（既有 `.venv`）、Tkinter（內建）、`markitdown[all]`、pytest。

## Global Constraints

- 所有指令都用專案 venv 的直譯器：`D:\MarkitDown\.venv\Scripts\python.exe`
- 輸出檔名 = 來源主檔名 + `.md`，同名直接覆寫
- Markdown 一律以 UTF-8 寫入
- 單一檔案失敗不得中斷整批轉換
- UI 只能在 Tkinter 主執行緒更新（背景執行緒只塞 queue）
- Python 原始檔以 UTF-8 儲存

---

### Task 1: 轉換層 `convert_one()`

**Files:**
- Create: `D:\MarkitDown\gui.py`（本任務只含轉換層）
- Create: `D:\MarkitDown\requirements.txt`
- Test: `D:\MarkitDown\tests\test_convert.py`

**Interfaces:**
- Produces: `convert_one(src_path: str | Path, out_dir: str | Path) -> tuple[bool, str]` — 成功回 `(True, 輸出檔完整路徑)`，失敗回 `(False, 錯誤訊息)`。Task 2 的 UI 會呼叫它。

- [ ] **Step 1: 安裝依賴並寫 requirements.txt**

```powershell
& D:\MarkitDown\.venv\Scripts\python.exe -m pip install "markitdown[all]" pytest
```

`requirements.txt` 內容：

```
markitdown[all]
pytest
```

- [ ] **Step 2: 寫失敗測試**

`tests\test_convert.py`：

```python
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
```

- [ ] **Step 3: 執行測試，確認失敗**

Run: `& D:\MarkitDown\.venv\Scripts\python.exe -m pytest tests -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'gui'` 或 import error）

- [ ] **Step 4: 實作 `gui.py` 轉換層**

```python
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
```

- [ ] **Step 5: 執行測試，確認通過**

Run: `& D:\MarkitDown\.venv\Scripts\python.exe -m pytest tests -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```powershell
git add gui.py requirements.txt tests
git commit -m "feat: add convert_one conversion layer with tests"
```

---

### Task 2: Tkinter UI 層

**Files:**
- Modify: `D:\MarkitDown\gui.py`（附加 UI 程式碼於 `convert_one` 之後）

**Interfaces:**
- Consumes: `convert_one(src_path, out_dir) -> tuple[bool, str]`（Task 1）
- Produces: `main() -> None`，且檔尾有 `if __name__ == "__main__": main()`（Task 3 的 .bat 依賴直接執行 `gui.py`）

- [ ] **Step 1: 在 `gui.py` 檔頭補 import，檔尾加入 UI 程式碼**

檔頭 import 區改為：

```python
from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
```

檔尾附加：

```python
POLL_MS = 100

STATUS_WAITING = "等待中"
STATUS_RUNNING = "⏳ 轉換中…"


def main() -> None:
    root = tk.Tk()
    root.title("MarkitDown 批次轉換器")
    root.geometry("680x500")
    root.minsize(560, 400)

    progress_q: queue.Queue = queue.Queue()

    # --- 檔案清單 ---
    list_frame = ttk.Frame(root, padding=(8, 8, 8, 0))
    list_frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(
        list_frame, columns=("name", "status"), show="headings", selectmode="extended"
    )
    tree.heading("name", text="檔案")
    tree.heading("status", text="狀態")
    tree.column("name", width=430)
    tree.column("status", width=180)
    scroll = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    out_var = tk.StringVar()

    def add_files() -> None:
        paths = filedialog.askopenfilenames(title="選擇要轉換的檔案")
        for p in paths:
            if not tree.exists(p):  # 以完整路徑當 iid，自動去重
                tree.insert("", "end", iid=p, values=(Path(p).name, STATUS_WAITING))
        if paths and not out_var.get():
            out_var.set(str(Path(paths[0]).parent))

    def remove_selected() -> None:
        for iid in tree.selection():
            tree.delete(iid)

    def clear_all() -> None:
        tree.delete(*tree.get_children())

    btn_frame = ttk.Frame(root, padding=8)
    btn_frame.pack(fill="x")
    ttk.Button(btn_frame, text="加入檔案", command=add_files).pack(side="left")
    ttk.Button(btn_frame, text="移除選取", command=remove_selected).pack(
        side="left", padx=(8, 0)
    )
    ttk.Button(btn_frame, text="清空清單", command=clear_all).pack(
        side="left", padx=(8, 0)
    )

    # --- 輸出資料夾 ---
    out_frame = ttk.Frame(root, padding=(8, 0, 8, 8))
    out_frame.pack(fill="x")
    ttk.Label(out_frame, text="輸出資料夾：").pack(side="left")
    ttk.Entry(out_frame, textvariable=out_var).pack(
        side="left", fill="x", expand=True, padx=(4, 4)
    )

    def browse_out() -> None:
        chosen = filedialog.askdirectory(title="選擇輸出資料夾")
        if chosen:
            out_var.set(chosen)

    ttk.Button(out_frame, text="瀏覽…", command=browse_out).pack(side="left")

    # --- 進度區 ---
    bottom = ttk.Frame(root, padding=(8, 0, 8, 8))
    bottom.pack(fill="x")
    progress = ttk.Progressbar(bottom, mode="determinate")
    progress.pack(fill="x")
    status_var = tk.StringVar(value="請加入檔案")
    ttk.Label(bottom, textvariable=status_var).pack(anchor="w", pady=(4, 0))
    start_btn = ttk.Button(bottom, text="開始轉換")
    start_btn.pack(anchor="e", pady=(4, 0))

    def worker(paths: list[str], out_dir: str) -> None:
        total = len(paths)
        done = ok_count = 0
        for p in paths:
            progress_q.put(("start", p))
            ok, msg = convert_one(p, out_dir)
            done += 1
            ok_count += ok
            progress_q.put(("done", p, ok, msg, done, total))
        progress_q.put(("finished", ok_count, total, out_dir))

    def start() -> None:
        paths = list(tree.get_children())
        out_dir = out_var.get().strip()
        if not paths:
            messagebox.showwarning("尚未選擇檔案", "請先按「加入檔案」選擇要轉換的檔案。")
            return
        if not out_dir:
            messagebox.showwarning("尚未選擇輸出資料夾", "請先選擇 Markdown 的輸出資料夾。")
            return
        start_btn.config(state="disabled")
        progress.config(maximum=len(paths), value=0)
        for p in paths:
            tree.set(p, "status", STATUS_WAITING)
        status_var.set(f"0/{len(paths)} 完成")
        threading.Thread(target=worker, args=(paths, out_dir), daemon=True).start()

    start_btn.config(command=start)

    def poll() -> None:
        try:
            while True:
                event = progress_q.get_nowait()
                kind = event[0]
                if kind == "start":
                    tree.set(event[1], "status", STATUS_RUNNING)
                elif kind == "done":
                    _, path, ok, msg, done, total = event
                    tree.set(path, "status", "✅ 完成" if ok else f"❌ {msg}")
                    progress.config(value=done)
                    status_var.set(f"{done}/{total} 完成")
                elif kind == "finished":
                    _, ok_count, total, out_dir = event
                    start_btn.config(state="normal")
                    status_var.set(f"完成：成功 {ok_count}／失敗 {total - ok_count}")
                    if messagebox.askyesno(
                        "轉換完成",
                        f"成功 {ok_count} 個、失敗 {total - ok_count} 個。\n要開啟輸出資料夾嗎？",
                    ):
                        os.startfile(out_dir)  # noqa: S606 - 本機工具，路徑來自使用者選擇
        except queue.Empty:
            pass
        root.after(POLL_MS, poll)

    root.after(POLL_MS, poll)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 確認既有測試仍通過（UI 程式碼不影響匯入）**

Run: `& D:\MarkitDown\.venv\Scripts\python.exe -m pytest tests -v`
Expected: 3 passed

- [ ] **Step 3: 手動煙霧測試**

Run: `& D:\MarkitDown\.venv\Scripts\python.exe D:\MarkitDown\gui.py`（背景執行）
驗證：視窗開啟、加入一個 .txt 測試檔、選輸出資料夾、按開始轉換、狀態變 ✅、輸出資料夾出現同主檔名 .md。無法互動時至少確認視窗能開啟且無例外輸出。

- [ ] **Step 4: Commit**

```powershell
git add gui.py
git commit -m "feat: add Tkinter batch-conversion UI"
```

---

### Task 3: 雙擊啟動檔

**Files:**
- Create: `D:\MarkitDown\MarkitDown轉換器.bat`

**Interfaces:**
- Consumes: `gui.py` 可直接執行（Task 2 的 `if __name__ == "__main__"`）

- [ ] **Step 1: 建立 .bat**

內容（ASCII，`%~dp0` 指到 .bat 所在資料夾，`pythonw.exe` 不開黑窗）：

```bat
@echo off
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0gui.py"
```

- [ ] **Step 2: 驗證啟動**

Run: `cmd /c "D:\MarkitDown\MarkitDown轉換器.bat"`
Expected: 立即返回、無錯誤輸出，GUI 視窗開啟（以工作管理員或 `Get-Process pythonw` 確認）。

- [ ] **Step 3: Commit**

```powershell
git add "MarkitDown轉換器.bat"
git commit -m "feat: add double-click launcher"
```
