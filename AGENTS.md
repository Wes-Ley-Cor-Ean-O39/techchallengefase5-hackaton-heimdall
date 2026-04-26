# AGENTS.md · Heimdail

## Contexto rápido
- Repo: `techchallengefase5-hackaton-heimdall`
- Papel: worker assíncrono de análise de diagramas (imagem/PDF)
- Runtime principal: container Python
- Infra local: LocalStack (`s3`, `sqs`, `dynamodb`)

## Objetivo funcional
- Consumir mensagens da fila `analise-solicitada`.
- Ler arquivo do bucket bruto.
- Analisar diagrama via OpenAI API.
- Persistir resultado no DynamoDB.
- Publicar evento `ANALYSIS_COMPLETED` em `relatorio-solicitado`.

## Contratos e dados
- Fila entrada: `analise-solicitada`
- Fila saída: `relatorio-solicitado`
- Tabela: `analises-arquitetura` (PK: `uploadId`)
- Bucket bruto: `techchallenge-fase5-raw`
- Bucket de relatórios: `techchallenge-fase5-reports`

## Guardrails de inferência
- `MAX_OUTPUT_TOKENS`
- `MAX_INPUT_BYTES`
- `MAX_PDF_PAGES`
- `OPENAI_API_KEY` deve ficar em Secret Kubernetes (`heimdail-openai`), nao inline no Deployment.

## Comandos úteis
```bash
cd /Users/wesleyazevedo/fiap/techchallengefase5-hackaton-heimdall

# subir stack local
export OPENAI_API_KEY=<SUA_OPENAI_API_KEY>
docker compose up -d --build

# logs worker
docker compose logs -f heimdail

# validar item no ddb
docker exec tc5-heimdail-localstack awslocal dynamodb get-item --table-name analises-arquitetura --key '{"uploadId":{"S":"demo-arq-001-diagrama-arquitetura"}}'

# validar evento de saída
docker exec tc5-heimdail-localstack awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/relatorio-solicitado --max-number-of-messages 1
```

## CI/CD
- Workflow: `.github/workflows/ci.yml`
- Jobs: build, deploy (main), open-pr
- Deploy: build/push ECR + apply em EKS via `k8s/deployment.yaml`
- Gates de qualidade: testes unitários com cobertura mínima de `80%` + SonarCloud (condicional por token).

## Repositórios relacionados
- `techchallengefase5-hackaton-gatekeeper` (entrada/presign)
- `techchallengefase5-hackaton-infra-k8s` (plataforma EKS)

## Convenções desta pós
- README com `TL;DR`, contratos e guia de execução local.
- Arquitetura padrão do serviço: **Hexagonal (Ports and Adapters)**.
- Role padrão para infraestrutura/workloads AWS: **`LabRole`** (salvo exceção explícita).
- Qualidade mínima: cobertura unitária >= `80%` nos repos de app.
- Sempre criar `AGENTS.md` ao iniciar repo novo.
- Evitar lógica de relatório final aqui: este serviço publica evento para downstream.
- Atualizar README sempre que mudar variáveis de ambiente ou fluxo de filas.

## Base de conhecimento obrigatoria
- Ler `docs/knowledge-base-fase3-fase4.md` antes de propor mudancas de arquitetura, CI/CD, IaC ou operacao.
- Ler `docs/operational-playbook.md` antes de alterar fluxo funcional, pipeline ou configuracoes do repositorio.
- Quando houver conflito entre implementacao atual e padrao historico (fase 3/4), documentar a decisao no README e manter consistencia no pipeline.
