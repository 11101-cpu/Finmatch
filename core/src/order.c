#include "../include/order.h"
#include "../include/matching_engine.h"
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

int order_validate(const char* trader_id, const char* symbol, int side, int64_t price, uint32_t qty) {
    if (!trader_id || strlen(trader_id) == 0 || strlen(trader_id) >= 32) {
        return FM_ERR_INVALID_ARGUMENT;
    }
    if (!symbol || strlen(symbol) == 0 || strlen(symbol) >= 16) {
        return FM_ERR_INVALID_ARGUMENT;
    }
    if (side != SIDE_BUY && side != SIDE_SELL) {
        return FM_ERR_INVALID_ARGUMENT;
    }
    if (price <= 0) {
        return FM_ERR_INVALID_ARGUMENT;
    }
    if (qty == 0) {
        return FM_ERR_INVALID_ARGUMENT;
    }

    /* Check for uppercase alphanumeric in symbol */
    for (size_t i = 0; symbol[i] != '\0'; i++) {
        if (!isalnum((unsigned char)symbol[i]) && symbol[i] != '_') {
            return FM_ERR_INVALID_ARGUMENT;
        }
    }

    /* Overflow check for total order turnover: price * qty <= INT64_MAX */
    if ((int64_t)qty > 0 && price > (INT64_MAX / (int64_t)qty)) {
        return FM_ERR_INVALID_ARGUMENT;
    }

    return FM_OK;
}

Order* order_create(uint64_t order_id, const char* trader_id, const char* symbol,
                    int side, int64_t price, uint32_t qty, uint64_t sequence, int64_t timestamp) {
    if (order_validate(trader_id, symbol, side, price, qty) != FM_OK) {
        return NULL;
    }

    Order* order = (Order*)malloc(sizeof(Order));
    if (!order) {
        return NULL;
    }

    order->order_id = order_id;
    strncpy(order->trader_id, trader_id, sizeof(order->trader_id) - 1);
    order->trader_id[sizeof(order->trader_id) - 1] = '\0';

    strncpy(order->symbol, symbol, sizeof(order->symbol) - 1);
    order->symbol[sizeof(order->symbol) - 1] = '\0';

    order->side = side;
    order->price = price;
    order->original_qty = qty;
    order->remaining_qty = qty;
    order->sequence = sequence;
    order->status = ORDER_STATUS_OPEN;
    order->timestamp = timestamp;

    return order;
}

void order_destroy(Order* order) {
    if (order) {
        free(order);
    }
}

const char* order_status_to_string(int status) {
    switch (status) {
        case ORDER_STATUS_OPEN: return "OPEN";
        case ORDER_STATUS_PARTIALLY_FILLED: return "PARTIALLY_FILLED";
        case ORDER_STATUS_FILLED: return "FILLED";
        case ORDER_STATUS_CANCELLED: return "CANCELLED";
        default: return "UNKNOWN";
    }
}

const char* order_side_to_string(int side) {
    switch (side) {
        case SIDE_BUY: return "BUY";
        case SIDE_SELL: return "SELL";
        default: return "UNKNOWN";
    }
}
