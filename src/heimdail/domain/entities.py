from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ProcessingRequest:
    upload_id: str
    bucket: str
    key: str


@dataclass(frozen=True)
class AnalysisResult:
    upload_id: str
    source_bucket: str
    source_key: str
    media_type: str
    analysis: str
    strategy_used: str
    fallback_reason: str
    confidence: float
    created_at: str

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
