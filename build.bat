@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Vizable — build + publish script
::
:: Builds the extension zip and regenerates the GitHub Pages repo index.
:: Run this from the repo root each time you want to cut a new release.
::
:: Usage:  build.bat
:: ─────────────────────────────────────────────────────────────────────────────

:: Adjust this path if Blender is installed elsewhere
set BLENDER="C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"

if not exist %BLENDER% (
    echo.
    echo  ERROR: Blender not found at %BLENDER%
    echo  Edit the BLENDER variable at the top of build.bat to match your install.
    echo.
    pause
    exit /b 1
)

:: Ensure the docs folder exists
if not exist docs mkdir docs

echo.
echo  [1/2] Building extension zip...
%BLENDER% --command extension build --source-dir . --output-dir docs
if %errorlevel% neq 0 (
    echo  Build failed.
    pause
    exit /b 1
)

echo.
echo  [2/2] Generating repository index...
%BLENDER% --command extension server-generate --repo-dir docs
if %errorlevel% neq 0 (
    echo  server-generate failed.
    pause
    exit /b 1
)

echo.
echo  Done. Files in docs\:
dir /b docs
echo.
echo  Commit and push docs\ to deploy the update to GitHub Pages.
echo.
pause
