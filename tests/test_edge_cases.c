#include "../core/include/matching_engine.h"
#include "../core/include/persistence.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

/* Scenarios 11, 12, 13: Order Cancellation */
static void test_order_cancellations(void) {
    printf("\n--- Test Suite: Order Cancellation (Scenarios 11, 12, 13) ---\n");
    MatchingEngine* engine = engine_create();

    /* Scenario 11: Cancellation of an OPEN order */
    OrderResult o_open;
    engine_place_order(engine, "Trader1", "SBIN", SIDE_BUY, 75000, 100, &o_open);
    TEST_ASSERT(o_open.status == ORDER_STATUS_OPEN, "Placed OPEN order");

    CancelResult cr1;
    int rc = engine_cancel_order(engine, o_open.order_id, &cr1);
    TEST_ASSERT(rc == FM_OK, "Cancelled OPEN order successfully");
    TEST_ASSERT(cr1.status == ORDER_STATUS_CANCELLED, "Status reported as CANCELLED");
    TEST_ASSERT(cr1.cancelled_qty == 100, "Cancelled quantity is 100");

    /* Verifying order is removed from book */
    OrderBook* book = engine_get_book(engine, "SBIN");
    TEST_ASSERT(order_book_total_volume(book, SIDE_BUY) == 0, "Book has 0 buy volume after cancellation");
    TEST_ASSERT(engine->active_orders->count == 0, "Active orders hash table is empty");

    /* Attempting to cancel already cancelled order (Scenario 13 variant) */
    CancelResult cr_again;
    rc = engine_cancel_order(engine, o_open.order_id, &cr_again);
    TEST_ASSERT(rc == FM_ERR_ORDER_NOT_FOUND, "Attempt to cancel already cancelled order returns error");

    /* Scenario 12: Cancellation of a PARTIALLY FILLED order */
    OrderResult o_part_sell, o_incoming_buy;
    engine_place_order(engine, "Trader2", "SBIN", SIDE_SELL, 76000, 100, &o_part_sell);
    engine_place_order(engine, "Trader3", "SBIN", SIDE_BUY, 76000, 40, &o_incoming_buy);

    /* o_part_sell now has 60 remaining */
    CancelResult cr_part;
    rc = engine_cancel_order(engine, o_part_sell.order_id, &cr_part);
    TEST_ASSERT(rc == FM_OK, "Cancelled PARTIALLY_FILLED order successfully");
    TEST_ASSERT(cr_part.cancelled_qty == 60, "Cancelled remaining quantity is 60");
    TEST_ASSERT(order_book_total_volume(book, SIDE_SELL) == 0, "Ask volume is now 0");

    /* Scenario 13: Attempted cancellation of an already FILLED order */
    CancelResult cr_filled;
    rc = engine_cancel_order(engine, o_incoming_buy.order_id, &cr_filled);
    TEST_ASSERT(rc == FM_ERR_ORDER_NOT_FOUND, "Attempt to cancel FILLED order rejected");

    engine_destroy(engine);
}

/* Scenarios 15 & 16: Multiple stock symbols & empty order book edge cases */
static void test_multi_symbols_and_empty_books(void) {
    printf("\n--- Test Suite: Multiple Symbols & Empty Books (Scenarios 15 & 16) ---\n");
    MatchingEngine* engine = engine_create();

    /* Scenario 16: Operations on completely empty books */
    MarketStats stats;
    int rc = engine_get_stats(engine, "NONEXISTENT", &stats);
    TEST_ASSERT(rc == FM_OK, "Getting stats on non-existent symbol succeeds safely");
    TEST_ASSERT(stats.best_bid_paise == 0 && stats.best_ask_paise == 0, "Empty book has 0 bids and 0 asks");
    TEST_ASSERT(stats.total_buy_volume == 0 && stats.total_sell_volume == 0, "Empty book has 0 volume");

    CancelResult cr_empty;
    rc = engine_cancel_order(engine, 99999, &cr_empty);
    TEST_ASSERT(rc == FM_ERR_ORDER_NOT_FOUND, "Cancellation on nonexistent order ID safely fails");

    /* Scenario 15: Multiple stock symbols must remain isolated */
    OrderResult r_rel, r_tcs, r_infy;
    engine_place_order(engine, "Alice", "RELIANCE", SIDE_BUY, 250000, 10, &r_rel);
    engine_place_order(engine, "Bob", "TCS", SIDE_SELL, 350000, 20, &r_tcs);
    engine_place_order(engine, "Charlie", "INFY", SIDE_BUY, 150000, 30, &r_infy);

    TEST_ASSERT(engine->book_count == 3, "Engine maintains 3 distinct symbol books");

    OrderBook* b_rel = engine_get_book(engine, "RELIANCE");
    OrderBook* b_tcs = engine_get_book(engine, "TCS");
    OrderBook* b_infy = engine_get_book(engine, "INFY");

    TEST_ASSERT(order_book_total_volume(b_rel, SIDE_BUY) == 10, "RELIANCE has 10 buy vol");
    TEST_ASSERT(order_book_total_volume(b_rel, SIDE_SELL) == 0, "RELIANCE has 0 sell vol");

    TEST_ASSERT(order_book_total_volume(b_tcs, SIDE_BUY) == 0, "TCS has 0 buy vol");
    TEST_ASSERT(order_book_total_volume(b_tcs, SIDE_SELL) == 20, "TCS has 20 sell vol");

    TEST_ASSERT(order_book_total_volume(b_infy, SIDE_BUY) == 30, "INFY has 30 buy vol");

    /* Matching in one symbol does NOT affect other symbols */
    OrderResult r_rel_sell;
    engine_place_order(engine, "Dave", "RELIANCE", SIDE_SELL, 250000, 10, &r_rel_sell);
    TEST_ASSERT(r_rel_sell.trades_generated == 1, "RELIANCE trade executed");
    TEST_ASSERT(order_book_total_volume(b_rel, SIDE_BUY) == 0, "RELIANCE buy vol depleted");
    TEST_ASSERT(order_book_total_volume(b_tcs, SIDE_SELL) == 20, "TCS sell vol remains untouched");
    TEST_ASSERT(order_book_total_volume(b_infy, SIDE_BUY) == 30, "INFY buy vol remains untouched");

    engine_destroy(engine);
}

/* CSV Persistence Round-Trip */
static void test_persistence_roundtrip(void) {
    printf("\n--- Test Suite: Persistence Round-Trip ---\n");
    MatchingEngine* engine1 = engine_create();

    OrderResult r1, r2, r3;
    engine_place_order(engine1, "PersistUser1", "HDFCBANK", SIDE_BUY, 160000, 50, &r1);
    engine_place_order(engine1, "PersistUser2", "HDFCBANK", SIDE_SELL, 165000, 80, &r2);
    /* Executed match */
    engine_place_order(engine1, "PersistUser3", "HDFCBANK", SIDE_BUY, 165000, 30, &r3);

    const char* orders_file = "data/test_orders.csv";
    const char* trades_file = "data/test_trades.csv";

    int exp_rc = persistence_export_orders(engine1, orders_file);
    TEST_ASSERT(exp_rc == FM_OK, "Exported orders to CSV");
    int exp_tr_rc = persistence_export_trades(engine1->trade_history, trades_file);
    TEST_ASSERT(exp_tr_rc == FM_OK, "Exported trades to CSV");

    /* Create fresh engine and import */
    MatchingEngine* engine2 = engine_create();
    int imp_tr_rc = persistence_import_trades(engine2->trade_history, trades_file);
    TEST_ASSERT(imp_tr_rc == FM_OK, "Imported trades into fresh engine");
    TEST_ASSERT(engine2->trade_history->count == 1, "Trade history restored with 1 trade");

    int imp_ord_rc = persistence_import_orders(engine2, orders_file);
    TEST_ASSERT(imp_ord_rc == FM_OK, "Imported active orders into fresh engine");

    OrderBook* book2 = engine_get_book(engine2, "HDFCBANK");
    TEST_ASSERT(book2 != NULL, "Restored HDFCBANK book exists");
    TEST_ASSERT(order_book_total_volume(book2, SIDE_BUY) == 50, "Restored 50 buy volume");
    TEST_ASSERT(order_book_total_volume(book2, SIDE_SELL) == 50, "Restored remaining 50 sell volume");

    engine_destroy(engine1);
    engine_destroy(engine2);
}

/* Deep Regression: Strict Cross-Symbol Isolation with Identical Prices */
static void test_deep_symbol_isolation_regression(void) {
    printf("\n--- Test Suite: Cross-Symbol Isolation Regression ---\n");
    MatchingEngine* engine = engine_create();

    /* Place BUY on AAPL at Rs 150.00 */
    OrderResult r1;
    int rc1 = engine_place_order(engine, "Trader1", "AAPL", SIDE_BUY, 15000, 100, &r1);
    TEST_ASSERT(rc1 == FM_OK, "AAPL BUY order placed");

    /* Place SELL on MSFT at Rs 150.00 (identical price, opposite side) */
    OrderResult r2;
    int rc2 = engine_place_order(engine, "Trader2", "MSFT", SIDE_SELL, 15000, 100, &r2);
    TEST_ASSERT(rc2 == FM_OK, "MSFT SELL order placed at identical price");

    /* Ensure NO match occurs between different symbols */
    TEST_ASSERT(r1.trades_generated == 0, "AAPL has 0 trades");
    TEST_ASSERT(r2.trades_generated == 0, "MSFT has 0 trades");
    TEST_ASSERT(engine->trade_history->count == 0, "Global trade history is empty");

    OrderBook* b_aapl = engine_get_book(engine, "AAPL");
    OrderBook* b_msft = engine_get_book(engine, "MSFT");

    TEST_ASSERT(order_book_total_volume(b_aapl, SIDE_BUY) == 100, "AAPL retains 100 buy volume");
    TEST_ASSERT(order_book_total_volume(b_aapl, SIDE_SELL) == 0, "AAPL has 0 sell volume");

    TEST_ASSERT(order_book_total_volume(b_msft, SIDE_BUY) == 0, "MSFT has 0 buy volume");
    TEST_ASSERT(order_book_total_volume(b_msft, SIDE_SELL) == 100, "MSFT retains 100 sell volume");

    engine_destroy(engine);
}

/* Deep Regression: Cancellation State Machine & Idempotency */
static void test_cancellation_state_machine_regression(void) {
    printf("\n--- Test Suite: Cancellation State Machine & Idempotency ---\n");
    MatchingEngine* engine = engine_create();

    OrderResult o1;
    engine_place_order(engine, "TraderA", "ITC", SIDE_BUY, 42000, 50, &o1);

    /* First cancel: Success */
    CancelResult c1;
    int rc_c1 = engine_cancel_order(engine, o1.order_id, &c1);
    TEST_ASSERT(rc_c1 == FM_OK, "First cancellation succeeds");
    TEST_ASSERT(c1.cancelled_qty == 50, "Released 50 shares");

    /* Second cancel on same ID: Must return error, NOT crash or double-free */
    CancelResult c2;
    int rc_c2 = engine_cancel_order(engine, o1.order_id, &c2);
    TEST_ASSERT(rc_c2 == FM_ERR_ORDER_NOT_FOUND, "Second cancellation on same order ID safely rejected");

    /* Cancel with invalid ID 0 */
    CancelResult c_zero;
    int rc_zero = engine_cancel_order(engine, 0, &c_zero);
    TEST_ASSERT(rc_zero == FM_ERR_ORDER_NOT_FOUND, "Cancellation with ID 0 safely rejected");

    engine_destroy(engine);
}

int main(void) {
    printf("=====================================================\n");
    printf("   Running FinMatch Test Suite: Edge Cases & Persist \n");
    printf("=====================================================\n");

    test_order_cancellations();
    test_multi_symbols_and_empty_books();
    test_persistence_roundtrip();
    test_deep_symbol_isolation_regression();
    test_cancellation_state_machine_regression();

    printf("\n=====================================================\n");
    printf("   Test Results: %d / %d assertions passed\n", g_tests_passed, g_tests_run);
    printf("=====================================================\n");

    return (g_tests_run == g_tests_passed) ? 0 : 1;
}
