#ifndef FINMATCH_ORDER_H
#define FINMATCH_ORDER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    SIDE_BUY = 1,
    SIDE_SELL = 2
} Side;

typedef enum {
    ORDER_STATUS_UNKNOWN = 0,
    ORDER_STATUS_OPEN = 1,
    ORDER_STATUS_PARTIALLY_FILLED = 2,
    ORDER_STATUS_FILLED = 3,
    ORDER_STATUS_CANCELLED = 4
} OrderStatus;

typedef struct Order {
    uint64_t order_id;
    char trader_id[32];
    char symbol[16];
    int32_t side;           /* Side enum (SIDE_BUY or SIDE_SELL) */
    int64_t price;          /* Limit price in paise (1 INR = 100 paise) */
    uint32_t original_qty;  /* Initial ordered quantity */
    uint32_t remaining_qty; /* Remaining unfilled quantity */
    uint64_t sequence;      /* Global arrival sequence number for FIFO */
    int32_t status;         /* OrderStatus enum */
    int64_t timestamp;      /* Epoch timestamp in milliseconds */
} Order;

/* Validates incoming order fields. Returns 0 if valid, non-zero error code if invalid. */
int order_validate(const char* trader_id, const char* symbol, int side, int64_t price, uint32_t qty);

/* Creates a new dynamically allocated Order instance. */
Order* order_create(uint64_t order_id, const char* trader_id, const char* symbol, 
                     int side, int64_t price, uint32_t qty, uint64_t sequence, int64_t timestamp);

/* Frees an Order instance. */
void order_destroy(Order* order);

/* Helper string representation */
const char* order_status_to_string(int status);
const char* order_side_to_string(int side);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_ORDER_H */
