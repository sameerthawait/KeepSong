import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from app.db import SessionLocal
from app.models import Caregiver, Patient, Recording, AICallLog, AuditLog
from app.core.security import get_password_hash, create_access_token
from app.ai.observability import instrumented_ai_call
from app.ai.asr import transcribe_audio

client = TestClient(app)



def test_ai_call_instrumentation_wrapper(clean_db: Session):
    """
    Verifies that instrumented_ai_call captures latency, token usage, cost, and prompt_version into AICallLog.
    """
    def sample_func(text: str):
        time.sleep(0.005)
        return {"theme": "family", "prompt_tokens": 50, "completion_tokens": 20}

    res = instrumented_ai_call(
        "classification",
        "classification_v2.0",
        sample_func,
        "sample text",
        db=clean_db
    )
    assert res["theme"] == "family"

    logs = clean_db.query(AICallLog).all()
    assert len(logs) == 1
    log = logs[0]
    assert log.call_type == "classification"
    assert log.prompt_version == "classification_v2.0"
    assert log.latency_ms > 0
    assert log.input_tokens == 50
    assert log.output_tokens == 20
    assert log.estimated_cost_usd > 0
    assert log.status == "success"

def test_admin_ai_metrics_endpoint(clean_db: Session):
    """
    Verifies GET /admin/ai-metrics aggregates latency, costs, and unit economics.
    """
    c1 = Caregiver(email="admin_cg@example.com", password_hash=get_password_hash("pass"), name="Admin Caregiver")
    clean_db.add(c1)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    log1 = AICallLog(call_type="classification", prompt_version="v1.0", latency_ms=120.0, input_tokens=100, output_tokens=50, estimated_cost_usd=0.002, status="success")
    log2 = AICallLog(call_type="asr", prompt_version="v1.0", latency_ms=450.0, input_tokens=200, output_tokens=0, estimated_cost_usd=0.005, status="success")
    clean_db.add(log1)
    clean_db.add(log2)
    clean_db.commit()

    res = client.get("/admin/ai-metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["system_status"] == "healthy"
    assert data["alert_triggered"] is False
    assert data["total_ai_calls"] == 2
    assert "metrics_by_call_type" in data
    assert "classification" in data["metrics_by_call_type"]

def test_simulated_failure_spike_alert(clean_db: Session):
    """
    SIMULATED FAILURE SPIKE ALERT:
    Injects simulated ASR failures to exceed the 10% failure threshold and verifies GET /admin/ai-metrics triggers alert.
    """
    c1 = Caregiver(email="alert_cg@example.com", password_hash=get_password_hash("pass"), name="Alert Caregiver")
    clean_db.add(c1)
    clean_db.commit()

    token = create_access_token({"sub": str(c1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    p1 = Patient(name="Alert Patient", primary_caregiver_id=c1.id)
    clean_db.add(p1)
    clean_db.commit()

    for i in range(5):
        try:
            transcribe_audio("https://example.com/bad.mp3", patient_id=p1.id, db=clean_db, force_failure=True)
        except Exception:
            pass

    transcribe_audio("https://example.com/good.mp3", patient_id=p1.id, db=clean_db, force_failure=False)

    metrics_res = client.get("/admin/ai-metrics", headers=headers)
    assert metrics_res.status_code == 200
    m_data = metrics_res.json()

    assert m_data["alert_triggered"] is True
    assert m_data["system_status"] == "alerting"
    assert "CRITICAL ALERT" in m_data["alert_message"]
