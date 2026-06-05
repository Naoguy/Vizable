@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Vizable suite — build + publish script
::
:: Builds EVERY extension under extensions\ into docs\, then regenerates the
:: GitHub Pages extension-repository index that hosts them all. Your team adds
:: one repo URL in Blender and can install/update any tool individually.
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

if not exist docs mkdir docs

echo.
echo  Building all extensions under extensions\ ...
for /d %%E in (extensions\*) do (
    echo.
    echo   - %%~nxE
    %BLENDER% --command extension build --source-dir "%%E" --output-dir docs
    if errorlevel 1 (
        echo  Build failed for %%E
        pause
        exit /b 1
    )
)

echo.
echo  Generating repository index...
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
