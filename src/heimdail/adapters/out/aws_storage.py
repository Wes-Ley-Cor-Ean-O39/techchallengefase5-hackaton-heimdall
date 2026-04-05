from typing import Any


class S3StorageAdapter:
    _SUPPORTED_TYPES = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "gif": "image/gif",
        "pdf": "application/pdf",
    }

    def __init__(self, s3_client: Any) -> None:
        self._s3_client = s3_client

    def read_document(self, bucket: str, key: str) -> tuple[bytes, str]:
        obj = self._s3_client.get_object(Bucket=bucket, Key=key)
        content = obj["Body"].read()
        extension = key.lower().rsplit(".", 1)[-1] if "." in key else ""
        media_type = self._SUPPORTED_TYPES.get(extension)

        if not media_type:
            raise ValueError(
                "Formato de arquivo nao suportado. Envie imagem/PDF (png, jpg, jpeg, webp, bmp, gif, pdf)."
            )
        return content, media_type
