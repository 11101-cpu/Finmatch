CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O2 -Iinclude -DFINMATCH_STATIC
SRCDIR = src
BINDIR = ..

CORE_SRCS = $(SRCDIR)/order.c \
            $(SRCDIR)/order_book.c \
            $(SRCDIR)/heap.c \
            $(SRCDIR)/linked_list.c \
            $(SRCDIR)/hash_table.c \
            $(SRCDIR)/matching_engine.c \
            $(SRCDIR)/trades.c \
            $(SRCDIR)/persistence.c \
            $(SRCDIR)/finmatch_api.c

all: $(BINDIR)/finmatch.dll $(BINDIR)/finmatch.exe

$(BINDIR)/finmatch.dll: $(CORE_SRCS)
	$(CC) -Wall -Wextra -std=c11 -O2 -Iinclude -shared -DFINMATCH_EXPORTS $^ -o $@ -Wl,--out-implib,$(BINDIR)/libfinmatch.a

$(BINDIR)/finmatch.exe: $(SRCDIR)/main.c $(CORE_SRCS)
	$(CC) $(CFLAGS) $^ -o $@

clean:
	@if exist $(BINDIR)\finmatch.exe del /f /q $(BINDIR)\finmatch.exe
	@if exist $(BINDIR)\finmatch.dll del /f /q $(BINDIR)\finmatch.dll
	@if exist $(BINDIR)\libfinmatch.a del /f /q $(BINDIR)\libfinmatch.a

.PHONY: all clean
