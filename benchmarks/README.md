# FinMatch Performance Benchmark

This benchmark measures the core execution speed, matching throughput, and latency distribution of the C matching engine without Python or GUI overhead.

## Methodology

1. **Pre-generation of Workload:**
   Synthetic orders and cancellations are generated in contiguous memory before timing begins. Workload generation overhead is strictly isolated from execution measurement.

2. **High-Resolution Monotonic Timers:**
   Windows `QueryPerformanceCounter` (or POSIX `clock_gettime(CLOCK_MONOTONIC)`) is used for sub-microsecond precision timing.

3. **Realistic Market Dynamics:**
   - Simulated across multiple symbols (RELIANCE, TCS, INFY, HDFCBANK)
   - Realistic tick movements around base prices
   - 50/50 Buy/Sell ratio
   - 10% realistic order cancellation rate

4. **Metrics Reported:**
   - Throughput (Orders / sec)
   - Total execution duration
   - Complete latency distribution: Min, Mean, Median (p50), p90, p95, p99, and Max latency (in microseconds)
   - Order book integrity and memory stats after execution

## Running the Benchmark

```bash
# Build the benchmark executable
gcc -O3 -Wall -Wextra -std=c11 benchmarks/benchmark.c core/src/order.c core/src/order_book.c core/src/heap.c core/src/linked_list.c core/src/hash_table.c core/src/matching_engine.c core/src/trades.c -Icore/include -o benchmarks/benchmark.exe

# Run with default 50,000 orders
./benchmarks/benchmark.exe

# Or specify custom order count (e.g. 100,000 orders)
./benchmarks/benchmark.exe 100000
```
