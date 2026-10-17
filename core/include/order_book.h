#ifndef FINMATCH_ORDER_BOOK_H
#define FINMATCH_ORDER_BOOK_H

#include "heap.h"
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MAX_SYMBOL_LEN 16
#define MAX_SNAPSHOT_LEVELS 100

typedef struct PriceLevelSnapshot {
    int64_t price;          /* Price in paise */
    uint64_t total_volume;  /* Aggregate remaining shares at this price */
    uint32_t order_count;   /* Number of orders at this price */
} PriceLevelSnapshot;

typedef struct OrderBook {
    char symbol[MAX_SYMBOL_LEN];
    Heap* bids; /* Max-heap of Buy price levels */
    Heap* asks; /* Min-heap of Sell price levels */
} OrderBook;

/* Creates an order book for the given symbol */
OrderBook* order_book_create(const char* symbol);

/* Frees order book structure, heaps, and price levels */
void order_book_destroy(OrderBook* book);

/* Finds existing price level or creates and inserts a new one into the appropriate heap */
PriceLevel* order_book_find_or_create_level(OrderBook* book, int side, int64_t price);

/* Removes a price level from the heap and frees it */
void order_book_remove_level(OrderBook* book, int side, PriceLevel* level);

/* Returns best bid price level (NULL if no bids) */
PriceLevel* order_book_best_bid(const OrderBook* book);

/* Returns best ask price level (NULL if no asks) */
PriceLevel* order_book_best_ask(const OrderBook* book);

/* Extracts up to max_levels price level snapshots sorted from best to worst priority */
size_t order_book_get_levels(const OrderBook* book, int side, PriceLevelSnapshot* out_levels, size_t max_levels);

/* Calculates aggregate volume across all levels for a side */
uint64_t order_book_total_volume(const OrderBook* book, int side);

/* Calculates aggregate order count across all levels for a side */
size_t order_book_total_orders(const OrderBook* book, int side);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_ORDER_BOOK_H */
