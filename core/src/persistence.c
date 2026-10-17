#define __USE_MINGW_ANSI_STDIO 1
#include "../include/persistence.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

#ifdef _WIN32
#include <direct.h>
#define MKDIR(dir) _mkdir(dir)
#else
#include <sys/stat.h>
#define MKDIR(dir) mkdir(dir, 0755)
#endif

static void ensure_parent_dir(const char* filepath) {
    char buf[512];
    strncpy(buf, filepath, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';

    char* slash = strrchr(buf, '/');
    if (!slash) slash = strrchr(buf, '\\');
    if (slash) {
        *slash = '\0';
        MKDIR(buf);
    }
}

int persistence_export_trades(const TradeHistory* history, const char* filepath) {
    if (!history || !filepath) return FM_ERR_INVALID_ARGUMENT;

    ensure_parent_dir(filepath);

    FILE* fp = fopen(filepath, "w");
    if (!fp) return FM_ERR_IO_FAILURE;

    fprintf(fp, "trade_id,symbol,buy_order_id,sell_order_id,price_paise,quantity,timestamp,sequence\n");

    for (size_t i = 0; i < history->count; i++) {
        const Trade* t = &history->trades[i];
        fprintf(fp, "%" PRIu64 ",%s,%" PRIu64 ",%" PRIu64 ",%" PRId64 ",%u,%" PRId64 ",%" PRIu64 "\n",
                t->trade_id,
                t->symbol,
                t->buy_order_id,
                t->sell_order_id,
                t->price,
                t->quantity,
                t->timestamp,
                t->sequence);
    }

    fclose(fp);
    return FM_OK;
}

int persistence_import_trades(TradeHistory* history, const char* filepath) {
    if (!history || !filepath) return FM_ERR_INVALID_ARGUMENT;

    FILE* fp = fopen(filepath, "r");
    if (!fp) return FM_ERR_IO_FAILURE;

    char line[512];
    /* Skip header line */
    if (!fgets(line, sizeof(line), fp)) {
        fclose(fp);
        return FM_OK; /* Empty file */
    }

    while (fgets(line, sizeof(line), fp)) {
        uint64_t trade_id = 0, buy_id = 0, sell_id = 0, seq = 0;
        char symbol[16] = {0};
        int64_t price = 0, ts = 0;
        uint32_t qty = 0;

        int fields = sscanf(line, "%" SCNu64 ",%15[^,],%" SCNu64 ",%" SCNu64 ",%" SCNd64 ",%u,%" SCNd64 ",%" SCNu64,
                            &trade_id, symbol, &buy_id, &sell_id, &price, &qty, &ts, &seq);
        if (fields == 8) {
            trade_history_add(history, trade_id, symbol,
                              buy_id, sell_id,
                              price, qty, ts, seq);
        }
    }

    fclose(fp);
    return FM_OK;
}

int persistence_export_orders(const MatchingEngine* engine, const char* filepath) {
    if (!engine || !filepath) return FM_ERR_INVALID_ARGUMENT;

    ensure_parent_dir(filepath);

    FILE* fp = fopen(filepath, "w");
    if (!fp) return FM_ERR_IO_FAILURE;

    fprintf(fp, "order_id,trader_id,symbol,side,price_paise,original_qty,remaining_qty,sequence,status,timestamp\n");

    if (engine->active_orders) {
        for (size_t i = 0; i < engine->active_orders->num_buckets; i++) {
            HashEntry* entry = engine->active_orders->buckets[i];
            while (entry) {
                Order* o = entry->order;
                if (o) {
                    fprintf(fp, "%" PRIu64 ",%s,%s,%d,%" PRId64 ",%u,%u,%" PRIu64 ",%d,%" PRId64 "\n",
                            o->order_id,
                            o->trader_id,
                            o->symbol,
                            o->side,
                            o->price,
                            o->original_qty,
                            o->remaining_qty,
                            o->sequence,
                            o->status,
                            o->timestamp);
                }
                entry = entry->next;
            }
        }
    }

    fclose(fp);
    return FM_OK;
}

int persistence_import_orders(MatchingEngine* engine, const char* filepath) {
    if (!engine || !filepath) return FM_ERR_INVALID_ARGUMENT;

    FILE* fp = fopen(filepath, "r");
    if (!fp) return FM_ERR_IO_FAILURE;

    char line[512];
    /* Skip header line */
    if (!fgets(line, sizeof(line), fp)) {
        fclose(fp);
        return FM_OK;
    }

    while (fgets(line, sizeof(line), fp)) {
        uint64_t order_id = 0, seq = 0;
        char trader_id[32] = {0};
        char symbol[16] = {0};
        int side = 0, status = 0;
        int64_t price = 0, ts = 0;
        uint32_t orig_qty = 0, rem_qty = 0;

        int fields = sscanf(line, "%" SCNu64 ",%31[^,],%15[^,],%d,%" SCNd64 ",%u,%u,%" SCNu64 ",%d,%" SCNd64,
                            &order_id, trader_id, symbol, &side, &price,
                            &orig_qty, &rem_qty, &seq, &status, &ts);

        if (fields == 10) {
            /* Only restore active orders (OPEN or PARTIALLY_FILLED) */
            if (status != ORDER_STATUS_OPEN && status != ORDER_STATUS_PARTIALLY_FILLED) {
                continue;
            }
            if (rem_qty == 0) {
                continue;
            }

            Order* order = order_create((uint64_t)order_id, trader_id, symbol, side,
                                        (int64_t)price, (uint32_t)orig_qty, (uint64_t)seq, (int64_t)ts);
            if (!order) continue;

            order->remaining_qty = rem_qty;
            order->status = status;

            OrderBook* book = engine_get_or_create_book(engine, symbol);
            if (!book) {
                order_destroy(order);
                continue;
            }

            PriceLevel* level = order_book_find_or_create_level(book, side, (int64_t)price);
            if (!level) {
                order_destroy(order);
                continue;
            }

            OrderNode* node = order_queue_push_tail(level->queue, order);
            if (!node) {
                order_destroy(order);
                continue;
            }

            hash_table_insert(engine->active_orders, order->order_id, order, level, node);

            if (order->order_id > engine->next_order_id) {
                engine->next_order_id = order->order_id;
            }
            if (order->sequence > engine->sequence_counter) {
                engine->sequence_counter = order->sequence;
            }
        }
    }

    fclose(fp);
    return FM_OK;
}
