import base64
from io import BytesIO
from typing import Any

from pypdf import PdfReader


class OpenAiAdapter:
    def __init__(
        self,
        openai_client: Any,
        model: str,
        max_output_tokens: int,
        max_input_bytes: int,
        max_pdf_pages: int,
    ) -> None:
        self._openai_client = openai_client
        self._model = model
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

        input_content = [{"type": "input_text", "text": prompt}]
        if media_type.startswith("image/"):
            b64 = base64.b64encode(content).decode("utf-8")
            input_content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{media_type};base64,{b64}",
                }
            )
        elif media_type == "application/pdf":
            b64 = base64.b64encode(content).decode("utf-8")
            input_content.append(
                {
                    "type": "input_file",
                    "filename": "diagrama-arquitetura.pdf",
                    "file_data": f"data:application/pdf;base64,{b64}",
                }
            )
        else:
            raise ValueError(f"Media type nao suportado para analise: {media_type}")

        response = self._openai_client.responses.create(
            model=self._model,
            input=[{"role": "user", "content": input_content}],
            max_output_tokens=self._max_output_tokens,
        )

        output_text = self._extract_output_text(response)
        if not output_text:
            raise ValueError("Resposta da OpenAI sem texto de saida")

        return {
            "analysis": output_text,
            "confidence": 0.75,
            "strategy_used": "multimodal_openai",
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

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        output_text = getattr(response, "output_text", "")
        if output_text:
            return output_text.strip()

        response_dict = response.model_dump() if hasattr(response, "model_dump") else {}
        for item in response_dict.get("output", []):
            for content in item.get("content", []):
                text = content.get("text", "").strip()
                if text:
                    return text
        return ""
