"""
Máquina de estados do Modelo 1 — 3 LEDs Individuais (Cruzamento 1).

Ciclo: Verde (10s) → Amarelo (2s) → Vermelho (10s) → repete
Botões de pedestre podem antecipar a fase verde (após tempo mínimo de 5s).
"""

from __future__ import annotations

import threading
import time
from enum import auto, Enum
from typing import Optional

from src.config import MODEL1_PINS, MODEL1_TIMING, BUTTON_CONFIG, Model1Pins, Model1Timing
from src.gpio.base import GPIOBackend
from src.io_abstractions import DigitalOutput, ButtonInput
from src.utils.logger import get_logger

logger = get_logger("Modelo1")


class TrafficLightState(Enum):
    """Estados possíveis do semáforo do Modelo 1."""
    GREEN = auto()
    YELLOW = auto()
    RED = auto()


class Model1Controller:
    """
    Controlador do Modelo 1 — Semáforo de 3 LEDs individuais.

    Opera em thread própria, controlando o ciclo do semáforo e
    respondendo a botões de pedestre via interrupção.
    """

    def __init__(
        self,
        gpio: GPIOBackend,
        pins: Model1Pins = MODEL1_PINS,
        timing: Model1Timing = MODEL1_TIMING,
    ) -> None:
        self._gpio = gpio
        self._pins = pins
        self._timing = timing

        # Saídas (LEDs)
        self._led_green = DigitalOutput(gpio, pins.led_green, "M1-Verde")
        self._led_yellow = DigitalOutput(gpio, pins.led_yellow, "M1-Amarelo")
        self._led_red = DigitalOutput(gpio, pins.led_red, "M1-Vermelho")

        # Estado atual
        self._state = TrafficLightState.GREEN
        self._state_start_time: float = 0.0
        self._lock = threading.Lock()

        # Sinalização de antecipação por pedestre
        self._pedestrian_requested = threading.Event()

        # Evento para interrupção do sleep (para encerrar ou antecipar)
        self._wake_event = threading.Event()

        # Flag de execução
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Botões de pedestre
        self._btn_main = ButtonInput(
            gpio,
            pins.button_pedestrian_main,
            "M1-Ped.Principal",
            debounce_ms=BUTTON_CONFIG.debounce_ms,
            callback=self._on_pedestrian_button,
        )
        self._btn_cross = ButtonInput(
            gpio,
            pins.button_pedestrian_cross,
            "M1-Ped.Cruzamento",
            debounce_ms=BUTTON_CONFIG.debounce_ms,
            callback=self._on_pedestrian_button,
        )

    def _on_pedestrian_button(self, button: ButtonInput) -> None:
        """Callback chamado quando qualquer botão de pedestre do Modelo 1 é pressionado."""
        timestamp = time.strftime("%H:%M:%S")
        logger.info(
            f"🚶 BOTÃO DETECTADO | Modelo 1 | {button.name} (GPIO {button.pin}) | {timestamp}"
        )

        with self._lock:
            current_state = self._state

        if current_state == TrafficLightState.GREEN:
            self._pedestrian_requested.set()
            self._wake_event.set()  # Acorda o sleep para verificar
            logger.info(f"   → Solicitação de pedestre registrada (estado atual: VERDE)")
        else:
            logger.info(
                f"   → Sem efeito (estado atual: {current_state.name})"
            )

    def _set_leds(self, green: bool, yellow: bool, red: bool) -> None:
        """Define o estado dos 3 LEDs."""
        self._led_green.set_state(green)
        self._led_yellow.set_state(yellow)
        self._led_red.set_state(red)

    def _enter_state(self, state: TrafficLightState) -> None:
        """Transiciona para um novo estado, atualizando LEDs e log."""
        with self._lock:
            self._state = state
            self._state_start_time = time.monotonic()

        if state == TrafficLightState.GREEN:
            self._set_leds(green=True, yellow=False, red=False)
            logger.info("🟢 Modelo 1: VERDE")
        elif state == TrafficLightState.YELLOW:
            self._set_leds(green=False, yellow=True, red=False)
            logger.info("🟡 Modelo 1: AMARELO")
        elif state == TrafficLightState.RED:
            self._set_leds(green=False, yellow=False, red=True)
            logger.info("🔴 Modelo 1: VERMELHO")

    def _interruptible_sleep(self, duration: float) -> bool:
        """
        Dorme por `duration` segundos, mas pode ser interrompido por
        _wake_event (pedestre ou encerramento).

        Returns:
            True se foi interrompido, False se expirou normalmente.
        """
        self._wake_event.clear()
        return self._wake_event.wait(timeout=duration)

    def _run_green_phase(self) -> None:
        """
        Executa a fase verde com suporte a antecipação por pedestre.

        Lógica:
        1. Dorme pelo tempo mínimo (5s). Se pedestre solicitar antes, será
           processado ao final do tempo mínimo.
        2. Após o tempo mínimo, verifica se há pedestre pendente.
           - Se sim: transiciona imediatamente para amarelo.
           - Se não: dorme pelo tempo restante (até 10s total), mas pode
             ser interrompido por pedestre a qualquer momento.
        """
        self._enter_state(TrafficLightState.GREEN)
        self._pedestrian_requested.clear()

        total_duration = self._timing.green_duration
        min_time = self._timing.green_min_time

        # Fase 1: Espera tempo mínimo (5s)
        interrupted = self._interruptible_sleep(min_time)

        if not self._running:
            return

        # Após o tempo mínimo, verifica se há pedestre pendente
        if self._pedestrian_requested.is_set():
            self._pedestrian_requested.clear()
            logger.info("   → Antecipação por pedestre após tempo mínimo")
            return  # Vai para amarelo

        # Fase 2: Espera restante do verde (mais 5s)
        remaining = total_duration - min_time
        if remaining > 0:
            self._interruptible_sleep(remaining)

            if not self._running:
                return

            # Se pedestre solicitou durante o restante
            if self._pedestrian_requested.is_set():
                self._pedestrian_requested.clear()
                logger.info("   → Antecipação por pedestre (restante do verde)")
                return  # Vai para amarelo

    def _run_cycle(self) -> None:
        """Executa um ciclo completo do semáforo."""
        # Verde (com suporte a pedestre)
        self._run_green_phase()
        if not self._running:
            return

        # Amarelo (2s — sem efeito de botão)
        self._enter_state(TrafficLightState.YELLOW)
        self._interruptible_sleep(self._timing.yellow_duration)
        if not self._running:
            return

        # Vermelho (10s — sem efeito de botão, limpa pedestre pendente)
        self._enter_state(TrafficLightState.RED)
        self._pedestrian_requested.clear()
        self._interruptible_sleep(self._timing.red_duration)

    def _main_loop(self) -> None:
        """Loop principal da thread do Modelo 1."""
        logger.info("═══ Modelo 1 iniciado ═══")
        while self._running:
            self._run_cycle()
        # Desliga todos os LEDs ao parar
        self._set_leds(False, False, False)
        logger.info("═══ Modelo 1 encerrado ═══")

    def start(self) -> None:
        """Inicia o controlador em uma thread separada."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop,
            name="Model1-Thread",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Para o controlador de forma limpa."""
        self._running = False
        self._wake_event.set()  # Acorda qualquer sleep em andamento
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        # Cleanup botões
        self._btn_main.cleanup()
        self._btn_cross.cleanup()
        logger.info("Modelo 1: cleanup concluído")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_state(self) -> TrafficLightState:
        with self._lock:
            return self._state
