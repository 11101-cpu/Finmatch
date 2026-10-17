"""
FinMatch End-to-End Integration Check
Verifies C DLL loads correctly and all Python<->C API calls work.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'interface'))
from engine import FinMatchEngine

eng = FinMatchEngine()
assert eng.is_available(), "FAIL: DLL not loaded"
print("[PASS] C DLL loaded successfully")

eng.reset_engine()

# --- Scenario: BUY 10 @ Rs100, SELL 6 @ Rs99 ---
r_buy = eng.place_order("Alice", "TESTX", "BUY", 100.0, 10)
assert r_buy["status"] == "OPEN",           f"FAIL: expected OPEN, got {r_buy['status']}"
assert r_buy["remaining_qty"] == 10,        f"FAIL: expected 10 remaining, got {r_buy['remaining_qty']}"
assert r_buy["trades_generated"] == 0,      f"FAIL: expected 0 trades, got {r_buy['trades_generated']}"
print("[PASS] BUY 10 @ Rs100 rests OPEN with 10 shares, 0 trades")

r_sell = eng.place_order("Bob", "TESTX", "SELL", 99.0, 6)
assert r_sell["status"] == "FILLED",        f"FAIL: expected FILLED, got {r_sell['status']}"
assert r_sell["trades_generated"] == 1,     f"FAIL: expected 1 trade, got {r_sell['trades_generated']}"
print("[PASS] SELL 6 @ Rs99 is FILLED, generated 1 trade")

# Verify resting BUY state
resting = eng.get_order(r_buy["order_id"])
assert resting["status"] == "PARTIALLY_FILLED",  f"FAIL: expected PARTIALLY_FILLED, got {resting['status']}"
assert resting["remaining_qty"] == 4,             f"FAIL: expected 4 remaining, got {resting['remaining_qty']}"
print("[PASS] Resting BUY: PARTIALLY_FILLED with 4 shares remaining")

# Verify trade record
trades = eng.get_trade_history()
assert len(trades) == 1,           f"FAIL: expected 1 trade, got {len(trades)}"
t = trades[0]
assert t["executed_qty"] == 6,    f"FAIL: trade qty expected 6, got {t['executed_qty']}"
assert t["price"] == 100.0,       f"FAIL: execution price should be resting price 100.0, got {t['price']}"
print(f"[PASS] Trade record: {t['executed_qty']} shares @ Rs{t['price']:.2f} (resting price)")

# --- Symbol isolation ---
eng.reset_engine()
eng.place_order("Alice", "AAA", "BUY",  100.0, 50)
eng.place_order("Bob",   "BBB", "SELL", 100.0, 50)
isolation_trades = eng.get_trade_history()
assert len(isolation_trades) == 0, f"FAIL: cross-symbol trade must NOT occur, got {len(isolation_trades)}"
print("[PASS] Symbol isolation: AAA BUY vs BBB SELL did not match")

# --- Order cancellation ---
eng.reset_engine()
r = eng.place_order("Carol", "RELIANCE", "BUY", 2500.0, 20)
cancel_result = eng.cancel_order(r["order_id"])
assert cancel_result["success"],   "FAIL: cancellation returned failure"
status_after = eng.get_order(r["order_id"])
assert status_after["status"] == "CANCELLED", f"FAIL: expected CANCELLED, got {status_after['status']}"
print("[PASS] Order cancellation: OPEN -> CANCELLED successfully")

print()
print("=" * 50)
print("  ALL INTEGRATION ASSERTIONS PASSED")
print("=" * 50)
