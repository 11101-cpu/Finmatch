"""
engine.py - Python ctypes wrapper for FinMatch C matching engine shared library (finmatch.dll).
"""

import ctypes
import os
import platform
import sys
from typing import Dict, List, Optional, Any

# Structure definitions matching finmatch_api.h

FM_MAX_SYMBOL_LEN = 16
FM_MAX_TRADER_LEN = 32
FM_MAX_BOOK_LEVELS = 100

class ApiOrderResult(ctypes.Structure):
    _fields_ = [
        ("order_id", ctypes.c_uint64),
        ("status", ctypes.c_int32),
        ("original_qty", ctypes.c_uint32),
        ("filled_qty", ctypes.c_uint32),
        ("remaining_qty", ctypes.c_uint32),
        ("trades_generated", ctypes.c_uint32),
        ("error_code", ctypes.c_int32),
    ]

class ApiCancelResult(ctypes.Structure):
    _fields_ = [
        ("order_id", ctypes.c_uint64),
        ("status", ctypes.c_int32),
        ("cancelled_qty", ctypes.c_uint32),
        ("error_code", ctypes.c_int32),
    ]

class OrderSnapshot(ctypes.Structure):
    _fields_ = [
        ("order_id", ctypes.c_uint64),
        ("trader_id", ctypes.c_char * FM_MAX_TRADER_LEN),
        ("symbol", ctypes.c_char * FM_MAX_SYMBOL_LEN),
        ("side", ctypes.c_int32),
        ("price_paise", ctypes.c_int64),
        ("original_qty", ctypes.c_uint32),
        ("remaining_qty", ctypes.c_uint32),
        ("sequence", ctypes.c_uint64),
        ("status", ctypes.c_int32),
        ("timestamp", ctypes.c_int64),
    ]

class PriceLevelSnapshotApi(ctypes.Structure):
    _fields_ = [
        ("price_paise", ctypes.c_int64),
        ("total_volume", ctypes.c_uint64),
        ("order_count", ctypes.c_uint32),
    ]

class OrderBookSnapshot(ctypes.Structure):
    _fields_ = [
        ("symbol", ctypes.c_char * FM_MAX_SYMBOL_LEN),
        ("bids", PriceLevelSnapshotApi * FM_MAX_BOOK_LEVELS),
        ("bid_count", ctypes.c_uint32),
        ("asks", PriceLevelSnapshotApi * FM_MAX_BOOK_LEVELS),
        ("ask_count", ctypes.c_uint32),
        ("total_bid_volume", ctypes.c_uint64),
        ("total_ask_volume", ctypes.c_uint64),
    ]

class TradeSnapshot(ctypes.Structure):
    _fields_ = [
        ("trade_id", ctypes.c_uint64),
        ("symbol", ctypes.c_char * FM_MAX_SYMBOL_LEN),
        ("buy_order_id", ctypes.c_uint64),
        ("sell_order_id", ctypes.c_uint64),
        ("price_paise", ctypes.c_int64),
        ("quantity", ctypes.c_uint32),
        ("timestamp", ctypes.c_int64),
        ("sequence", ctypes.c_uint64),
    ]

class ApiMarketStats(ctypes.Structure):
    _fields_ = [
        ("symbol", ctypes.c_char * FM_MAX_SYMBOL_LEN),
        ("best_bid_paise", ctypes.c_int64),
        ("best_ask_paise", ctypes.c_int64),
        ("spread_paise", ctypes.c_int64),
        ("last_trade_price_paise", ctypes.c_int64),
        ("last_trade_qty", ctypes.c_uint32),
        ("total_buy_volume", ctypes.c_uint64),
        ("total_sell_volume", ctypes.c_uint64),
        ("total_orders", ctypes.c_uint64),
        ("total_trades", ctypes.c_uint64),
        ("total_shares_traded", ctypes.c_uint64),
        ("total_turnover_paise", ctypes.c_int64),
    ]


class FinMatchEngine:
    """Python interface to the FinMatch C matching engine library."""

    STATUS_NAMES = {
        0: "UNKNOWN",
        1: "OPEN",
        2: "PARTIALLY_FILLED",
        3: "FILLED",
        4: "CANCELLED"
    }

    SIDE_NAMES = {
        1: "BUY",
        2: "SELL"
    }

    def __init__(self, lib_path: Optional[str] = None):
        self.lib = None
        self.load_error = None
        self.dll_path = None
        self._orders_cache: Dict[int, Dict[str, Any]] = {}
        self._load_library(lib_path)

    def _find_library(self, custom_path: Optional[str] = None) -> Optional[str]:
        if custom_path and os.path.exists(custom_path):
            return os.path.abspath(custom_path)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            os.path.join(base_dir, "finmatch.dll"),
            os.path.join(base_dir, "core", "finmatch.dll"),
            os.path.join(base_dir, "libfinmatch.dll"),
            os.path.join(base_dir, "finmatch.so"),
            os.path.join(base_dir, "core", "finmatch.so"),
        ]

        for cand in candidates:
            if os.path.exists(cand):
                return cand
        return None

    def _load_library(self, custom_path: Optional[str] = None):
        cand = self._find_library(custom_path)
        if not cand:
            self.load_error = (
                "Compiled C engine shared library ('finmatch.dll') not found.\n"
                "Please compile the engine using GCC or mingw32-make:\n"
                "  gcc -O2 -shared core/src/*.c -Icore/include -o finmatch.dll"
            )
            return

        self.dll_path = cand
        try:
            self.lib = ctypes.CDLL(cand)
            self._setup_function_signatures()
            init_rc = self.lib.fm_init()
            if init_rc != 0:
                self.load_error = f"fm_init() returned non-zero code: {init_rc}"
        except OSError as e:
            bitness = 8 * ctypes.sizeof(ctypes.c_voidp)
            self.load_error = (
                f"Failed to load '{cand}': {e}.\n"
                f"Note: Current Python process is {bitness}-bit. "
                f"Ensure the DLL is compiled for the matching {bitness}-bit target architecture."
            )

    def _setup_function_signatures(self):
        # fm_init
        self.lib.fm_init.argtypes = []
        self.lib.fm_init.restype = ctypes.c_int

        # fm_shutdown
        self.lib.fm_shutdown.argtypes = []
        self.lib.fm_shutdown.restype = None

        # fm_reset
        self.lib.fm_reset.argtypes = []
        self.lib.fm_reset.restype = ctypes.c_int

        # fm_place_order
        self.lib.fm_place_order.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_int32,
            ctypes.c_int64,
            ctypes.c_uint32,
            ctypes.POINTER(ApiOrderResult),
        ]
        self.lib.fm_place_order.restype = ctypes.c_int

        # fm_cancel_order
        self.lib.fm_cancel_order.argtypes = [
            ctypes.c_uint64,
            ctypes.POINTER(ApiCancelResult),
        ]
        self.lib.fm_cancel_order.restype = ctypes.c_int

        # fm_get_order
        self.lib.fm_get_order.argtypes = [
            ctypes.c_uint64,
            ctypes.POINTER(OrderSnapshot),
        ]
        self.lib.fm_get_order.restype = ctypes.c_int

        # fm_get_order_book
        self.lib.fm_get_order_book.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(OrderBookSnapshot),
        ]
        self.lib.fm_get_order_book.restype = ctypes.c_int

        # fm_get_recent_trades
        self.lib.fm_get_recent_trades.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(TradeSnapshot),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
        ]
        self.lib.fm_get_recent_trades.restype = ctypes.c_int

        # fm_get_stats
        self.lib.fm_get_stats.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ApiMarketStats),
        ]
        self.lib.fm_get_stats.restype = ctypes.c_int

        # fm_export_csv
        self.lib.fm_export_csv.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.fm_export_csv.restype = ctypes.c_int

        # fm_import_csv
        self.lib.fm_import_csv.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.fm_import_csv.restype = ctypes.c_int

        # fm_get_error_message
        self.lib.fm_get_error_message.argtypes = [ctypes.c_int32]
        self.lib.fm_get_error_message.restype = ctypes.c_char_p

    def is_available(self) -> bool:
        return self.lib is not None

    def get_error_message(self, code: int) -> str:
        if not self.lib:
            return "Library not loaded"
        msg_ptr = self.lib.fm_get_error_message(code)
        if msg_ptr:
            return msg_ptr.decode("utf-8", errors="replace")
        return f"Error code {code}"

    def reset_engine(self) -> bool:
        if not self.lib:
            return False
        self._orders_cache.clear()
        return self.lib.fm_reset() == 0

    def place_order(self, trader_id: str, symbol: str, side: str, price_inr: float, quantity: int) -> Dict[str, Any]:
        """Places a limit order through the C matching engine."""
        if not self.lib:
            return {"success": False, "error": self.load_error or "Engine not loaded"}

        side_int = 1 if side.upper() == "BUY" else 2
        price_paise = int(round(price_inr * 100))

        if price_paise <= 0:
            return {"success": False, "error": "Price must be strictly positive"}
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be strictly positive"}

        trader_b = trader_id.encode("utf-8")
        symbol_b = symbol.upper().encode("utf-8")

        res = ApiOrderResult()
        rc = self.lib.fm_place_order(trader_b, symbol_b, side_int, price_paise, quantity, ctypes.byref(res))

        if rc != 0 or res.error_code != 0:
            err_code = res.error_code if res.error_code != 0 else rc
            return {
                "success": False,
                "error": self.get_error_message(err_code),
                "error_code": err_code,
            }

        order_dict = {
            "success": True,
            "order_id": res.order_id,
            "trader_id": trader_id,
            "symbol": symbol.upper(),
            "side": side.upper(),
            "price": price_inr,
            "status": self.STATUS_NAMES.get(res.status, "UNKNOWN"),
            "status_code": res.status,
            "original_qty": res.original_qty,
            "filled_qty": res.filled_qty,
            "remaining_qty": res.remaining_qty,
            "trades_generated": res.trades_generated,
        }
        self._orders_cache[res.order_id] = order_dict
        return order_dict

    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """Cancels an active order through the C matching engine."""
        if not self.lib:
            return {"success": False, "error": self.load_error or "Engine not loaded"}

        res = ApiCancelResult()
        rc = self.lib.fm_cancel_order(order_id, ctypes.byref(res))

        if rc != 0 or res.error_code != 0:
            err_code = res.error_code if res.error_code != 0 else rc
            return {
                "success": False,
                "error": self.get_error_message(err_code),
                "error_code": err_code,
            }

        cancel_dict = {
            "success": True,
            "order_id": res.order_id,
            "status": self.STATUS_NAMES.get(res.status, "CANCELLED"),
            "cancelled_qty": res.cancelled_qty,
        }
        if res.order_id in self._orders_cache:
            self._orders_cache[res.order_id]["status"] = "CANCELLED"
            self._orders_cache[res.order_id]["remaining_qty"] = 0
        return cancel_dict

    def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """Retrieves a depth snapshot of the order book for a given symbol."""
        if not self.lib:
            return {"symbol": symbol, "bids": [], "asks": [], "total_bid_vol": 0, "total_ask_vol": 0}

        book = OrderBookSnapshot()
        symbol_b = symbol.upper().encode("utf-8")
        rc = self.lib.fm_get_order_book(symbol_b, ctypes.byref(book))

        if rc != 0:
            return {"symbol": symbol, "bids": [], "asks": [], "total_bid_vol": 0, "total_ask_vol": 0}

        bids = []
        for i in range(book.bid_count):
            bids.append({
                "price": book.bids[i].price_paise / 100.0,
                "volume": book.bids[i].total_volume,
                "orders": book.bids[i].order_count,
            })

        asks = []
        for i in range(book.ask_count):
            asks.append({
                "price": book.asks[i].price_paise / 100.0,
                "volume": book.asks[i].total_volume,
                "orders": book.asks[i].order_count,
            })

        return {
            "symbol": symbol.upper(),
            "bids": bids,
            "asks": asks,
            "total_bid_vol": book.total_bid_volume,
            "total_ask_vol": book.total_ask_volume,
        }

    def get_recent_trades(self, symbol: Optional[str] = None, max_trades: int = 50) -> List[Dict[str, Any]]:
        """Retrieves completed trade history from C engine."""
        if not self.lib:
            return []

        trades_array = (TradeSnapshot * max_trades)()
        count = ctypes.c_uint32(0)
        symbol_b = symbol.upper().encode("utf-8") if symbol else None

        rc = self.lib.fm_get_recent_trades(symbol_b, trades_array, max_trades, ctypes.byref(count))
        if rc != 0:
            return []

        results = []
        for i in range(count.value):
            t = trades_array[i]
            results.append({
                "trade_id": t.trade_id,
                "symbol": t.symbol.decode("utf-8", errors="replace"),
                "buy_order_id": t.buy_order_id,
                "sell_order_id": t.sell_order_id,
                "price": t.price_paise / 100.0,
                "quantity": t.quantity,
                "executed_qty": t.quantity,
                "timestamp": t.timestamp,
                "sequence": t.sequence,
            })
        return results

    def get_trade_history(self, symbol: Optional[str] = None, max_trades: int = 100) -> List[Dict[str, Any]]:
        """Alias for get_recent_trades with backwards compatibility."""
        return self.get_recent_trades(symbol=symbol, max_trades=max_trades)

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves details of an active or recent order by ID."""
        if not self.lib:
            return None
        snap = OrderSnapshot()
        rc = self.lib.fm_get_order(order_id, ctypes.byref(snap))
        if rc == 0:
            order_dict = {
                "order_id": snap.order_id,
                "trader_id": snap.trader_id.decode("utf-8", errors="replace"),
                "symbol": snap.symbol.decode("utf-8", errors="replace"),
                "side": self.SIDE_NAMES.get(snap.side, "UNKNOWN"),
                "price": snap.price_paise / 100.0,
                "original_qty": snap.original_qty,
                "remaining_qty": snap.remaining_qty,
                "filled_qty": snap.original_qty - snap.remaining_qty,
                "status": self.STATUS_NAMES.get(snap.status, "UNKNOWN"),
                "sequence": snap.sequence,
                "timestamp": snap.timestamp,
            }
            self._orders_cache[order_id] = order_dict
            return order_dict
        return self._orders_cache.get(order_id)

    def get_market_stats(self, symbol: str) -> Dict[str, Any]:
        """Retrieves aggregated market statistics for a symbol."""
        if not self.lib:
            return {}

        stats = ApiMarketStats()
        symbol_b = symbol.upper().encode("utf-8")
        rc = self.lib.fm_get_stats(symbol_b, ctypes.byref(stats))
        if rc != 0:
            return {}

        best_bid = stats.best_bid_paise / 100.0 if stats.best_bid_paise > 0 else None
        best_ask = stats.best_ask_paise / 100.0 if stats.best_ask_paise > 0 else None
        spread = (stats.spread_paise / 100.0) if (best_bid and best_ask) else None

        return {
            "symbol": symbol.upper(),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "last_trade_price": (stats.last_trade_price_paise / 100.0) if stats.last_trade_price_paise > 0 else None,
            "last_trade_qty": stats.last_trade_qty,
            "total_buy_volume": stats.total_buy_volume,
            "total_sell_volume": stats.total_sell_volume,
            "total_orders": stats.total_orders,
            "total_trades": stats.total_trades,
            "total_shares_traded": stats.total_shares_traded,
            "total_turnover": stats.total_turnover_paise / 100.0,
        }

    def export_csv(self, orders_file: str, trades_file: str) -> bool:
        if not self.lib:
            return False
        rc = self.lib.fm_export_csv(orders_file.encode("utf-8"), trades_file.encode("utf-8"))
        return rc == 0

    def import_csv(self, orders_file: str, trades_file: str) -> bool:
        if not self.lib:
            return False
        rc = self.lib.fm_import_csv(orders_file.encode("utf-8"), trades_file.encode("utf-8"))
        return rc == 0
