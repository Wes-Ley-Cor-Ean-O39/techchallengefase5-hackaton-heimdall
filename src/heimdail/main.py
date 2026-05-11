import logging

from heimdail.config.container import build_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def main() -> None:
    worker = build_worker()
    worker.run_forever()


if __name__ == "__main__":
    main()
