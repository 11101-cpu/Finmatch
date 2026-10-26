"""
test_redesign_suite.py - Automated End-to-End Test Suite for FinMatch Redesign.
Verifies Authentication, Database Persistence, Market Data Feeds,
Chart Generation, Portfolio Accounting, and C Matching Engine Integration.
"""

import os
import sys
import tempfile
import unittest

# Ensure interface and tests directories are reachable
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_dir, "interface"))

import auth
import market_data
from engine import FinMatchEngine


class TestAuthAndPortfolio(unittest.TestCase):
    """Verifies SQLite authentication, password hashing, and user portfolio accounting."""

    def setUp(self):
        auth.init_db()

    def test_registration_validation(self):
        # Short name
        ok, msg = auth.register_user("A", "test@example.com", "secret123", "secret123")
        self.assertFalse(ok)

        # Invalid email
        ok, msg = auth.register_user("Alice", "invalid-email", "secret123", "secret123")
        self.assertFalse(ok)

        # Short password
        ok, msg = auth.register_user("Alice", "alice@example.com", "12345", "12345")
        self.assertFalse(ok)

        # Password mismatch
        ok, msg = auth.register_user("Alice", "alice@example.com", "secret123", "secret456")
        self.assertFalse(ok)

        # Valid registration
        unique_email = f"alice_{os.urandom(4).hex()}@example.com"
        ok, msg = auth.register_user("Alice Wonderland", unique_email, "securepwd", "securepwd")
        self.assertTrue(ok)

        # Duplicate registration
        ok, msg = auth.register_user("Alice 2", unique_email, "securepwd", "securepwd")
        self.assertFalse(ok)

    def test_authentication_and_password_reset(self):
        unique_email = f"bob_{os.urandom(4).hex()}@example.com"
        auth.register_user("Bob Trader", unique_email, "mypassword1", "mypassword1")

        # Wrong password
        user, msg = auth.authenticate_user(unique_email, "wrongpassword")
        self.assertIsNone(user)

        # Correct password
        user, msg = auth.authenticate_user(unique_email, "mypassword1")
        self.assertIsNotNone(user)
        self.assertEqual(user["full_name"], "Bob Trader")
        self.assertEqual(user["cash_balance"], auth.DEFAULT_STARTING_BALANCE)

        # Reset password
        ok, msg = auth.reset_password(unique_email, "newpassword2", "newpassword2")
        self.assertTrue(ok)

        # Auth with old password fails
        user_old, _ = auth.authenticate_user(unique_email, "mypassword1")
        self.assertIsNone(user_old)

        # Auth with new password succeeds
        user_new, _ = auth.authenticate_user(unique_email, "newpassword2")
        self.assertIsNotNone(user_new)

    def test_portfolio_buy_and_sell_accounting(self):
        unique_email = f"trader_{os.urandom(4).hex()}@example.com"
        auth.register_user("Charlie Capital", unique_email, "password123", "password123")
        user, _ = auth.authenticate_user(unique_email, "password123")
        uid = user["id"]

        # Initial portfolio
        port0 = auth.get_user_portfolio(uid)
        self.assertEqual(port0["cash_balance"], 1000000.0)
        self.assertEqual(len(port0["holdings"]), 0)

        # Buy 10 RELIANCE @ 2500.00 (Total = 25,000)
        ok = auth.process_trade_execution(uid, "RELIANCE", "BUY", 2500.00, 10)
        self.assertTrue(ok)

        port1 = auth.get_user_portfolio(uid)
        self.assertEqual(port1["cash_balance"], 975000.0)
        self.assertEqual(len(port1["holdings"]), 1)
        h = port1["holdings"][0]
        self.assertEqual(h["symbol"], "RELIANCE")
        self.assertEqual(h["quantity"], 10)
        self.assertEqual(h["avg_buy_price"], 2500.00)
        self.assertEqual(h["total_invested"], 25000.00)

        # Buy 10 more RELIANCE @ 2600.00 (Total = 26,000, new avg = 2550.00)
        auth.process_trade_execution(uid, "RELIANCE", "BUY", 2600.00, 10)
        port2 = auth.get_user_portfolio(uid)
        self.assertEqual(port2["cash_balance"], 949000.0)
        h2 = port2["holdings"][0]
        self.assertEqual(h2["quantity"], 20)
        self.assertEqual(h2["avg_buy_price"], 2550.00)
        self.assertEqual(h2["total_invested"], 51000.00)

        # Sell 5 RELIANCE @ 2700.00 (Credit = 13,500)
        auth.process_trade_execution(uid, "RELIANCE", "SELL", 2700.00, 5)
        port3 = auth.get_user_portfolio(uid)
        self.assertEqual(port3["cash_balance"], 962500.0)
        h3 = port3["holdings"][0]
        self.assertEqual(h3["quantity"], 15)

        # Faucet funds
        ok, _ = auth.add_simulated_funds(uid, 50000.0)
        self.assertTrue(ok)
        port4 = auth.get_user_portfolio(uid)
        self.assertEqual(port4["cash_balance"], 1012500.0)

        # Reset account
        ok, _ = auth.reset_user_account(uid)
        self.assertTrue(ok)
        port_reset = auth.get_user_portfolio(uid)
        self.assertEqual(port_reset["cash_balance"], 1000000.0)
        self.assertEqual(len(port_reset["holdings"]), 0)


class TestMarketDataAndCharts(unittest.TestCase):
    """Verifies simulated market feed, synthetic timeframes, and Groww chart building."""

    def setUp(self):
        self.feed = market_data.MarketDataFeed()

    def test_stock_catalog_and_timeframes(self):
        for sym in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]:
            stock = self.feed.get_stock(sym)
            self.assertEqual(stock["symbol"], sym)
            self.assertGreater(stock["current_price"], 0)
            self.assertIn("histories", stock)
            
            for tf in ["1D", "1W", "1M", "3M", "1Y"]:
                self.assertIn(tf, stock["histories"])
                df = stock["histories"][tf]
                self.assertGreater(len(df), 5)
                self.assertIn("timestamp", df.columns)
                self.assertIn("price", df.columns)
                self.assertIn("volume", df.columns)

    def test_tick_and_trade_updates(self):
        stock = self.feed.get_stock("INFY")
        initial_price = stock["current_price"]
        
        # Simulate tick
        self.feed.simulate_tick("INFY")
        updated_stock = self.feed.get_stock("INFY")
        self.assertGreater(updated_stock["current_price"], 0)
        self.assertIn(updated_stock["is_positive"], [True, False])

        # Simulate C Engine trade update
        self.feed.update_from_engine_trade("INFY", 1650.00, 200)
        self.assertEqual(updated_stock["current_price"], 1650.00)
        self.assertGreaterEqual(updated_stock["day_high"], 1650.00)

    def test_groww_chart_rendering(self):
        stock = self.feed.get_stock("TCS")
        df_1d = stock["histories"]["1D"]

        # Line chart
        fig_line = market_data.build_groww_chart(df_1d, "TCS", chart_type="line", is_positive=True)
        self.assertIsNotNone(fig_line)
        self.assertEqual(len(fig_line.data), 1)
        self.assertEqual(fig_line.data[0].line.color, market_data.GROWW_GREEN)

        # Candlestick chart
        fig_candle = market_data.build_groww_chart(df_1d, "TCS", chart_type="candlestick", is_positive=False)
        self.assertIsNotNone(fig_candle)
        self.assertEqual(len(fig_candle.data), 2)  # Candlestick + Volume bars


class TestEngineIntegration(unittest.TestCase):
    """Verifies that the Python ctypes wrapper and C11 engine work seamlessly."""

    def setUp(self):
        self.eng = FinMatchEngine()
        self.assertTrue(self.eng.is_available(), "DLL must be loaded")
        self.eng.reset_engine()

    def test_order_placement_matching_and_cancellation(self):
        # Place resting BUY
        r1 = self.eng.place_order("Buyer1", "RELIANCE", "BUY", 2500.0, 50)
        self.assertTrue(r1["success"])
        self.assertEqual(r1["status"], "OPEN")
        self.assertEqual(r1["remaining_qty"], 50)

        # Query order book
        book = self.eng.get_order_book("RELIANCE")
        self.assertEqual(len(book["bids"]), 1)
        self.assertEqual(book["bids"][0]["price"], 2500.0)
        self.assertEqual(book["bids"][0]["volume"], 50)

        # Place aggressive SELL that matches 20 shares
        r2 = self.eng.place_order("Seller1", "RELIANCE", "SELL", 2500.0, 20)
        self.assertTrue(r2["success"])
        self.assertEqual(r2["status"], "FILLED")
        self.assertEqual(r2["filled_qty"], 20)
        self.assertEqual(r2["trades_generated"], 1)

        # Check resting buyer order
        resting = self.eng.get_order(r1["order_id"])
        self.assertEqual(resting["status"], "PARTIALLY_FILLED")
        self.assertEqual(resting["remaining_qty"], 30)

        # Check trades
        trades = self.eng.get_recent_trades("RELIANCE")
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["quantity"], 20)
        self.assertEqual(trades[0]["price"], 2500.0)

        # Cancel remaining 30 shares
        c_res = self.eng.cancel_order(r1["order_id"])
        self.assertTrue(c_res["success"])
        self.assertEqual(c_res["cancelled_qty"], 30)

        # Confirm cancellation in book
        book_after = self.eng.get_order_book("RELIANCE")
        self.assertEqual(book_after["total_bid_vol"], 0)


if __name__ == "__main__":
    unittest.main()
