import math
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models import AICallLog, Recording, Caregiver
from app.core.auth import get_current_caregiver

router = APIRouter(prefix="/admin", tags=["Admin Observability"])

@router.get("/ai-metrics")
def get_ai_observability_metrics(
    current_caregiver: Caregiver = Depends(get_current_caregiver),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated AI call telemetry: Average/P95 latency, total tokens, daily costs,
    unit cost per recording processed, and failure rate alerting.
    """
    logs = db.query(AICallLog).all()

    if not logs:
        return {
            "system_status": "healthy",
            "alert_triggered": False,
            "total_calls": 0,
            "total_cost_usd": 0.0,
            "unit_cost_per_recording_usd": 0.012,
            "metrics_by_call_type": {},
            "message": "No telemetry data recorded yet."
        }

    total_calls = len(logs)
    failed_calls = sum(1 for l in logs if l.status == "failed")
    overall_failure_rate = (failed_calls / total_calls) * 100.0

    call_types = set(l.call_type for l in logs)
    metrics_by_call_type = {}

    for c_type in call_types:
        type_logs = [l for l in logs if l.call_type == c_type]
        t_count = len(type_logs)
        t_failed = sum(1 for l in type_logs if l.status == "failed")
        
        latencies = sorted([l.latency_ms for l in type_logs])
        avg_lat = sum(latencies) / t_count if t_count else 0.0
        
        p95_idx = math.ceil(0.95 * t_count) - 1
        p95_lat = latencies[max(0, p95_idx)] if latencies else 0.0

        t_cost = sum(l.estimated_cost_usd for l in type_logs)

        metrics_by_call_type[c_type] = {
            "call_count": t_count,
            "failed_count": t_failed,
            "failure_rate_pct": round((t_failed / t_count) * 100.0, 1) if t_count else 0.0,
            "avg_latency_ms": round(avg_lat, 2),
            "p95_latency_ms": round(p95_lat, 2),
            "total_cost_usd": round(t_cost, 6)
        }

    total_cost_usd = sum(l.estimated_cost_usd for l in logs)

    # Unit cost per recording processed (ASR + Classification + Graph + Embedding)
    # Standard baseline formula: ASR ($0.007) + NIM Class ($0.002) + Graph ($0.002) + Emb ($0.001) = $0.012
    completed_recordings_count = db.query(Recording).filter(Recording.processing_status == "done").count()
    unit_cost_usd = round(total_cost_usd / max(1, completed_recordings_count), 4)

    # Alerting threshold check: failure rate > 10% or P95 latency > 120,000 ms (2 minutes PRD limit)
    max_p95 = max([m["p95_latency_ms"] for m in metrics_by_call_type.values()], default=0.0)
    alert_triggered = (overall_failure_rate > 10.0) or (max_p95 > 120000.0)

    alert_message = "Normal operation"
    if alert_triggered:
        if overall_failure_rate > 10.0:
            alert_message = f"CRITICAL ALERT: AI Pipeline failure rate ({overall_failure_rate:.1f}%) exceeds 10% threshold!"
        elif max_p95 > 120000.0:
            alert_message = f"WARNING ALERT: P95 AI latency ({max_p95:.0f} ms) exceeds 2-minute PRD target!"

    return {
        "system_status": "alerting" if alert_triggered else "healthy",
        "alert_triggered": alert_triggered,
        "alert_message": alert_message,
        "overall_failure_rate_pct": round(overall_failure_rate, 1),
        "total_ai_calls": total_calls,
        "total_cost_usd": round(total_cost_usd, 6),
        "unit_cost_per_recording_usd": unit_cost_usd,
        "unit_cost_formula_breakdown": {
            "asr_rate": "$0.0043 / min",
            "nim_llama_rate": "$0.0007 / 1k in, $0.0009 / 1k out",
            "vector_embedding_rate": "$0.0001 / 1k tokens"
        },
        "metrics_by_call_type": metrics_by_call_type
    }
