"""
Utilitário de logging centralizado.

Produz saídas formatadas com timestamp, nome do módulo e nível.
Thread-safe por design do módulo logging padrão.
"""

import logging
import sys
from typing import Optional

_LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(levelname)-5s | %(name)-18s | %(message)s"
_DATE_FORMAT = "%H:%M:%S"
_configured = False


def _configure_root_logger() -> None:
    """Configura o logger raiz uma única vez."""
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    _configured = True


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Retorna um logger configurado com o formato padrão do projeto.

    Args:
        name: Nome do logger (geralmente o nome do módulo/classe).
        level: Nível de log opcional. Se None, herda do root.

    Returns:
        Logger configurado.
    """
    _configure_root_logger()
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
