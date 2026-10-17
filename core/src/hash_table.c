#include "../include/hash_table.h"
#include "../include/matching_engine.h"
#include <stdlib.h>

static inline size_t hash_uint64(uint64_t x) {
    x = (x ^ (x >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
    x = (x ^ (x >> 27)) * UINT64_C(0x94d049bb133111eb);
    x = x ^ (x >> 31);
    return (size_t)x;
}

HashTable* hash_table_create(size_t initial_buckets) {
    if (initial_buckets < 16) initial_buckets = 16;

    HashTable* table = (HashTable*)malloc(sizeof(HashTable));
    if (!table) return NULL;

    table->buckets = (HashEntry**)calloc(initial_buckets, sizeof(HashEntry*));
    if (!table->buckets) {
        free(table);
        return NULL;
    }

    table->num_buckets = initial_buckets;
    table->count = 0;
    return table;
}

void hash_table_destroy(HashTable* table) {
    if (!table) return;

    for (size_t i = 0; i < table->num_buckets; i++) {
        HashEntry* entry = table->buckets[i];
        while (entry) {
            HashEntry* next = entry->next;
            free(entry);
            entry = next;
        }
    }

    free(table->buckets);
    free(table);
}

void hash_table_clear(HashTable* table) {
    if (!table) return;

    for (size_t i = 0; i < table->num_buckets; i++) {
        HashEntry* entry = table->buckets[i];
        while (entry) {
            HashEntry* next = entry->next;
            free(entry);
            entry = next;
        }
        table->buckets[i] = NULL;
    }
    table->count = 0;
}

static int hash_table_resize(HashTable* table, size_t new_capacity) {
    HashEntry** new_buckets = (HashEntry**)calloc(new_capacity, sizeof(HashEntry*));
    if (!new_buckets) return FM_ERR_OUT_OF_MEMORY;

    for (size_t i = 0; i < table->num_buckets; i++) {
        HashEntry* entry = table->buckets[i];
        while (entry) {
            HashEntry* next = entry->next;
            size_t new_idx = hash_uint64(entry->order_id) % new_capacity;

            entry->next = new_buckets[new_idx];
            new_buckets[new_idx] = entry;

            entry = next;
        }
    }

    free(table->buckets);
    table->buckets = new_buckets;
    table->num_buckets = new_capacity;
    return FM_OK;
}

int hash_table_insert(HashTable* table, uint64_t order_id, Order* order, PriceLevel* price_level, OrderNode* node) {
    if (!table || !order) return FM_ERR_INVALID_ARGUMENT;

    /* Check load factor (> 0.75) */
    if (table->count >= (table->num_buckets * 3) / 4) {
        hash_table_resize(table, table->num_buckets * 2);
    }

    size_t idx = hash_uint64(order_id) % table->num_buckets;

    /* Check if already present */
    HashEntry* curr = table->buckets[idx];
    while (curr) {
        if (curr->order_id == order_id) {
            curr->order = order;
            curr->price_level = price_level;
            curr->node = node;
            return FM_OK;
        }
        curr = curr->next;
    }

    /* Allocate new entry */
    HashEntry* entry = (HashEntry*)malloc(sizeof(HashEntry));
    if (!entry) return FM_ERR_OUT_OF_MEMORY;

    entry->order_id = order_id;
    entry->order = order;
    entry->price_level = price_level;
    entry->node = node;
    entry->next = table->buckets[idx];
    table->buckets[idx] = entry;
    table->count++;

    return FM_OK;
}

HashEntry* hash_table_lookup(const HashTable* table, uint64_t order_id) {
    if (!table || table->num_buckets == 0) return NULL;

    size_t idx = hash_uint64(order_id) % table->num_buckets;
    HashEntry* curr = table->buckets[idx];
    while (curr) {
        if (curr->order_id == order_id) {
            return curr;
        }
        curr = curr->next;
    }
    return NULL;
}

int hash_table_remove(HashTable* table, uint64_t order_id) {
    if (!table || table->num_buckets == 0) return FM_ERR_ORDER_NOT_FOUND;

    size_t idx = hash_uint64(order_id) % table->num_buckets;
    HashEntry* curr = table->buckets[idx];
    HashEntry* prev = NULL;

    while (curr) {
        if (curr->order_id == order_id) {
            if (prev) {
                prev->next = curr->next;
            } else {
                table->buckets[idx] = curr->next;
            }
            free(curr);
            table->count--;
            return FM_OK;
        }
        prev = curr;
        curr = curr->next;
    }

    return FM_ERR_ORDER_NOT_FOUND;
}
