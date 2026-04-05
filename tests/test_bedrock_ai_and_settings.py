import os
from io import BytesIO

import pytest
from pypdf import PdfWriter

from heimdail.adapters.out.bedrock_ai import BedrockAiAdapter
from heimdail.config.settings import Settings
from heimdail.domain.entities import AnalysisResult


class BedrockClient:
    def converse(self, **kwargs):
        return {"output": {"message": {"content": [{"text": "analise"}]}}}


def _sample_pdf_bytes(num_pages=1):
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_bedrock_adapter_success_image():
    adapter = BedrockAiAdapter(BedrockClient(), "model", 100, 1024 * 1024, 5)
    out = adapter.analyze_image(b"img", "image/png")
    assert out["analysis"] == "analise"


def test_bedrock_adapter_size_limit():
    adapter = BedrockAiAdapter(BedrockClient(), "model", 100, 2, 5)
    with pytest.raises(ValueError, match="MAX_INPUT_BYTES"):
        adapter.analyze_image(b"123", "image/png")


def test_bedrock_adapter_pdf_page_limit():
    adapter = BedrockAiAdapter(BedrockClient(), "model", 100, 10_000_000, 1)
    pdf = _sample_pdf_bytes(num_pages=2)
    with pytest.raises(ValueError, match="MAX_PDF_PAGES"):
        adapter.analyze_image(pdf, "application/pdf")


def test_settings_validation(monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", "in")
    monkeypatch.setenv("REPORT_REQUEST_QUEUE_URL", "out")
    monkeypatch.setenv("ANALYSIS_TABLE_NAME", "t")
    s = Settings.from_env()
    assert s.aws_region == "us-east-1"


def test_settings_missing(monkeypatch):
    monkeypatch.delenv("SQS_QUEUE_URL", raising=False)
    monkeypatch.delenv("REPORT_REQUEST_QUEUE_URL", raising=False)
    monkeypatch.delenv("ANALYSIS_TABLE_NAME", raising=False)
    with pytest.raises(ValueError):
        Settings.from_env()


def test_entity_now_iso():
    assert "T" in AnalysisResult.now_iso()
