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
  --queue-url https://sqs.us-east-1.amazonaws.com/590184113966/requested-analysis \
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
  --queue-url https://sqs.us-east-1.amazonaws.com/590184113966/requested-report \
  --max-number-of-messages 1
```

## 5) Erros comuns
- `QueueDoesNotExist`: criar filas `requested-analysis` e `requested-report`.
- `AccessDenied`: revisar se as credenciais temporarias do Secret `heimdail-aws` ainda estao validas e possuem permissao para SQS/S3/DynamoDB.
- `AccessDenied` com `explicit deny`: atualizar `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` e `AWS_SESSION_TOKEN` nos GitHub Secrets com as credenciais atuais do AWS Academy e rodar a esteira novamente.
- `Unable to locate credentials`: conferir se `awsCredentials.enabled=true`, se o Secret `heimdail-aws` existe e se o pod foi recriado depois do deploy.
- `NoSuchBucket`: criar bucket `techchallenge-fase5-raw`.
- `ResourceNotFoundException` (DynamoDB): criar tabela `analises-arquitetura`.
