#ifndef FINMATCH_TRADES_H
#define FINMATCH_TRADES_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct Trade {
    uint64_t trade_id;
    char symbol[16];
    uint64_t buy_order_id;
    uint64_t sell_order_id;
    int64_t price;         /* Execution price in paise */
    uint32_t quantity;     /* Executed quantity */
    int64_t timestamp;     /* Epoch timestamp in milliseconds */
    uint64_t sequence;     /* Match sequence counter */
} Trade;

typedef struct TradeHistory {
    Trade* trades;
    size_t count;
    size_t capacity;
    uint64_t total_volume;        /* Sum of executed quantities */
    int64_t total_turnover_paise; /* Sum of (price * quantity) in paise */
} TradeHistory;

/* Creates a TradeHistory container */
TradeHistory* trade_history_create(size_t initial_capacity);

/* Frees the TradeHistory structure and array */
void trade_history_destroy(TradeHistory* history);

/* Appends a new completed trade to history */
int trade_history_add(TradeHistory* history, uint64_t trade_id, const char* symbol,
                      uint64_t buy_order_id, uint64_t sell_order_id,
                      int64_t price, uint32_t quantity, int64_t timestamp, uint64_t sequence);

/* Retrieves a trade record by index (0 to count-1) */
const Trade* trade_history_get(const TradeHistory* history, size_t index);

/* Resets trade history */
void trade_history_clear(TradeHistory* history);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_TRADES_H */
