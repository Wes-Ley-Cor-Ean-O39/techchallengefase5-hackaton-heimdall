class FakeAiAdapter:
    """Adapter local para testes: simula analise de diagrama em imagem/PDF."""

    def analyze_image(self, content: bytes, media_type: str) -> dict:
        size_kb = max(len(content) // 1024, 1)

        return {
            "analysis": (
                "Resumo tecnico (modo fake):\n"
                f"Entrada recebida: {media_type} (~{size_kb} KB).\n"
                "1. Componentes identificados: API Gateway, processamento assíncrono com SQS e armazenamento em S3.\n"
                "2. Riscos potenciais: acoplamento entre serviços sem contrato versionado e ausência de DLQ configurada no fluxo.\n"
                "3. Recomendações: padronizar rastreabilidade (correlation-id), validar payloads de eventos e ampliar observabilidade."
            ),
            "confidence": 0.82,
            "strategy_used": "multimodal_fake",
            "fallback_reason": "",
        }
