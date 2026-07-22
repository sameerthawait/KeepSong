import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models import Recording
from app.ai.asr import transcribe_audio
from app.ai.classifier import classify_transcript
from app.ai.embeddings import generate_embedding
from app.ai.graph import extract_and_link_entities

logger = logging.getLogger("keepsong.ai_pipeline")

def run_ai_pipeline(
    recording_id: UUID,
    db: Session,
    force_asr_fail: bool = False,
    force_llm_malformed: bool = False
) -> Optional[Recording]:
    """
    Asynchronous AI processing pipeline:
    Stage 1: ASR Speech-to-Text
    Stage 2: NIM Llama-3.3-70b Classification & Captioning
    Stage 3: 1536-d Vector Embedding Generation
    Stage 4: Knowledge Graph Entity & Relationship Extraction
    """
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        logger.error(f"Recording {recording_id} not found in database.")
        return None

    patient_id = recording.patient_id

    try:
        # Stage 1: ASR Transcription
        recording.processing_status = "transcribing"
        db.commit()

        transcript = transcribe_audio(
            recording.audio_url,
            patient_id=patient_id,
            recording_id=recording_id,
            db=db,
            force_failure=force_asr_fail
        )
        recording.transcript = transcript

        # Stage 2: NIM LLM Classification & Captioning
        recording.processing_status = "classifying"
        db.commit()

        classification = classify_transcript(
            transcript,
            force_malformed_llm=force_llm_malformed,
            patient_id=patient_id,
            recording_id=recording_id,
            db=db
        )
        recording.theme = classification["theme"]
        recording.estimated_decade = classification["estimated_decade"]
        recording.ai_caption = classification["ai_caption"]
        recording.classification_confidence = classification["classification_confidence"]
        recording.classification_rationale = classification["classification_rationale"]
        recording.model_identifier = classification["model_identifier"]
        recording.prompt_version = classification["prompt_version"]

        # Stage 3: Vector Embedding Generation
        recording.processing_status = "embedding"
        db.commit()

        embedding = generate_embedding(
            transcript,
            patient_id=patient_id,
            recording_id=recording_id,
            db=db
        )
        recording.embedding = embedding

        # Stage 4: Knowledge Graph Entity & Relationship Extraction
        recording.processing_status = "extracting_graph"
        db.commit()

        extract_and_link_entities(
            transcript,
            patient_id=patient_id,
            recording_id=recording_id,
            db=db
        )

        recording.processing_status = "done"
        recording.failure_stage = None
        db.commit()
        logger.info(f"AI Pipeline successfully completed for recording {recording_id}")
        return recording

    except Exception as e:
        logger.error(f"AI Pipeline failed for recording {recording_id} at stage {recording.processing_status}: {str(e)}")
        recording.failure_stage = "asr" if recording.processing_status == "transcribing" else recording.processing_status
        recording.processing_status = "failed"
        db.commit()
        return recording
