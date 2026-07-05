"""MarkitDown GUI 批次轉換工具。"""
from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

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
                        os.startfile(out_dir)
        except queue.Empty:
            pass
        root.after(POLL_MS, poll)

    root.after(POLL_MS, poll)
    root.mainloop()


if __name__ == "__main__":
    import sys

    # 隱藏參數：--selftest <來源檔> <輸出資料夾>，供打包後自動驗證用（windowed 模式無主控台，以結束碼回報）
    if len(sys.argv) == 4 and sys.argv[1] == "--selftest":
        ok, _msg = convert_one(sys.argv[2], sys.argv[3])
        sys.exit(0 if ok else 1)
    main()
