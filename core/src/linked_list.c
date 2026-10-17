#include "../include/linked_list.h"
#include <stdlib.h>

OrderQueue* order_queue_create(void) {
    OrderQueue* queue = (OrderQueue*)malloc(sizeof(OrderQueue));
    if (!queue) {
        return NULL;
    }
    queue->head = NULL;
    queue->tail = NULL;
    queue->count = 0;
    queue->total_volume = 0;
    return queue;
}

void order_queue_destroy(OrderQueue* queue) {
    if (!queue) return;
    OrderNode* curr = queue->head;
    while (curr) {
        OrderNode* next = curr->next;
        free(curr);
        curr = next;
    }
    free(queue);
}

void order_queue_destroy_deep(OrderQueue* queue) {
    if (!queue) return;
    OrderNode* curr = queue->head;
    while (curr) {
        OrderNode* next = curr->next;
        if (curr->order) {
            order_destroy(curr->order);
        }
        free(curr);
        curr = next;
    }
    free(queue);
}

OrderNode* order_queue_push_tail(OrderQueue* queue, Order* order) {
    if (!queue || !order) return NULL;

    OrderNode* node = (OrderNode*)malloc(sizeof(OrderNode));
    if (!node) return NULL;

    node->order = order;
    node->next = NULL;
    node->prev = queue->tail;

    if (queue->tail) {
        queue->tail->next = node;
        queue->tail = node;
    } else {
        queue->head = node;
        queue->tail = node;
    }

    queue->count++;
    queue->total_volume += order->remaining_qty;
    return node;
}

Order* order_queue_peek_head(const OrderQueue* queue) {
    if (!queue || !queue->head) return NULL;
    return queue->head->order;
}

Order* order_queue_pop_head(OrderQueue* queue) {
    if (!queue || !queue->head) return NULL;

    OrderNode* node = queue->head;
    Order* order = node->order;

    queue->head = node->next;
    if (queue->head) {
        queue->head->prev = NULL;
    } else {
        queue->tail = NULL;
    }

    queue->count--;
    if (queue->total_volume >= order->remaining_qty) {
        queue->total_volume -= order->remaining_qty;
    } else {
        queue->total_volume = 0;
    }

    free(node);
    return order;
}

int order_queue_remove_node(OrderQueue* queue, OrderNode* node) {
    if (!queue || !node) return -1;

    if (node->prev) {
        node->prev->next = node->next;
    } else {
        queue->head = node->next;
    }

    if (node->next) {
        node->next->prev = node->prev;
    } else {
        queue->tail = node->prev;
    }

    queue->count--;
    if (node->order && queue->total_volume >= node->order->remaining_qty) {
        queue->total_volume -= node->order->remaining_qty;
    } else {
        queue->total_volume = 0;
    }

    free(node);
    return 0;
}

bool order_queue_is_empty(const OrderQueue* queue) {
    return (queue == NULL || queue->head == NULL || queue->count == 0);
}
