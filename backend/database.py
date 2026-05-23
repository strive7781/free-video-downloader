"""SQLite persistence for users, purchases, and webhook idempotency."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(__file__).resolve().parent / "data" / "app.db"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                is_vip INTEGER NOT NULL DEFAULT 0,
                stripe_customer_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stripe_checkout_session_id TEXT NOT NULL UNIQUE,
                stripe_payment_intent_id TEXT,
                amount_cny INTEGER,
                currency TEXT NOT NULL DEFAULT 'cny',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS processed_stripe_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                processed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS download_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_download_logs_user_day
                ON download_logs(user_id, created_at);
            """
        )


def row_to_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "email": row["email"],
        "is_vip": bool(row["is_vip"]),
        "stripe_customer_id": row["stripe_customer_id"],
        "created_at": row["created_at"],
    }


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
            (email.strip(),),
        ).fetchone()
        return row_to_user(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_user(row)


def get_user_password_hash(email: str) -> str | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE email = ? COLLATE NOCASE",
            (email.strip(),),
        ).fetchone()
        return row["password_hash"] if row else None


def create_user(email: str, password_hash: str) -> dict[str, Any]:
    now = _utc_now()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.strip().lower(), password_hash, now),
        )
        user_id = cur.lastrowid
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_user(row)  # type: ignore[return-value]


def set_user_vip(user_id: int, is_vip: bool = True) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET is_vip = ? WHERE id = ?",
            (1 if is_vip else 0, user_id),
        )


def set_stripe_customer_id(user_id: int, customer_id: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET stripe_customer_id = ? WHERE id = ?",
            (customer_id, user_id),
        )


def create_purchase(
    user_id: int,
    checkout_session_id: str,
    amount_cny: int | None = None,
    currency: str = "cny",
) -> dict[str, Any]:
    now = _utc_now()
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO purchases
                (user_id, stripe_checkout_session_id, amount_cny, currency, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (user_id, checkout_session_id, amount_cny, currency, now),
        )
        row = conn.execute(
            "SELECT * FROM purchases WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return dict(row)


def complete_purchase(
    checkout_session_id: str,
    payment_intent_id: str | None,
    amount_cny: int | None,
) -> dict[str, Any] | None:
    now = _utc_now()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE stripe_checkout_session_id = ?",
            (checkout_session_id,),
        ).fetchone()
        if row is None:
            return None
        if row["status"] == "completed":
            return dict(row)
        conn.execute(
            """
            UPDATE purchases
            SET status = 'completed',
                stripe_payment_intent_id = COALESCE(?, stripe_payment_intent_id),
                amount_cny = COALESCE(?, amount_cny),
                completed_at = ?
            WHERE stripe_checkout_session_id = ?
            """,
            (payment_intent_id, amount_cny, now, checkout_session_id),
        )
        conn.execute(
            "UPDATE users SET is_vip = 1 WHERE id = ?",
            (row["user_id"],),
        )
        updated = conn.execute(
            "SELECT * FROM purchases WHERE stripe_checkout_session_id = ?",
            (checkout_session_id,),
        ).fetchone()
        return dict(updated)


def get_purchase_by_payment_intent(payment_intent_id: str) -> dict[str, Any] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE stripe_payment_intent_id = ?",
            (payment_intent_id,),
        ).fetchone()
        return dict(row) if row else None


def refund_purchase(payment_intent_id: str) -> dict[str, Any] | None:
    """Mark purchase refunded and revoke VIP for that user."""
    now = _utc_now()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM purchases WHERE stripe_payment_intent_id = ?",
            (payment_intent_id,),
        ).fetchone()
        if row is None:
            return None
        if row["status"] == "refunded":
            return dict(row)
        conn.execute(
            """
            UPDATE purchases
            SET status = 'refunded', completed_at = COALESCE(completed_at, ?)
            WHERE stripe_payment_intent_id = ?
            """,
            (now, payment_intent_id),
        )
        user_id = row["user_id"]
        # Revoke VIP only if user has no other completed purchase
        other = conn.execute(
            """
            SELECT 1 FROM purchases
            WHERE user_id = ? AND status = 'completed' AND stripe_payment_intent_id != ?
            LIMIT 1
            """,
            (user_id, payment_intent_id),
        ).fetchone()
        if not other:
            conn.execute("UPDATE users SET is_vip = 0 WHERE id = ?", (user_id,))
        updated = conn.execute(
            "SELECT * FROM purchases WHERE stripe_payment_intent_id = ?",
            (payment_intent_id,),
        ).fetchone()
        return dict(updated)


def user_has_active_vip(user_id: int) -> bool:
    """VIP is valid only when there is at least one completed (non-refunded) purchase."""
    _sync_stripe_refunds_for_user(user_id)
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM purchases WHERE user_id = ? AND status = 'completed' LIMIT 1",
            (user_id,),
        ).fetchone()
        has_purchase = row is not None
        user_row = conn.execute("SELECT is_vip FROM users WHERE id = ?", (user_id,)).fetchone()
        if user_row is None:
            return False
        db_flag = bool(user_row["is_vip"])
        if db_flag != has_purchase:
            conn.execute(
                "UPDATE users SET is_vip = ? WHERE id = ?",
                (1 if has_purchase else 0, user_id),
            )
        return has_purchase


def _sync_stripe_refunds_for_user(user_id: int) -> None:
    """Best-effort: if Stripe shows refunded, mark local purchase refunded (no webhook needed)."""
    import os

    if not os.getenv("STRIPE_SECRET_KEY", "").strip():
        return
    try:
        import stripe

        stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT stripe_payment_intent_id FROM purchases
                WHERE user_id = ? AND status = 'completed' AND stripe_payment_intent_id IS NOT NULL
                """,
                (user_id,),
            ).fetchall()
        for row in rows:
            pi_id = row["stripe_payment_intent_id"]
            charges = stripe.Charge.list(payment_intent=pi_id, limit=1)
            if charges.data and getattr(charges.data[0], "refunded", False):
                refund_purchase(pi_id)
    except Exception:
        pass


def is_event_processed(event_id: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_stripe_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return row is not None


def mark_event_processed(event_id: str, event_type: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO processed_stripe_events (event_id, event_type, processed_at)
            VALUES (?, ?, ?)
            """,
            (event_id, event_type, _utc_now()),
        )


def count_downloads_today(user_id: int) -> int:
    """Count downloads since UTC midnight."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt FROM download_logs
            WHERE user_id = ? AND created_at >= ?
            """,
            (user_id, f"{today}T00:00:00+00:00"),
        ).fetchone()
        return int(row["cnt"]) if row else 0


def log_download(user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO download_logs (user_id, created_at) VALUES (?, ?)",
            (user_id, _utc_now()),
        )
