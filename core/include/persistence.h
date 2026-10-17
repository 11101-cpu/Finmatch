#ifndef FINMATCH_PERSISTENCE_H
#define FINMATCH_PERSISTENCE_H

#include "matching_engine.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Exports trade history to CSV file */
int persistence_export_trades(const TradeHistory* history, const char* filepath);

/* Imports completed trade history from CSV file */
int persistence_import_trades(TradeHistory* history, const char* filepath);

/* Exports all currently active orders to CSV file */
int persistence_export_orders(const MatchingEngine* engine, const char* filepath);

/* Imports orders from CSV file, rebuilding heaps and hash index for active orders only */
int persistence_import_orders(MatchingEngine* engine, const char* filepath);

#ifdef __cplusplus
}
#endif

#endif /* FINMATCH_PERSISTENCE_H */
