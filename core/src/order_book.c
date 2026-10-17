#include "../include/order_book.h"
#include "../include/order.h"
#include "../include/matching_engine.h"
#include <stdlib.h>
#include <string.h>

OrderBook* order_book_create(const char* symbol) {
    if (!symbol) return NULL;

    OrderBook* book = (OrderBook*)malloc(sizeof(OrderBook));
    if (!book) return NULL;

    strncpy(book->symbol, symbol, sizeof(book->symbol) - 1);
    book->symbol[sizeof(book->symbol) - 1] = '\0';

    book->bids = heap_create(HEAP_MAX, 16);
    book->asks = heap_create(HEAP_MIN, 16);

    if (!book->bids || !book->asks) {
        if (book->bids) heap_destroy(book->bids);
        if (book->asks) heap_destroy(book->asks);
        free(book);
        return NULL;
    }

    return book;
}

void order_book_destroy(OrderBook* book) {
    if (!book) return;

    if (book->bids) heap_destroy_deep(book->bids);
    if (book->asks) heap_destroy_deep(book->asks);
    free(book);
}

PriceLevel* order_book_find_or_create_level(OrderBook* book, int side, int64_t price) {
    if (!book) return NULL;

    Heap* heap = (side == SIDE_BUY) ? book->bids : book->asks;

    /* Check if price level already exists in heap */
    for (size_t i = 0; i < heap->size; i++) {
        if (heap->items[i]->price == price) {
            return heap->items[i];
        }
    }

    /* Create new price level */
    PriceLevel* level = price_level_create(price);
    if (!level) return NULL;

    if (heap_push(heap, level) != FM_OK) {
        price_level_destroy(level);
        return NULL;
    }

    return level;
}

void order_book_remove_level(OrderBook* book, int side, PriceLevel* level) {
    if (!book || !level) return;

    Heap* heap = (side == SIDE_BUY) ? book->bids : book->asks;
    if (level->heap_index < heap->size && heap->items[level->heap_index] == level) {
        heap_remove_at(heap, level->heap_index);
        price_level_destroy(level);
    }
}

PriceLevel* order_book_best_bid(const OrderBook* book) {
    if (!book) return NULL;
    return heap_peek(book->bids);
}

PriceLevel* order_book_best_ask(const OrderBook* book) {
    if (!book) return NULL;
    return heap_peek(book->asks);
}

static int compare_bid_levels(const void* a, const void* b) {
    const PriceLevel* la = *(const PriceLevel**)a;
    const PriceLevel* lb = *(const PriceLevel**)b;
    if (la->price > lb->price) return -1;
    if (la->price < lb->price) return 1;
    return 0;
}

static int compare_ask_levels(const void* a, const void* b) {
    const PriceLevel* la = *(const PriceLevel**)a;
    const PriceLevel* lb = *(const PriceLevel**)b;
    if (la->price < lb->price) return -1;
    if (la->price > lb->price) return 1;
    return 0;
}

size_t order_book_get_levels(const OrderBook* book, int side, PriceLevelSnapshot* out_levels, size_t max_levels) {
    if (!book || !out_levels || max_levels == 0) return 0;

    Heap* heap = (side == SIDE_BUY) ? book->bids : book->asks;
    if (heap->size == 0) return 0;

    size_t count = heap->size;
    PriceLevel** temp = (PriceLevel**)malloc(sizeof(PriceLevel*) * count);
    if (!temp) return 0;

    for (size_t i = 0; i < count; i++) {
        temp[i] = heap->items[i];
    }

    if (side == SIDE_BUY) {
        qsort(temp, count, sizeof(PriceLevel*), compare_bid_levels);
    } else {
        qsort(temp, count, sizeof(PriceLevel*), compare_ask_levels);
    }

    size_t written = (count < max_levels) ? count : max_levels;
    for (size_t i = 0; i < written; i++) {
        out_levels[i].price = temp[i]->price;
        out_levels[i].total_volume = temp[i]->queue->total_volume;
        out_levels[i].order_count = (uint32_t)temp[i]->queue->count;
    }

    free(temp);
    return written;
}

uint64_t order_book_total_volume(const OrderBook* book, int side) {
    if (!book) return 0;
    Heap* heap = (side == SIDE_BUY) ? book->bids : book->asks;
    uint64_t sum = 0;
    for (size_t i = 0; i < heap->size; i++) {
        sum += heap->items[i]->queue->total_volume;
    }
    return sum;
}

size_t order_book_total_orders(const OrderBook* book, int side) {
    if (!book) return 0;
    Heap* heap = (side == SIDE_BUY) ? book->bids : book->asks;
    size_t count = 0;
    for (size_t i = 0; i < heap->size; i++) {
        count += heap->items[i]->queue->count;
    }
    return count;
}
