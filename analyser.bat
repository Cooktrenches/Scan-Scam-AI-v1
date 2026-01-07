@echo off
chcp 65001 >nul
color 0B
cls

echo.
echo ===============================================================
echo          SCAM AI - SOLANA SECURITY SCANNER
echo          Token Analysis Tool
echo ===============================================================
echo.
echo.

:input
echo Enter the token address to analyze:
echo (or type 'exit' to quit)
echo.
set /p token=Address: 

if "%token%"=="exit" goto end
if "%token%"=="" goto input

echo.
echo Analyzing...
echo.

python main.py %token%

echo.
echo ---------------------------------------------------------------
echo.
echo Press any key to analyze another token...
pause >nul
cls
goto input

:end
echo Goodbye!
timeout /t 2 >nul
