import time
import json
import logging
from typing import Callable, Any, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models import AICallLog

logger = logging.getLogger("keepsong.ai_observability")

# Standard Provider Unit Cost Pricing Constants (USD)
# ASR: Deepgram/AssemblyAI @ $0.0043 per minute ($0.0000717 per second)
ASR_COST_PER_SECOND = 0.0043 / 60.0

# NIM Llama-3.3-70b-instruct: $0.0007 / 1,000 input tokens, $0.0009 / 1,000 output tokens
NIM_INPUT_COST_PER_1K = 0.0007
NIM_OUTPUT_COST_PER_1K = 0.0009

# 1536-d Vector Embedding API: $0.0001 / 1,000 tokens
EMBEDDING_COST_PER_1K = 0.0001

def estimate_tokens(text: str) -> int:
    """Rough rule of thumb: ~4 characters per token."""
    if not text:
        return 0
    return max(1, len(text) // 4)

def compute_cost_usd(
    call_type: str,
    duration_seconds: float = 0.0,
    input_tokens: int = 0,
    output_tokens: int = 0
) -> float:
    if call_type == "asr":
        return round(duration_seconds * ASR_COST_PER_SECOND, 6)
    elif call_type in ["classification", "entity_extraction", "photo_captioning"]:
        in_cost = (input_tokens / 1000.0) * NIM_INPUT_COST_PER_1K
        out_cost = (output_tokens / 1000.0) * NIM_OUTPUT_COST_PER_1K
        return round(in_cost + out_cost, 6)
    elif call_type == "embedding":
        return round((input_tokens / 1000.0) * EMBEDDING_COST_PER_1K, 6)
    return 0.0

def instrumented_ai_call(
    call_type: str,
    prompt_version: str,
    func: Callable[..., Any],
    *args,
    patient_id: Optional[UUID] = None,
    recording_id: Optional[UUID] = None,
    db: Optional[Session] = None,
    **kwargs
) -> Any:
    """
    Centralized instrumented wrapper around all NIM and ASR calls.
    Captures: timestamp, call_type, latency (ms), token usage, estimated cost ($), and prompt_version.
    """
    start_time = time.perf_counter()
    status = "success"
    error_msg = None
    result = None

    try:
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        status = "failed"
        error_msg = str(e)
        raise e
    finally:
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        
        input_tokens = 0
        output_tokens = 0
        duration_sec = 0.0

        if call_type == "asr" and isinstance(result, str):
            input_tokens = estimate_tokens(result)
            duration_sec = max(5.0, len(result) * 0.1)
        elif isinstance(result, dict):
            if "prompt_tokens" in result:
                input_tokens = result["prompt_tokens"]
                output_tokens = result.get("completion_tokens", 0)
            else:
                input_tokens = estimate_tokens(str(args))
                output_tokens = estimate_tokens(json.dumps(result))
        elif isinstance(result, list):  # Embedding vector
            input_tokens = estimate_tokens(str(args))

        cost_usd = compute_cost_usd(
            call_type=call_type,
            duration_seconds=duration_sec,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        log_payload = {
            "event": "AI_CALL_TELEMETRY",
            "call_type": call_type,
            "prompt_version": prompt_version,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": cost_usd,
            "status": status,
            "patient_id": str(patient_id) if patient_id else None,
            "recording_id": str(recording_id) if recording_id else None
        }
        if error_msg:
            log_payload["error_message"] = error_msg

        logger.info(json.dumps(log_payload))

        if db is not None:
            try:
                log_row = AICallLog(
                    patient_id=patient_id,
                    recording_id=recording_id,
                    call_type=call_type,
                    prompt_version=prompt_version,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost_usd=cost_usd,
                    status=status,
                    error_message=error_msg
                )
                db.add(log_row)
                db.commit()
            except Exception as db_err:
                logger.warning(f"Failed to persist AICallLog row: {str(db_err)}")
