@echo off
title Webcam Studio Pro
cd /d "%~dp0"
python main.py
if errorlevel 1 pause
