import json
import time
import redis

from datetime import datetime, timezone

from app.schemas import AlertRule, AlertEvent, PortfolioMetricsUpdate


def check_threshold(value: float, operator: str, threshold: float) -> bool:
    if operator == "lt":
        return value < threshold
    elif operator == "lte":
        return value <= threshold
    elif operator == "gt":
        return value > threshold
    elif operator == "gte":
        return value >= threshold
    return False

def save_alert_rule(client: redis.Redis, rule: AlertRule) -> AlertRule:
    client.hset("alert_rules", rule.rule_id, rule.model_dump_json())
    return rule
def evaluate_portfolio_rules(
    client: redis.Redis,
    metrics: PortfolioMetricsUpdate
) -> list[AlertEvent]:
    rules_data = client.hgetall("alert_rules")
    fired_alerts = []
    for rule_id, rule_json in rules_data.items():

        rule = AlertRule(**json.loads(rule_json))

        if rule.portfolio_id != metrics.portfolio_id:
            continue
        current_val = getattr(metrics, rule.metric, 0.0)


        is_breached = check_threshold(
            current_val,
            rule.operator,
            rule.threshold_value
        )
        state_key = f"alert_state:{rule.rule_id}"
        existing_raw = client.get(state_key)
        now_sec = int(time.time())

        now_iso = datetime.now(timezone.utc).isoformat()

        if is_breached:
            if existing_raw:
                existing = json.loads(existing_raw)
                if (
                    existing["state"] in ["TRIGGERED", "ACKNOWLEDGED"]
                    and now_sec - existing.get("last_fired_sec", 0)
                    < rule.cooldown_seconds
                ):
                    continue


            alert = AlertEvent(
                event_type="alert_triggered",
                alert_id=f"ALT-{rule.rule_id}",
                state="TRIGGERED",
                rule_name=rule.rule_name,
                breach_value=current_val,
                threshold_value=rule.threshold_value,
                timestamp=now_iso
            )

            state_data = alert.model_dump()

            state_data["last_fired_sec"] = now_sec

            client.set(state_key, json.dumps(state_data))

            fired_alerts.append(alert)

            print(
                f"ALERT TRIGGERED: {rule.rule_name} | "
                f"Value: {current_val} vs Threshold: {rule.threshold_value}"
            )
        else:
            if existing_raw:
                existing = json.loads(existing_raw)
                if existing["state"] in ["TRIGGERED", "ACKNOWLEDGED"]:

                    alert = AlertEvent(
                        event_type="alert_resolved",
                        alert_id=f"ALT-{rule.rule_id}",
                        state="RESOLVED",
                        rule_name=rule.rule_name,
                        breach_value=current_val,
                        threshold_value=rule.threshold_value,
                        timestamp=now_iso
                    )
                    client.set(state_key, alert.model_dump_json())
                    fired_alerts.append(alert)
                    print(
                        f"ALERT RESOLVED: {rule.rule_name} | "
                        f"Recovered Value: {current_val}"
                    )

    return fired_alerts