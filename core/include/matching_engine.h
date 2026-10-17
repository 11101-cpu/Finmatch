#ifndef FINMATCH_MATCHING_ENGINE_H
#define FINMATCH_MATCHING_ENGINE_H

#include "order.h"
#include "order_book.h"
#include "hash_table.h"
#include "trades.h"
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_SUPPORTED_BOOKS 32

/* Error codes */
typedef enum {
    FM_OK = 0,
    FM_ERR_INVALID_ARGUMENT = -1,
    FM_ERR_ORDER_NOT_FOUND = -2,
    FM_ERR_ORDER_ALREADY_FILLED = -3,
    FM_ERR_ORDER_ALREADY_CANCELLED = -4,
    FM_ERR_OUT_OF_MEMORY = -5,
    FM_ERR_BOOK_NOT_FOUND = -6,
    FM_ERR_IO_FAILURE = -7,
    FM_ERR_PARSE_ERROR = -8,
    FM_ERR_INVALID_STATE = -9
} FmErrorCode;

typedef struct OrderResult {
    uint64_t order_id;
    int32_t status;
    uint32_t original_qty;
    uint32_t filled_qty;
    uint32_t remaining_qty;
    uint32_t trades_generated;
    int error_code;
} OrderResult;

typedef struct CancelResult {
    uint64_t order_id;
    int32_t status;
    uint32_t cancelled_qty;
    int error_code;
} CancelResult;

typedef struct MarketStats {
    char symbol[MAX_SYMBOL_LEN];
    int64_t best_bid_paise;
    int64_t best_ask_paise;
    int64_t spread_paise;
    int64_t last_trade_price_paise;
    uint32_t last_trade_qty;
    uint64_t total_buy_volume;
    uint64_t total_sell_volume;
    uint64_t total_orders;
    uint64_t total_trades;
    uint64_t total_shares_traded;
    int64_t total_turnover_paise;
} MarketStats;

typedef struct MatchingEngine {
    OrderBook* books[MAX_SUPPORTED_BOOKS];
    size_t book_count;
    HashTable* active_orders;
    TradeHistory* trade_history;
    uint64_t next_order_id;
    uint64_t next_trade_id;
    uint64_t sequence_counter;
    uint64_t total_orders_submitted;
    bool initialized;
} MatchingEngine;

/* Engine lifecycle */
MatchingEngine* engine_create(void);
void engine_destroy(MatchingEngine* engine);
void engine_reset(MatchingEngine* engine);

/* Order management */
int engine_place_order(MatchingEngine* engine, const char* trader_id, const char* symbol,
                       int side, int64_t price_paise, uint32_t qty, OrderResult* out_result);

int engine_cancel_order(MatchingEngine* engine, uint64_t order_id, CancelResult* out_result);

int engine_get_order(MatchingEngine* engine, uint64_t order_id, Order* out_order);

/* Order book access */
OrderBook* engine_get_or_create_book(MatchingEngine* engine, const char* symbol);
OrderBook* engine_get_book(MatchingEngine* engine, const char* symbol);

/* Market statistics */
int engine_get_stats(MatchingEngine* engine, const char* symbol, MarketStats* out_stats);

/* Helper string */
const char* fm_error_string(int err_code);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_MATCHING_ENGINE_H */
