# 🧠 Heimdail · Fase 5 Hackaton

## TL;DR
- **O que é:** worker assíncrono de análise de diagramas.
- **O que faz:** consome SQS, analisa imagem/PDF, persiste no DynamoDB e publica evento para relatório.
- **Comando rápido:** `docker compose up -d --build`.

Worker assíncrono responsável pela análise de diagramas de arquitetura.
Consome eventos, lê o documento no S3, executa análise com IA, persiste resultado e publica evento para o serviço gerador de relatório.

## 🎯 Objetivo do repositório
- Consumir eventos da fila de entrada (`analise-solicitada`).
- Ler imagem/PDF no bucket bruto.
- Analisar com Bedrock (ou modo fake local).
- Persistir análise no DynamoDB.
- Publicar `ANALYSIS_COMPLETED` em fila de saída.

## ✅ O que este serviço entrega
- Persistência do resultado bruto da análise.
- Evento padronizado para desacoplar geração de relatório em outra aplicação.
- Controles de custo e segurança de inferência:
  - `MAX_OUTPUT_TOKENS`
  - `MAX_INPUT_BYTES`
  - `MAX_PDF_PAGES`

## 🧱 Estrutura
```txt
src/
  heimdail/
    domain/
      entities.py
    application/
      ports.py
      use_cases/process_message.py
      services/worker_service.py
    adapters/
      out/
        aws_queue.py
        aws_storage.py
        bedrock_ai.py
        dynamodb_analysis_repository.py
        sqs_publisher.py
    config/
      settings.py
      container.py
    main.py
```

## 📨 Contratos
### Entrada esperada (SQS)
```json
{
  "Records": [
    {
      "eventSource": "aws:s3",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": { "name": "techchallenge-fase5-raw" },
        "object": { "key": "uploads/uuid-arquivo.png" }
      }
    }
  ]
}
```

Também aceita payload legado com `uploadId`, `bucket` e `key`.

### Saídas
1. Item no DynamoDB (`analises-arquitetura`).
2. Mensagem na fila `relatorio-solicitado`:
```json
{
  "eventType": "ANALYSIS_COMPLETED",
  "uploadId": "...",
  "source": {
    "bucket": "...",
    "key": "...",
    "mediaType": "image/png"
  },
  "analysis": {
    "text": "...",
    "confidence": 0.82,
    "strategyUsed": "multimodal_fake",
    "fallbackReason": "",
    "createdAt": "..."
  }
}
```

## ⚙️ Variáveis de ambiente
- `AWS_REGION` (`us-east-1`)
- `AWS_ENDPOINT_URL` (opcional; LocalStack)
- `SQS_QUEUE_URL`
- `REPORT_REQUEST_QUEUE_URL`
- `ANALYSIS_TABLE_NAME`
- `RAW_BUCKET_NAME`
- `REPORTS_BUCKET_NAME` (opcional)
- `BEDROCK_MODEL_ID` (`anthropic.claude-3-haiku-20240307-v1:0`)
- `BEDROCK_USE_FAKE` (`false`)
- `MAX_OUTPUT_TOKENS` (`700`)
- `MAX_INPUT_BYTES` (`5242880`)
- `MAX_PDF_PAGES` (`8`)
- `POLL_WAIT_SECONDS` (`20`)
- `MAX_MESSAGES` (`5`)

## 🧪 Execução local
### 1) Subir ambiente
```bash
docker compose up -d --build
```

### 2) Acompanhar logs
```bash
docker compose logs -f heimdail
```

Esperado: `Mensagem processada com sucesso. upload_id=demo-arq-001-diagrama-arquitetura`

### 3) Validar item no DynamoDB
```bash
docker exec tc5-heimdail-localstack awslocal dynamodb get-item \
  --table-name analises-arquitetura \
  --key '{"uploadId":{"S":"demo-arq-001-diagrama-arquitetura"}}'
```

### 4) Validar evento na fila de saída
```bash
docker exec tc5-heimdail-localstack awslocal sqs receive-message \
  --queue-url http://localhost:4566/000000000000/relatorio-solicitado \
  --max-number-of-messages 1
```

### 5) Encerrar ambiente
```bash
docker compose down -v
```

## 🚀 Deploy (EKS)
Manifesto base: `k8s/deployment.yaml`

O CI substitui placeholders e aplica no cluster:
- `REPLACE_ECR_IMAGE_URI`
- `REPLACE_SQS_URL`
- `REPLACE_REPORT_REQUEST_QUEUE_URL`
- `REPLACE_ANALYSIS_TABLE_NAME`
- `REPLACE_RAW_BUCKET_NAME`
- `REPLACE_REPORTS_BUCKET_NAME`

Defaults de deploy (quando secrets nao informados):
- Cluster EKS: `tc-fase5-hackaton-eks`
- ECR: `339713015255.dkr.ecr.us-east-1.amazonaws.com/techchallenge-fase5-uploads`
- Bucket bruto: `techchallenge-fase5-raw`
- Bucket relatorios: `techchallenge-fase5-reports`

## 🤖 CI/CD
Workflow: `.github/workflows/ci.yml`

- `build`: valida Python, executa testes unitários com cobertura mínima de `80%` e builda Docker.
- `deploy`: push da imagem no ECR + deploy no EKS (somente `main`).
- `open-pr`: abre PR automático para `main` em branches de feature.
- `sonar`: análise SonarCloud condicional (quando `SONAR_TOKEN` e `SONAR_ORGANIZATION` estão configurados).

### 🔐 Secrets recomendados
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `ECR_REGISTRY`
- `IMAGE_NAME`
- `EKS_CLUSTER`
- `EKS_NAMESPACE`
- `SQS_QUEUE_URL`
- `REPORT_REQUEST_QUEUE_URL`
- `ANALYSIS_TABLE_NAME`
- `RAW_BUCKET_NAME` (opcional)
- `REPORTS_BUCKET_NAME` (opcional)
- `GH_PR_TOKEN` (opcional)
- `SONAR_TOKEN` (opcional)
- `SONAR_ORGANIZATION` (opcional)

## 🔗 Repositórios relacionados
- `techchallengefase5-hackaton-gatekeeper`: entrada/presign e registro inicial do upload.
- `techchallengefase5-hackaton-infra-k8s`: cluster EKS, Kong e observabilidade.
