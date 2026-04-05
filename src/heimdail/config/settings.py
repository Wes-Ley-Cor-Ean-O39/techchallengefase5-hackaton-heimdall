import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    aws_region: str
    aws_endpoint_url: str
    sqs_queue_url: str
    report_request_queue_url: str
    analysis_table_name: str
    raw_bucket_name: str
    bedrock_model_id: str
    bedrock_use_fake: bool
    max_output_tokens: int
    max_input_bytes: int
    max_pdf_pages: int
    poll_wait_seconds: int
    max_messages: int

    @staticmethod
    def from_env() -> "Settings":
        settings = Settings(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            aws_endpoint_url=os.getenv("AWS_ENDPOINT_URL", ""),
            sqs_queue_url=os.getenv("SQS_QUEUE_URL", ""),
            report_request_queue_url=os.getenv("REPORT_REQUEST_QUEUE_URL", ""),
            analysis_table_name=os.getenv("ANALYSIS_TABLE_NAME", ""),
            raw_bucket_name=os.getenv("RAW_BUCKET_NAME", ""),
            bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
            bedrock_use_fake=os.getenv("BEDROCK_USE_FAKE", "false").lower() == "true",
            max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "700")),
            max_input_bytes=int(os.getenv("MAX_INPUT_BYTES", "5242880")),
            max_pdf_pages=int(os.getenv("MAX_PDF_PAGES", "8")),
            poll_wait_seconds=int(os.getenv("POLL_WAIT_SECONDS", "20")),
            max_messages=int(os.getenv("MAX_MESSAGES", "5")),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        required = {
            "SQS_QUEUE_URL": self.sqs_queue_url,
            "REPORT_REQUEST_QUEUE_URL": self.report_request_queue_url,
            "ANALYSIS_TABLE_NAME": self.analysis_table_name,
        }

        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")
        if self.max_output_tokens <= 0:
            raise ValueError("MAX_OUTPUT_TOKENS deve ser maior que zero")
        if self.max_input_bytes <= 0:
            raise ValueError("MAX_INPUT_BYTES deve ser maior que zero")
        if self.max_pdf_pages <= 0:
            raise ValueError("MAX_PDF_PAGES deve ser maior que zero")
