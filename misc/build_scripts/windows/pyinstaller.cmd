@echo off
setlocal EnableExtensions

set "RUN_DIR=%CD%"
set "PYINSTALLER_TAG=v6.11.1"
if not defined TARGET_ENV set "TARGET_ENV=%RUN_DIR%\env_build"
set "TEMP_DIR=%TEMP%\pyinstaller_%RANDOM%%RANDOM%"
set "PYINSTALLER_DIR=%TEMP_DIR%\pyinstaller"

if defined MSYSTEM (
    echo Run this script from CMD. 1>&2
    exit /b 1
)

where git >nul 2>&1 || (
    echo git was not found in PATH 1>&2
    exit /b 1
)

if not exist "%TARGET_ENV%\Scripts\python.exe" (
    echo Python virtual environment not found at: %TARGET_ENV% 1>&2
    echo Create one with: "python -m venv env_build" or set the TARGET_ENV variable. 1>&2
    exit /b 1
)

set "VCVARS_BAT="
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

if not exist "%VSWHERE%" (
    echo vswhere.exe not found. 1>&2
    exit /b 1
)

for /f "usebackq delims=" %%I in (`
    "%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath -nologo
`) do (
    set "VCVARS_BAT=%%I\VC\Auxiliary\Build\vcvars64.bat"
)

if not defined VCVARS_BAT (
    echo vcvars64.bat not found. 1>&2
    exit /b 1
)

call "%VCVARS_BAT%" >nul
if errorlevel 1 (
    echo Loading the MSVC environment failed. 1>&2
    exit /b 1
)

mkdir "%TEMP_DIR%" || exit /b 1
git clone -b "%PYINSTALLER_TAG%" --depth 1 https://github.com/pyinstaller/pyinstaller.git "%PYINSTALLER_DIR%"
if errorlevel 1 goto cleanup_fail

cd /d "%PYINSTALLER_DIR%\bootloader" || goto cleanup_fail
"%TARGET_ENV%\Scripts\python.exe" waf all
if errorlevel 1 goto cleanup_fail

cd /d "%PYINSTALLER_DIR%" || goto cleanup_fail
"%TARGET_ENV%\Scripts\python.exe" -m pip install .
if errorlevel 1 goto cleanup_fail

cd /d "%RUN_DIR%"
rmdir /s /q "%TEMP_DIR%" >nul 2>&1
exit /b 0

:cleanup_fail
cd /d "%RUN_DIR%"
rmdir /s /q "%TEMP_DIR%" >nul 2>&1
exit /b 1
