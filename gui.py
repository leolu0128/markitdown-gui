"""MarkitDown GUI 批次轉換工具（中／英雙語）。"""
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

# 介面字串翻譯表。兩種語言必須有完全相同的鍵（由 test_translation_keys_match 保證）。
# lang_button 顯示「另一個」語言，點下去即切換到該語言。
STRINGS = {
    "zh": {
        "title": "MarkitDown 批次轉換器",
        "lang_button": "EN",
        "add_files": "加入檔案",
        "remove_selected": "移除選取",
        "clear_all": "清空清單",
        "col_file": "檔案",
        "col_status": "狀態",
        "output_folder": "輸出資料夾：",
        "browse": "瀏覽…",
        "start": "開始轉換",
        "hint_add": "請加入檔案",
        "status_waiting": "等待中",
        "status_running": "⏳ 轉換中…",
        "status_ok": "✅ 完成",
        "status_fail": "❌ {msg}",
        "progress": "{done}/{total} 完成",
        "finished_status": "完成：成功 {ok}／失敗 {fail}",
        "dlg_pick_files": "選擇要轉換的檔案",
        "dlg_pick_out": "選擇輸出資料夾",
        "warn_no_files_title": "尚未選擇檔案",
        "warn_no_files_msg": "請先按「加入檔案」選擇要轉換的檔案。",
        "warn_no_out_title": "尚未選擇輸出資料夾",
        "warn_no_out_msg": "請先選擇 Markdown 的輸出資料夾。",
        "done_title": "轉換完成",
        "done_msg": "成功 {ok} 個、失敗 {fail} 個。\n要開啟輸出資料夾嗎？",
    },
    "en": {
        "title": "MarkitDown Batch Converter",
        "lang_button": "中",
        "add_files": "Add Files",
        "remove_selected": "Remove Selected",
        "clear_all": "Clear List",
        "col_file": "File",
        "col_status": "Status",
        "output_folder": "Output folder:",
        "browse": "Browse…",
        "start": "Start Converting",
        "hint_add": "Please add files",
        "status_waiting": "Waiting",
        "status_running": "⏳ Converting…",
        "status_ok": "✅ Done",
        "status_fail": "❌ {msg}",
        "progress": "{done}/{total} done",
        "finished_status": "Finished: {ok} succeeded / {fail} failed",
        "dlg_pick_files": "Select files to convert",
        "dlg_pick_out": "Select output folder",
        "warn_no_files_title": "No files selected",
        "warn_no_files_msg": 'Please click "Add Files" to choose files first.',
        "warn_no_out_title": "No output folder",
        "warn_no_out_msg": "Please select an output folder for the Markdown files.",
        "done_title": "Conversion complete",
        "done_msg": "{ok} succeeded, {fail} failed.\nOpen the output folder?",
    },
}


def main() -> None:
    root = tk.Tk()
    root.geometry("680x520")
    root.minsize(560, 420)

    # 目前語言與各列狀態都放在可變 dict，供閉包更新用。
    ui = {"lang": "zh"}
    # iid -> ("waiting" | "running" | "ok" | "fail", 錯誤訊息)
    row_state: dict[str, tuple[str, str]] = {}
    # 狀態列狀態：("hint",) / ("progress", done, total) / ("finished", ok, fail)
    line_state: tuple = ("hint",)

    progress_q: queue.Queue = queue.Queue()
    out_var = tk.StringVar()

    def t(key: str, **kw) -> str:
        text = STRINGS[ui["lang"]][key]
        return text.format(**kw) if kw else text

    # --- 頂部語言列 ---
    topbar = ttk.Frame(root, padding=(8, 8, 8, 0))
    topbar.pack(fill="x")
    lang_btn = ttk.Button(topbar, width=4)
    lang_btn.pack(side="right")

    # --- 檔案清單 ---
    list_frame = ttk.Frame(root, padding=(8, 8, 8, 0))
    list_frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(
        list_frame, columns=("name", "status"), show="headings", selectmode="extended"
    )
    tree.column("name", width=430)
    tree.column("status", width=180)
    scroll = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # --- 檔案操作按鈕 ---
    btn_frame = ttk.Frame(root, padding=8)
    btn_frame.pack(fill="x")
    add_btn = ttk.Button(btn_frame)
    add_btn.pack(side="left")
    remove_btn = ttk.Button(btn_frame)
    remove_btn.pack(side="left", padx=(8, 0))
    clear_btn = ttk.Button(btn_frame)
    clear_btn.pack(side="left", padx=(8, 0))

    # --- 輸出資料夾 ---
    out_frame = ttk.Frame(root, padding=(8, 0, 8, 8))
    out_frame.pack(fill="x")
    out_label = ttk.Label(out_frame)
    out_label.pack(side="left")
    ttk.Entry(out_frame, textvariable=out_var).pack(
        side="left", fill="x", expand=True, padx=(4, 4)
    )
    browse_btn = ttk.Button(out_frame)
    browse_btn.pack(side="left")

    # --- 進度區 ---
    bottom = ttk.Frame(root, padding=(8, 0, 8, 8))
    bottom.pack(fill="x")
    progress = ttk.Progressbar(bottom, mode="determinate")
    progress.pack(fill="x")
    status_var = tk.StringVar()
    ttk.Label(bottom, textvariable=status_var).pack(anchor="w", pady=(4, 0))
    start_btn = ttk.Button(bottom)
    start_btn.pack(anchor="e", pady=(4, 0))

    def render_row(iid: str) -> None:
        state, msg = row_state[iid]
        if state == "fail":
            tree.set(iid, "status", t("status_fail", msg=msg))
        else:
            tree.set(iid, "status", t(f"status_{state}"))

    def render_status_line() -> None:
        kind = line_state[0]
        if kind == "hint":
            status_var.set(t("hint_add"))
        elif kind == "progress":
            status_var.set(t("progress", done=line_state[1], total=line_state[2]))
        elif kind == "finished":
            status_var.set(t("finished_status", ok=line_state[1], fail=line_state[2]))

    def apply_lang() -> None:
        root.title(t("title"))
        lang_btn.config(text=t("lang_button"))
        add_btn.config(text=t("add_files"))
        remove_btn.config(text=t("remove_selected"))
        clear_btn.config(text=t("clear_all"))
        tree.heading("name", text=t("col_file"))
        tree.heading("status", text=t("col_status"))
        out_label.config(text=t("output_folder"))
        browse_btn.config(text=t("browse"))
        start_btn.config(text=t("start"))
        for iid in row_state:
            render_row(iid)
        render_status_line()

    def toggle_lang() -> None:
        ui["lang"] = "en" if ui["lang"] == "zh" else "zh"
        apply_lang()

    def add_files() -> None:
        paths = filedialog.askopenfilenames(title=t("dlg_pick_files"))
        for p in paths:
            if not tree.exists(p):  # 以完整路徑當 iid，自動去重
                tree.insert("", "end", iid=p, values=(Path(p).name, ""))
                row_state[p] = ("waiting", "")
                render_row(p)
        if paths and not out_var.get():
            out_var.set(str(Path(paths[0]).parent))

    def remove_selected() -> None:
        for iid in tree.selection():
            tree.delete(iid)
            row_state.pop(iid, None)

    def clear_all() -> None:
        tree.delete(*tree.get_children())
        row_state.clear()

    def browse_out() -> None:
        chosen = filedialog.askdirectory(title=t("dlg_pick_out"))
        if chosen:
            out_var.set(chosen)

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
        nonlocal line_state
        paths = list(tree.get_children())
        out_dir = out_var.get().strip()
        if not paths:
            messagebox.showwarning(t("warn_no_files_title"), t("warn_no_files_msg"))
            return
        if not out_dir:
            messagebox.showwarning(t("warn_no_out_title"), t("warn_no_out_msg"))
            return
        start_btn.config(state="disabled")
        progress.config(maximum=len(paths), value=0)
        for p in paths:
            row_state[p] = ("waiting", "")
            render_row(p)
        line_state = ("progress", 0, len(paths))
        render_status_line()
        threading.Thread(target=worker, args=(paths, out_dir), daemon=True).start()

    def poll() -> None:
        nonlocal line_state
        try:
            while True:
                event = progress_q.get_nowait()
                kind = event[0]
                if kind == "start":
                    iid = event[1]
                    row_state[iid] = ("running", "")
                    render_row(iid)
                elif kind == "done":
                    _, path, ok, msg, done, total = event
                    row_state[path] = ("ok", "") if ok else ("fail", msg)
                    render_row(path)
                    progress.config(value=done)
                    line_state = ("progress", done, total)
                    render_status_line()
                elif kind == "finished":
                    _, ok_count, total, out_dir = event
                    start_btn.config(state="normal")
                    line_state = ("finished", ok_count, total - ok_count)
                    render_status_line()
                    if messagebox.askyesno(
                        t("done_title"),
                        t("done_msg", ok=ok_count, fail=total - ok_count),
                    ):
                        os.startfile(out_dir)
        except queue.Empty:
            pass
        root.after(POLL_MS, poll)

    lang_btn.config(command=toggle_lang)
    add_btn.config(command=add_files)
    remove_btn.config(command=remove_selected)
    clear_btn.config(command=clear_all)
    browse_btn.config(command=browse_out)
    start_btn.config(command=start)

    apply_lang()
    root.after(POLL_MS, poll)
    root.mainloop()


if __name__ == "__main__":
    import sys

    # 隱藏參數：--selftest <來源檔> <輸出資料夾>，供打包後自動驗證用（windowed 模式無主控台，以結束碼回報）
    if len(sys.argv) == 4 and sys.argv[1] == "--selftest":
        ok, _msg = convert_one(sys.argv[2], sys.argv[3])
        sys.exit(0 if ok else 1)
    main()
