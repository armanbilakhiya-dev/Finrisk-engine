from fastapi import FastAPI
from app.schemas import PriceTick, PortfolioMetricsUpdate, AlertEvent ,AlertRule


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
    return rule

@app.get("/portfolios/{portfolio_id}/metrics", response_model=PortfolioMetricsUpdate)
async def get_portfolio_metrics(portfolio_id: str):
   
    return {
        "event_type": "metrics_update",
        "portfolio_id": portfolio_id,
        "live_pnl": 2500.0,
        "var_1d": -10000.0,
        "total_delta": 150.0,
        "positions": [
            {
                "ticker": "AAPL",
                "current_price": 250.0,
                "position_pnl": 1500.0
            },
            {
                "ticker": "MSFT",
                "current_price": 500.0,
                "position_pnl": 1000.0
            }
        ]
    }
@app.patch(
    "/alerts/{alert_id}/acknowledge",
    response_model=AlertEvent
)
async def acknowledge_alert(alert_id: str):
    return {
        "event_type": "alert_acknowledged",
        "alert_id": alert_id,
        "state": "ACKNOWLEDGED",
        "rule_name": "MAX_1D_VAR_EXCEEDED",
        "breach_value": -12000.0,
        "threshold_value": -10000.0,
        "timestamp": "2026-10-20T10:00:00Z"
    }