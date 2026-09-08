"""Shared logging configuration (project prompt section 7).

NEVER log secret keys or shared secrets. Use safe identifiers
(session IDs, device IDs) as placeholders instead.
"""
import logging


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
