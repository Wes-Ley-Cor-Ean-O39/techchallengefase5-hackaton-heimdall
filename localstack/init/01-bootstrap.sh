#!/bin/sh
set -e

echo "[init] creating buckets"
awslocal s3 mb s3://techchallenge-fase5-raw || true
awslocal s3 mb s3://techchallenge-fase5-reports || true

echo "[init] creating queue"
awslocal sqs create-queue --queue-name analise-solicitada >/dev/null
awslocal sqs create-queue --queue-name relatorio-solicitado >/dev/null

QUEUE_URL=$(awslocal sqs get-queue-url --queue-name analise-solicitada --query QueueUrl --output text)

echo "[init] creating analysis table"
awslocal dynamodb create-table \
  --table-name analises-arquitetura \
  --attribute-definitions AttributeName=uploadId,AttributeType=S \
  --key-schema AttributeName=uploadId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST >/dev/null

echo "[init] uploading architecture diagram image to raw bucket"
awslocal s3 cp /init/sample-diagrama-arquitetura.png s3://techchallenge-fase5-raw/uploads/demo-arq-001-diagrama-arquitetura.png

echo "[init] enqueue processing message"
awslocal sqs send-message \
  --queue-url "$QUEUE_URL" \
  --message-body '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2026-03-11T00:00:00.000Z","eventName":"ObjectCreated:Put","s3":{"bucket":{"name":"techchallenge-fase5-raw"},"object":{"key":"uploads/demo-arq-001-diagrama-arquitetura.png"}}}]}' >/dev/null

echo "[init] done"
