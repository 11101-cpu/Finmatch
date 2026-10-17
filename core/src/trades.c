#include "../include/trades.h"
#include "../include/matching_engine.h"
#include <stdlib.h>
#include <string.h>

TradeHistory* trade_history_create(size_t initial_capacity) {
    if (initial_capacity < 32) initial_capacity = 32;

    TradeHistory* history = (TradeHistory*)malloc(sizeof(TradeHistory));
    if (!history) return NULL;

    history->trades = (Trade*)malloc(sizeof(Trade) * initial_capacity);
    if (!history->trades) {
        free(history);
        return NULL;
    }

    history->count = 0;
    history->capacity = initial_capacity;
    history->total_volume = 0;
    history->total_turnover_paise = 0;
    return history;
}

void trade_history_destroy(TradeHistory* history) {
    if (!history) return;
    if (history->trades) {
        free(history->trades);
    }
    free(history);
}

void trade_history_clear(TradeHistory* history) {
    if (!history) return;
    history->count = 0;
    history->total_volume = 0;
    history->total_turnover_paise = 0;
}

int trade_history_add(TradeHistory* history, uint64_t trade_id, const char* symbol,
                      uint64_t buy_order_id, uint64_t sell_order_id,
                      int64_t price, uint32_t quantity, int64_t timestamp, uint64_t sequence) {
    if (!history || !symbol) return FM_ERR_INVALID_ARGUMENT;

    if (history->count >= history->capacity) {
        size_t new_cap = history->capacity * 2;
        Trade* new_trades = (Trade*)realloc(history->trades, sizeof(Trade) * new_cap);
        if (!new_trades) return FM_ERR_OUT_OF_MEMORY;
        history->trades = new_trades;
        history->capacity = new_cap;
    }

    Trade* t = &history->trades[history->count++];
    t->trade_id = trade_id;
    strncpy(t->symbol, symbol, sizeof(t->symbol) - 1);
    t->symbol[sizeof(t->symbol) - 1] = '\0';
    t->buy_order_id = buy_order_id;
    t->sell_order_id = sell_order_id;
    t->price = price;
    t->quantity = quantity;
    t->timestamp = timestamp;
    t->sequence = sequence;

    history->total_volume += quantity;
    history->total_turnover_paise += (price * (int64_t)quantity);

    return FM_OK;
}

const Trade* trade_history_get(const TradeHistory* history, size_t index) {
    if (!history || index >= history->count) return NULL;
    return &history->trades[index];
}
