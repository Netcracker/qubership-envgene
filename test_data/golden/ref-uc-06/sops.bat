@echo off
if "%1" == "--decrypt" (
  type %4
) else if "%1" == "--extract" (
  echo extracted
) else if "%1" == "edit" (
  python %EDITOR% %4
) else (
  exit /b 0
)
