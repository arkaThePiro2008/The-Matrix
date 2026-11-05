import sqlite3
import threading
import time
from typing import List, Dict, Any

DB_PATH = "matrix_town.db"
_lock = threading.Lock()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    with _lock:
        conn = get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER,
                speaker_id INTEGER,
                listener_id INTEGER,
                category TEXT,
                line TEXT,
                timestamp REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS world_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER,
                mode TEXT,
                timestamp REAL
            )
        """)
        conn.commit()
        conn.close()


def log_dialogue(tick: int, speaker_id: int, listener_id: int, category: str, line: str) -> None:
    with _lock:
        conn = get_conn()
        conn.execute(
            "INSERT INTO interactions (tick, speaker_id, listener_id, category, line, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (tick, int(speaker_id), int(listener_id), category, line, time.time()),
        )
        conn.commit()
        conn.close()


def log_mode_change(tick: int, mode: str) -> None:
    with _lock:
        conn = get_conn()
        conn.execute(
            "INSERT INTO world_events (tick, mode, timestamp) VALUES (?, ?, ?)",
            (tick, mode, time.time()),
        )
        conn.commit()
        conn.close()


def get_recent_dialogues(limit: int = 6) -> List[Dict[str, Any]]:
    with _lock:
        conn = get_conn()
        rows = conn.execute(
            "SELECT tick, speaker_id, listener_id, category, line FROM interactions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]