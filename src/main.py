"""
Ponto de entrada principal do sistema de controle de semáforos.

Gerencia o ciclo de vida dos controladores (Modelo 1 e Modelo 2),
trata sinais de encerramento e provê a interface de linha de comando.
"""

from __future__ import annotations

import argparse
import signal
import sys
import threading
import time
from typing import Optional

from src.gpio.base import GPIOBackend
from src.model1 import Model1Controller
from src.model2 import Model2Controller
from src.utils.logger import get_logger

logger = get_logger("Main")


class TrafficSystem:
    """
    Gerenciador principal do sistema de semáforos.

    Coordena a inicialização, execução e encerramento dos controladores.
    """

    def __init__(self, gpio: GPIOBackend) -> None:
        self._gpio = gpio
        self._model1: Optional[Model1Controller] = None
        self._model2: Optional[Model2Controller] = None
        self._shutdown_event = threading.Event()

    def start(self, run_model1: bool = True, run_model2: bool = True) -> None:
        """
        Inicia os controladores selecionados.

        Args:
            run_model1: Se True, inicia o Modelo 1.
            run_model2: Se True, inicia o Modelo 2.
        """
        logger.info("╔══════════════════════════════════════════════════╗")
        logger.info("║   Controle de Semáforos — Entrega 1             ║")
        logger.info("║   Fundamentos de Sistemas Embarcados (2026/1)   ║")
        logger.info("╚══════════════════════════════════════════════════╝")
        logger.info("")

        if run_model1:
            logger.info("Iniciando Modelo 1 (3 LEDs — Cruzamento 1)...")
            self._model1 = Model1Controller(self._gpio)
            self._model1.start()

        if run_model2:
            logger.info("Iniciando Modelo 2 (Cruzamento completo — Cruzamento 2)...")
            self._model2 = Model2Controller(self._gpio)
            self._model2.start()

        active = []
        if run_model1:
            active.append("Modelo 1")
        if run_model2:
            active.append("Modelo 2")

        logger.info("")
        logger.info(f"Sistema ativo: {', '.join(active)}")
        logger.info("Pressione Ctrl+C para encerrar.")
        logger.info("─" * 52)

    def wait(self) -> None:
        """Bloqueia até que o shutdown seja solicitado (Ctrl+C)."""
        try:
            while not self._shutdown_event.is_set():
                self._shutdown_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            pass

    def shutdown(self) -> None:
        """Encerra todos os controladores e limpa recursos GPIO."""
        logger.info("")
        logger.info("─" * 52)
        logger.info("Encerrando sistema...")

        if self._model1 is not None:
            self._model1.stop()

        if self._model2 is not None:
            self._model2.stop()

        self._gpio.cleanup()
        logger.info("GPIO cleanup realizado. Sistema encerrado com sucesso.")
        self._shutdown_event.set()

    def request_shutdown(self) -> None:
        """Solicita encerramento do sistema (chamado por signal handlers)."""
        self._shutdown_event.set()


def _create_gpio_backend(use_mock: bool) -> GPIOBackend:
    """Cria o backend GPIO apropriado."""
    if use_mock:
        from src.gpio.mock_backend import MockGPIOBackend
        logger.info("Usando backend GPIO MOCK (simulação)")
        return MockGPIOBackend()
    else:
        from src.gpio.rpi_backend import RpiGPIOBackend
        logger.info("Usando backend GPIO RPi.GPIO (hardware real)")
        return RpiGPIOBackend()


def _parse_args() -> argparse.Namespace:
    """Parse dos argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Controle de Semáforos — Entrega 1 (FSE 2026/1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m src.main                    # Roda ambos os modelos (hardware real)
  python -m src.main --mock             # Roda ambos em modo simulação
  python -m src.main --model modelo1    # Roda apenas o Modelo 1
  python -m src.main --model modelo2    # Roda apenas o Modelo 2
  python -m src.main --model ambos      # Roda ambos (explícito)
  python -m src.main --mock --model modelo1  # Modelo 1 em simulação
        """,
    )

    parser.add_argument(
        "--model",
        choices=["modelo1", "modelo2", "ambos"],
        default="ambos",
        help="Qual modelo executar (default: ambos)",
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        default=False,
        help="Usar backend GPIO mock (para testes sem Raspberry Pi)",
    )

    return parser.parse_args()


def main() -> None:
    """Função principal do programa."""
    args = _parse_args()

    # Cria backend GPIO
    gpio = _create_gpio_backend(args.mock)

    # Determina quais modelos rodar
    run_m1 = args.model in ("modelo1", "ambos")
    run_m2 = args.model in ("modelo2", "ambos")

    # Cria e inicia o sistema
    system = TrafficSystem(gpio)

    # Simulador de botões (apenas em modo mock)
    btn_sim = None
    if args.mock:
        from src.gpio.mock_backend import MockGPIOBackend
        from src.button_simulator import ButtonSimulator
        if isinstance(gpio, MockGPIOBackend):
            btn_sim = ButtonSimulator(gpio)

    # Registra handlers de sinal para encerramento limpo
    def signal_handler(signum: int, frame: object) -> None:
        logger.info(f"\nSinal recebido ({signal.Signals(signum).name}). Encerrando...")
        system.request_shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        system.start(run_model1=run_m1, run_model2=run_m2)

        # Inicia simulador de botões se em modo mock
        if btn_sim is not None:
            btn_sim.start()

        system.wait()
    finally:
        if btn_sim is not None:
            btn_sim.stop()
        system.shutdown()


if __name__ == "__main__":
    main()
