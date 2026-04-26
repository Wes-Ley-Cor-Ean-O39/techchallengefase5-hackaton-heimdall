from io import BytesIO

import pytest
from pypdf import PdfWriter

from heimdail.adapters.out.openai_ai import OpenAiAdapter
from heimdail.config.settings import Settings
from heimdail.domain.entities import AnalysisResult


class OpenAiResponsesClient:
    def __init__(self):
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return type("Resp", (), {"output_text": "analise"})()


class OpenAiClient:
    def __init__(self):
        self.responses = OpenAiResponsesClient()


def _sample_pdf_bytes(num_pages=1):
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_openai_adapter_success_image():
    client = OpenAiClient()
    adapter = OpenAiAdapter(client, "gpt-4.1-mini", 100, 1024 * 1024, 5)
    out = adapter.analyze_image(b"img", "image/png")
    assert out["analysis"] == "analise"
    assert client.responses.last_kwargs["model"] == "gpt-4.1-mini"


def test_openai_adapter_success_pdf_uses_input_file():
    client = OpenAiClient()
    adapter = OpenAiAdapter(client, "gpt-4.1-mini", 100, 10_000_000, 5)
    out = adapter.analyze_image(_sample_pdf_bytes(), "application/pdf")
    content = client.responses.last_kwargs["input"][0]["content"]
    pdf_input = next(item for item in content if item["type"] == "input_file")

    assert out["strategy_used"] == "multimodal_openai"
    assert pdf_input["filename"] == "diagrama-arquitetura.pdf"
    assert pdf_input["file_data"].startswith("data:application/pdf;base64,")


def test_openai_adapter_size_limit():
    adapter = OpenAiAdapter(OpenAiClient(), "model", 100, 2, 5)
    with pytest.raises(ValueError, match="MAX_INPUT_BYTES"):
        adapter.analyze_image(b"123", "image/png")


def test_openai_adapter_pdf_page_limit():
    adapter = OpenAiAdapter(OpenAiClient(), "model", 100, 10_000_000, 1)
    pdf = _sample_pdf_bytes(num_pages=2)
    with pytest.raises(ValueError, match="MAX_PDF_PAGES"):
        adapter.analyze_image(pdf, "application/pdf")


def test_settings_validation(monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", "in")
    monkeypatch.setenv("REPORT_REQUEST_QUEUE_URL", "out")
    monkeypatch.setenv("ANALYSIS_TABLE_NAME", "t")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    s = Settings.from_env()
    assert s.aws_region == "us-east-1"


def test_settings_missing(monkeypatch):
    monkeypatch.delenv("SQS_QUEUE_URL", raising=False)
    monkeypatch.delenv("REPORT_REQUEST_QUEUE_URL", raising=False)
    monkeypatch.delenv("ANALYSIS_TABLE_NAME", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        Settings.from_env()


def test_entity_now_iso():
    assert "T" in AnalysisResult.now_iso()
