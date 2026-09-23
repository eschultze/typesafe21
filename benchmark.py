"""Aggregate persisted rounds into benchmark metrics for Jev vs Laya.

Single source of truth: the live game page fetches this for both the current
session and all-time, so the numbers never diverge between scopes.
"""

import math

import database as db

AI_NAMES = ["Jev (AI)", "Laya (AI)"]

# (label, predicate) over the true count at bet time.
TC_BUCKETS = [
    ("≤ 0", lambda tc: tc <= 0),
    ("+1…+2", lambda tc: 1 <= tc <= 2),
    ("+3…+4", lambda tc: 3 <= tc <= 4),
    ("≥ +5", lambda tc: tc >= 5),
]


def _player_rounds(session_id: int | None) -> list[dict]:
    """Collapse raw player-round rows into one record per (session, round, player)."""
    per_round: dict[tuple, dict[str, dict]] = {}
    sessions: set[int] = set()

    for row in db.get_benchmark_rows(session_id):
        sessions.add(row["session_id"])
        players = per_round.setdefault((row["session_id"], row["round_number"]), {})
        rec = players.setdefault(
            row["player_name"],
            {"bet": 0.0, "latency_ms": 0.0, "tokens": 0, "decisions": 0, "true_count": None},
        )
        rec["bet"] += row["bet"] or 0
        # Rows are ordered by id, so the last write wins for these fields.
        rec["balance_after"] = row["balance_after"]
        rec["result"] = row["result"]
        rec["decision"] = row["decision"] or ""
        rec["confidence"] = row["confidence"] or 0.0
        # Latency/tokens/decisions are player-round aggregates, so they are
        # repeated on each split-hand row; take the last, do not sum.
        rec["latency_ms"] = row["latency_ms"] or rec["latency_ms"]
        rec["tokens"] = row["tokens"] or rec["tokens"]
        rec["decisions"] = row["decisions"] or rec["decisions"]
        if row["true_count"] is not None:
            rec["true_count"] = row["true_count"]

    ordered = sorted(per_round.items())  # by (session_id, round_number)
    last_balance: dict[tuple, float] = {}
    records: list[dict] = []
    round_profits: dict[tuple, dict[str, float]] = {}

    for (sid, rnum), players in ordered:
        for name, rec in players.items():
            key = (sid, name)
            before = last_balance.get(key, 100)
            after = rec["balance_after"] if rec["balance_after"] is not None else before
            profit = after - before
            last_balance[key] = after
            record = {
                "session_id": sid,
                "round_number": rnum,
                "name": name,
                "bet": rec["bet"],
                "profit": profit,
                "result": "win" if profit > 0 else "lose" if profit < 0 else "push",
                "decision": rec["decision"],
                "confidence": rec["confidence"],
                "latency_ms": rec["latency_ms"],
                "tokens": rec["tokens"],
                "decisions": rec["decisions"],
                "true_count": rec["true_count"],
            }
            records.append(record)
            round_profits.setdefault((sid, rnum), {})[name] = profit

    return records, round_profits, len(sessions), len(ordered)


def _metrics(rows: list[dict]) -> dict:
    n = len(rows)
    wagered = sum(r["bet"] for r in rows)
    profit = sum(r["profit"] for r in rows)
    wins = sum(1 for r in rows if r["result"] == "win")
    losses = sum(1 for r in rows if r["result"] == "lose")
    pushes = n - wins - losses
    decisive = wins + losses
    win_rate = (wins / decisive * 100) if decisive else 0.0
    avg_bet = (wagered / n) if n else 0.0
    max_bet = max((r["bet"] for r in rows), default=0)

    conf_rows = [r for r in rows if r["confidence"] > 0]
    avg_confidence = (
        sum(r["confidence"] for r in conf_rows) / len(conf_rows) * 100 if conf_rows else 0.0
    )

    cal_rows = [r for r in rows if r["confidence"] > 0 and r["result"] != "push"]
    calib_gap = None
    brier = None
    if cal_rows:
        brier = sum(
            (r["confidence"] - (1 if r["result"] == "win" else 0)) ** 2 for r in cal_rows
        ) / len(cal_rows)
        mean_conf = sum(r["confidence"] for r in cal_rows) / len(cal_rows) * 100
        actual = sum(1 for r in cal_rows if r["result"] == "win") / len(cal_rows) * 100
        calib_gap = abs(mean_conf - actual)

    # Only use rows with decision counts: older rows predate per-decision
    # averaging, so their latency/tokens mean something different.
    latencies = sorted(r["latency_ms"] for r in rows if r["decisions"] > 0 and r["latency_ms"] > 0)
    p50_latency = latencies[int(len(latencies) * 0.5)] if latencies else 0.0
    p95_latency = latencies[min(int(len(latencies) * 0.95), len(latencies) - 1)] if latencies else 0.0

    # `tokens` is the per-decision average for a round and `decisions` its
    # count, so weight by decisions to get the exact global average.
    decisions_total = sum(r["decisions"] for r in rows)
    tokens_total = sum(r["tokens"] * r["decisions"] for r in rows)
    tokens_per_decision = (tokens_total / decisions_total) if decisions_total else 0.0
    decisions_per_round = (decisions_total / n) if n else 0.0

    peak = cum = max_drawdown = 0.0
    for r in rows:
        cum += r["profit"]
        peak = max(peak, cum)
        max_drawdown = max(max_drawdown, peak - cum)

    mean = profit / n if n else 0.0
    variance = sum((r["profit"] - mean) ** 2 for r in rows) / n if n else 0.0
    volatility = math.sqrt(variance)
    ret_vol = (mean / volatility) if volatility else 0.0
    edge = (profit / wagered * 100) if wagered else 0.0

    return {
        "n": n,
        "wagered": round(wagered, 2),
        "profit": round(profit, 2),
        "edge": round(edge, 2),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_rate": round(win_rate, 1),
        "avg_bet": round(avg_bet, 2),
        "max_bet": max_bet,
        "avg_confidence": round(avg_confidence, 1),
        "calib_gap": round(calib_gap, 1) if calib_gap is not None else None,
        "brier": round(brier, 4) if brier is not None else None,
        "p50_latency": round(p50_latency, 1),
        "p95_latency": round(p95_latency, 1),
        "tokens_per_decision": round(tokens_per_decision, 1),
        "tokens_total": int(tokens_total),
        "decisions_per_round": round(decisions_per_round, 2),
        "max_drawdown": round(max_drawdown, 2),
        "volatility": round(volatility, 2),
        "ret_vol": round(ret_vol, 3),
    }


def _head_to_head(round_profits: dict[tuple, dict[str, float]]) -> dict:
    diffs: list[float] = []
    jev_wins = laya_wins = ties = 0
    for key in sorted(round_profits):
        players = round_profits[key]
        j = players.get(AI_NAMES[0])
        l = players.get(AI_NAMES[1])
        if j is None or l is None:
            continue
        d = j - l
        diffs.append(d)
        if d > 0:
            jev_wins += 1
        elif d < 0:
            laya_wins += 1
        else:
            ties += 1

    n = len(diffs)
    mean = sum(diffs) / n if n else 0.0
    variance = sum((d - mean) ** 2 for d in diffs) / n if n else 0.0
    ci = 1.96 * math.sqrt(variance / n) if n else 0.0
    return {
        "n": n,
        "mean": round(mean, 2),
        "ci": round(ci, 2),
        "jev_wins": jev_wins,
        "laya_wins": laya_wins,
        "ties": ties,
    }


def build_benchmark(session_id: int | None = None) -> dict:
    records, round_profits, session_count, total_rounds = _player_rounds(session_id)

    players = {name: _metrics([r for r in records if r["name"] == name]) for name in AI_NAMES}

    by_true_count = []
    for label, test in TC_BUCKETS:
        entry = {"label": label}
        for name, key in ((AI_NAMES[0], "jev"), (AI_NAMES[1], "laya")):
            rows = [
                r
                for r in records
                if r["name"] == name
                and r["true_count"] is not None
                and test(r["true_count"])
            ]
            n = len(rows)
            entry[key] = {
                "n": n,
                "avg_bet": round(sum(r["bet"] for r in rows) / n, 1) if n else 0.0,
                "ev": round(sum(r["profit"] for r in rows) / n, 2) if n else 0.0,
            }
        by_true_count.append(entry)

    return {
        "scope": "session" if session_id is not None else "all_time",
        "session_id": session_id,
        "total_rounds": total_rounds,
        "sessions": session_count,
        "players": players,
        "head_to_head": _head_to_head(round_profits),
        "by_true_count": by_true_count,
    }
