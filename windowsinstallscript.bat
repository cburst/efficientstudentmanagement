@echo off
:: Request administrator privileges and run the PowerShell script

powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File ""%~dp0setup.ps1""' -Verb RunAs"

:: Pause to keep the window open after completion
pause