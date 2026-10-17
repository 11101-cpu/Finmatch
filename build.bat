@echo off
setlocal enabledelayedexpansion

echo === Building FinMatch (C11 Core Engine) ===

REM Check if 64-bit GCC is in WinGet packages
set GCC_CMD=gcc
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-ChildItem -Path \"$env:LOCALAPPDATA\Microsoft\WinGet\Packages\" -Recurse -Filter \"x86_64-w64-mingw32-gcc.exe\" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName"') do (
    set GCC_CMD=%%i
)

echo Using compiler: %GCC_CMD%

set CORE_SRCS=core/src/order.c core/src/order_book.c core/src/heap.c core/src/linked_list.c core/src/hash_table.c core/src/matching_engine.c core/src/trades.c core/src/persistence.c core/src/finmatch_api.c

echo Building finmatch.dll...
"%GCC_CMD%" -O2 -Wall -Wextra -std=c11 -shared -DFINMATCH_EXPORTS %CORE_SRCS% -Icore/include -o finmatch.dll -Wl,--out-implib,libfinmatch.a
if %ERRORLEVEL% NEQ 0 (
    echo Error building finmatch.dll
    exit /b %ERRORLEVEL%
)

echo Building finmatch.exe (CLI)...
"%GCC_CMD%" -O2 -Wall -Wextra -std=c11 -DFINMATCH_STATIC core/src/main.c %CORE_SRCS% -Icore/include -o finmatch.exe
if %ERRORLEVEL% NEQ 0 (
    echo Error building finmatch.exe
    exit /b %ERRORLEVEL%
)

echo Building tests...
"%GCC_CMD%" -O2 -Wall -Wextra -std=c11 tests/test_orders.c %CORE_SRCS% -Icore/include -o tests/test_orders.exe
"%GCC_CMD%" -O2 -Wall -Wextra -std=c11 tests/test_matching.c %CORE_SRCS% -Icore/include -o tests/test_matching.exe
"%GCC_CMD%" -O2 -Wall -Wextra -std=c11 tests/test_edge_cases.c %CORE_SRCS% -Icore/include -o tests/test_edge_cases.exe

echo Building benchmark...
"%GCC_CMD%" -O3 -Wall -Wextra -std=c11 benchmarks/benchmark.c %CORE_SRCS% -Icore/include -o benchmarks/benchmark.exe

echo.
echo Build Succeeded! Run finmatch.exe or streamlit run interface/app.py
