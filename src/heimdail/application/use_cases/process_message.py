import re
from typing import Any, Dict
from urllib.parse import unquote_plus

from heimdail.application.ports import (
    AiAnalysisPort,
    AnalysisRepositoryPort,
    MessageParserPort,
    PublisherPort,
    StoragePort,
)
from heimdail.domain.entities import AnalysisResult, ProcessingRequest


UUID_PREFIX_REGEX = re.compile(r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})-")


class DefaultMessageParser(MessageParserPort):
    def __init__(self, default_raw_bucket: str) -> None:
        self._default_raw_bucket = default_raw_bucket

    def parse(self, message_body: Dict[str, Any]) -> ProcessingRequest:
        if isinstance(message_body.get("Records"), list):
            return self._parse_s3_event(message_body)

        upload_id = message_body.get("uploadId") or message_body.get("id")
        key = message_body.get("key")
        bucket = message_body.get("bucket") or self._default_raw_bucket

        if not upload_id or not key:
            raise ValueError("Mensagem precisa conter uploadId e key")

        if not bucket:
            raise ValueError("Bucket de origem ausente na mensagem e em RAW_BUCKET_NAME")

        return ProcessingRequest(upload_id=upload_id, bucket=bucket, key=key)

    def _parse_s3_event(self, message_body: Dict[str, Any]) -> ProcessingRequest:
        records = message_body.get("Records", [])
        if not records:
            raise ValueError("Evento S3 sem Records")

        first = records[0]
        s3_data = first.get("s3", {})
        bucket = s3_data.get("bucket", {}).get("name", "")
        raw_key = s3_data.get("object", {}).get("key", "")
        key = unquote_plus(raw_key)

        if not bucket or not key:
            raise ValueError("Evento S3 invalido: bucket/key ausentes")

        upload_id = self._extract_upload_id_from_key(key)
        return ProcessingRequest(upload_id=upload_id, bucket=bucket, key=key)

    @staticmethod
    def _extract_upload_id_from_key(key: str) -> str:
        file_name = key.split("/")[-1]
        match = UUID_PREFIX_REGEX.match(file_name)
        if match:
            return match.group(1)
        if "." in file_name:
            return file_name.rsplit(".", 1)[0]
        return file_name


class ProcessMessageUseCase:
    def __init__(
        self,
        parser: MessageParserPort,
        storage: StoragePort,
        ai_analysis: AiAnalysisPort,
        repository: AnalysisRepositoryPort,
        publisher: PublisherPort,
    ) -> None:
        self._parser = parser
        self._storage = storage
        self._ai_analysis = ai_analysis
        self._repository = repository
        self._publisher = publisher

    def execute(self, message_body: Dict[str, Any]) -> str:
        request = self._parser.parse(message_body)

        content, media_type = self._storage.read_document(bucket=request.bucket, key=request.key)
        analysis_payload = self._ai_analysis.analyze_image(content=content, media_type=media_type)

        result = AnalysisResult(
            upload_id=request.upload_id,
            source_bucket=request.bucket,
            source_key=request.key,
            media_type=media_type,
            analysis=analysis_payload.get("analysis", "").strip(),
            strategy_used=analysis_payload.get("strategy_used", "multimodal"),
            fallback_reason=analysis_payload.get("fallback_reason", ""),
            confidence=float(analysis_payload.get("confidence", 0.0)),
            created_at=AnalysisResult.now_iso(),
        )
        self._repository.save(result)

        self._publisher.publish(
            {
                "eventType": "ANALYSIS_COMPLETED",
                "uploadId": result.upload_id,
                "source": {
                    "bucket": result.source_bucket,
                    "key": result.source_key,
                    "mediaType": result.media_type,
                },
                "analysis": {
                    "text": result.analysis,
                    "confidence": result.confidence,
                    "strategyUsed": result.strategy_used,
                    "fallbackReason": result.fallback_reason,
                    "createdAt": result.created_at,
                },
            }
        )

        return result.upload_id
