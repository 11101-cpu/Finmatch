"""
auth.py - Database-backed Authentication & Portfolio Persistence for FinMatch.
Provides secure password hashing (PBKDF2-HMAC-SHA256 with cryptographically random salts),
user isolation, session management, and SQLite persistence for simulated trading accounts.
"""

import os
import re
import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "finmatch_auth.db")

DEFAULT_STARTING_BALANCE = 1000000.0  # ₹10,00,000 (10 Lakhs) virtual cash


def get_db_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database with row factory enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _hash_password(password: str, salt_hex: Optional[str] = None) -> Tuple[str, str]:
    """Hashes a password with PBKDF2-HMAC-SHA256 and returns (salt_hex, hash_hex)."""
    if salt_hex is None:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)

    derived = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        iterations=100000
    )
    return salt_hex, derived.hex()


def init_db():
    """Initializes the database schema if tables do not already exist."""
    conn = get_db_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            cash_balance REAL NOT NULL DEFAULT 1000000.0,
            theme_preference TEXT DEFAULT 'light',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            avg_buy_price REAL NOT NULL DEFAULT 0.0,
            total_invested REAL NOT NULL DEFAULT 0.0,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, symbol)
        );

        CREATE TABLE IF NOT EXISTS user_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL,
            filled_qty INTEGER NOT NULL DEFAULT 0,
            remaining_qty INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_orders_user ON user_orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_holdings_user ON user_holdings(user_id);
        """)
        
        # Seed default demo account if no users exist
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM users")
        row = cur.fetchone()
        if row and row["cnt"] == 0:
            salt, pwd_hash = _hash_password("groww123")
            now_str = datetime.now().isoformat()
            cur.execute(
                """
                INSERT INTO users (email, full_name, password_hash, salt, cash_balance, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("demo@groww.in", "Aditya Sharma", pwd_hash, salt, DEFAULT_STARTING_BALANCE, now_str)
            )
            demo_user_id = cur.lastrowid
            # Seed initial holdings for demo user
            cur.execute(
                """
                INSERT INTO user_holdings (user_id, symbol, quantity, avg_buy_price, total_invested, updated_at)
                VALUES 
                (?, 'RELIANCE', 50, 2480.00, 124000.00, ?),
                (?, 'TCS', 25, 3810.00, 95250.00, ?),
                (?, 'HDFCBANK', 70, 1630.00, 114100.00, ?)
                """,
                (demo_user_id, now_str, demo_user_id, now_str, demo_user_id, now_str)
            )
            conn.commit()
    conn.close()


# Ensure DB schema exists on import
init_db()


def validate_email(email: str) -> bool:
    """Checks for standard email syntax."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def register_user(full_name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
    """Registers a new simulated user account."""
    full_name = full_name.strip()
    email = email.strip().lower()

    if len(full_name) < 2:
        return False, "Full name must be at least 2 characters long."
    if not validate_email(email):
        return False, "Please enter a valid email address (e.g. trader@example.com)."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if password != confirm_password:
        return False, "Passwords do not match. Please verify both entries."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone() is not None:
            return False, f"An account with email '{email}' already exists. Please log in instead."

        salt, pwd_hash = _hash_password(password)
        now_str = datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO users (email, full_name, password_hash, salt, cash_balance, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, full_name, pwd_hash, salt, DEFAULT_STARTING_BALANCE, now_str)
        )
        conn.commit()
        return True, "Registration successful! You may now log in to access your simulated portfolio."
    except Exception as e:
        return False, f"Database error during registration: {str(e)}"
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Validates user credentials and returns user profile dict if successful."""
    email = email.strip().lower()
    if not email or not password:
        return None, "Please provide both email and password."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            return None, "No account found with this email. Please check spelling or sign up."

        salt = row["salt"]
        stored_hash = row["password_hash"]
        _, test_hash = _hash_password(password, salt)

        if hmac_compare(stored_hash, test_hash):
            user_data = {
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "cash_balance": row["cash_balance"],
                "theme_preference": row["theme_preference"],
                "created_at": row["created_at"],
            }
            return user_data, "Login successful."
        else:
            return None, "Invalid password. Please verify your credentials."
    except Exception as e:
        return None, f"Authentication error: {str(e)}"
    finally:
        conn.close()


def hmac_compare(val1: str, val2: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return secrets.compare_digest(val1, val2)


def reset_password(email: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
    """Updates password for a user after email validation."""
    email = email.strip().lower()
    if not validate_email(email):
        return False, "Invalid email address format."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
    if new_password != confirm_password:
        return False, "Passwords do not match."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            return False, "Account with this email does not exist."

        salt, pwd_hash = _hash_password(new_password)
        cur.execute("UPDATE users SET password_hash = ?, salt = ? WHERE email = ?", (pwd_hash, salt, email))
        conn.commit()
        return True, "Password reset successfully. You can now log in with your new password."
    except Exception as e:
        return False, f"Failed to reset password: {str(e)}"
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user profile details by ID."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, full_name, cash_balance, theme_preference, created_at FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def get_user_portfolio(user_id: int) -> Dict[str, Any]:
    """Retrieves user's simulated cash balance and all active stock holdings."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT cash_balance FROM users WHERE id = ?", (user_id,))
        user_row = cur.fetchone()
        cash = user_row["cash_balance"] if user_row else 0.0

        cur.execute("SELECT symbol, quantity, avg_buy_price, total_invested, updated_at FROM user_holdings WHERE user_id = ? AND quantity > 0", (user_id,))
        holdings_rows = cur.fetchall()

        holdings = []
        total_invested = 0.0
        for r in holdings_rows:
            h = dict(r)
            holdings.append(h)
            total_invested += h["total_invested"]

        return {
            "cash_balance": cash,
            "holdings": holdings,
            "total_invested": total_invested,
        }
    finally:
        conn.close()


def record_user_order(user_id: int, order: Dict[str, Any]) -> bool:
    """Logs an order placed by the user."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO user_orders (user_id, order_id, symbol, side, price, quantity, status, filled_qty, remaining_qty, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                order.get("order_id", 0),
                order.get("symbol", "").upper(),
                order.get("side", "").upper(),
                float(order.get("price", 0.0)),
                int(order.get("original_qty", order.get("quantity", 0))),
                order.get("status", "OPEN"),
                int(order.get("filled_qty", 0)),
                int(order.get("remaining_qty", order.get("quantity", 0))),
                now_str
            )
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def update_user_order_status(order_id: int, status: str, filled_qty: int, remaining_qty: int) -> bool:
    """Updates order status in DB."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE user_orders
            SET status = ?, filled_qty = ?, remaining_qty = ?
            WHERE order_id = ?
            """,
            (status, filled_qty, remaining_qty, order_id)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_user_orders(user_id: int, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns order history for a specific user, optionally filtered by symbol."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if symbol and symbol != "ALL":
            cur.execute(
                """
                SELECT id, order_id, symbol, side, price, quantity, status, filled_qty, remaining_qty, created_at
                FROM user_orders
                WHERE user_id = ? AND symbol = ?
                ORDER BY id DESC
                """,
                (user_id, symbol.upper())
            )
        else:
            cur.execute(
                """
                SELECT id, order_id, symbol, side, price, quantity, status, filled_qty, remaining_qty, created_at
                FROM user_orders
                WHERE user_id = ?
                ORDER BY id DESC
                """,
                (user_id,)
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def process_trade_execution(user_id: int, symbol: str, side: str, price: float, quantity: int) -> bool:
    """
    Updates user's portfolio and cash balance upon trade execution.
    For BUY: deducts (price * quantity) from cash, adds quantity to holding, updates avg_buy_price.
    For SELL: credits (price * quantity) to cash, reduces holding quantity.
    """
    symbol = symbol.upper()
    trade_value = price * quantity
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Fetch current user cash
        cur.execute("SELECT cash_balance FROM users WHERE id = ?", (user_id,))
        user_row = cur.fetchone()
        if not user_row:
            return False
        current_cash = user_row["cash_balance"]

        # Fetch current holding for symbol
        cur.execute("SELECT * FROM user_holdings WHERE user_id = ? AND symbol = ?", (user_id, symbol))
        holding = cur.fetchone()
        now_str = datetime.now().isoformat()

        if side.upper() == "BUY":
            new_cash = max(0.0, current_cash - trade_value)
            if holding:
                old_qty = holding["quantity"]
                old_invested = holding["total_invested"]
                new_qty = old_qty + quantity
                new_invested = old_invested + trade_value
                new_avg = new_invested / new_qty if new_qty > 0 else 0.0
                cur.execute(
                    """
                    UPDATE user_holdings
                    SET quantity = ?, avg_buy_price = ?, total_invested = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_qty, new_avg, new_invested, now_str, holding["id"])
                )
            else:
                cur.execute(
                    """
                    INSERT INTO user_holdings (user_id, symbol, quantity, avg_buy_price, total_invested, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, symbol, quantity, price, trade_value, now_str)
                )
            cur.execute("UPDATE users SET cash_balance = ? WHERE id = ?", (new_cash, user_id))

        elif side.upper() == "SELL":
            new_cash = current_cash + trade_value
            if holding:
                old_qty = holding["quantity"]
                old_avg = holding["avg_buy_price"]
                new_qty = max(0, old_qty - quantity)
                new_invested = new_qty * old_avg
                cur.execute(
                    """
                    UPDATE user_holdings
                    SET quantity = ?, total_invested = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_qty, new_invested, now_str, holding["id"])
                )
            cur.execute("UPDATE users SET cash_balance = ? WHERE id = ?", (new_cash, user_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def add_simulated_funds(user_id: int, amount: float = 100000.0) -> Tuple[bool, str]:
    """Adds simulated practice funds to user's wallet."""
    if amount <= 0:
        return False, "Amount must be strictly positive."
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET cash_balance = cash_balance + ? WHERE id = ?", (amount, user_id))
        conn.commit()
        return True, f"Successfully deposited ₹{amount:,.2f} virtual funds into your account."
    except Exception as e:
        return False, f"Failed to deposit funds: {str(e)}"
    finally:
        conn.close()


def reset_user_account(user_id: int) -> Tuple[bool, str]:
    """Resets user portfolio back to ₹10,00,000 cash and clears all active holdings and orders."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET cash_balance = ? WHERE id = ?", (DEFAULT_STARTING_BALANCE, user_id))
        cur.execute("DELETE FROM user_holdings WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM user_orders WHERE user_id = ?", (user_id,))
        conn.commit()
        return True, f"Account reset successfully to ₹{DEFAULT_STARTING_BALANCE:,.2f} initial balance."
    except Exception as e:
        return False, f"Failed to reset account: {str(e)}"
    finally:
        conn.close()
