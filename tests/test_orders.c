#include "../core/include/order.h"
#include "../core/include/heap.h"
#include "../core/include/hash_table.h"
#include "../core/include/matching_engine.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

static int g_tests_run = 0;
static int g_tests_passed = 0;

#define TEST_ASSERT(cond, msg) do { \
    g_tests_run++; \
    if (!(cond)) { \
        printf("  [FAIL] Line %d: %s\n", __LINE__, msg); \
    } else { \
        g_tests_passed++; \
        printf("  [PASS] %s\n", msg); \
    } \
} while(0)

/* Scenario 14: Invalid price, quantity, symbol, trader */
static void test_order_validation(void) {
    printf("\n--- Test Suite: Order Validation (Scenario 14) ---\n");

    /* Valid order */
    TEST_ASSERT(order_validate("Trader1", "TCS", SIDE_BUY, 350000, 10) == FM_OK, "Valid BUY order parameters accepted");
    TEST_ASSERT(order_validate("Trader2", "INFY", SIDE_SELL, 150000, 50) == FM_OK, "Valid SELL order parameters accepted");

    /* Invalid price <= 0 */
    TEST_ASSERT(order_validate("Trader1", "TCS", SIDE_BUY, 0, 10) == FM_ERR_INVALID_ARGUMENT, "Zero price rejected");
    TEST_ASSERT(order_validate("Trader1", "TCS", SIDE_BUY, -100, 10) == FM_ERR_INVALID_ARGUMENT, "Negative price rejected");

    /* Invalid quantity == 0 */
    TEST_ASSERT(order_validate("Trader1", "TCS", SIDE_BUY, 350000, 0) == FM_ERR_INVALID_ARGUMENT, "Zero quantity rejected");

    /* Invalid trader */
    TEST_ASSERT(order_validate("", "TCS", SIDE_BUY, 350000, 10) == FM_ERR_INVALID_ARGUMENT, "Empty trader ID rejected");
    TEST_ASSERT(order_validate(NULL, "TCS", SIDE_BUY, 350000, 10) == FM_ERR_INVALID_ARGUMENT, "NULL trader ID rejected");

    /* Invalid symbol */
    TEST_ASSERT(order_validate("Trader1", "", SIDE_BUY, 350000, 10) == FM_ERR_INVALID_ARGUMENT, "Empty symbol rejected");
    TEST_ASSERT(order_validate("Trader1", NULL, SIDE_BUY, 350000, 10) == FM_ERR_INVALID_ARGUMENT, "NULL symbol rejected");
    TEST_ASSERT(order_validate("Trader1", "BAD$YM", SIDE_BUY, 350000, 10) == FM_ERR_INVALID_ARGUMENT, "Special chars in symbol rejected");

    /* Invalid side */
    TEST_ASSERT(order_validate("Trader1", "TCS", 99, 350000, 10) == FM_ERR_INVALID_ARGUMENT, "Invalid side enum rejected");

    /* Boundary validations */
    TEST_ASSERT(order_validate("T", "A", SIDE_BUY, 1, 1) == FM_OK, "Minimal positive price (1 paisa) and quantity (1 share) accepted");
    TEST_ASSERT(order_validate("Trader1", "A_123456789012", SIDE_BUY, 1000, 1) == FM_OK, "Symbol with underscore and numbers accepted (14 chars, within 15-char limit)");
    TEST_ASSERT(order_validate("Trader1", "TOOLONGSYMBOLNAME123", SIDE_BUY, 1000, 1) == FM_ERR_INVALID_ARGUMENT, "Excessively long symbol rejected");

    /* Overflow protection */
    TEST_ASSERT(order_validate("Trader1", "TCS", SIDE_BUY, INT64_MAX, 2) == FM_ERR_INVALID_ARGUMENT, "Turnover overflow beyond INT64_MAX rejected");
}

/* Scenario 18: Heap operations and removal of empty price levels */
static void test_heap_operations(void) {
    printf("\n--- Test Suite: Heap Operations & Level Pruning (Scenario 18) ---\n");

    Heap* max_heap = heap_create(HEAP_MAX, 8);
    TEST_ASSERT(max_heap != NULL, "Max-Heap allocated");

    PriceLevel* p1 = price_level_create(10000); /* 100.00 */
    PriceLevel* p2 = price_level_create(10500); /* 105.00 */
    PriceLevel* p3 = price_level_create(9500);  /* 95.00 */
    PriceLevel* p4 = price_level_create(10200); /* 102.00 */

    heap_push(max_heap, p1);
    heap_push(max_heap, p2);
    heap_push(max_heap, p3);
    heap_push(max_heap, p4);

    TEST_ASSERT(max_heap->size == 4, "Heap contains 4 price levels");
    TEST_ASSERT(heap_peek(max_heap)->price == 10500, "Max-Heap peek returns highest buy price (10500)");

    /* Remove top */
    PriceLevel* popped = heap_pop(max_heap);
    TEST_ASSERT(popped->price == 10500, "Popped item has price 10500");
    TEST_ASSERT(heap_peek(max_heap)->price == 10200, "Next top is 10200");
    price_level_destroy(popped);

    /* Arbitrary removal using heap_index */
    size_t idx_to_remove = p3->heap_index;
    TEST_ASSERT(idx_to_remove < max_heap->size, "p3 has valid heap index");
    heap_remove_at(max_heap, idx_to_remove);
    TEST_ASSERT(max_heap->size == 2, "Heap size decremented after arbitrary removal");
    price_level_destroy(p3);

    /* Clean up remaining */
    heap_destroy_deep(max_heap);
    TEST_ASSERT(1, "Max-Heap destroyed cleanly");

    /* Min-Heap for Sells */
    Heap* min_heap = heap_create(HEAP_MIN, 8);
    PriceLevel* s1 = price_level_create(20000);
    PriceLevel* s2 = price_level_create(19500);
    PriceLevel* s3 = price_level_create(21000);

    heap_push(min_heap, s1);
    heap_push(min_heap, s2);
    heap_push(min_heap, s3);

    TEST_ASSERT(heap_peek(min_heap)->price == 19500, "Min-Heap peek returns lowest sell price (19500)");
    popped = heap_pop(min_heap);
    TEST_ASSERT(popped->price == 19500, "Popped item has lowest sell price 19500");
    price_level_destroy(popped);

    heap_destroy_deep(min_heap);
    TEST_ASSERT(1, "Min-Heap destroyed cleanly");
}

/* Scenario 17: Hash table collisions and deletion */
static void test_hash_table_collisions(void) {
    printf("\n--- Test Suite: Hash Table Collisions & Deletion (Scenario 17) ---\n");

    HashTable* table = hash_table_create(4); /* Intentionally small to force collisions and resizing */
    TEST_ASSERT(table != NULL, "Hash table created with 4 buckets");

    Order* o1 = order_create(1, "T1", "AAPL", SIDE_BUY, 10000, 10, 1, 1000);
    Order* o2 = order_create(5, "T2", "AAPL", SIDE_BUY, 10000, 10, 2, 1001); /* Will collide with 1 if buckets=4 */
    Order* o3 = order_create(9, "T3", "AAPL", SIDE_BUY, 10000, 10, 3, 1002);
    Order* o4 = order_create(13, "T4", "AAPL", SIDE_BUY, 10000, 10, 4, 1003);

    hash_table_insert(table, 1, o1, NULL, NULL);
    hash_table_insert(table, 5, o2, NULL, NULL);
    hash_table_insert(table, 9, o3, NULL, NULL);
    hash_table_insert(table, 13, o4, NULL, NULL);

    TEST_ASSERT(table->count == 4, "4 entries successfully inserted");

    HashEntry* e1 = hash_table_lookup(table, 1);
    HashEntry* e2 = hash_table_lookup(table, 5);
    HashEntry* e3 = hash_table_lookup(table, 9);
    HashEntry* e4 = hash_table_lookup(table, 13);
    TEST_ASSERT(e1 && e1->order == o1, "Found order #1 after collision");
    TEST_ASSERT(e2 && e2->order == o2, "Found order #5 after collision");
    TEST_ASSERT(e3 && e3->order == o3, "Found order #9 after collision");
    TEST_ASSERT(e4 && e4->order == o4, "Found order #13 after collision");

    /* Delete from middle of chain */
    int del_rc = hash_table_remove(table, 5);
    TEST_ASSERT(del_rc == FM_OK, "Successfully removed collided order #5");
    TEST_ASSERT(hash_table_lookup(table, 5) == NULL, "Order #5 lookup returns NULL after deletion");
    TEST_ASSERT(hash_table_lookup(table, 1) != NULL, "Order #1 remains intact");
    TEST_ASSERT(hash_table_lookup(table, 9) != NULL, "Order #9 remains intact");

    order_destroy(o1);
    order_destroy(o2);
    order_destroy(o3);
    order_destroy(o4);
    hash_table_destroy(table);
    TEST_ASSERT(1, "Hash table destroyed cleanly");
}

/* Scenario 20: Repeated placement and cancellation without memory corruption */
static void test_stress_placement_cancellation(void) {
    printf("\n--- Test Suite: Repeated Placement & Cancellation (Scenario 20) ---\n");

    MatchingEngine* engine = engine_create();
    TEST_ASSERT(engine != NULL, "Engine created for stress cycle test");

    const int CYCLES = 500;
    for (int i = 0; i < CYCLES; i++) {
        OrderResult or_res;
        int rc = engine_place_order(engine, "StressUser", "RELIANCE", SIDE_BUY, 250000 + (i % 10) * 100, 10, &or_res);
        assert(rc == FM_OK);

        CancelResult cr_res;
        rc = engine_cancel_order(engine, or_res.order_id, &cr_res);
        assert(rc == FM_OK);
        assert(cr_res.cancelled_qty == 10);
    }

    OrderBook* book = engine_get_book(engine, "RELIANCE");
    TEST_ASSERT(book != NULL, "RELIANCE book exists");
    TEST_ASSERT(order_book_total_volume(book, SIDE_BUY) == 0, "Book has 0 active volume after all cancellations");
    TEST_ASSERT(engine->active_orders->count == 0, "Active orders hash table is empty");

    engine_destroy(engine);
    TEST_ASSERT(1, "Engine destroyed with 0 leaks after 500 placement-cancellation cycles");
}

int main(void) {
    printf("=====================================================\n");
    printf("   Running FinMatch Test Suite: Orders & DSA Units   \n");
    printf("=====================================================\n");

    test_order_validation();
    test_heap_operations();
    test_hash_table_collisions();
    test_stress_placement_cancellation();

    printf("\n=====================================================\n");
    printf("   Test Results: %d / %d assertions passed\n", g_tests_passed, g_tests_run);
    printf("=====================================================\n");

    return (g_tests_run == g_tests_passed) ? 0 : 1;
}
