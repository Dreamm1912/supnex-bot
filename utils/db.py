"""SQLite persistence for economy, levels, warns and giveaways.

One connection reused module-wide (check_same_thread=False keeps each
command task able to query). Data dir created on first import.
"""
import os
import sqlite3
import time

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(_DATA_DIR, "supnex.db")

_CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
_CONN.row_factory = sqlite3.Row

START_BALANCE = 100
LEVEL_FORMULA = 100  # xp needed for level L = LEVEL_FORMULA * L ** 2


def _init() -> None:
    _CONN.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 100,
            xp INTEGER NOT NULL DEFAULT 0,
            last_daily INTEGER NOT NULL DEFAULT 0,
            last_work INTEGER NOT NULL DEFAULT 0,
            last_fish INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL DEFAULT 'No reason',
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS giveaway (
            message_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            prize TEXT NOT NULL,
            ends_at INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            ended INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS giveaway_entries (
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (message_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS ses (
            guild_id INTEGER PRIMARY KEY,
            kanal_id INTEGER
        );
        """
    )
    _CONN.commit()


_init()


def _ensure_user(user_id: int) -> None:
    _CONN.execute(
        "INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)",
        (user_id, START_BALANCE),
    )
    _CONN.commit()


# --- economy ---
def get_balance(user_id: int) -> int:
    _ensure_user(user_id)
    row = _CONN.execute(
        "SELECT balance FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row["balance"]


def set_balance(user_id: int, amount: int) -> None:
    _ensure_user(user_id)
    _CONN.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id)
    )
    _CONN.commit()


def add_money(user_id: int, delta: int) -> int:
    new = max(0, get_balance(user_id) + delta)
    set_balance(user_id, new)
    return new


def top_balances(limit: int = 10) -> list[sqlite3.Row]:
    return _CONN.execute(
        "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ?",
        (limit,),
    ).fetchall()


# --- leveling ---
def level_from_xp(xp: int) -> tuple[int, int, int]:
    level = int(xp ** 0.5 // 10) if xp else 0
    while LEVEL_FORMULA * (level + 1) ** 2 <= xp:
        level += 1
    current = xp - LEVEL_FORMULA * level * level
    needed = LEVEL_FORMULA * ((level + 1) ** 2 - level * level)
    return level, current, needed


def add_xp(user_id: int, amount: int) -> int:
    _ensure_user(user_id)
    _CONN.execute(
        "UPDATE users SET xp = xp + ? WHERE user_id = ?", (amount, user_id)
    )
    _CONN.commit()
    row = _CONN.execute(
        "SELECT xp FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row["xp"]


def get_xp(user_id: int) -> int:
    _ensure_user(user_id)
    row = _CONN.execute("SELECT xp FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return row["xp"]


def top_xp(limit: int = 10) -> list[sqlite3.Row]:
    return _CONN.execute(
        "SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT ?", (limit,)
    ).fetchall()


# --- warns ---
def add_warn(guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
    cur = _CONN.execute(
        "INSERT INTO warns (guild_id, user_id, moderator_id, reason, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (guild_id, user_id, moderator_id, reason, int(time.time())),
    )
    _CONN.commit()
    return cur.lastrowid


def get_warns(guild_id: int, user_id: int) -> list[sqlite3.Row]:
    return _CONN.execute(
        "SELECT * FROM warns WHERE guild_id = ? AND user_id = ?"
        " ORDER BY id DESC",
        (guild_id, user_id),
    ).fetchall()


def clear_warns(guild_id: int, user_id: int) -> int:
    cur = _CONN.execute(
        "DELETE FROM warns WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id),
    )
    _CONN.commit()
    return cur.rowcount


# --- giveaways ---
def create_giveaway(message_id, channel_id, prize, ends_at, owner_id) -> None:
    _CONN.execute(
        "INSERT OR REPLACE INTO giveaway"
        " (message_id, channel_id, prize, ends_at, owner_id, ended)"
        " VALUES (?, ?, ?, ?, ?, 0)",
        (message_id, channel_id, prize, ends_at, owner_id),
    )
    _CONN.commit()


def get_giveaway(message_id) -> sqlite3.Row | None:
    return _CONN.execute(
        "SELECT * FROM giveaway WHERE message_id = ? AND ended = 0",
        (message_id,),
    ).fetchone()


def get_active_giveaways() -> list[sqlite3.Row]:
    return _CONN.execute(
        "SELECT * FROM giveaway WHERE ended = 0 AND ends_at <= ?",
        (int(time.time()),),
    ).fetchall()


def mark_ended(message_id) -> None:
    _CONN.execute(
        "UPDATE giveaway SET ended = 1 WHERE message_id = ?", (message_id,)
    )
    _CONN.commit()


def add_entry(message_id, user_id) -> str:
    _CONN.execute(
        "INSERT OR IGNORE INTO giveaway_entries (message_id, user_id)"
        " VALUES (?, ?)",
        (message_id, user_id),
    )
    _CONN.commit()
    return "Entered"


def get_entries(message_id) -> list[sqlite3.Row]:
    return _CONN.execute(
        "SELECT user_id FROM giveaway_entries WHERE message_id = ?",
        (message_id,),
    ).fetchall()


def get_ses(guild_id: int) -> int | None:
    satir = _CONN.execute(
        "SELECT kanal_id FROM ses WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    return satir["kanal_id"] if satir else None


def set_ses(guild_id: int, kanal_id: int | None) -> None:
    _CONN.execute(
        "INSERT INTO ses (guild_id, kanal_id) VALUES (?, ?) "
        "ON CONFLICT(guild_id) DO UPDATE SET kanal_id = excluded.kanal_id",
        (guild_id, kanal_id),
    )
    _CONN.commit()