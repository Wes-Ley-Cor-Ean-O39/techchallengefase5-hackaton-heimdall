from typing import Any

from heimdail.domain.entities import AnalysisResult


class DynamoDbAnalysisRepository:
    def __init__(self, dynamodb_table: Any) -> None:
        self._table = dynamodb_table

    def save(self, result: AnalysisResult) -> None:
        self._table.put_item(
            Item={
                "uploadId": result.upload_id,
                "sourceBucket": result.source_bucket,
                "sourceKey": result.source_key,
                "mediaType": result.media_type,
                "analysis": result.analysis,
                "confidence": str(result.confidence),
                "strategyUsed": result.strategy_used,
                "fallbackReason": result.fallback_reason,
                "createdAt": result.created_at,
            }
        )
