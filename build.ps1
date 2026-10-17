# FinMatch Build Script for Windows PowerShell
param (
    [switch]$RunTests,
    [switch]$RunBenchmark,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

if ($Clean) {
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    Remove-Item -Force -ErrorAction SilentlyContinue finmatch.dll, finmatch.exe, libfinmatch.a
    Remove-Item -Force -ErrorAction SilentlyContinue tests/*.exe
    Remove-Item -Force -ErrorAction SilentlyContinue benchmarks/*.exe
    Write-Host "Clean complete." -ForegroundColor Green
    exit 0
}

Write-Host "=== Building FinMatch (C11 Core Engine) ===" -ForegroundColor Cyan

# Locate 64-bit GCC compiler
$gccCmd = "gcc"
$wingetGcc = (Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "x86_64-w64-mingw32-gcc.exe" -ErrorAction SilentlyContinue | Select-Object -First 1)

if ($wingetGcc) {
    $gccCmd = $wingetGcc.FullName
    $gccDir = $wingetGcc.DirectoryName
    $env:Path = "$gccDir;" + $env:Path
    Write-Host "Using 64-bit MinGW GCC from: $gccDir" -ForegroundColor Gray
} else {
    Write-Host "Using system default: $gccCmd" -ForegroundColor Gray
}

$coreSrcs = @(
    "core/src/order.c",
    "core/src/order_book.c",
    "core/src/heap.c",
    "core/src/linked_list.c",
    "core/src/hash_table.c",
    "core/src/matching_engine.c",
    "core/src/trades.c",
    "core/src/persistence.c",
    "core/src/finmatch_api.c"
)

# 1. Build Shared Library (finmatch.dll)
Write-Host "Building shared library (finmatch.dll)..." -ForegroundColor Yellow
& $gccCmd -O2 -Wall -Wextra -std=c11 -shared -DFINMATCH_EXPORTS $coreSrcs -Icore/include -o finmatch.dll "-Wl,--out-implib,libfinmatch.a"
if ($LASTEXITCODE -ne 0) { throw "Failed to build finmatch.dll" }
Write-Host "Built finmatch.dll successfully." -ForegroundColor Green

# 2. Build CLI Executable (finmatch.exe)
Write-Host "Building standalone CLI (finmatch.exe)..." -ForegroundColor Yellow
& $gccCmd -O2 -Wall -Wextra -std=c11 -DFINMATCH_STATIC core/src/main.c $coreSrcs -Icore/include -o finmatch.exe
if ($LASTEXITCODE -ne 0) { throw "Failed to build finmatch.exe" }
Write-Host "Built finmatch.exe successfully." -ForegroundColor Green

# 3. Build Tests
Write-Host "Building test suite..." -ForegroundColor Yellow
& $gccCmd -O2 -Wall -Wextra -std=c11 tests/test_orders.c $coreSrcs -Icore/include -o tests/test_orders.exe
& $gccCmd -O2 -Wall -Wextra -std=c11 tests/test_matching.c $coreSrcs -Icore/include -o tests/test_matching.exe
& $gccCmd -O2 -Wall -Wextra -std=c11 tests/test_edge_cases.c $coreSrcs -Icore/include -o tests/test_edge_cases.exe
Write-Host "Built test executables successfully." -ForegroundColor Green

# 4. Build Benchmark
Write-Host "Building benchmark executable..." -ForegroundColor Yellow
& $gccCmd -O3 -Wall -Wextra -std=c11 benchmarks/benchmark.c $coreSrcs -Icore/include -o benchmarks/benchmark.exe
Write-Host "Built benchmark.exe successfully." -ForegroundColor Green

if ($RunTests) {
    Write-Host "`n=== Running Automated Tests ===" -ForegroundColor Cyan
    & .\tests\test_orders.exe
    & .\tests\test_matching.exe
    & .\tests\test_edge_cases.exe
}

if ($RunBenchmark) {
    Write-Host "`n=== Running Benchmark (50,000 orders) ===" -ForegroundColor Cyan
    & .\benchmarks\benchmark.exe 50000
}

Write-Host "`nBuild completed successfully!" -ForegroundColor Green
