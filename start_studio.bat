@echo off
setlocal
title GOAT LangGraph Studio Server
echo ===================================================
echo Starting GOAT LangGraph Studio Server...
echo ===================================================
set PYTHONIOENCODING=utf-8
langgraph dev --port 2024
pause


