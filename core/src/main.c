#define __USE_MINGW_ANSI_STDIO 1
#include "../include/finmatch_api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

static void print_banner(void) {
    printf("====================================================================\n");
    printf("      FinMatch: C-Based Stock Market Trading Simulator CLI          \n");
    printf("           Data Structures & Algorithms Mini-Project                \n");
    printf("====================================================================\n");
}

static void print_order_book(const char* symbol) {
    OrderBookSnapshot book;
    if (fm_get_order_book(symbol, &book) != 0) {
        printf("Error fetching order book for symbol %s\n", symbol);
        return;
    }

    printf("\n--- ORDER BOOK FOR %s ---\n", symbol);
    printf("%-10s | %-12s | %-8s  ||  %-8s | %-12s | %-10s\n",
           "BID QTY", "BID (INR)", "ORDERS", "ORDERS", "ASK (INR)", "ASK QTY");
    printf("--------------------------------------------------------------------\n");

    uint32_t max_rows = (book.bid_count > book.ask_count) ? book.bid_count : book.ask_count;
    if (max_rows == 0) {
        printf("                    [ Order Book is Empty ]                         \n");
    }

    for (uint32_t i = 0; i < max_rows; i++) {
        char bid_str[32] = "-", bid_vol_str[32] = "-", bid_ord_str[32] = "-";
        char ask_str[32] = "-", ask_vol_str[32] = "-", ask_ord_str[32] = "-";

        if (i < book.bid_count) {
            snprintf(bid_str, sizeof(bid_str), "%.2f", (double)book.bids[i].price_paise / 100.0);
            snprintf(bid_vol_str, sizeof(bid_vol_str), "%" PRIu64, book.bids[i].total_volume);
            snprintf(bid_ord_str, sizeof(bid_ord_str), "%u", book.bids[i].order_count);
        }

        if (i < book.ask_count) {
            snprintf(ask_str, sizeof(ask_str), "%.2f", (double)book.asks[i].price_paise / 100.0);
            snprintf(ask_vol_str, sizeof(ask_vol_str), "%" PRIu64, book.asks[i].total_volume);
            snprintf(ask_ord_str, sizeof(ask_ord_str), "%u", book.asks[i].order_count);
        }

        printf("%-10s | %-12s | %-8s  ||  %-8s | %-12s | %-10s\n",
               bid_vol_str, bid_str, bid_ord_str, ask_ord_str, ask_str, ask_vol_str);
    }
    printf("--------------------------------------------------------------------\n");
    printf("Total Bid Vol: %" PRIu64 " | Total Ask Vol: %" PRIu64 "\n\n",
           book.total_bid_volume, book.total_ask_volume);
}

static void print_trades(const char* symbol) {
    TradeSnapshot trades[64];
    uint32_t count = 0;
    if (fm_get_recent_trades(symbol, trades, 64, &count) != 0) {
        printf("Error fetching trades\n");
        return;
    }

    printf("\n--- RECENT TRADES (%u) ---\n", count);
    printf("%-8s | %-10s | %-8s | %-8s | %-12s | %-10s\n",
           "TRADE ID", "SYMBOL", "BUY ID", "SELL ID", "PRICE (INR)", "QTY");
    printf("--------------------------------------------------------------------\n");
    if (count == 0) {
        printf("                    [ No Trades Executed ]                          \n");
    }
    for (uint32_t i = 0; i < count; i++) {
        printf("%-8" PRIu64 " | %-10s | %-8" PRIu64 " | %-8" PRIu64 " | %-12.2f | %-10u\n",
               trades[i].trade_id,
               trades[i].symbol,
               trades[i].buy_order_id,
               trades[i].sell_order_id,
               (double)trades[i].price_paise / 100.0,
               trades[i].quantity);
    }
    printf("--------------------------------------------------------------------\n\n");
}

static void run_demo(void) {
    printf("\n=== Running Live Simulation Demo ===\n");
    fm_reset();

    printf("1. Placing Sell limit orders for RELIANCE:\n");
    ApiOrderResult r;
    fm_place_order("Alice", "RELIANCE", 2, 250000, 100, &r); /* Sell 100 @ 2500.00 */
    printf("   Order #%" PRIu64 ": SELL 100 @ 2500.00 (Status: %d)\n", r.order_id, r.status);

    fm_place_order("Bob", "RELIANCE", 2, 252000, 50, &r);   /* Sell 50 @ 2520.00 */
    printf("   Order #%" PRIu64 ": SELL 50 @ 2520.00 (Status: %d)\n", r.order_id, r.status);

    fm_place_order("Charlie", "RELIANCE", 2, 250000, 75, &r); /* Sell 75 @ 2500.00 (FIFO behind Alice) */
    printf("   Order #%" PRIu64 ": SELL 75 @ 2500.00 (Status: %d)\n", r.order_id, r.status);

    print_order_book("RELIANCE");

    printf("2. Placing Buy order for RELIANCE (David, BUY 150 @ 2510.00):\n");
    printf("   Matches Alice's 100 @ 2500.00, then Charlie's 50 @ 2500.00 (Charlie has 25 rem)!\n");
    fm_place_order("David", "RELIANCE", 1, 251000, 150, &r);
    printf("   Order #%" PRIu64 " result: filled=%u, rem=%u, trades=%u, status=%d\n",
           r.order_id, r.filled_qty, r.remaining_qty, r.trades_generated, r.status);

    print_order_book("RELIANCE");
    print_trades("RELIANCE");

    printf("3. Cancelling Charlie's remaining 25 shares (Order #3):\n");
    ApiCancelResult cr;
    fm_cancel_order(3, &cr);
    printf("   Cancellation result: status=%d, cancelled_qty=%u, err=%d\n",
           cr.status, cr.cancelled_qty, cr.error_code);

    print_order_book("RELIANCE");

    printf("4. Exporting records to data/demo_orders.csv and data/demo_trades.csv...\n");
    fm_export_csv("data/demo_orders.csv", "data/demo_trades.csv");
    printf("   Export complete!\n");
    printf("=== Demo Completed Successfully ===\n\n");
}

int main(int argc, char** argv) {
    if (fm_init() != 0) {
        fprintf(stderr, "Failed to initialize FinMatch engine\n");
        return 1;
    }

    if (argc > 1 && strcmp(argv[1], "--demo") == 0) {
        print_banner();
        run_demo();
        fm_shutdown();
        return 0;
    }

    print_banner();
    printf("Run with '--demo' to see automated simulation walk-through.\n");
    run_demo();

    fm_shutdown();
    return 0;
}
