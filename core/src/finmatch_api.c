#ifndef FINMATCH_EXPORTS
#define FINMATCH_EXPORTS
#endif
#include "../include/finmatch_api.h"
#include "../include/matching_engine.h"
#include "../include/persistence.h"
#include <stdlib.h>
#include <string.h>

static MatchingEngine* g_engine = NULL;

FM_API int fm_init(void) {
    if (g_engine) {
        return FM_OK;
    }
    g_engine = engine_create();
    return g_engine ? FM_OK : FM_ERR_OUT_OF_MEMORY;
}

FM_API void fm_shutdown(void) {
    if (g_engine) {
        engine_destroy(g_engine);
        g_engine = NULL;
    }
}

FM_API int fm_reset(void) {
    if (!g_engine) {
        return fm_init();
    }
    engine_reset(g_engine);
    return FM_OK;
}

FM_API int fm_place_order(const char* trader_id, const char* symbol,
                          int32_t side, int64_t price_paise, uint32_t qty,
                          ApiOrderResult* out_result) {
    if (!g_engine) {
        int init_rc = fm_init();
        if (init_rc != FM_OK) return init_rc;
    }
    return engine_place_order(g_engine, trader_id, symbol, side, price_paise, qty, (OrderResult*)out_result);
}

FM_API int fm_cancel_order(uint64_t order_id, ApiCancelResult* out_result) {
    if (!g_engine) return FM_ERR_INVALID_STATE;
    return engine_cancel_order(g_engine, order_id, (CancelResult*)out_result);
}

FM_API int fm_get_order(uint64_t order_id, OrderSnapshot* out_order) {
    if (!g_engine || !out_order) return FM_ERR_INVALID_STATE;

    Order o;
    int rc = engine_get_order(g_engine, order_id, &o);
    if (rc != FM_OK) return rc;

    out_order->order_id = o.order_id;
    strncpy(out_order->trader_id, o.trader_id, sizeof(out_order->trader_id) - 1);
    out_order->trader_id[sizeof(out_order->trader_id) - 1] = '\0';

    strncpy(out_order->symbol, o.symbol, sizeof(out_order->symbol) - 1);
    out_order->symbol[sizeof(out_order->symbol) - 1] = '\0';

    out_order->side = o.side;
    out_order->price_paise = o.price;
    out_order->original_qty = o.original_qty;
    out_order->remaining_qty = o.remaining_qty;
    out_order->sequence = o.sequence;
    out_order->status = o.status;
    out_order->timestamp = o.timestamp;

    return FM_OK;
}

FM_API int fm_get_order_book(const char* symbol, OrderBookSnapshot* out_book) {
    if (!g_engine || !symbol || !out_book) return FM_ERR_INVALID_STATE;

    memset(out_book, 0, sizeof(OrderBookSnapshot));
    strncpy(out_book->symbol, symbol, sizeof(out_book->symbol) - 1);
    out_book->symbol[sizeof(out_book->symbol) - 1] = '\0';

    OrderBook* book = engine_get_book(g_engine, symbol);
    if (!book) {
        /* No orders yet for this symbol: return empty book */
        return FM_OK;
    }

    /* Snapshot Bids */
    PriceLevelSnapshot bid_levels[FM_MAX_BOOK_LEVELS];
    size_t bid_count = order_book_get_levels(book, SIDE_BUY, bid_levels, FM_MAX_BOOK_LEVELS);
    out_book->bid_count = (uint32_t)bid_count;
    for (size_t i = 0; i < bid_count; i++) {
        out_book->bids[i].price_paise = bid_levels[i].price;
        out_book->bids[i].total_volume = bid_levels[i].total_volume;
        out_book->bids[i].order_count = bid_levels[i].order_count;
    }

    /* Snapshot Asks */
    PriceLevelSnapshot ask_levels[FM_MAX_BOOK_LEVELS];
    size_t ask_count = order_book_get_levels(book, SIDE_SELL, ask_levels, FM_MAX_BOOK_LEVELS);
    out_book->ask_count = (uint32_t)ask_count;
    for (size_t i = 0; i < ask_count; i++) {
        out_book->asks[i].price_paise = ask_levels[i].price;
        out_book->asks[i].total_volume = ask_levels[i].total_volume;
        out_book->asks[i].order_count = ask_levels[i].order_count;
    }

    out_book->total_bid_volume = order_book_total_volume(book, SIDE_BUY);
    out_book->total_ask_volume = order_book_total_volume(book, SIDE_SELL);

    return FM_OK;
}

FM_API int fm_get_recent_trades(const char* symbol, TradeSnapshot* out_trades,
                                uint32_t max_trades, uint32_t* out_count) {
    if (!g_engine || !out_trades || !out_count || max_trades == 0) return FM_ERR_INVALID_STATE;

    *out_count = 0;
    TradeHistory* history = g_engine->trade_history;
    if (!history || history->count == 0) return FM_OK;

    uint32_t count = 0;
    /* Retrieve latest trades first (backwards iteration) */
    for (int64_t i = (int64_t)history->count - 1; i >= 0 && count < max_trades; i--) {
        const Trade* t = &history->trades[i];
        if (!symbol || strlen(symbol) == 0 || strcmp(t->symbol, symbol) == 0) {
            out_trades[count].trade_id = t->trade_id;
            strncpy(out_trades[count].symbol, t->symbol, sizeof(out_trades[count].symbol) - 1);
            out_trades[count].symbol[sizeof(out_trades[count].symbol) - 1] = '\0';
            out_trades[count].buy_order_id = t->buy_order_id;
            out_trades[count].sell_order_id = t->sell_order_id;
            out_trades[count].price_paise = t->price;
            out_trades[count].quantity = t->quantity;
            out_trades[count].timestamp = t->timestamp;
            out_trades[count].sequence = t->sequence;
            count++;
        }
    }

    *out_count = count;
    return FM_OK;
}

FM_API int fm_get_stats(const char* symbol, ApiMarketStats* out_stats) {
    if (!g_engine || !symbol || !out_stats) return FM_ERR_INVALID_STATE;
    return engine_get_stats(g_engine, symbol, (MarketStats*)out_stats);
}

FM_API int fm_export_csv(const char* orders_file, const char* trades_file) {
    if (!g_engine) return FM_ERR_INVALID_STATE;

    int rc = FM_OK;
    if (orders_file && strlen(orders_file) > 0) {
        rc = persistence_export_orders(g_engine, orders_file);
        if (rc != FM_OK) return rc;
    }
    if (trades_file && strlen(trades_file) > 0) {
        rc = persistence_export_trades(g_engine->trade_history, trades_file);
        if (rc != FM_OK) return rc;
    }
    return rc;
}

FM_API int fm_import_csv(const char* orders_file, const char* trades_file) {
    if (!g_engine) {
        int init_rc = fm_init();
        if (init_rc != FM_OK) return init_rc;
    }

    int rc = FM_OK;
    if (trades_file && strlen(trades_file) > 0) {
        rc = persistence_import_trades(g_engine->trade_history, trades_file);
        if (rc != FM_OK) return rc;
    }
    if (orders_file && strlen(orders_file) > 0) {
        rc = persistence_import_orders(g_engine, orders_file);
        if (rc != FM_OK) return rc;
    }
    return rc;
}

FM_API const char* fm_get_error_message(int32_t err_code) {
    return fm_error_string(err_code);
}
