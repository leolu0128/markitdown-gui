# 打包成免安裝資料夾（PyInstaller onedir 模式）
# 用法：在專案根目錄執行 .\build.ps1，輸出在 dist\MarkitDown轉換器\，並產生對應 zip
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

& .\.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed `
    --name "MarkitDown轉換器" `
    --collect-all markitdown `
    --collect-all magika `
    --collect-all speech_recognition `
    gui.py

Copy-Item "使用說明.txt" "dist\MarkitDown轉換器\" -Force
Compress-Archive -Path "dist\MarkitDown轉換器" -DestinationPath "dist\MarkitDown轉換器-Windows免安裝版.zip" -Force
Write-Host "完成：dist\MarkitDown轉換器-Windows免安裝版.zip"
