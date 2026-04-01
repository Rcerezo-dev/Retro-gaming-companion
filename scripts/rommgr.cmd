@echo off
setlocal enabledelayedexpansion

REM Try to find and activate conda environment rom_manager
REM Works on multiple computers with different usernames/paths

set PYTHONPATH=src
set FOUND_PYTHON=0

REM Method 1: Check if conda is in PATH and activate it
for /f "delims=" %%A in ('where conda.exe 2^>nul') do (
    if exist "%%A" (
        REM Get conda root directory
        for /f "delims=" %%B in ('conda info --base 2^>nul') do (
            if exist "%%B\envs\rom_manager\python.exe" (
                echo [rom_manager] Using conda environment at: %%B\envs\rom_manager
                "%%B\envs\rom_manager\python.exe" -m rom_manager %*
                set FOUND_PYTHON=1
                goto :end
            )
        )
    )
)

REM Method 2: Try common anaconda install paths for current user
for %%P in (
    "%USERPROFILE%\anaconda3\envs\rom_manager\python.exe"
    "%USERPROFILE%\miniconda3\envs\rom_manager\python.exe"
    "C:\anaconda3\envs\rom_manager\python.exe"
    "C:\miniconda3\envs\rom_manager\python.exe"
) do (
    if exist %%P (
        echo [rom_manager] Using python from: %%P
        %%P -m rom_manager %*
        set FOUND_PYTHON=1
        goto :end
    )
)

REM Method 3: If python is in PATH and rom_manager module is importable
if !FOUND_PYTHON!==0 (
    python.exe -m rom_manager %* 2>nul
    if !ERRORLEVEL!==0 (
        set FOUND_PYTHON=1
        goto :end
    )
)

REM Fallback: error message
if !FOUND_PYTHON!==0 (
    echo.
    echo [ERROR] Could not find rom_manager conda environment.
    echo.
    echo Options:
    echo 1. Ensure conda is installed and in PATH
    echo 2. Create/activate the environment manually:
    echo    ^> conda activate rom_manager
    echo    ^> cd "%~dp0.."
    echo    ^> python -m rom_manager %*
    echo.
    echo 3. Or set PYTHONPATH and run python directly:
    echo    ^> cd "%~dp0.."
    echo    ^> python -m rom_manager %*
    echo.
    exit /b 1
)

:end
endlocal
