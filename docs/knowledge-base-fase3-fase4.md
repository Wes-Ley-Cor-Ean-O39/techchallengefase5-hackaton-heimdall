# Base de Conhecimento (Prioridade: Fase 3 e 4)

## Objetivo
Consolidar padroes ja validados nas fases 3 e 4 para reduzir retrabalho na fase 5.

## Padroes de arquitetura e operacao reutilizados
- CI/CD com 3 estagios claros: validar/build, plan, apply/deploy.
- Regras de branch:
  - `main/master` para apply/deploy automatico.
  - branches de feature com abertura automatica de PR.
- Infra AWS com Terraform e backend remoto S3.
- Workloads em EKS com addon opcional por variavel (feature toggle).
- Servicos desacoplados por mensageria (SQS/eventos) e contratos explicitos.

## Padroes de qualidade (herdados)
- README com `TL;DR`, objetivo, fluxo e comandos executaveis.
- Variaveis e outputs alterados exigem atualizacao do README.
- Validacoes minimas em IaC:
  - `terraform fmt -check`
  - `terraform validate`
- Validacoes minimas em app:
  - testes unitarios e cobertura minima definida no repo.

## Padroes CI/CD observados na fase 3/4
- Pipelines orientadas a ambiente AWS Academy/LabRole.
- Secrets padrao:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_SESSION_TOKEN`
  - `GH_PR_TOKEN` (opcional)
- Para repos com EKS/Helm, evitar acoplamento no primeiro apply:
  - subir base do cluster primeiro
  - aplicar addons depois

## Padroes de AWS para reaproveitamento
- Role padrao: `LabRole` (salvo excecao explicita documentada).
- Regiao base: `us-east-1`.
- Nomes e contratos de recursos devem ser estaveis e documentados.
- Evitar permissoes amplas sem justificativa em IAM.

## Anti-padroes que causaram falhas
- Tentar instalar CRDs Helm ja existentes sem estrategia de ownership/adocao.
- Primeiro apply de cluster + helm release no mesmo passo de CI sem ordem de dependencia.
- Alterar pipeline sem refletir README/AGENTS.

## Checklists obrigatorios antes de merge
1. Validar localmente os comandos principais do repo.
2. Confirmar secrets necessarios no workflow.
3. Atualizar README para mudancas de variaveis/fluxo.
4. Atualizar AGENTS/docs quando o padrao operacional mudar.
