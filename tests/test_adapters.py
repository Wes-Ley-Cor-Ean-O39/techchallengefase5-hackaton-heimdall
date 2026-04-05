import pytest

from heimdail.adapters.out.aws_queue import SqsQueueAdapter
from heimdail.adapters.out.aws_storage import S3StorageAdapter
from heimdail.adapters.out.dynamodb_analysis_repository import DynamoDbAnalysisRepository
from heimdail.adapters.out.fake_ai import FakeAiAdapter
from heimdail.adapters.out.sqs_publisher import SqsPublisherAdapter
from heimdail.domain.entities import AnalysisResult


class Body:
    def read(self):
        return b"abc"


class S3Client:
    def get_object(self, Bucket, Key):
        return {"Body": Body()}


class SqsClient:
    def __init__(self):
        self.sent = None

    def receive_message(self, **kwargs):
        return {"Messages": [{"Body": "{}"}]}

    def delete_message(self, **kwargs):
        self.deleted = kwargs

    def send_message(self, **kwargs):
        self.sent = kwargs


class Table:
    def __init__(self):
        self.item = None

    def put_item(self, Item):
        self.item = Item


def test_aws_storage_supported_and_unsupported():
    storage = S3StorageAdapter(S3Client())
    content, media = storage.read_document("b", "uploads/a.png")
    assert content == b"abc"
    assert media == "image/png"

    with pytest.raises(ValueError):
        storage.read_document("b", "uploads/a.txt")


def test_queue_and_publisher_and_repo():
    sqs = SqsClient()
    queue = SqsQueueAdapter(sqs, "url")
    assert queue.receive_messages(1, 1)
    queue.delete_message("rh")

    pub = SqsPublisherAdapter(sqs, "url-out")
    pub.publish({"a": 1})
    assert sqs.sent["QueueUrl"] == "url-out"

    table = Table()
    repo = DynamoDbAnalysisRepository(table)
    repo.save(
        AnalysisResult(
            upload_id="u1",
            source_bucket="b",
            source_key="k",
            media_type="image/png",
            analysis="x",
            strategy_used="fake",
            fallback_reason="",
            confidence=0.8,
            created_at="now",
        )
    )
    assert table.item["uploadId"] == "u1"


def test_fake_ai_returns_payload():
    payload = FakeAiAdapter().analyze_image(b"1234", "image/png")
    assert payload["strategy_used"] == "multimodal_fake"
