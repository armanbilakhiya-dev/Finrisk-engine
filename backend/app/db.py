import os 
import psycopg2
from app.schemas import PortfolioMetricsUpdate

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", 5433)),
        user=os.getenv("POSTGRES_USER", "finrisk_user"),
        password=os.getenv("POSTGRES_PASSWORD", "finrisk_pass"),
        dbname=os.getenv("POSTGRES_DB", "finrisk_db")
    )

def init_db() -> None:

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics_history (
            id SERIAL PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            live_pnl DOUBLE PRECISION NOT NULL,
            var_1d DOUBLE PRECISION NOT NULL,
            total_delta DOUBLE PRECISION NOT NULL,
            recorded_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    conn.commit()

    cur.close()
    conn.close()


def save_metrics_snapshot(metrics: PortfolioMetricsUpdate) -> None:

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO metrics_history (portfolio_id, live_pnl, var_1d, total_delta)
        VALUES (%s, %s, %s, %s);
        """,
        (
            metrics.portfolio_id,
            metrics.live_pnl,
            metrics.var_1d,
            metrics.total_delta
        )
    )

    conn.commit()

    cur.close()
    conn.close()


def get_metrics_history(
    portfolio_id: str,
    limit: int = 50
) -> list[dict]:

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT portfolio_id, live_pnl, var_1d, total_delta, recorded_at
        FROM metrics_history
        WHERE portfolio_id = %s
        ORDER BY recorded_at DESC
        LIMIT %s;
        """,
        (portfolio_id, limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    history = []

    for r in rows:
        history.append({
            "portfolio_id": r[0],
            "live_pnl": r[1],
            "var_1d": r[2],
            "total_delta": r[3],
            "recorded_at": r[4].isoformat()
        })

    return history
