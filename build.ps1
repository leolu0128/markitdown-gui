# 打包成免安裝資料夾（PyInstaller onedir 模式）
# 用法：在專案根目錄執行 .\build.ps1，輸出在 dist\MarkitDown轉換器\，並產生對應 zip
# 注意：本檔須以「UTF-8 含 BOM」儲存，否則 Windows PowerShell 5.1 會用 ANSI 讀取而使中文引號解析錯亂。
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# zip 檔名刻意使用純 ASCII：GitHub Releases 會把附件檔名中的非 ASCII 字元濾掉，
# 中文檔名上傳後會變成 MarkitDown.-Windows.zip 這種殘缺名稱。
$zip = "dist\MarkitDown-Batch-Converter-Windows-portable.zip"

& .\.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed `
    --name "MarkitDown轉換器" `
    --collect-all markitdown `
    --collect-all magika `
    --collect-all speech_recognition `
    gui.py

Copy-Item "使用說明.txt" "dist\MarkitDown轉換器\" -Force
Compress-Archive -Path "dist\MarkitDown轉換器" -DestinationPath $zip -Force
Write-Host "完成：$zip"
