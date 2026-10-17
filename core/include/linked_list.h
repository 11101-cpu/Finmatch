#ifndef FINMATCH_LINKED_LIST_H
#define FINMATCH_LINKED_LIST_H

#include "order.h"
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct OrderNode {
    Order* order;
    struct OrderNode* prev;
    struct OrderNode* next;
} OrderNode;

typedef struct OrderQueue {
    OrderNode* head;
    OrderNode* tail;
    size_t count;
    uint64_t total_volume; /* Sum of remaining quantities in this queue */
} OrderQueue;

/* Allocates and initializes a new OrderQueue */
OrderQueue* order_queue_create(void);

/* Frees the queue and its nodes. Does not free the underlying Order pointers. */
void order_queue_destroy(OrderQueue* queue);

/* Frees the queue, its nodes, AND the underlying Order pointers. */
void order_queue_destroy_deep(OrderQueue* queue);

/* Pushes an order to the tail of the queue (FIFO). Returns created node. */
OrderNode* order_queue_push_tail(OrderQueue* queue, Order* order);

/* Peeks the order at the head without removing it. */
Order* order_queue_peek_head(const OrderQueue* queue);

/* Removes and returns the order at the head of the queue. Node is freed. */
Order* order_queue_pop_head(OrderQueue* queue);

/* Removes a specific node in O(1) time. The node is freed. */
int order_queue_remove_node(OrderQueue* queue, OrderNode* node);

/* Checks if queue is empty */
bool order_queue_is_empty(const OrderQueue* queue);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_LINKED_LIST_H */
