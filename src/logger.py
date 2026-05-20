import logging
import sys

_logger: logging.Logger | None = None


def _setup() -> logging.Logger:
	global _logger
	if _logger is not None:
		return _logger
	_logger = logging.getLogger('mse1h2026-helper')
	_logger.setLevel(logging.INFO)
	handler = logging.StreamHandler(sys.stderr)
	handler.setLevel(logging.INFO)
	handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))
	_logger.addHandler(handler)
	return _logger


def info(msg: str) -> None:
	_setup().info(msg)


def warning(msg: str) -> None:
	_setup().warning(msg)


def error(msg: str) -> None:
	_setup().error(msg)


def set_quiet(quiet: bool) -> None:
	level = logging.WARNING if quiet else logging.INFO
	_setup().setLevel(level)
	for handler in _setup().handlers:
		handler.setLevel(level)