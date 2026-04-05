import json
import logging
import time
from typing import Any, Dict

from heimdail.application.ports import QueuePort
from heimdail.application.use_cases.process_message import ProcessMessageUseCase

LOGGER = logging.getLogger(__name__)


class WorkerService:
    def __init__(
        self,
        queue: QueuePort,
        use_case: ProcessMessageUseCase,
        max_messages: int,
        poll_wait_seconds: int,
    ) -> None:
        self._queue = queue
        self._use_case = use_case
        self._max_messages = max_messages
        self._poll_wait_seconds = poll_wait_seconds

    def run_forever(self) -> None:
        LOGGER.info(
            "Processador iniciado. max_messages=%s poll_wait_seconds=%s",
            self._max_messages,
            self._poll_wait_seconds,
        )

        while True:
            try:
                messages = self._queue.receive_messages(
                    max_messages=self._max_messages,
                    wait_seconds=self._poll_wait_seconds,
                )
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Falha ao ler fila: %s", exc)
                time.sleep(2)
                continue
            if not messages:
                continue

            for message in messages:
                self._process_message_safe(message)

    def _process_message_safe(self, message: Dict[str, Any]) -> None:
        receipt_handle = message.get("ReceiptHandle", "")
        try:
            body = json.loads(message.get("Body", "{}"))
            upload_id = self._use_case.execute(body)
            LOGGER.info("Mensagem processada com sucesso. upload_id=%s", upload_id)
            if receipt_handle:
                self._queue.delete_message(receipt_handle)
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Falha ao processar mensagem: %s", exc)
            # Sem delete: mensagem volta para fila e depois DLQ
            time.sleep(1)
