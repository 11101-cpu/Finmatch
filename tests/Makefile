CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2 -I../core/include
CORE_SRCS = ../core/src/order.c \
            ../core/src/order_book.c \
            ../core/src/heap.c \
            ../core/src/linked_list.c \
            ../core/src/hash_table.c \
            ../core/src/matching_engine.c \
            ../core/src/trades.c \
            ../core/src/persistence.c

TEST_TARGETS = test_orders.exe test_matching.exe test_edge_cases.exe

all: $(TEST_TARGETS)

test_orders.exe: test_orders.c $(CORE_SRCS)
	$(CC) $(CFLAGS) $^ -o $@

test_matching.exe: test_matching.c $(CORE_SRCS)
	$(CC) $(CFLAGS) $^ -o $@

test_edge_cases.exe: test_edge_cases.c $(CORE_SRCS)
	$(CC) $(CFLAGS) $^ -o $@

run: all
	@echo ========================================
	@echo Running test_orders...
	@./test_orders.exe
	@echo ========================================
	@echo Running test_matching...
	@./test_matching.exe
	@echo ========================================
	@echo Running test_edge_cases...
	@./test_edge_cases.exe
	@echo ========================================

clean:
	@if exist *.exe del /f /q *.exe

.PHONY: all run clean
