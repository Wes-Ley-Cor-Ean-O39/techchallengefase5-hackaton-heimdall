# Playbook Operacional - Heimdall

## Escopo
Worker assincrono para analise de diagramas com consumo de SQS, leitura S3 e persistencia em DynamoDB.

## Fluxo esperado
1. consumir evento de `requested-analysis`
2. buscar arquivo no bucket bruto
3. executar analise (OpenAI API)
4. persistir resultado
5. publicar `ANALYSIS_COMPLETED` em `requested-report`

## Comandos base
```bash
docker compose up -d --build
docker compose logs -f heimdail
```

## CI/CD padrao
- build + testes + cobertura minima
- push ECR e deploy EKS apenas em `main`

## Guardrails
- Nao gerar relatorio final aqui; publicar evento para downstream.
- Limites de inferencia devem permanecer explicitos e configuraveis.
- Manter `OPENAI_API_KEY` em Secret Kubernetes (`heimdail-openai`) no EKS.
- PDFs devem ser enviados para OpenAI como arquivo (`input_file`) para preservar texto e imagens das paginas.
