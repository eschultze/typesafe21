import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "game_history.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_rounds INTEGER DEFAULT 0,
                is_complete INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER REFERENCES sessions(id),
                round_number INTEGER,
                dealer_final_value INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id INTEGER REFERENCES rounds(id),
                player_index INTEGER,
                player_name TEXT,
                result TEXT,
                bet INTEGER,
                confidence REAL,
                decision TEXT,
                balance_after INTEGER
            )
        """)

        conn.commit()


def create_session() -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (started_at) VALUES (?)", (datetime.now(),))
        session_id = cursor.lastrowid
        conn.commit()
        return session_id


def save_round(
    session_id: int,
    round_number: int,
    player_results: list[dict],
    dealer_final_value: int,
):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rounds (session_id, round_number, dealer_final_value) VALUES (?, ?, ?)",
            (session_id, round_number, dealer_final_value),
        )
        round_id = cursor.lastrowid

        for pr in player_results:
            cursor.execute(
                """
                INSERT INTO player_rounds
                (round_id, player_index, player_name, result, bet, confidence, decision, balance_after)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    round_id,
                    pr["player_index"],
                    pr["player_name"],
                    pr["result"],
                    pr.get("bet", 0),
                    pr.get("confidence", 0.0),
                    pr.get("decision", ""),
                    pr.get("balance_after", 0),
                ),
            )

        conn.commit()


def complete_session(session_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET is_complete = 1, total_rounds = (SELECT COUNT(*) FROM rounds WHERE session_id = ?) WHERE id = ?",
            (session_id, session_id),
        )
        conn.commit()


def get_last_incomplete_session() -> dict | None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE is_complete = 0 ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_round_count(session_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM rounds WHERE session_id = ?", (session_id,)
        )
        result = cursor.fetchone()
        return result["cnt"] if result else 0


def get_session_stats(session_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                pr.player_name,
                SUM(CASE WHEN pr.result = 'win' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pr.result = 'lose' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN pr.result = 'push' THEN 1 ELSE 0 END) as pushes,
                AVG(pr.confidence) as avg_confidence,
                COUNT(*) as total_rounds
            FROM player_rounds pr
            JOIN rounds r ON pr.round_id = r.id
            WHERE r.session_id = ?
            GROUP BY pr.player_name
            """,
            (session_id,),
        )
        rows = cursor.fetchall()

        players = {}
        for row in rows:
            name = row["player_name"]
            players[name] = {
                "wins": row["wins"],
                "losses": row["losses"],
                "pushes": row["pushes"],
                "avg_confidence": row["avg_confidence"],
                "total_rounds": row["total_rounds"],
            }

        cursor.execute(
            "SELECT COUNT(*) as total_rounds FROM rounds WHERE session_id = ?",
            (session_id,),
        )
        total = cursor.fetchone()
        total_rounds = total["total_rounds"] if total else 0

        return {"players": players, "total_rounds": total_rounds}


def get_all_sessions() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE is_complete = 1 ORDER BY id DESC LIMIT 10"
        )
        sessions = [dict(row) for row in cursor.fetchall()]
        return sessions


def get_top_single_turn_profits() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            WITH you_rounds AS (
                SELECT
                    r.session_id,
                    r.round_number,
                    pr.bet,
                    pr.result,
                    pr.balance_after,
                    LAG(pr.balance_after) OVER (
                        PARTITION BY r.session_id ORDER BY r.round_number
                    ) AS prev_balance
                FROM player_rounds pr
                JOIN rounds r ON pr.round_id = r.id
                JOIN sessions s ON s.id = r.session_id
                WHERE pr.player_name = 'You'
                    AND s.is_complete = 1
            )
            SELECT
                session_id,
                round_number,
                bet,
                result,
                balance_after,
                COALESCE(prev_balance, 100) AS prev_balance,
                balance_after - COALESCE(prev_balance, 100) AS profit
            FROM you_rounds
            WHERE prev_balance IS NOT NULL
            ORDER BY profit DESC
            LIMIT 5
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_top_session_profits() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            WITH you_last AS (
                SELECT
                    r.session_id,
                    pr.balance_after AS final_balance,
                    s.total_rounds,
                    ROW_NUMBER() OVER (
                        PARTITION BY r.session_id ORDER BY r.round_number DESC
                    ) AS rn
                FROM player_rounds pr
                JOIN rounds r ON pr.round_id = r.id
                JOIN sessions s ON s.id = r.session_id
                WHERE pr.player_name = 'You'
                    AND s.is_complete = 1
            )
            SELECT
                session_id,
                final_balance,
                final_balance - 100 AS profit,
                ROUND((final_balance - 100.0) / 100.0 * 100, 1) AS pct,
                total_rounds
            FROM you_last
            WHERE rn = 1
            ORDER BY profit DESC
            LIMIT 5
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_session_rounds(session_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM rounds WHERE session_id = ? ORDER BY round_number",
            (session_id,),
        )
        rounds = [dict(row) for row in cursor.fetchall()]

        for r in rounds:
            cursor.execute(
                """
                SELECT player_index, player_name, result, bet, confidence, decision, balance_after
                FROM player_rounds WHERE round_id = ?
                """,
                (r["id"],),
            )
            r["players"] = [dict(row) for row in cursor.fetchall()]

        return rounds
