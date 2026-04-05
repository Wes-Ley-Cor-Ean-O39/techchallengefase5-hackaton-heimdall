import pytest

from heimdail.application.use_cases.process_message import DefaultMessageParser, ProcessMessageUseCase


class Storage:
    def read_document(self, bucket, key):
        return b"img-bytes", "image/png"


class Ai:
    def analyze_image(self, content, media_type):
        return {
            "analysis": "ok",
            "strategy_used": "multimodal",
            "fallback_reason": "",
            "confidence": 0.9,
        }


class Repo:
    def __init__(self):
        self.saved = None

    def save(self, result):
        self.saved = result


class Pub:
    def __init__(self):
        self.payload = None

    def publish(self, payload):
        self.payload = payload


def test_parser_s3_event_and_custom_payload():
    parser = DefaultMessageParser(default_raw_bucket="default-b")

    req1 = parser.parse(
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "raw-b"},
                        "object": {"key": "uploads/abc-file.png"},
                    }
                }
            ]
        }
    )
    assert req1.bucket == "raw-b"
    assert req1.upload_id == "abc-file"

    req2 = parser.parse({"uploadId": "u1", "key": "uploads/f.png"})
    assert req2.upload_id == "u1"
    assert req2.bucket == "default-b"


def test_parser_invalid_payloads():
    parser = DefaultMessageParser(default_raw_bucket="")
    with pytest.raises(ValueError):
        parser.parse({"uploadId": "u1"})

    with pytest.raises(ValueError):
        parser.parse({"Records": []})


def test_use_case_execute_persists_and_publishes():
    parser = DefaultMessageParser(default_raw_bucket="raw-b")
    repo = Repo()
    pub = Pub()
    use_case = ProcessMessageUseCase(parser, Storage(), Ai(), repo, pub)

    upload_id = use_case.execute({"uploadId": "u9", "key": "uploads/u9.png"})
    assert upload_id == "u9"
    assert repo.saved.upload_id == "u9"
    assert pub.payload["eventType"] == "ANALYSIS_COMPLETED"
