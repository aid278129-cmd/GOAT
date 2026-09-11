@echo off
setlocal
title Zyntrix LangGraph Studio Server
echo ===================================================
echo Starting Zyntrix LangGraph Studio Server...
echo ===================================================
set PYTHONIOENCODING=utf-8
langgraph dev --port 2024
pause


