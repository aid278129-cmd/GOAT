@echo off
setlocal
echo ===================================================
echo Starting Zyntrix LangGraph Studio Server...
echo ===================================================
set PYTHONIOENCODING=utf-8
"C:\Users\jeffi\AppData\Local\Python\pythoncore-3.14-64\Scripts\langgraph.exe" dev --port 2024
pause
