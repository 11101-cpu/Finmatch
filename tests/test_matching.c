#include "../core/include/matching_engine.h"
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

/* Scenarios 1 & 2: Buy/Sell orders with no compatible counter-orders */
static void test_no_counter_order(void) {
    printf("\n--- Test Suite: No Counter Orders (Scenarios 1 & 2) ---\n");
    MatchingEngine* engine = engine_create();

    /* 1. Buy order placed into empty book */
    OrderResult res1;
    int rc = engine_place_order(engine, "Alice", "INFY", SIDE_BUY, 150000, 100, &res1);
    TEST_ASSERT(rc == FM_OK, "Placed BUY order into empty book");
    TEST_ASSERT(res1.status == ORDER_STATUS_OPEN, "Status is OPEN");
    TEST_ASSERT(res1.filled_qty == 0, "Filled quantity is 0");
    TEST_ASSERT(res1.remaining_qty == 100, "Remaining quantity is 100");
    TEST_ASSERT(res1.trades_generated == 0, "No trades generated");

    OrderBook* book = engine_get_book(engine, "INFY");
    TEST_ASSERT(order_book_total_volume(book, SIDE_BUY) == 100, "Book has 100 buy volume");
    TEST_ASSERT(order_book_best_bid(book)->price == 150000, "Best bid is 1500.00");

    /* 2. Sell order placed with price higher than bid */
    OrderResult res2;
    rc = engine_place_order(engine, "Bob", "INFY", SIDE_SELL, 152000, 50, &res2);
    TEST_ASSERT(rc == FM_OK, "Placed SELL order above best bid");
    TEST_ASSERT(res2.status == ORDER_STATUS_OPEN, "Status is OPEN");
    TEST_ASSERT(res2.trades_generated == 0, "No match occurs (bid < ask)");
    TEST_ASSERT(order_book_total_volume(book, SIDE_SELL) == 50, "Book has 50 sell volume");

    engine_destroy(engine);
}

/* Scenarios 3, 4, 5: Exact match, limit price exceeds sell price, limit below best ask */
static void test_price_matching_rules(void) {
    printf("\n--- Test Suite: Price Matching Rules (Scenarios 3, 4, 5) ---\n");
    MatchingEngine* engine = engine_create();

    /* Place resting sell order: 50 @ 100.00 */
    OrderResult sell_res;
    engine_place_order(engine, "Seller", "TCS", SIDE_SELL, 10000, 50, &sell_res);

    /* Scenario 5: Buy order with limit price BELOW best ask (98.00 < 100.00) */
    OrderResult buy_below;
    engine_place_order(engine, "BuyerLow", "TCS", SIDE_BUY, 9800, 20, &buy_below);
    TEST_ASSERT(buy_below.trades_generated == 0, "Buy order below best ask does not match");
    TEST_ASSERT(buy_below.status == ORDER_STATUS_OPEN, "Buy order below best ask rests in book");

    /* Scenario 3: Exact price and exact quantity match: 50 @ 100.00 */
    /* Wait: first let's match the 50 resting sell with an incoming buy */
    /* Scenario 4: Buy order with price EXCEEDING resting sell price (105.00 >= 100.00) */
    OrderResult buy_above;
    engine_place_order(engine, "BuyerHigh", "TCS", SIDE_BUY, 10500, 50, &buy_above);
    TEST_ASSERT(buy_above.trades_generated == 1, "Buy order exceeding ask matches 1 trade");
    TEST_ASSERT(buy_above.status == ORDER_STATUS_FILLED, "Buy order is completely FILLED");
    TEST_ASSERT(buy_above.filled_qty == 50, "Filled quantity is 50");

    /* Check execution price: must be resting order's price (100.00 = 10000 paise) */
    const Trade* t = trade_history_get(engine->trade_history, 0);
    TEST_ASSERT(t != NULL, "Trade recorded");
    TEST_ASSERT(t->price == 10000, "Execution took place at resting order's limit price (10000 paise)");
    TEST_ASSERT(t->quantity == 50, "Trade quantity is 50");

    /* Order book should now have 0 asks and 1 bid (BuyerLow: 20 @ 9800) */
    OrderBook* book = engine_get_book(engine, "TCS");
    TEST_ASSERT(order_book_total_volume(book, SIDE_SELL) == 0, "Asks are fully depleted");
    TEST_ASSERT(order_book_total_volume(book, SIDE_BUY) == 20, "BuyerLow rests in bids");

    engine_destroy(engine);
}

/* Scenarios 6 & 7: Price priority for competing orders */
static void test_price_priority(void) {
    printf("\n--- Test Suite: Price Priority (Scenarios 6 & 7) ---\n");
    MatchingEngine* engine = engine_create();

    /* Scenario 6: Competing buy orders: Buyer1 bids 100, Buyer2 bids 102. Incoming sell @ 99 must match Buyer2 first! */
    OrderResult b1, b2, s1;
    engine_place_order(engine, "Buyer1", "WIPRO", SIDE_BUY, 10000, 50, &b1);
    engine_place_order(engine, "Buyer2", "WIPRO", SIDE_BUY, 10200, 50, &b2);

    /* Incoming sell 40 @ 99.00 */
    engine_place_order(engine, "Seller", "WIPRO", SIDE_SELL, 9900, 40, &s1);
    TEST_ASSERT(s1.trades_generated == 1, "Sell matched 1 trade");

    const Trade* t1 = trade_history_get(engine->trade_history, 0);
    TEST_ASSERT(t1 != NULL && t1->buy_order_id == b2.order_id, "Matched Buyer2 (higher price priority) instead of Buyer1");
    TEST_ASSERT(t1->price == 10200, "Executed at Buyer2's resting price (10200 paise)");

    /* Scenario 7: Competing sell orders: Seller1 asks 200, Seller2 asks 198. Incoming buy @ 205 must match Seller2 first! */
    OrderResult s_comp1, s_comp2, b_incoming;
    engine_place_order(engine, "Seller1", "HDFC", SIDE_SELL, 20000, 50, &s_comp1);
    engine_place_order(engine, "Seller2", "HDFC", SIDE_SELL, 19800, 50, &s_comp2);

    engine_place_order(engine, "Buyer", "HDFC", SIDE_BUY, 20500, 30, &b_incoming);
    TEST_ASSERT(b_incoming.trades_generated == 1, "Buy matched 1 trade");

    const Trade* t2 = trade_history_get(engine->trade_history, 1);
    TEST_ASSERT(t2 != NULL && t2->sell_order_id == s_comp2.order_id, "Matched Seller2 (lower ask price priority) first");
    TEST_ASSERT(t2->price == 19800, "Executed at Seller2's resting price (19800 paise)");

    engine_destroy(engine);
}

/* Scenarios 8, 9, 10, 19: FIFO priority at same price, partial fills, multi-order matches */
static void test_fifo_and_multi_match(void) {
    printf("\n--- Test Suite: FIFO & Multi-Order Matches (Scenarios 8, 9, 10, 19) ---\n");
    MatchingEngine* engine = engine_create();

    /* Scenario 8 & 19: Orders at the EXACT same price must execute in FIFO arrival order */
    OrderResult s1, s2, s3;
    engine_place_order(engine, "SellerEarly", "TATAMOTORS", SIDE_SELL, 50000, 30, &s1);
    engine_place_order(engine, "SellerMiddle", "TATAMOTORS", SIDE_SELL, 50000, 40, &s2);
    engine_place_order(engine, "SellerLate", "TATAMOTORS", SIDE_SELL, 50000, 50, &s3);

    /* Scenario 10: One incoming buy order for 60 shares matching multiple resting orders (s1 for 30, then s2 for 30) */
    OrderResult b_multi;
    engine_place_order(engine, "BigBuyer", "TATAMOTORS", SIDE_BUY, 50000, 60, &b_multi);

    TEST_ASSERT(b_multi.trades_generated == 2, "Incoming order matched 2 resting orders");
    TEST_ASSERT(b_multi.status == ORDER_STATUS_FILLED, "BigBuyer is FILLED");

    const Trade* t1 = trade_history_get(engine->trade_history, 0);
    const Trade* t2 = trade_history_get(engine->trade_history, 1);

    TEST_ASSERT(t1 && t1->sell_order_id == s1.order_id && t1->quantity == 30, "First matched SellerEarly (FIFO)");
    TEST_ASSERT(t2 && t2->sell_order_id == s2.order_id && t2->quantity == 30, "Second matched SellerMiddle for partial 30 (FIFO)");

    /* SellerMiddle should now have 10 remaining shares */
    Order middle_order;
    int rc = engine_get_order(engine, s2.order_id, &middle_order);
    TEST_ASSERT(rc == FM_OK, "SellerMiddle is still active in engine");
    TEST_ASSERT(middle_order.remaining_qty == 10, "SellerMiddle remaining_qty is 10");
    TEST_ASSERT(middle_order.status == ORDER_STATUS_PARTIALLY_FILLED, "SellerMiddle status is PARTIALLY_FILLED");

    /* Scenario 9: Partial fill of incoming order */
    /* Remaining in book: SellerMiddle (10 @ 50000), SellerLate (50 @ 50000) -> total ask vol = 60 */
    /* Incoming buy for 100 shares @ 50000 -> matches 60 shares, 40 shares remain as OPEN buy! */
    OrderResult b_partial;
    engine_place_order(engine, "GiantBuyer", "TATAMOTORS", SIDE_BUY, 50000, 100, &b_partial);
    TEST_ASSERT(b_partial.trades_generated == 2, "GiantBuyer consumed rest of s2 and all of s3");
    TEST_ASSERT(b_partial.filled_qty == 60, "GiantBuyer filled 60 shares");
    TEST_ASSERT(b_partial.remaining_qty == 40, "GiantBuyer has 40 shares remaining");
    TEST_ASSERT(b_partial.status == ORDER_STATUS_PARTIALLY_FILLED, "GiantBuyer status is PARTIALLY_FILLED");

    OrderBook* book = engine_get_book(engine, "TATAMOTORS");
    TEST_ASSERT(order_book_total_volume(book, SIDE_SELL) == 0, "All asks exhausted");
    TEST_ASSERT(order_book_total_volume(book, SIDE_BUY) == 40, "GiantBuyer resting with 40 shares on bid side");

    engine_destroy(engine);
}

/* Master Specification Scenario: BUY 10 @ ₹100, then SELL 6 @ ₹99 */
static void test_specification_scenario_buy10_sell6(void) {
    printf("\n--- Test Suite: Master Specification Scenario (BUY 10 @ Rs 100, SELL 6 @ Rs 99) ---\n");
    MatchingEngine* engine = engine_create();

    /* 1. Place BUY order for 10 shares at Rs 100 (10000 paise) */
    OrderResult buy_res;
    int rc1 = engine_place_order(engine, "Alice", "SPEC_TEST", SIDE_BUY, 10000, 10, &buy_res);
    TEST_ASSERT(rc1 == FM_OK, "BUY order for 10 shares @ Rs 100 accepted");
    TEST_ASSERT(buy_res.status == ORDER_STATUS_OPEN, "BUY order is OPEN in empty book");
    TEST_ASSERT(buy_res.filled_qty == 0, "BUY order initial filled quantity is 0");
    TEST_ASSERT(buy_res.remaining_qty == 10, "BUY order initial remaining quantity is 10");
    TEST_ASSERT(buy_res.trades_generated == 0, "No trades on initial BUY placement");

    /* 2. Place SELL order for 6 shares at Rs 99 (9900 paise) */
    OrderResult sell_res;
    int rc2 = engine_place_order(engine, "Bob", "SPEC_TEST", SIDE_SELL, 9900, 6, &sell_res);
    TEST_ASSERT(rc2 == FM_OK, "SELL order for 6 shares @ Rs 99 accepted");

    /* 3. Verify sell order execution status */
    TEST_ASSERT(sell_res.status == ORDER_STATUS_FILLED, "SELL order is marked FILLED");
    TEST_ASSERT(sell_res.filled_qty == 6, "SELL order filled quantity is 6");
    TEST_ASSERT(sell_res.remaining_qty == 0, "SELL order remaining quantity is 0");
    TEST_ASSERT(sell_res.trades_generated == 1, "SELL order generated exactly 1 trade");

    /* 4. Verify resting BUY order status in engine */
    Order buy_order_state;
    int rc_get = engine_get_order(engine, buy_res.order_id, &buy_order_state);
    TEST_ASSERT(rc_get == FM_OK, "Resting BUY order retrieved from active orders");
    TEST_ASSERT(buy_order_state.status == ORDER_STATUS_PARTIALLY_FILLED, "Resting BUY order status is PARTIALLY_FILLED");
    TEST_ASSERT(buy_order_state.original_qty == 10, "BUY order original quantity remains 10");
    TEST_ASSERT(buy_order_state.remaining_qty == 4, "BUY order retains exactly 4 shares (10 - 6)");

    /* 5. Verify trade execution record */
    TEST_ASSERT(engine->trade_history->count == 1, "Exactly one trade recorded in history");
    const Trade* trade = trade_history_get(engine->trade_history, 0);
    TEST_ASSERT(trade != NULL, "Trade record retrieved successfully");
    TEST_ASSERT(trade->buy_order_id == buy_res.order_id, "Trade buyer order ID matches Alice");
    TEST_ASSERT(trade->sell_order_id == sell_res.order_id, "Trade seller order ID matches Bob");
    TEST_ASSERT(trade->quantity == 6, "Trade executed quantity is 6 shares");
    TEST_ASSERT(trade->price == 10000, "Trade execution price is resting order price (Rs 100 / 10000 paise)");

    /* 6. Verify order book depth state */
    OrderBook* book = engine_get_book(engine, "SPEC_TEST");
    TEST_ASSERT(book != NULL, "Order book exists");
    TEST_ASSERT(order_book_total_volume(book, SIDE_BUY) == 4, "Order book has 4 shares remaining in Bids");
    TEST_ASSERT(order_book_total_volume(book, SIDE_SELL) == 0, "Order book has 0 shares in Asks");

    PriceLevel* best_bid = order_book_best_bid(book);
    TEST_ASSERT(best_bid != NULL && best_bid->price == 10000, "Best bid is Rs 100");
    TEST_ASSERT(best_bid->queue->total_volume == 4, "Best bid price level volume is 4 shares");

    PriceLevel* best_ask = order_book_best_ask(book);
    TEST_ASSERT(best_ask == NULL, "Best ask is NULL (no resting sells)");

    engine_destroy(engine);
}

int main(void) {
    printf("=====================================================\n");
    printf("   Running FinMatch Test Suite: Matching Engine      \n");
    printf("=====================================================\n");

    test_no_counter_order();
    test_price_matching_rules();
    test_price_priority();
    test_fifo_and_multi_match();
    test_specification_scenario_buy10_sell6();

    printf("\n=====================================================\n");
    printf("   Test Results: %d / %d assertions passed\n", g_tests_passed, g_tests_run);
    printf("=====================================================\n");

    return (g_tests_run == g_tests_passed) ? 0 : 1;
}
