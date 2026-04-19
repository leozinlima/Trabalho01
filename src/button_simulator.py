"""
Simulador interativo de botões para o backend mock.

Permite simular pressionamento de botões via teclado durante
a execução do sistema em modo mock.
"""

from __future__ import annotations

import threading
import time
from typing import Optional

from src.gpio.mock_backend import MockGPIOBackend
from src.config import MODEL1_PINS, MODEL2_PINS
from src.utils.logger import get_logger

logger = get_logger("Simulador")

# Mapeamento de tecla -> (pino GPIO, descrição)
_KEY_MAP: dict[str, tuple[int, str]] = {
    "1": (MODEL1_PINS.button_pedestrian_main, "M1 - Ped. Principal"),
    "2": (MODEL1_PINS.button_pedestrian_cross, "M1 - Ped. Cruzamento"),
    "3": (MODEL2_PINS.button_pedestrian_main, "M2 - Ped. Principal"),
    "4": (MODEL2_PINS.button_pedestrian_cross, "M2 - Ped. Cruzamento"),
}


class ButtonSimulator:
    """
    Thread que lê entrada do teclado para simular botões no modo mock.

    Teclas:
        1 = Modelo 1 / Pedestre Principal (GPIO 1)
        2 = Modelo 1 / Pedestre Cruzamento (GPIO 12)
        3 = Modelo 2 / Pedestre Principal (GPIO 25)
        4 = Modelo 2 / Pedestre Cruzamento (GPIO 22)
        q = Sair
    """

    def __init__(self, mock_gpio: MockGPIOBackend) -> None:
        self._gpio = mock_gpio
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Inicia a thread do simulador de botões."""
        self._running = True
        self._thread = threading.Thread(
            target=self._input_loop,
            name="ButtonSimulator-Thread",
            daemon=True,
        )
        self._thread.start()
        self._print_help()

    def _print_help(self) -> None:
        """Imprime instruções do simulador."""
        logger.info("")
        logger.info("╔══════════════════════════════════════════════════╗")
        logger.info("║  Simulador de Botões (modo mock)                ║")
        logger.info("║                                                 ║")
        logger.info("║  Tecla 1 → M1 Pedestre Principal   (GPIO  1)   ║")
        logger.info("║  Tecla 2 → M1 Pedestre Cruzamento  (GPIO 12)   ║")
        logger.info("║  Tecla 3 → M2 Pedestre Principal   (GPIO 25)   ║")
        logger.info("║  Tecla 4 → M2 Pedestre Cruzamento  (GPIO 22)   ║")
        logger.info("║  Tecla q → Encerrar                            ║")
        logger.info("╚══════════════════════════════════════════════════╝")
        logger.info("")

    def _input_loop(self) -> None:
        """Loop de leitura de teclado."""
        while self._running:
            try:
                key = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if key == "q":
                logger.info("Simulador: Comando de saída recebido")
                break

            entry = _KEY_MAP.get(key)
            if entry is not None:
                pin, desc = entry
                logger.info(f"▶ Simulando botão: {desc} (GPIO {pin})")
                self._gpio.simulate_button_press(pin)
            elif key:
                logger.warning(f"Tecla '{key}' não reconhecida. Use 1, 2, 3, 4 ou q.")

    def stop(self) -> None:
        """Para o simulador."""
        self._running = False
