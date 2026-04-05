from typing import Any, Dict, List


class SqsQueueAdapter:
    def __init__(self, sqs_client: Any, queue_url: str) -> None:
        self._sqs_client = sqs_client
        self._queue_url = queue_url

    def receive_messages(self, max_messages: int, wait_seconds: int) -> List[Dict[str, Any]]:
        response = self._sqs_client.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=max_messages,
            WaitTimeSeconds=wait_seconds,
            VisibilityTimeout=120,
        )
        return response.get("Messages", [])

    def delete_message(self, receipt_handle: str) -> None:
        self._sqs_client.delete_message(QueueUrl=self._queue_url, ReceiptHandle=receipt_handle)
