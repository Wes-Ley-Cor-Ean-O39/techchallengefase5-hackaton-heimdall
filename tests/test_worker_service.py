from heimdail.application.services.worker_service import WorkerService


class Queue:
    def __init__(self):
        self.deleted = []
        self.called = 0

    def receive_messages(self, max_messages, wait_seconds):
        self.called += 1
        if self.called == 1:
            return [{"Body": '{"uploadId":"u1","key":"k"}', "ReceiptHandle": "rh-1"}]
        raise RuntimeError("stop")

    def delete_message(self, receipt_handle):
        self.deleted.append(receipt_handle)


class UseCase:
    def execute(self, body):
        assert body["uploadId"] == "u1"
        return "u1"


def test_process_message_safe_deletes_on_success():
    q = Queue()
    w = WorkerService(q, UseCase(), 1, 1)
    w._process_message_safe({"Body": '{"uploadId":"u1","key":"k"}', "ReceiptHandle": "rh-1"})
    assert q.deleted == ["rh-1"]


def test_run_forever_handles_receive_error(monkeypatch):
    q = Queue()
    w = WorkerService(q, UseCase(), 1, 1)

    monkeypatch.setattr("heimdail.application.services.worker_service.time.sleep", lambda _: (_ for _ in ()).throw(SystemExit))
    try:
        w.run_forever()
    except SystemExit:
        pass

    assert q.called >= 1
