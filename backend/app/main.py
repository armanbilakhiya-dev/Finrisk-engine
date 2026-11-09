import json
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from app.schemas import PriceTick, PortfolioMetricsUpdate, AlertEvent ,AlertRule
from app.replay import get_redis_client
from datetime import datetime, timezone
from app.db import get_metrics_history
from app.alerts import save_alert_rule
import asyncio

app = FastAPI(
    title="Finrisk Engine APi",
    version="0.1.0"
)

@app.get("/health")
async def health_check():
    return{
        "status": "healthy",
        "service":"finrisk_backend"
    }

@app.get("/")
async def read_root():
    return {"message": "FinRisk Backend is Live", "status": "Ready for Week 1"}

@app.post("/rules", response_model=AlertRule)
async def create_alert_rule(rule: AlertRule):
    client = get_redis_client()

    saved_rule = save_alert_rule(client, rule)

    client.close()




    return rule

@app.get("/portfolios/{portfolio_id}/metrics", response_model=PortfolioMetricsUpdate)
async def get_portfolio_metrics(portfolio_id: str):
   
    client=get_redis_client()
    redis_key=f"portfolio:{portfolio_id}:metrics"
    cached_data = client.get(redis_key)
    client.close()

    if not cached_data:
        raise HTTPException(status_code=404, detail=f"Metrics not found for {portfolio_id}")
    return json.loads(cached_data)


@app.patch(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertEvent
)
def acknowledge_alert(alert_id: str):

    client = get_redis_client()

    rule_id = alert_id.replace("ALT-", "")

    state_key = f"alert_state:{rule_id}"

    existing_raw = client.get(state_key)

    if not existing_raw:
        client.close()
        raise HTTPException(
            status_code=404,
            detail=f"Active alert {alert_id} not found"
        )

    state_data = json.loads(existing_raw)

    state_data["event_type"] = "alert_acknowledged"
    state_data["state"] = "ACKNOWLEDGED"
    state_data["timestamp"] = datetime.now(timezone.utc).isoformat()

    client.set(state_key, json.dumps(state_data))

    client.close()

    return AlertEvent(**state_data)
@app.get("/portfolios/{portfolio_id}/history")
async def read_portfolio_history(portfolio_id: str, limit: int = 50):
    return get_metrics_history(portfolio_id, limit=limit)

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket, portfolio_id: str = "PTF-TECH-ALPHA"):
    await websocket.accept()

    client = get_redis_client()

    redis_key = f"portfolio:{portfolio_id}:metrics"
    try:
        while True:

            cached_data = client.get(redis_key)

            if cached_data:
                await websocket.send_json(json.loads(cached_data))

            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        print(f"WebSocket client disconnected for {portfolio_id}")

    finally:
        client.close()
