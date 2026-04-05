from typing import Any, Dict, List, Protocol

from heimdail.domain.entities import AnalysisResult, ProcessingRequest


class QueuePort(Protocol):
    def receive_messages(self, max_messages: int, wait_seconds: int) -> List[Dict[str, Any]]:
        ...

    def delete_message(self, receipt_handle: str) -> None:
        ...


class StoragePort(Protocol):
    def read_document(self, bucket: str, key: str) -> tuple[bytes, str]:
        ...

class AiAnalysisPort(Protocol):
    def analyze_image(self, content: bytes, media_type: str) -> Dict[str, Any]:
        ...


class AnalysisRepositoryPort(Protocol):
    def save(self, result: AnalysisResult) -> None:
        ...


class PublisherPort(Protocol):
    def publish(self, payload: Dict[str, Any]) -> None:
        ...


class MessageParserPort(Protocol):
    def parse(self, message_body: Dict[str, Any]) -> ProcessingRequest:
        ...
