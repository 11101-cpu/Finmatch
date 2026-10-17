#ifndef FINMATCH_HASH_TABLE_H
#define FINMATCH_HASH_TABLE_H

#include "order.h"
#include "heap.h"
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct HashEntry {
    uint64_t order_id;
    Order* order;
    PriceLevel* price_level;
    OrderNode* node;
    struct HashEntry* next;
} HashEntry;

typedef struct HashTable {
    HashEntry** buckets;
    size_t num_buckets;
    size_t count;
} HashTable;

/* Creates a hash table with initial bucket count */
HashTable* hash_table_create(size_t initial_buckets);

/* Frees the hash table and its entries. Does not free referenced Orders or PriceLevels. */
void hash_table_destroy(HashTable* table);

/* Inserts an active order mapping into the hash table. Handles collision and resizing. */
int hash_table_insert(HashTable* table, uint64_t order_id, Order* order, PriceLevel* price_level, OrderNode* node);

/* Looks up an active order entry by order_id. Returns NULL if not found. */
HashEntry* hash_table_lookup(const HashTable* table, uint64_t order_id);

/* Removes an entry by order_id. Returns 0 on success, non-zero if not found. */
int hash_table_remove(HashTable* table, uint64_t order_id);

/* Clears all entries from the hash table without freeing the table itself. */
void hash_table_clear(HashTable* table);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_HASH_TABLE_H */
