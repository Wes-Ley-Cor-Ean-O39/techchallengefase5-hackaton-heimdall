import json
from typing import Any, Dict


class SqsPublisherAdapter:
    def __init__(self, sqs_client: Any, queue_url: str) -> None:
        self._sqs_client = sqs_client
        self._queue_url = queue_url

    def publish(self, payload: Dict[str, Any]) -> None:
        self._sqs_client.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(payload, ensure_ascii=False),
        )
