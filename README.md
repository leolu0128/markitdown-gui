# MarkitDown Batch Converter / MarkitDown 批次轉換器

A small desktop GUI that batch-converts documents (PDF, Word, PowerPoint, Excel,
images, HTML, CSV, and more) into Markdown, built on Microsoft's
[markitdown](https://github.com/microsoft/markitdown) **v0.1.6**. Bilingual
interface (English / 繁體中文) with a one-click language toggle.

一個把各種文件（PDF、Word、PowerPoint、Excel、圖片、HTML、CSV…）批次轉成
Markdown 的桌面工具，底層使用微軟的
[markitdown](https://github.com/microsoft/markitdown) **v0.1.6**。介面支援中英雙語，一鍵切換。

---

## Features / 功能

- **Batch conversion** — pick many files at once and convert them in one go.
- **Choose the output folder** — Markdown files are written wherever you want.
- **Original filenames preserved** — `report.docx` becomes `report.md`.
- **Live progress** — per-file status (waiting / converting / done / failed) plus a progress bar.
- **Bilingual UI** — switch between English and 繁體中文 with the button in the top-right corner.
- **Runs fully offline** — nothing is uploaded anywhere.

—

- **批次轉換** — 一次選取多個檔案，一鍵全部轉完。
- **自選輸出資料夾** — Markdown 檔想放哪就放哪。
- **沿用原始檔名** — `報告.docx` → `報告.md`。
- **即時進度** — 每個檔案顯示狀態（等待中／轉換中／完成／失敗）並有進度條。
- **中英雙語** — 用右上角的按鈕切換介面語言。
- **完全離線** — 檔案不會上傳到任何地方。

## Supported formats / 支援格式

PDF, Word (`.docx`), PowerPoint (`.pptx`), Excel (`.xlsx`), images, HTML, CSV,
JSON, XML, ZIP, EPUB, and more — see the
[markitdown documentation](https://github.com/microsoft/markitdown) for the full list.

> Audio transcription additionally requires [ffmpeg](https://ffmpeg.org/) to be
> installed on the machine. All other formats work out of the box.
>
> 音訊轉錄需要電腦另外安裝 [ffmpeg](https://ffmpeg.org/)，其他格式皆可直接使用。

## For end users (no Python needed) / 一般使用者（免安裝 Python）

1. Download the latest `MarkitDown轉換器-Windows免安裝版.zip` from the
   [Releases](../../releases) page.
2. Unzip the **whole folder** anywhere (don't copy just the `.exe` out on its own).
3. Double-click `MarkitDown轉換器.exe`.
4. On first launch Windows SmartScreen may warn "Windows protected your PC" —
   click **More info → Run anyway** (the app is unsigned).

Then: **Add Files** → confirm the **Output folder** → **Start Converting**.

—

1. 到 [Releases](../../releases) 頁面下載最新的 `MarkitDown轉換器-Windows免安裝版.zip`。
2. 把**整個資料夾**解壓縮到任意位置（不要只把 `.exe` 單獨複製出來）。
3. 雙擊 `MarkitDown轉換器.exe`。
4. 第一次開啟時 Windows 可能顯示「Windows 已保護您的電腦」，
   點**其他資訊 → 仍要執行**即可（本程式未購買數位簽章）。

接著：**加入檔案** → 確認**輸出資料夾** → **開始轉換**。

## Run from source / 從原始碼執行

Requires Python 3.10+ (developed on 3.13). / 需要 Python 3.10 以上（開發於 3.13）。

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python gui.py
```

On Windows you can also just double-click `MarkitDown轉換器.bat`, which launches
the GUI with `pythonw.exe` (no console window).

Windows 上也可以直接雙擊 `MarkitDown轉換器.bat`，它會用 `pythonw.exe`
啟動 GUI（不會出現命令列黑窗）。

## Build a distributable / 打包成免安裝版

```powershell
.\build.ps1
```

This runs PyInstaller in onedir mode and produces
`dist\MarkitDown轉換器-Windows免安裝版.zip` (~109 MB zipped, ~203 MB unzipped).

會以 PyInstaller onedir 模式打包，產出
`dist\MarkitDown轉換器-Windows免安裝版.zip`（壓縮後約 109 MB，解壓後約 203 MB）。

## Run the tests / 執行測試

```bash
pytest
```

## Project layout / 專案結構

```
gui.py                     # Conversion layer (convert_one) + Tkinter bilingual UI
MarkitDown轉換器.bat        # Double-click launcher (uses pythonw.exe)
build.ps1                  # PyInstaller packaging script
requirements.txt           # Dependencies
tests/                     # pytest unit tests
使用說明.txt                # Bundled quick-start guide (shipped inside the zip)
docs/superpowers/          # Design doc and implementation plan
```

## License / 授權

Released under the [MIT License](LICENSE). Third-party dependencies keep their
own licenses (markitdown is MIT; PyInstaller-built binaries are exempt from
PyInstaller's GPL, per its licensing terms).

本專案採用 [MIT 授權](LICENSE)。第三方依賴各自沿用其授權（markitdown 為 MIT；
依 PyInstaller 授權條款，用它打包出的執行檔不受其 GPL 拘束）。
