import csv
import time
import redis
from app.schemas import PriceTick

def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )

def publish_tick(
    client: redis.Redis,
    tick: PriceTick,
    stream_name: str = "market_ticks"
) -> str:

    tick_data = tick.model_dump()

    msg_id = client.xadd(stream_name, tick_data)

    return msg_id

def run_replay(csv_path: str, delay_seconds: float = 1.0) -> None:

    client = get_redis_client()

    with open(csv_path, mode="r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            tick = PriceTick(
                ticker=row["ticker"],
                price=float(row["price"]),
                timestamp=row["timestamp"],
                sent_at_ms=int(time.time() * 1000)
            )

            msg_id = publish_tick(client, tick)

            print(
                f"Published: {tick.ticker} | "
                f"Price: {tick.price} | "
                f"ID: {msg_id}"
            )

            time.sleep(delay_seconds)

    client.close()
if __name__=="__main__":
    run_replay("data/sample_ticks.csv", delay_seconds=1.0)

