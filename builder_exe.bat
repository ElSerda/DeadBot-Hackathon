@echo off
REM === Build DeadBot exe crowd-style ===
REM Usage : double-clique ou lance "builder_exe.bat" dans l'invite de commandes

SET NAME=deadbot

REM Nettoie les anciens builds
if exist dist\%NAME%.exe del /f /q dist\%NAME%.exe
if exist build rmdir /s /q build
if exist %NAME%.spec del /f /q %NAME%.spec

REM Compile avec PyInstaller
pyinstaller --onefile --name %NAME% --add-data "config.yaml;." plugin.py

REM === Copie auto du .exe compilé crowd dans le dossier plugin NVIDIA ===
set TARGET_DIR="C:\ProgramData\NVIDIA Corporation\nvtopps\rise\plugins\deadbot"
if exist %TARGET_DIR% (
    copy /Y dist\deadbot.exe %TARGET_DIR%
    echo [OK] Copie crowd deadbot.exe --> %TARGET_DIR%
) else (
    echo [WARN] Le dossier plugin NVIDIA n'existe pas : %TARGET_DIR%
    echo [INFO] Copie non effectuée.
)

REM Feedback crowd
if exist dist\%NAME%.exe (
    echo.
    echo [OK] Build crowd réussi : dist\%NAME%.exe
) else (
    echo.
    echo [FAIL] Build rate, check la log PyInstaller !
)
