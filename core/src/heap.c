#include "../include/heap.h"
#include "../include/matching_engine.h"
#include <stdlib.h>

PriceLevel* price_level_create(int64_t price) {
    PriceLevel* level = (PriceLevel*)malloc(sizeof(PriceLevel));
    if (!level) return NULL;

    level->price = price;
    level->queue = order_queue_create();
    if (!level->queue) {
        free(level);
        return NULL;
    }
    level->heap_index = (size_t)-1;
    return level;
}

void price_level_destroy(PriceLevel* level) {
    if (!level) return;
    if (level->queue) {
        order_queue_destroy(level->queue);
    }
    free(level);
}

void price_level_destroy_deep(PriceLevel* level) {
    if (!level) return;
    if (level->queue) {
        order_queue_destroy_deep(level->queue);
    }
    free(level);
}

Heap* heap_create(HeapType type, size_t initial_capacity) {
    if (initial_capacity == 0) initial_capacity = 16;

    Heap* heap = (Heap*)malloc(sizeof(Heap));
    if (!heap) return NULL;

    heap->items = (PriceLevel**)malloc(sizeof(PriceLevel*) * initial_capacity);
    if (!heap->items) {
        free(heap);
        return NULL;
    }

    heap->size = 0;
    heap->capacity = initial_capacity;
    heap->type = type;
    return heap;
}

void heap_destroy(Heap* heap) {
    if (!heap) return;
    if (heap->items) {
        free(heap->items);
    }
    free(heap);
}

void heap_destroy_deep(Heap* heap) {
    if (!heap) return;
    if (heap->items) {
        for (size_t i = 0; i < heap->size; i++) {
            price_level_destroy_deep(heap->items[i]);
        }
        free(heap->items);
    }
    free(heap);
}

static inline bool higher_priority(HeapType type, int64_t p1, int64_t p2) {
    if (type == HEAP_MAX) {
        return p1 > p2; /* Buy side: higher price is better */
    } else {
        return p1 < p2; /* Sell side: lower price is better */
    }
}

static void sift_up(Heap* heap, size_t index) {
    size_t idx = index;
    while (idx > 0) {
        size_t parent = (idx - 1) / 2;
        if (higher_priority(heap->type, heap->items[idx]->price, heap->items[parent]->price)) {
            PriceLevel* tmp = heap->items[idx];
            heap->items[idx] = heap->items[parent];
            heap->items[parent] = tmp;

            heap->items[idx]->heap_index = idx;
            heap->items[parent]->heap_index = parent;

            idx = parent;
        } else {
            break;
        }
    }
}

static void sift_down(Heap* heap, size_t index) {
    size_t idx = index;
    while (1) {
        size_t left = 2 * idx + 1;
        size_t right = 2 * idx + 2;
        size_t best = idx;

        if (left < heap->size && higher_priority(heap->type, heap->items[left]->price, heap->items[best]->price)) {
            best = left;
        }
        if (right < heap->size && higher_priority(heap->type, heap->items[right]->price, heap->items[best]->price)) {
            best = right;
        }

        if (best != idx) {
            PriceLevel* tmp = heap->items[idx];
            heap->items[idx] = heap->items[best];
            heap->items[best] = tmp;

            heap->items[idx]->heap_index = idx;
            heap->items[best]->heap_index = best;

            idx = best;
        } else {
            break;
        }
    }
}

int heap_push(Heap* heap, PriceLevel* level) {
    if (!heap || !level) return FM_ERR_INVALID_ARGUMENT;

    if (heap->size >= heap->capacity) {
        size_t new_cap = heap->capacity * 2;
        PriceLevel** new_items = (PriceLevel**)realloc(heap->items, sizeof(PriceLevel*) * new_cap);
        if (!new_items) return FM_ERR_OUT_OF_MEMORY;
        heap->items = new_items;
        heap->capacity = new_cap;
    }

    size_t idx = heap->size++;
    heap->items[idx] = level;
    level->heap_index = idx;
    sift_up(heap, idx);
    return FM_OK;
}

PriceLevel* heap_peek(const Heap* heap) {
    if (!heap || heap->size == 0) return NULL;
    return heap->items[0];
}

PriceLevel* heap_pop(Heap* heap) {
    if (!heap || heap->size == 0) return NULL;

    PriceLevel* top = heap->items[0];
    top->heap_index = (size_t)-1;

    heap->size--;
    if (heap->size > 0) {
        heap->items[0] = heap->items[heap->size];
        heap->items[0]->heap_index = 0;
        sift_down(heap, 0);
    }

    return top;
}

int heap_remove_at(Heap* heap, size_t index) {
    if (!heap || index >= heap->size) return FM_ERR_INVALID_ARGUMENT;

    PriceLevel* removed = heap->items[index];
    removed->heap_index = (size_t)-1;

    heap->size--;
    if (index < heap->size) {
        heap->items[index] = heap->items[heap->size];
        heap->items[index]->heap_index = index;

        sift_down(heap, index);
        sift_up(heap, index);
    }

    return FM_OK;
}

bool heap_is_empty(const Heap* heap) {
    return (heap == NULL || heap->size == 0);
}
