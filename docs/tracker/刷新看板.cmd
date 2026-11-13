@echo off
chcp 65001 >nul
"H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe" -B "H:\UltimaAI\UltimaAgent\devtools\tracker-live.py"
start "" "H:\UltimaAI\UltimaAgent\docs\tracker\北极星上线任务清单.html"
exit
