@echo off
if "%1"=="docs" (
    python -m mkdocs serve
) else if "%1"=="test" (
    python -m unittest discover -s code/tests
) else if "%1"=="run" (
    python code/main.py
) else (
    echo Usage: make [docs^|test^|run]
)

