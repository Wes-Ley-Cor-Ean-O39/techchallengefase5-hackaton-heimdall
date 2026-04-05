from io import BytesIO
from typing import Any

from pypdf import PdfReader


class BedrockAiAdapter:
    def __init__(
        self,
        bedrock_client: Any,
        model_id: str,
        max_output_tokens: int,
        max_input_bytes: int,
        max_pdf_pages: int,
    ) -> None:
        self._bedrock_client = bedrock_client
        self._model_id = model_id
        self._max_output_tokens = max_output_tokens
        self._max_input_bytes = max_input_bytes
        self._max_pdf_pages = max_pdf_pages

    def analyze_image(self, content: bytes, media_type: str) -> dict:
        self._validate_input(content=content, media_type=media_type)

        prompt = (
            "Analise o diagrama de arquitetura e gere um relatorio tecnico em portugues com:\n"
            "1) componentes identificados,\n"
            "2) riscos arquiteturais,\n"
            "3) recomendacoes praticas.\n"
            "Seja objetivo, estruturado e conciso."
        )

        content_blocks = [{"text": prompt}]
        if media_type.startswith("image/"):
            content_blocks.append(
                {
                    "image": {
                        "format": media_type.split("/", 1)[1],
                        "source": {"bytes": content},
                    }
                }
            )
        elif media_type == "application/pdf":
            content_blocks.append(
                {
                    "document": {
                        "format": "pdf",
                        "name": "diagrama-arquitetura",
                        "source": {"bytes": content},
                    }
                }
            )
        else:
            raise ValueError(f"Media type nao suportado para analise: {media_type}")

        response = self._bedrock_client.converse(
            modelId=self._model_id,
            messages=[
                {
                    "role": "user",
                    "content": content_blocks,
                }
            ],
            inferenceConfig={
                "maxTokens": self._max_output_tokens,
                "temperature": 0.2,
                "topP": 0.9,
            },
        )

        content_items = response.get("output", {}).get("message", {}).get("content", [])
        output_text = ""
        for item in content_items:
            text = item.get("text")
            if text:
                output_text = text.strip()
                break
        if not output_text:
            raise ValueError("Resposta do Bedrock sem texto de saida")

        return {
            "analysis": output_text,
            "confidence": 0.75,
            "strategy_used": "multimodal_bedrock",
            "fallback_reason": "",
        }

    def _validate_input(self, content: bytes, media_type: str) -> None:
        size = len(content)
        if size > self._max_input_bytes:
            raise ValueError(
                f"Documento excede limite configurado: {size} bytes > {self._max_input_bytes} bytes (MAX_INPUT_BYTES)."
            )

        if media_type == "application/pdf":
            pages = self._count_pdf_pages(content)
            if pages > self._max_pdf_pages:
                raise ValueError(
                    f"PDF excede limite configurado: {pages} paginas > {self._max_pdf_pages} (MAX_PDF_PAGES)."
                )

    @staticmethod
    def _count_pdf_pages(content: bytes) -> int:
        try:
            return len(PdfReader(BytesIO(content)).pages)
        except Exception as exc:
            raise ValueError(f"Falha ao ler paginas do PDF: {exc}") from exc
