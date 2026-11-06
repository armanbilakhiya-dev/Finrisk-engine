from typing import List , Literal
from pydantic import BaseModel, Field  

class PriceTick(BaseModel):
    ticker: str
    price: float=Field(gt=0)
    timestamp: str
    sent_at_ms: int

class PositionMetric(BaseModel):
    ticker: str
    current_price: float =Field(gt=0)
    position_pnl: float

class PortfolioMetricsUpdate(BaseModel):
    event_type: Literal["metrics_update"]
    portfolio_id: str
    live_pnl: float
    var_1d: float
    total_delta: float
    positions: List[PositionMetric]

class AlertEvent(BaseModel):
    event_type :Literal["alert_triggered", "alert_acknowledged", "alert_resolved"]
    alert_id: str
    state: Literal["TRIGGERED", "ACKNOWLEDGED", "RESOLVED"]
    rule_name: str
    breach_value: float
    threshold_value: float
    timestamp: str

class AlertRule(BaseModel):
    rule_id: str
    portfolio_id: str
    rule_name: str
    metric: Literal["var_1d","live_pnl","total_delta","exposure","drawdown"]
    operator: Literal["lt", "lte", "gt", "gte"]
    threshold_value: float
    cooldown_seconds: int = Field(default=60, ge=0)