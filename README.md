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
- Analisar com OpenAI API.
- Persistir análise no DynamoDB.
- Publicar `ANALYSIS_COMPLETED` em fila de saída.

PDFs sao enviados para a OpenAI como `input_file` em base64, preservando texto e imagens das paginas para analise multimodal do diagrama.

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
        openai_ai.py
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
Extensoes suportadas no S3: `png`, `jpg`, `jpeg`, `webp`, `bmp`, `gif`, `pdf`.

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
    "strategyUsed": "multimodal_openai",
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
- `OPENAI_MODEL` (`gpt-4.1-mini`)
- `OPENAI_API_KEY` (obrigatória)
- `MAX_OUTPUT_TOKENS` (`700`)
- `MAX_INPUT_BYTES` (`5242880`)
- `MAX_PDF_PAGES` (`8`)
- `POLL_WAIT_SECONDS` (`20`)
- `MAX_MESSAGES` (`5`)

## 🧪 Execução local
### 1) Subir ambiente
```bash
export OPENAI_API_KEY=<SUA_OPENAI_API_KEY>
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
- `REPLACE_OPENAI_MODEL`

O `OPENAI_API_KEY` nao e substituido no manifesto. O deploy cria/atualiza o Secret Kubernetes
`heimdail-openai` e o pod le a chave via `secretKeyRef`.

Defaults de deploy (quando secrets nao informados):
- Cluster EKS: `tc-fase5-hackaton-eks`
- ECR: `339713015255.dkr.ecr.us-east-1.amazonaws.com/techchallenge-fase5-uploads`
- Bucket bruto: `techchallenge-fase5-raw`
- Bucket relatorios: `techchallenge-fase5-reports`
- `OPENAI_MODEL`: `gpt-4.1-mini`
- `OPENAI_API_KEY`: obrigatorio via secret `OPENAI_API_KEY`

### Deploy manual (padrao fase 4)
```bash
aws eks update-kubeconfig --name tc-fase5-hackaton-eks --region us-east-1

IMAGE_URI=339713015255.dkr.ecr.us-east-1.amazonaws.com/techchallenge-fase5-uploads:<TAG>
SQS_IN=https://sqs.us-east-1.amazonaws.com/339713015255/analise-solicitada
SQS_OUT=https://sqs.us-east-1.amazonaws.com/339713015255/relatorio-solicitado
TABLE=analises-arquitetura
RAW_BUCKET=techchallenge-fase5-raw
REPORTS_BUCKET=techchallenge-fase5-reports
OPENAI_MODEL=gpt-4.1-mini
OPENAI_API_KEY=<SUA_OPENAI_API_KEY>

cp k8s/deployment.yaml /tmp/heimdall-deployment.yaml
sed -i "s|REPLACE_ECR_IMAGE_URI|$IMAGE_URI|g" /tmp/heimdall-deployment.yaml
sed -i "s|REPLACE_SQS_URL|$SQS_IN|g" /tmp/heimdall-deployment.yaml
sed -i "s|REPLACE_REPORT_REQUEST_QUEUE_URL|$SQS_OUT|g" /tmp/heimdall-deployment.yaml
sed -i "s|REPLACE_ANALYSIS_TABLE_NAME|$TABLE|g" /tmp/heimdall-deployment.yaml
sed -i "s|REPLACE_RAW_BUCKET_NAME|$RAW_BUCKET|g" /tmp/heimdall-deployment.yaml
sed -i "s|REPLACE_REPORTS_BUCKET_NAME|$REPORTS_BUCKET|g" /tmp/heimdall-deployment.yaml
sed -i "s|REPLACE_OPENAI_MODEL|$OPENAI_MODEL|g" /tmp/heimdall-deployment.yaml

kubectl create secret generic heimdail-openai \
  --from-literal=api-key="$OPENAI_API_KEY" \
  -n default \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n default -f /tmp/heimdall-deployment.yaml
kubectl rollout status deployment/hackaton-heimdail -n default --timeout=180s
```

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
- `OPENAI_API_KEY`
- `GH_PR_TOKEN` (opcional)
- `SONAR_TOKEN` (opcional)
- `SONAR_ORGANIZATION` (opcional)

## 🔎 Operacao (EKS)
- Ver deployment: `kubectl get deploy -n default hackaton-heimdail`
- Ver pods: `kubectl get pods -n default -l app=hackaton-heimdail -o wide`
- Rollout status: `kubectl rollout status deployment/hackaton-heimdail -n default --timeout=180s`
- Reiniciar worker: `kubectl rollout restart deployment/hackaton-heimdail -n default`
- Eventos recentes: `kubectl get events -n default --sort-by=.lastTimestamp | tail -n 30`

### Logs e diagnostico
- Logs ultimo pod: `kubectl logs -n default deploy/hackaton-heimdail --tail=200`
- Follow logs: `kubectl logs -f -n default deploy/hackaton-heimdail`
- Describe do pod (falha de agendamento/imagem/env):  
  `kubectl describe pod -n default $(kubectl get pod -n default -l app=hackaton-heimdail -o jsonpath='{.items[0].metadata.name}')`

### Validacao fim a fim no cluster
Pre-reqs minimos:
- fila de entrada `analise-solicitada`
- fila de saida `relatorio-solicitado`
- tabela DynamoDB `analises-arquitetura`
- bucket `techchallenge-fase5-raw`

1) Enviar mensagem de teste para a fila de entrada:
```bash
aws sqs send-message \
  --region us-east-1 \
  --queue-url https://sqs.us-east-1.amazonaws.com/339713015255/analise-solicitada \
  --message-body '{"Records":[{"eventVersion":"2.1","eventSource":"aws:s3","awsRegion":"us-east-1","eventTime":"2026-04-05T00:00:00.000Z","eventName":"ObjectCreated:Put","s3":{"bucket":{"name":"techchallenge-fase5-raw"},"object":{"key":"uploads/demo-arq-001-diagrama-arquitetura.png"}}}]}'
```

2) Acompanhar processamento:
```bash
kubectl logs -f -n default deploy/hackaton-heimdail
```

3) Validar escrita no DynamoDB:
```bash
aws dynamodb get-item \
  --region us-east-1 \
  --table-name analises-arquitetura \
  --key '{"uploadId":{"S":"demo-arq-001-diagrama-arquitetura"}}'
```

4) Validar evento de saida:
```bash
aws sqs receive-message \
  --region us-east-1 \
  --queue-url https://sqs.us-east-1.amazonaws.com/339713015255/relatorio-solicitado \
  --max-number-of-messages 1
```

## ✅ Checklist de pronto
- [ ] imagem publicada no ECR `techchallenge-fase5-uploads`
- [ ] deployment `hackaton-heimdail` em `Running`
- [ ] filas SQS criadas (`analise-solicitada`, `relatorio-solicitado`)
- [ ] tabela `analises-arquitetura` existente
- [ ] bucket `techchallenge-fase5-raw` existente
- [ ] logs sem erro de credencial/permissao AWS

## 🔗 Repositórios relacionados
- `techchallengefase5-hackaton-gatekeeper`: entrada/presign e registro inicial do upload.
- `techchallengefase5-hackaton-infra-k8s`: cluster EKS, Kong e observabilidade.
