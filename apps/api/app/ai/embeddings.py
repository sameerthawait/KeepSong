import math
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.ai.observability import instrumented_ai_call

def _generate_embedding_raw(text: str) -> List[float]:
    if not text:
        return [0.0] * 1536

    words = text.lower().split()
    vector = [0.0] * 1536

    for idx, word in enumerate(words):
        hash_val = sum(ord(c) for c in word)
        pos = hash_val % 1536
        vector[pos] += 1.0 / (idx + 1)

    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]

    return vector


def generate_embedding(
    text: str,
    patient_id: Optional[UUID] = None,
    recording_id: Optional[UUID] = None,
    db: Optional[Session] = None
) -> List[float]:
    """
    Generates 1536-dimensional vector embedding wrapped with telemetry observability.
    """
    return instrumented_ai_call(
        "embedding",
        "embedding_v1.0",
        _generate_embedding_raw,
        text,
        patient_id=patient_id,
        recording_id=recording_id,
        db=db
    )
