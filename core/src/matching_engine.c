#include "../include/matching_engine.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#ifdef _WIN32
#include <windows.h>
static int64_t current_timestamp_ms(void) {
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    ULARGE_INTEGER uli;
    uli.LowPart = ft.dwLowDateTime;
    uli.HighPart = ft.dwHighDateTime;
    return (int64_t)((uli.QuadPart - 116444736000000000ULL) / 10000ULL);
}
#else
#include <sys/time.h>
static int64_t current_timestamp_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (int64_t)tv.tv_sec * 1000 + (tv.tv_usec / 1000);
}
#endif

MatchingEngine* engine_create(void) {
    MatchingEngine* engine = (MatchingEngine*)malloc(sizeof(MatchingEngine));
    if (!engine) return NULL;

    memset(engine->books, 0, sizeof(engine->books));
    engine->book_count = 0;

    engine->active_orders = hash_table_create(256);
    engine->trade_history = trade_history_create(128);

    if (!engine->active_orders || !engine->trade_history) {
        if (engine->active_orders) hash_table_destroy(engine->active_orders);
        if (engine->trade_history) trade_history_destroy(engine->trade_history);
        free(engine);
        return NULL;
    }

    engine->next_order_id = 0;
    engine->next_trade_id = 0;
    engine->sequence_counter = 0;
    engine->total_orders_submitted = 0;
    engine->initialized = true;

    return engine;
}

void engine_reset(MatchingEngine* engine) {
    if (!engine) return;

    /* Destroy all books and their orders */
    for (size_t i = 0; i < engine->book_count; i++) {
        if (engine->books[i]) {
            order_book_destroy(engine->books[i]);
            engine->books[i] = NULL;
        }
    }
    engine->book_count = 0;

    /* Clear hash table and trade history */
    hash_table_clear(engine->active_orders);
    trade_history_clear(engine->trade_history);

    engine->next_order_id = 0;
    engine->next_trade_id = 0;
    engine->sequence_counter = 0;
    engine->total_orders_submitted = 0;
}

void engine_destroy(MatchingEngine* engine) {
    if (!engine) return;

    for (size_t i = 0; i < engine->book_count; i++) {
        if (engine->books[i]) {
            order_book_destroy(engine->books[i]);
            engine->books[i] = NULL;
        }
    }

    if (engine->active_orders) {
        hash_table_destroy(engine->active_orders);
    }
    if (engine->trade_history) {
        trade_history_destroy(engine->trade_history);
    }

    free(engine);
}

OrderBook* engine_get_or_create_book(MatchingEngine* engine, const char* symbol) {
    if (!engine || !symbol) return NULL;

    for (size_t i = 0; i < engine->book_count; i++) {
        if (strcmp(engine->books[i]->symbol, symbol) == 0) {
            return engine->books[i];
        }
    }

    if (engine->book_count >= MAX_SUPPORTED_BOOKS) {
        return NULL;
    }

    OrderBook* book = order_book_create(symbol);
    if (!book) return NULL;

    engine->books[engine->book_count++] = book;
    return book;
}

OrderBook* engine_get_book(MatchingEngine* engine, const char* symbol) {
    if (!engine || !symbol) return NULL;

    for (size_t i = 0; i < engine->book_count; i++) {
        if (strcmp(engine->books[i]->symbol, symbol) == 0) {
            return engine->books[i];
        }
    }
    return NULL;
}

int engine_place_order(MatchingEngine* engine, const char* trader_id, const char* symbol,
                       int side, int64_t price_paise, uint32_t qty, OrderResult* out_result) {
    if (!engine || !out_result) return FM_ERR_INVALID_ARGUMENT;

    memset(out_result, 0, sizeof(OrderResult));

    int val_err = order_validate(trader_id, symbol, side, price_paise, qty);
    if (val_err != FM_OK) {
        out_result->error_code = val_err;
        return val_err;
    }

    OrderBook* book = engine_get_or_create_book(engine, symbol);
    if (!book) {
        out_result->error_code = FM_ERR_OUT_OF_MEMORY;
        return FM_ERR_OUT_OF_MEMORY;
    }

    uint64_t order_id = ++engine->next_order_id;
    uint64_t sequence = ++engine->sequence_counter;
    int64_t now_ms = current_timestamp_ms();

    Order* incoming = order_create(order_id, trader_id, symbol, side, price_paise, qty, sequence, now_ms);
    if (!incoming) {
        out_result->error_code = FM_ERR_OUT_OF_MEMORY;
        return FM_ERR_OUT_OF_MEMORY;
    }

    engine->total_orders_submitted++;
    uint32_t trades_generated = 0;

    /* MATCHING ENGINE LOGIC with Price-Time Priority */
    if (side == SIDE_BUY) {
        while (incoming->remaining_qty > 0) {
            PriceLevel* best_ask = order_book_best_ask(book);
            if (!best_ask || best_ask->price > incoming->price) {
                break; /* Best ask exceeds buy limit price: cannot match further */
            }

            Order* resting = order_queue_peek_head(best_ask->queue);
            if (!resting) {
                /* Empty queue at this price level, prune it */
                order_book_remove_level(book, SIDE_SELL, best_ask);
                continue;
            }

            /* Execution takes place at the RESTING order's price */
            int64_t exec_price = resting->price;
            uint32_t match_qty = (incoming->remaining_qty < resting->remaining_qty) ? 
                                  incoming->remaining_qty : resting->remaining_qty;

            uint64_t trade_id = ++engine->next_trade_id;
            uint64_t trade_seq = ++engine->sequence_counter;

            trade_history_add(engine->trade_history, trade_id, symbol,
                              incoming->order_id, resting->order_id,
                              exec_price, match_qty, now_ms, trade_seq);
            trades_generated++;

            incoming->remaining_qty -= match_qty;
            resting->remaining_qty -= match_qty;
            best_ask->queue->total_volume -= match_qty;

            if (resting->remaining_qty == 0) {
                resting->status = ORDER_STATUS_FILLED;
                order_queue_pop_head(best_ask->queue);
                hash_table_remove(engine->active_orders, resting->order_id);
                order_destroy(resting);

                if (order_queue_is_empty(best_ask->queue)) {
                    order_book_remove_level(book, SIDE_SELL, best_ask);
                }
            } else {
                resting->status = ORDER_STATUS_PARTIALLY_FILLED;
            }
        }
    } else { /* SIDE_SELL */
        while (incoming->remaining_qty > 0) {
            PriceLevel* best_bid = order_book_best_bid(book);
            if (!best_bid || best_bid->price < incoming->price) {
                break; /* Best bid is below sell limit price: cannot match further */
            }

            Order* resting = order_queue_peek_head(best_bid->queue);
            if (!resting) {
                /* Empty queue at this price level, prune it */
                order_book_remove_level(book, SIDE_BUY, best_bid);
                continue;
            }

            /* Execution takes place at the RESTING order's price */
            int64_t exec_price = resting->price;
            uint32_t match_qty = (incoming->remaining_qty < resting->remaining_qty) ? 
                                  incoming->remaining_qty : resting->remaining_qty;

            uint64_t trade_id = ++engine->next_trade_id;
            uint64_t trade_seq = ++engine->sequence_counter;

            trade_history_add(engine->trade_history, trade_id, symbol,
                              resting->order_id, incoming->order_id,
                              exec_price, match_qty, now_ms, trade_seq);
            trades_generated++;

            incoming->remaining_qty -= match_qty;
            resting->remaining_qty -= match_qty;
            best_bid->queue->total_volume -= match_qty;

            if (resting->remaining_qty == 0) {
                resting->status = ORDER_STATUS_FILLED;
                order_queue_pop_head(best_bid->queue);
                hash_table_remove(engine->active_orders, resting->order_id);
                order_destroy(resting);

                if (order_queue_is_empty(best_bid->queue)) {
                    order_book_remove_level(book, SIDE_BUY, best_bid);
                }
            } else {
                resting->status = ORDER_STATUS_PARTIALLY_FILLED;
            }
        }
    }

    /* Process incoming order state after matching */
    out_result->order_id = incoming->order_id;
    out_result->original_qty = incoming->original_qty;
    out_result->filled_qty = incoming->original_qty - incoming->remaining_qty;
    out_result->remaining_qty = incoming->remaining_qty;
    out_result->trades_generated = trades_generated;
    out_result->error_code = FM_OK;

    if (incoming->remaining_qty == 0) {
        incoming->status = ORDER_STATUS_FILLED;
        out_result->status = ORDER_STATUS_FILLED;
        order_destroy(incoming);
    } else {
        if (incoming->remaining_qty < incoming->original_qty) {
            incoming->status = ORDER_STATUS_PARTIALLY_FILLED;
            out_result->status = ORDER_STATUS_PARTIALLY_FILLED;
        } else {
            incoming->status = ORDER_STATUS_OPEN;
            out_result->status = ORDER_STATUS_OPEN;
        }

        /* Rest the remaining order in the order book */
        PriceLevel* level = order_book_find_or_create_level(book, side, incoming->price);
        if (!level) {
            order_destroy(incoming);
            out_result->error_code = FM_ERR_OUT_OF_MEMORY;
            return FM_ERR_OUT_OF_MEMORY;
        }

        OrderNode* node = order_queue_push_tail(level->queue, incoming);
        if (!node) {
            order_destroy(incoming);
            out_result->error_code = FM_ERR_OUT_OF_MEMORY;
            return FM_ERR_OUT_OF_MEMORY;
        }

        hash_table_insert(engine->active_orders, incoming->order_id, incoming, level, node);
    }

    return FM_OK;
}

int engine_cancel_order(MatchingEngine* engine, uint64_t order_id, CancelResult* out_result) {
    if (!engine || !out_result) return FM_ERR_INVALID_ARGUMENT;

    memset(out_result, 0, sizeof(CancelResult));
    out_result->order_id = order_id;

    HashEntry* entry = hash_table_lookup(engine->active_orders, order_id);
    if (!entry) {
        out_result->error_code = FM_ERR_ORDER_NOT_FOUND;
        return FM_ERR_ORDER_NOT_FOUND;
    }

    Order* order = entry->order;
    PriceLevel* level = entry->price_level;
    OrderNode* node = entry->node;

    if (!order || (order->status != ORDER_STATUS_OPEN && order->status != ORDER_STATUS_PARTIALLY_FILLED)) {
        out_result->error_code = FM_ERR_ORDER_ALREADY_FILLED;
        return FM_ERR_ORDER_ALREADY_FILLED;
    }

    out_result->status = ORDER_STATUS_CANCELLED;
    out_result->cancelled_qty = order->remaining_qty;
    out_result->error_code = FM_OK;

    char symbol[MAX_SYMBOL_LEN];
    strncpy(symbol, order->symbol, sizeof(symbol) - 1);
    symbol[sizeof(symbol) - 1] = '\0';
    int side = order->side;

    /* Remove from FIFO queue */
    order_queue_remove_node(level->queue, node);

    /* Remove from hash table index */
    hash_table_remove(engine->active_orders, order_id);

    /* Prune empty price level if needed */
    if (order_queue_is_empty(level->queue)) {
        OrderBook* book = engine_get_book(engine, symbol);
        if (book) {
            order_book_remove_level(book, side, level);
        }
    }

    order_destroy(order);
    return FM_OK;
}

int engine_get_order(MatchingEngine* engine, uint64_t order_id, Order* out_order) {
    if (!engine || !out_order) return FM_ERR_INVALID_ARGUMENT;

    HashEntry* entry = hash_table_lookup(engine->active_orders, order_id);
    if (!entry || !entry->order) {
        return FM_ERR_ORDER_NOT_FOUND;
    }

    memcpy(out_order, entry->order, sizeof(Order));
    return FM_OK;
}

int engine_get_stats(MatchingEngine* engine, const char* symbol, MarketStats* out_stats) {
    if (!engine || !symbol || !out_stats) return FM_ERR_INVALID_ARGUMENT;

    memset(out_stats, 0, sizeof(MarketStats));
    strncpy(out_stats->symbol, symbol, sizeof(out_stats->symbol) - 1);
    out_stats->symbol[sizeof(out_stats->symbol) - 1] = '\0';

    OrderBook* book = engine_get_book(engine, symbol);
    if (book) {
        PriceLevel* bb = order_book_best_bid(book);
        PriceLevel* ba = order_book_best_ask(book);

        out_stats->best_bid_paise = bb ? bb->price : 0;
        out_stats->best_ask_paise = ba ? ba->price : 0;

        if (bb && ba && ba->price >= bb->price) {
            out_stats->spread_paise = ba->price - bb->price;
        } else {
            out_stats->spread_paise = 0;
        }

        out_stats->total_buy_volume = order_book_total_volume(book, SIDE_BUY);
        out_stats->total_sell_volume = order_book_total_volume(book, SIDE_SELL);
    }

    out_stats->total_orders = engine->total_orders_submitted;

    /* Search trade history backwards for the latest trade of this symbol */
    if (engine->trade_history && engine->trade_history->count > 0) {
        for (int64_t i = (int64_t)engine->trade_history->count - 1; i >= 0; i--) {
            const Trade* t = &engine->trade_history->trades[i];
            if (strcmp(t->symbol, symbol) == 0) {
                out_stats->last_trade_price_paise = t->price;
                out_stats->last_trade_qty = t->quantity;
                break;
            }
        }

        /* Tally trades for this symbol */
        uint64_t sym_trades = 0;
        uint64_t sym_shares = 0;
        int64_t sym_turnover = 0;

        for (size_t i = 0; i < engine->trade_history->count; i++) {
            const Trade* t = &engine->trade_history->trades[i];
            if (strcmp(t->symbol, symbol) == 0) {
                sym_trades++;
                sym_shares += t->quantity;
                sym_turnover += (t->price * (int64_t)t->quantity);
            }
        }

        out_stats->total_trades = sym_trades;
        out_stats->total_shares_traded = sym_shares;
        out_stats->total_turnover_paise = sym_turnover;
    }

    return FM_OK;
}

const char* fm_error_string(int err_code) {
    switch (err_code) {
        case FM_OK: return "Success";
        case FM_ERR_INVALID_ARGUMENT: return "Invalid argument or parameters";
        case FM_ERR_ORDER_NOT_FOUND: return "Order not found in active order book";
        case FM_ERR_ORDER_ALREADY_FILLED: return "Order is already filled";
        case FM_ERR_ORDER_ALREADY_CANCELLED: return "Order is already cancelled";
        case FM_ERR_OUT_OF_MEMORY: return "Out of memory";
        case FM_ERR_BOOK_NOT_FOUND: return "Order book not found for symbol";
        case FM_ERR_IO_FAILURE: return "File I/O failure";
        case FM_ERR_PARSE_ERROR: return "CSV parsing error";
        case FM_ERR_INVALID_STATE: return "Invalid engine state";
        default: return "Unknown error";
    }
}
