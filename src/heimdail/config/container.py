import boto3

from heimdail.adapters.out.aws_queue import SqsQueueAdapter
from heimdail.adapters.out.dynamodb_analysis_repository import DynamoDbAnalysisRepository
from heimdail.adapters.out.aws_storage import S3StorageAdapter
from heimdail.adapters.out.bedrock_ai import BedrockAiAdapter
from heimdail.adapters.out.fake_ai import FakeAiAdapter
from heimdail.adapters.out.sqs_publisher import SqsPublisherAdapter
from heimdail.application.services.worker_service import WorkerService
from heimdail.application.use_cases.process_message import DefaultMessageParser, ProcessMessageUseCase
from heimdail.config.settings import Settings


def build_worker() -> WorkerService:
    settings = Settings.from_env()

    endpoint_url = settings.aws_endpoint_url or None

    sqs_client = boto3.client("sqs", region_name=settings.aws_region, endpoint_url=endpoint_url)
    s3_client = boto3.client("s3", region_name=settings.aws_region, endpoint_url=endpoint_url)
    dynamodb_resource = boto3.resource("dynamodb", region_name=settings.aws_region, endpoint_url=endpoint_url)
    analysis_table = dynamodb_resource.Table(settings.analysis_table_name)

    queue_adapter = SqsQueueAdapter(sqs_client=sqs_client, queue_url=settings.sqs_queue_url)
    storage_adapter = S3StorageAdapter(s3_client=s3_client)
    repository_adapter = DynamoDbAnalysisRepository(dynamodb_table=analysis_table)
    publisher_adapter = SqsPublisherAdapter(
        sqs_client=sqs_client,
        queue_url=settings.report_request_queue_url,
    )
    if settings.bedrock_use_fake:
        ai_adapter = FakeAiAdapter()
    else:
        bedrock_client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        ai_adapter = BedrockAiAdapter(
            bedrock_client=bedrock_client,
            model_id=settings.bedrock_model_id,
            max_output_tokens=settings.max_output_tokens,
            max_input_bytes=settings.max_input_bytes,
            max_pdf_pages=settings.max_pdf_pages,
        )
    parser = DefaultMessageParser(default_raw_bucket=settings.raw_bucket_name)

    use_case = ProcessMessageUseCase(
        parser=parser,
        storage=storage_adapter,
        ai_analysis=ai_adapter,
        repository=repository_adapter,
        publisher=publisher_adapter,
    )

    return WorkerService(
        queue=queue_adapter,
        use_case=use_case,
        max_messages=settings.max_messages,
        poll_wait_seconds=settings.poll_wait_seconds,
    )
