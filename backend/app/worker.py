
import time
import redis

from app.schemas import PriceTick, PositionMetric, PortfolioMetricsUpdate
from app.replay import get_redis_client
from app.alerts import evaluate_portfolio_rules
from app.db import init_db, save_metrics_snapshot

PORTFOLIO_POSITIONS = {
    "AAPL": {"qty": 100, "cost_basis": 180.0},
    "NVDA": {"qty": 50, "cost_basis": 430.0}
}

current_prices = {
    "AAPL": 180.0,
    "NVDA": 430.0
}


def process_tick(msg_id: str, tick_data: dict) -> PriceTick:

    tick = PriceTick(**tick_data)

    latency_ms = int(time.time() * 1000) - tick.sent_at_ms

    print(
        f"Message ID: {msg_id} | "
        f"Ticker: {tick.ticker} | "
        f"Price: {tick.price} | "
        f"Latency: {latency_ms} ms"
    )

    return tick


def calculate_and_cache_metrics(
    client: redis.Redis,
    tick: PriceTick,
    portfolio_id: str = "PTF-TECH-ALPHA"
) -> PortfolioMetricsUpdate:

    current_prices[tick.ticker] = tick.price

    positions_list = []
    total_pnl = 0.0
    total_exposure = 0.0

    for ticker, info in PORTFOLIO_POSITIONS.items():

        price = current_prices.get(ticker, info["cost_basis"])

        pos_pnl = round(
            (price - info["cost_basis"]) * info["qty"], 2
        )

        total_pnl += pos_pnl
        total_exposure += price * info["qty"]

        positions_list.append(
            PositionMetric(
                ticker=ticker,
                current_price=price,
                position_pnl=pos_pnl
            )
        )

    metrics = PortfolioMetricsUpdate(
        event_type="metrics_update",
        portfolio_id=portfolio_id,
        live_pnl=round(total_pnl, 2),
        var_1d=round(-0.02 * total_exposure, 2),
        total_delta=150.0,
        positions=positions_list
    )

    redis_key = f"portfolio:{portfolio_id}:metrics"

    client.set(redis_key, metrics.model_dump_json())

    print(
        f"Updated Cache [{redis_key}] -> "
        f"Live PnL: ${metrics.live_pnl} | "
        f"VaR: ${metrics.var_1d}"
    )

    return metrics


def run_worker(stream_name: str = "market_ticks") -> None:

    client = get_redis_client()
    last_id = "0-0"

    print(f"Worker listening on stream: {stream_name}...")

    try:
        while True:
            init_db()

            response = client.xread(
                streams={stream_name: last_id},
                count=10,
                block=5000
            )

            if not response:
                continue

            for stream, messages in response:

                for msg_id, tick_data in messages:

                    tick = process_tick(msg_id, tick_data)

                    metrics=calculate_and_cache_metrics(client, tick)
                    save_metrics_snapshot(metrics)
                    evaluate_portfolio_rules(client, metrics)
                    last_id = msg_id

    except KeyboardInterrupt:
        print("Worker stopped by user.")

    finally:
        client.close()


if __name__ == "__main__":
    run_worker()
