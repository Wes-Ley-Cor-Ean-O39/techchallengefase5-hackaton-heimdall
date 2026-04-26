# EKS Validation Runbook - Heimdall

## Objetivo
Checklist rapido para validar deploy e processamento do worker no EKS.

## 1) Conectar no cluster
```bash
aws eks update-kubeconfig --name tc-fase5-hackaton-eks --region us-east-1
kubectl config current-context
```

## 2) Validar status do workload
```bash
kubectl get deploy -n default hackaton-heimdail
kubectl get pods -n default -l app=hackaton-heimdail -o wide
kubectl rollout status deployment/hackaton-heimdail -n default --timeout=180s
```

## 3) Logs e diagnostico
```bash
kubectl logs -n default deploy/hackaton-heimdail --tail=200
kubectl logs -f -n default deploy/hackaton-heimdail
kubectl get events -n default --sort-by=.lastTimestamp | tail -n 30
```

## 4) Teste de processamento (SQS -> DynamoDB -> SQS)
Envie evento para fila de entrada:
```bash
aws sqs send-message \
  --region us-east-1 \
  --queue-url https://sqs.us-east-1.amazonaws.com/339713015255/analise-solicitada \
  --message-body '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2026-04-05T00:00:00.000Z","eventName":"ObjectCreated:Put","s3":{"bucket":{"name":"techchallenge-fase5-raw"},"object":{"key":"uploads/demo-arq-001-diagrama-arquitetura.png"}}}]}'
```

Verifique logs:
```bash
kubectl logs -f -n default deploy/hackaton-heimdail
```

Verifique DynamoDB:
```bash
aws dynamodb get-item \
  --region us-east-1 \
  --table-name analises-arquitetura \
  --key '{"uploadId":{"S":"demo-arq-001-diagrama-arquitetura"}}'
```

Verifique fila de saida:
```bash
aws sqs receive-message \
  --region us-east-1 \
  --queue-url https://sqs.us-east-1.amazonaws.com/339713015255/relatorio-solicitado \
  --max-number-of-messages 1
```

## 5) Erros comuns
- `QueueDoesNotExist`: criar filas `analise-solicitada` e `relatorio-solicitado`.
- `AccessDenied`: revisar IAM role associada aos nodes/pod para SQS/S3/DynamoDB.
- `NoSuchBucket`: criar bucket `techchallenge-fase5-raw`.
- `ResourceNotFoundException` (DynamoDB): criar tabela `analises-arquitetura`.
