#ifndef FINMATCH_API_H
#define FINMATCH_API_H

#include <stdint.h>
#include <stddef.h>

#if defined(_WIN32) && !defined(FINMATCH_STATIC)
  #ifdef FINMATCH_EXPORTS
    #define FM_API __declspec(dllexport)
  #else
    #define FM_API __declspec(dllimport)
  #endif
#else
  #define FM_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define FM_MAX_SYMBOL_LEN 16
#define FM_MAX_TRADER_LEN 32
#define FM_MAX_BOOK_LEVELS 100

/* Order snapshot representation */
typedef struct OrderSnapshot {
    uint64_t order_id;
    char trader_id[FM_MAX_TRADER_LEN];
    char symbol[FM_MAX_SYMBOL_LEN];
    int32_t side;            /* 1 = BUY, 2 = SELL */
    int64_t price_paise;     /* 1 INR = 100 paise */
    uint32_t original_qty;
    uint32_t remaining_qty;
    uint64_t sequence;
    int32_t status;          /* 1 = OPEN, 2 = PARTIAL, 3 = FILLED, 4 = CANCELLED */
    int64_t timestamp;
} OrderSnapshot;

/* Price level snapshot */
typedef struct PriceLevelSnapshotApi {
    int64_t price_paise;
    uint64_t total_volume;
    uint32_t order_count;
} PriceLevelSnapshotApi;

/* Order book snapshot */
typedef struct OrderBookSnapshot {
    char symbol[FM_MAX_SYMBOL_LEN];
    PriceLevelSnapshotApi bids[FM_MAX_BOOK_LEVELS];
    uint32_t bid_count;
    PriceLevelSnapshotApi asks[FM_MAX_BOOK_LEVELS];
    uint32_t ask_count;
    uint64_t total_bid_volume;
    uint64_t total_ask_volume;
} OrderBookSnapshot;

/* Trade snapshot */
typedef struct TradeSnapshot {
    uint64_t trade_id;
    char symbol[FM_MAX_SYMBOL_LEN];
    uint64_t buy_order_id;
    uint64_t sell_order_id;
    int64_t price_paise;
    uint32_t quantity;
    int64_t timestamp;
    uint64_t sequence;
} TradeSnapshot;

/* Order placement return */
typedef struct ApiOrderResult {
    uint64_t order_id;
    int32_t status;
    uint32_t original_qty;
    uint32_t filled_qty;
    uint32_t remaining_qty;
    uint32_t trades_generated;
    int32_t error_code;
} ApiOrderResult;

/* Order cancellation return */
typedef struct ApiCancelResult {
    uint64_t order_id;
    int32_t status;
    uint32_t cancelled_qty;
    int32_t error_code;
} ApiCancelResult;

/* Market Statistics */
typedef struct ApiMarketStats {
    char symbol[FM_MAX_SYMBOL_LEN];
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
} ApiMarketStats;

/* Lifecycle APIs */
FM_API int fm_init(void);
FM_API void fm_shutdown(void);
FM_API int fm_reset(void);

/* Order Operations */
FM_API int fm_place_order(const char* trader_id, const char* symbol, 
                          int32_t side, int64_t price_paise, uint32_t qty, 
                          ApiOrderResult* out_result);

FM_API int fm_cancel_order(uint64_t order_id, ApiCancelResult* out_result);

FM_API int fm_get_order(uint64_t order_id, OrderSnapshot* out_order);

/* Market Data Queries */
FM_API int fm_get_order_book(const char* symbol, OrderBookSnapshot* out_book);

FM_API int fm_get_recent_trades(const char* symbol, TradeSnapshot* out_trades, 
                                uint32_t max_trades, uint32_t* out_count);

FM_API int fm_get_stats(const char* symbol, ApiMarketStats* out_stats);

/* Persistence APIs */
FM_API int fm_export_csv(const char* orders_file, const char* trades_file);
FM_API int fm_import_csv(const char* orders_file, const char* trades_file);

/* Utilities */
FM_API const char* fm_get_error_message(int32_t err_code);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_API_H */
