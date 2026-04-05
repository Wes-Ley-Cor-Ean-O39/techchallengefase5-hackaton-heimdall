import logging

from heimdail.config.container import build_worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def main() -> None:
    worker = build_worker()
    worker.run_forever()


if __name__ == "__main__":
    main()
