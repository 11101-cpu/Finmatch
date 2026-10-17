#ifndef FINMATCH_HEAP_H
#define FINMATCH_HEAP_H

#include "linked_list.h"
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct PriceLevel {
    int64_t price;         /* Price in paise */
    OrderQueue* queue;     /* FIFO queue of orders at this price level */
    size_t heap_index;     /* Current index in heap array for O(log P) removal */
} PriceLevel;

typedef enum {
    HEAP_MAX = 1,          /* Max-heap: Bids (highest price prioritized) */
    HEAP_MIN = 2           /* Min-heap: Asks (lowest price prioritized) */
} HeapType;

typedef struct Heap {
    PriceLevel** items;
    size_t size;
    size_t capacity;
    HeapType type;
} Heap;

/* Creates and allocates a price level */
PriceLevel* price_level_create(int64_t price);

/* Frees price level and its queue (orders themselves are not destroyed) */
void price_level_destroy(PriceLevel* level);

/* Frees price level, its queue, AND all contained orders */
void price_level_destroy_deep(PriceLevel* level);

/* Creates a priority queue heap */
Heap* heap_create(HeapType type, size_t initial_capacity);

/* Frees the heap structure and level array (does not free PriceLevels) */
void heap_destroy(Heap* heap);

/* Frees the heap structure, PriceLevels, and all contained orders */
void heap_destroy_deep(Heap* heap);

/* Pushes a price level into the heap. Returns 0 on success. */
int heap_push(Heap* heap, PriceLevel* level);

/* Peeks the top priority price level without removing it. */
PriceLevel* heap_peek(const Heap* heap);

/* Removes and returns the top priority price level. */
PriceLevel* heap_pop(Heap* heap);

/* Removes a price level at an arbitrary index in O(log N) time. */
int heap_remove_at(Heap* heap, size_t index);

/* Checks if heap is empty */
bool heap_is_empty(const Heap* heap);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_HEAP_H */
