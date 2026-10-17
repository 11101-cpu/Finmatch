#include "../core/include/matching_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef _WIN32
#include <windows.h>
static double get_time_sec(void) {
    LARGE_INTEGER freq, count;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&count);
    return (double)count.QuadPart / (double)freq.QuadPart;
}
#else
#include <time.h>
static double get_time_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}
#endif

typedef enum {
    OP_PLACE = 1,
    OP_CANCEL = 2
} OpType;

typedef struct WorkloadOp {
    OpType type;
    char trader_id[32];
    char symbol[16];
    int side;
    int64_t price_paise;
    uint32_t qty;
    uint64_t cancel_order_id;
} WorkloadOp;

static int compare_doubles(const void* a, const void* b) {
    double da = *(const double*)a;
    double db = *(const double*)b;
    if (da < db) return -1;
    if (da > db) return 1;
    return 0;
}

int main(int argc, char** argv) {
    size_t num_orders = 50000;
    if (argc > 1) {
        long val = atol(argv[1]);
        if (val > 0) num_orders = (size_t)val;
    }

    printf("====================================================================\n");
    printf("         FinMatch Matching Engine High-Resolution Benchmark         \n");
    printf("====================================================================\n");
    printf("Target Workload: %zu operations\n", num_orders);
    printf("Simulated Symbols: RELIANCE, TCS, INFY, HDFCBANK\n");
    printf("Cancellation Rate: ~10%%\n");
    printf("Compiler: GCC C11 standard\n");
    printf("Timer: Monotonic High-Resolution Hardware Counter\n");
    printf("--------------------------------------------------------------------\n");
    printf("Generating synthetic workload in memory (un-timed)...\n");

    WorkloadOp* workload = (WorkloadOp*)malloc(sizeof(WorkloadOp) * num_orders);
    if (!workload) {
        fprintf(stderr, "Failed to allocate memory for synthetic workload\n");
        return 1;
    }

    const char* symbols[] = {"RELIANCE", "TCS", "INFY", "HDFCBANK"};
    const int64_t base_prices[] = {250000, 350000, 150000, 160000}; /* in paise */

    /* Seed pseudo-random generator with fixed seed for exact reproducibility */
    srand(42);

    /* Track some order IDs placed for realistic cancellation */
    uint64_t* cancellable_ids = (uint64_t*)malloc(sizeof(uint64_t) * num_orders);
    size_t cancellable_count = 0;
    uint64_t simulated_id = 1;

    for (size_t i = 0; i < num_orders; i++) {
        int sym_idx = rand() % 4;
        int do_cancel = (cancellable_count > 50 && (rand() % 10 == 0));

        if (do_cancel) {
            workload[i].type = OP_CANCEL;
            size_t pick = rand() % cancellable_count;
            workload[i].cancel_order_id = cancellable_ids[pick];
            /* swap with last */
            cancellable_ids[pick] = cancellable_ids[--cancellable_count];
        } else {
            workload[i].type = OP_PLACE;
            snprintf(workload[i].trader_id, sizeof(workload[i].trader_id), "Trader_%d", (rand() % 200) + 1);
            strncpy(workload[i].symbol, symbols[sym_idx], sizeof(workload[i].symbol) - 1);
            workload[i].side = (rand() % 2 == 0) ? SIDE_BUY : SIDE_SELL;

            /* Price variation +/- 2% around base price in 25 paise ticks */
            int tick_offset = (rand() % 81) - 40; /* -40 to +40 ticks */
            workload[i].price_paise = base_prices[sym_idx] + (tick_offset * 25);
            workload[i].qty = ((rand() % 20) + 1) * 10; /* 10 to 200 shares */

            cancellable_ids[cancellable_count++] = simulated_id++;
        }
    }

    free(cancellable_ids);

    double* latencies_us = (double*)malloc(sizeof(double) * num_orders);
    if (!latencies_us) {
        free(workload);
        fprintf(stderr, "Failed to allocate memory for latencies\n");
        return 1;
    }

    MatchingEngine* engine = engine_create();
    if (!engine) {
        free(workload);
        free(latencies_us);
        fprintf(stderr, "Failed to create matching engine\n");
        return 1;
    }

    printf("Executing timed benchmark loop...\n");

    double start_time = get_time_sec();
    size_t successful_matches = 0;
    size_t cancellations_executed = 0;

    for (size_t i = 0; i < num_orders; i++) {
        double t0 = get_time_sec();

        if (workload[i].type == OP_PLACE) {
            OrderResult res;
            engine_place_order(engine, workload[i].trader_id, workload[i].symbol,
                               workload[i].side, workload[i].price_paise,
                               workload[i].qty, &res);
            if (res.trades_generated > 0) {
                successful_matches += res.trades_generated;
            }
        } else {
            CancelResult cres;
            int rc = engine_cancel_order(engine, workload[i].cancel_order_id, &cres);
            if (rc == FM_OK) {
                cancellations_executed++;
            }
        }

        double t1 = get_time_sec();
        latencies_us[i] = (t1 - t0) * 1000000.0; /* Convert to microseconds */
    }

    double end_time = get_time_sec();
    double total_duration = end_time - start_time;

    /* Sort latencies to compute percentiles */
    qsort(latencies_us, num_orders, sizeof(double), compare_doubles);

    double total_latency_us = 0.0;
    for (size_t i = 0; i < num_orders; i++) {
        total_latency_us += latencies_us[i];
    }
    double avg_latency_us = total_latency_us / (double)num_orders;
    double median_latency_us = latencies_us[num_orders / 2];
    double p90_latency_us = latencies_us[(size_t)(num_orders * 0.90)];
    double p95_latency_us = latencies_us[(size_t)(num_orders * 0.95)];
    double p99_latency_us = latencies_us[(size_t)(num_orders * 0.99)];
    double min_latency_us = latencies_us[0];
    double max_latency_us = latencies_us[num_orders - 1];

    double orders_per_sec = (double)num_orders / total_duration;

    printf("\n====================================================================\n");
    printf("                     BENCHMARK RESULTS SUMMARY                      \n");
    printf("====================================================================\n");
    printf("  Total Operations Processed:  %zu\n", num_orders);
    printf("  Total Benchmark Duration:    %.4f seconds\n", total_duration);
    printf("  Throughput:                  %.2f orders/sec\n", orders_per_sec);
    printf("  Matches Triggered:           %zu\n", successful_matches);
    printf("  Trades Executed:             %zu\n", engine->trade_history->count);
    printf("  Total Traded Shares:         %llu\n", (unsigned long long)engine->trade_history->total_volume);
    printf("  Total Turnover (INR):        %.2f\n", (double)engine->trade_history->total_turnover_paise / 100.0);
    printf("  Remaining Active Orders:     %zu\n", engine->active_orders->count);
    printf("  Successful Cancellations:    %zu\n", cancellations_executed);
    printf("--------------------------------------------------------------------\n");
    printf("  LATENCY DISTRIBUTION (Microseconds per Operation):\n");
    printf("    Min Latency:               %8.2f us\n", min_latency_us);
    printf("    Average Latency:           %8.2f us\n", avg_latency_us);
    printf("    Median (50th percentile):  %8.2f us\n", median_latency_us);
    printf("    90th Percentile:           %8.2f us\n", p90_latency_us);
    printf("    95th Percentile:           %8.2f us\n", p95_latency_us);
    printf("    99th Percentile:           %8.2f us\n", p99_latency_us);
    printf("    Max Latency:               %8.2f us\n", max_latency_us);
    printf("====================================================================\n\n");

    /* Export benchmark summary to a simple text/json for Streamlit performance page */
    FILE* bf = fopen("benchmarks/last_benchmark.json", "w");
    if (bf) {
        fprintf(bf, "{\n");
        fprintf(bf, "  \"total_orders\": %zu,\n", num_orders);
        fprintf(bf, "  \"total_duration_sec\": %.4f,\n", total_duration);
        fprintf(bf, "  \"orders_per_sec\": %.2f,\n", orders_per_sec);
        fprintf(bf, "  \"trades_executed\": %zu,\n", engine->trade_history->count);
        fprintf(bf, "  \"total_shares_traded\": %llu,\n", (unsigned long long)engine->trade_history->total_volume);
        fprintf(bf, "  \"active_orders_remaining\": %zu,\n", engine->active_orders->count);
        fprintf(bf, "  \"min_latency_us\": %.2f,\n", min_latency_us);
        fprintf(bf, "  \"avg_latency_us\": %.2f,\n", avg_latency_us);
        fprintf(bf, "  \"median_latency_us\": %.2f,\n", median_latency_us);
        fprintf(bf, "  \"p95_latency_us\": %.2f,\n", p95_latency_us);
        fprintf(bf, "  \"p99_latency_us\": %.2f,\n", p99_latency_us);
        fprintf(bf, "  \"max_latency_us\": %.2f\n", max_latency_us);
        fprintf(bf, "}\n");
        fclose(bf);
    }

    engine_destroy(engine);
    free(workload);
    free(latencies_us);

    return 0;
}
