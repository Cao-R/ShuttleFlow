@echo off
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
chcp 65001 >nul 2>&1
title Clarification Agent - Interactive
d:\ShuttleFlow\venv\Scripts\python.exe d:\ShuttleFlow\clarification-agent\run_test.py
pause
