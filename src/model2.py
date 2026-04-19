"""
Máquina de estados do Modelo 2 — Cruzamento Completo (3 bits, Cruzamento 2).

Sequência: 1 → 2 → 4 → 5 → 6 → 4 → 1 → ...

Códigos de 3 bits enviados via GPIO controlam ambos os semáforos
do cruzamento (Via Principal e Via de Cruzamento).

Botões de pedestre antecipam a fase verde da via correspondente.
"""

from __future__ import annotations

import threading
import time
from typing import Optional

from src.config import (
    MODEL2_PINS,
    MODEL2_TIMING,
    BUTTON_CONFIG,
    CrossingState,
    CROSSING_STATE_SEQUENCE,
    Model2Pins,
    Model2Timing,
)
from src.gpio.base import GPIOBackend
from src.io_abstractions import DigitalOutput, ButtonInput
from src.utils.logger import get_logger

logger = get_logger("Modelo2")

# Descrição legível dos estados
_STATE_DESCRIPTIONS: dict[CrossingState, str] = {
    CrossingState.MAIN_GREEN_CROSS_RED: "Via Principal VERDE / Via Cruzamento VERMELHA",
    CrossingState.MAIN_YELLOW_CROSS_RED: "Via Principal AMARELA / Via Cruzamento VERMELHA",
    CrossingState.ALL_RED: "VERMELHO TOTAL",
    CrossingState.MAIN_RED_CROSS_GREEN: "Via Principal VERMELHA / Via Cruzamento VERDE",
    CrossingState.MAIN_RED_CROSS_YELLOW: "Via Principal VERMELHA / Via Cruzamento AMARELA",
}

# Emojis para log
_STATE_EMOJIS: dict[CrossingState, str] = {
    CrossingState.MAIN_GREEN_CROSS_RED: "🟢🔴",
    CrossingState.MAIN_YELLOW_CROSS_RED: "🟡🔴",
    CrossingState.ALL_RED: "🔴🔴",
    CrossingState.MAIN_RED_CROSS_GREEN: "🔴🟢",
    CrossingState.MAIN_RED_CROSS_YELLOW: "🔴🟡",
}


class Model2Controller:
    """
    Controlador do Modelo 2 — Cruzamento completo via código de 3 bits.

    Opera em thread própria, percorrendo a sequência de estados e
    respondendo a botões de pedestre de cada via.
    """

    def __init__(
        self,
        gpio: GPIOBackend,
        pins: Model2Pins = MODEL2_PINS,
        timing: Model2Timing = MODEL2_TIMING,
    ) -> None:
        self._gpio = gpio
        self._pins = pins
        self._timing = timing

        # Saídas (3 bits de controle)
        self._bit0 = DigitalOutput(gpio, pins.bit0, "M2-Bit0")
        self._bit1 = DigitalOutput(gpio, pins.bit1, "M2-Bit1")
        self._bit2 = DigitalOutput(gpio, pins.bit2, "M2-Bit2")

        # Estado atual
        self._current_state: CrossingState = CrossingState.MAIN_GREEN_CROSS_RED
        self._state_start_time: float = 0.0
        self._lock = threading.Lock()

        # Pedestre via principal: quer atravessar a principal → precisa que a principal fique vermelha
        # Ou seja, se a principal está verde, o pedestre quer antecipar para amarelo.
        self._ped_main_requested = threading.Event()

        # Pedestre via cruzamento: quer atravessar o cruzamento → precisa que o cruzamento fique vermelho
        # Ou seja, se o cruzamento está verde, o pedestre quer antecipar para amarelo.
        self._ped_cross_requested = threading.Event()

        # Evento para interrupção de sleep
        self._wake_event = threading.Event()

        # Flag de execução
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Botões de pedestre
        self._btn_main = ButtonInput(
            gpio,
            pins.button_pedestrian_main,
            "M2-Ped.Principal",
            debounce_ms=BUTTON_CONFIG.debounce_ms,
            callback=self._on_ped_main_button,
        )
        self._btn_cross = ButtonInput(
            gpio,
            pins.button_pedestrian_cross,
            "M2-Ped.Cruzamento",
            debounce_ms=BUTTON_CONFIG.debounce_ms,
            callback=self._on_ped_cross_button,
        )

    def _on_ped_main_button(self, button: ButtonInput) -> None:
        """
        Callback do botão Pedestre Principal do Modelo 2.
        Solicita antecipação da travessia da via principal.
        Se a via principal está verde → antecipa para amarelo.
        """
        timestamp = time.strftime("%H:%M:%S")
        logger.info(
            f"🚶 BOTÃO DETECTADO | Modelo 2 | {button.name} (GPIO {button.pin}) | {timestamp}"
        )

        with self._lock:
            current = self._current_state

        if current == CrossingState.MAIN_GREEN_CROSS_RED:
            self._ped_main_requested.set()
            self._wake_event.set()
            logger.info("   → Solicitação: antecipar verde da Via Principal")
        else:
            logger.info(f"   → Sem efeito (estado atual: {_STATE_DESCRIPTIONS.get(current, '?')})")

    def _on_ped_cross_button(self, button: ButtonInput) -> None:
        """
        Callback do botão Pedestre Cruzamento do Modelo 2.
        Solicita antecipação da travessia da via de cruzamento.
        Se a via de cruzamento está verde → antecipa para amarelo.
        """
        timestamp = time.strftime("%H:%M:%S")
        logger.info(
            f"🚶 BOTÃO DETECTADO | Modelo 2 | {button.name} (GPIO {button.pin}) | {timestamp}"
        )

        with self._lock:
            current = self._current_state

        if current == CrossingState.MAIN_RED_CROSS_GREEN:
            self._ped_cross_requested.set()
            self._wake_event.set()
            logger.info("   → Solicitação: antecipar verde da Via Cruzamento")
        else:
            logger.info(f"   → Sem efeito (estado atual: {_STATE_DESCRIPTIONS.get(current, '?')})")

    def _write_state_code(self, state: CrossingState) -> None:
        """Escreve o código de 3 bits nos pinos GPIO."""
        code = int(state)
        self._bit0.set_state(bool(code & 0b001))
        self._bit1.set_state(bool(code & 0b010))
        self._bit2.set_state(bool(code & 0b100))

    def _enter_state(self, state: CrossingState) -> None:
        """Transiciona para um novo estado."""
        with self._lock:
            self._current_state = state
            self._state_start_time = time.monotonic()

        self._write_state_code(state)

        emoji = _STATE_EMOJIS.get(state, "")
        desc = _STATE_DESCRIPTIONS.get(state, f"Estado {int(state)}")
        logger.info(f"{emoji} Modelo 2: {desc} (código={int(state)})")

    def _interruptible_sleep(self, duration: float) -> bool:
        """
        Dorme por `duration` segundos, interrompível por _wake_event.

        Returns:
            True se foi interrompido, False se expirou normalmente.
        """
        self._wake_event.clear()
        return self._wake_event.wait(timeout=duration)

    def _get_state_duration(self, state: CrossingState) -> float:
        """Retorna a duração máxima (default) de um estado."""
        if state == CrossingState.MAIN_GREEN_CROSS_RED:
            return self._timing.main_green_max
        elif state == CrossingState.MAIN_RED_CROSS_GREEN:
            return self._timing.cross_green_max
        elif state in (CrossingState.MAIN_YELLOW_CROSS_RED, CrossingState.MAIN_RED_CROSS_YELLOW):
            return self._timing.yellow_duration
        elif state == CrossingState.ALL_RED:
            return self._timing.all_red_duration
        else:
            return 2.0  # fallback

    def _get_min_green_time(self, state: CrossingState) -> float:
        """Retorna o tempo mínimo de verde para estados verdes."""
        if state == CrossingState.MAIN_GREEN_CROSS_RED:
            return self._timing.main_green_min
        elif state == CrossingState.MAIN_RED_CROSS_GREEN:
            return self._timing.cross_green_min
        return 0.0

    def _run_green_phase(self, state: CrossingState) -> None:
        """
        Executa uma fase verde (principal ou cruzamento) com suporte
        a antecipação por pedestre respeitando tempo mínimo.
        """
        self._enter_state(state)

        min_time = self._get_min_green_time(state)
        max_time = self._get_state_duration(state)

        # Determina qual evento de pedestre é relevante
        if state == CrossingState.MAIN_GREEN_CROSS_RED:
            ped_event = self._ped_main_requested
        else:
            ped_event = self._ped_cross_requested

        ped_event.clear()

        # Fase 1: Espera tempo mínimo
        self._interruptible_sleep(min_time)
        if not self._running:
            return

        # Verifica se pedestre solicitou durante tempo mínimo
        if ped_event.is_set():
            ped_event.clear()
            logger.info("   → Antecipação por pedestre após tempo mínimo")
            return

        # Fase 2: Espera restante do verde (interrompível)
        remaining = max_time - min_time
        if remaining > 0:
            self._interruptible_sleep(remaining)
            if not self._running:
                return

            if ped_event.is_set():
                ped_event.clear()
                logger.info("   → Antecipação por pedestre (restante do verde)")
                return

    def _run_fixed_phase(self, state: CrossingState) -> None:
        """Executa uma fase de duração fixa (amarelo ou vermelho total)."""
        self._enter_state(state)
        duration = self._get_state_duration(state)
        self._interruptible_sleep(duration)

    def _run_cycle(self) -> None:
        """
        Executa um ciclo completo do cruzamento.
        Sequência: 1 → 2 → 4 → 5 → 6 → 4 → 1 → ...
        """
        for state in CROSSING_STATE_SEQUENCE:
            if not self._running:
                return

            if state in (CrossingState.MAIN_GREEN_CROSS_RED, CrossingState.MAIN_RED_CROSS_GREEN):
                # Fases verdes: suportam antecipação por pedestre
                self._run_green_phase(state)
            else:
                # Fases fixas: amarelo ou vermelho total
                self._run_fixed_phase(state)

    def _main_loop(self) -> None:
        """Loop principal da thread do Modelo 2."""
        logger.info("═══ Modelo 2 iniciado ═══")
        while self._running:
            self._run_cycle()
        # Desliga todas as saídas ao parar (código 0 seria amarelo/amarelo, preferimos código 4 = tudo vermelho e depois LOW)
        self._write_state_code(CrossingState.ALL_RED)
        self._bit0.off()
        self._bit1.off()
        self._bit2.off()
        logger.info("═══ Modelo 2 encerrado ═══")

    def start(self) -> None:
        """Inicia o controlador em uma thread separada."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop,
            name="Model2-Thread",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Para o controlador de forma limpa."""
        self._running = False
        self._wake_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        # Cleanup botões
        self._btn_main.cleanup()
        self._btn_cross.cleanup()
        logger.info("Modelo 2: cleanup concluído")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_state(self) -> CrossingState:
        with self._lock:
            return self._current_state
