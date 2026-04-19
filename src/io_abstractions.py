"""
Abstrações de Input/Output sobre a camada GPIO.

Provê classes de alto nível para controlar saídas digitais,
ler entradas e gerenciar botões com debounce por interrupção.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from src.gpio.base import GPIOBackend, PinMode, PinState, Edge
from src.utils.logger import get_logger

logger = get_logger("IO")


class DigitalOutput:
    """
    Saída digital GPIO.

    Encapsula um pino de saída com operações on/off thread-safe.
    """

    def __init__(self, gpio: GPIOBackend, pin: int, name: str = "") -> None:
        self._gpio = gpio
        self._pin = pin
        self._name = name or f"pin{pin}"
        self._state = PinState.LOW
        self._lock = threading.Lock()

        self._gpio.setup_pin(pin, PinMode.OUTPUT)
        self._gpio.write(pin, PinState.LOW)

    @property
    def pin(self) -> int:
        return self._pin

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool:
        with self._lock:
            return self._state == PinState.HIGH

    def on(self) -> None:
        """Liga a saída (HIGH)."""
        with self._lock:
            self._state = PinState.HIGH
            self._gpio.write(self._pin, PinState.HIGH)

    def off(self) -> None:
        """Desliga a saída (LOW)."""
        with self._lock:
            self._state = PinState.LOW
            self._gpio.write(self._pin, PinState.LOW)

    def set_state(self, state: bool) -> None:
        """Define o estado da saída (True=HIGH, False=LOW)."""
        if state:
            self.on()
        else:
            self.off()


class ButtonInput:
    """
    Entrada digital GPIO com detecção por interrupção e debounce.

    Ao detectar uma borda de subida (botão pressionado), dispara
    o callback registrado, respeitando o tempo de debounce.
    """

    def __init__(
        self,
        gpio: GPIOBackend,
        pin: int,
        name: str,
        debounce_ms: int = 300,
        callback: Optional[Callable[["ButtonInput"], None]] = None,
    ) -> None:
        self._gpio = gpio
        self._pin = pin
        self._name = name
        self._debounce_ms = debounce_ms
        self._callback = callback
        self._lock = threading.Lock()
        self._last_press_time: float = 0.0

        # Configura pino como entrada com pull-down (normalmente LOW)
        self._gpio.setup_pin(pin, PinMode.INPUT, pull_up_down="down")

        # Registra detecção de evento por interrupção
        self._gpio.add_event_detect(
            pin,
            Edge.RISING,
            callback=self._on_interrupt,
            debounce_ms=debounce_ms,
        )

    @property
    def pin(self) -> int:
        return self._pin

    @property
    def name(self) -> str:
        return self._name

    def set_callback(self, callback: Callable[["ButtonInput"], None]) -> None:
        """Define ou altera o callback do botão."""
        with self._lock:
            self._callback = callback

    def _on_interrupt(self, channel: int) -> None:
        """Handler de interrupção interno com debounce por software."""
        now = time.monotonic()
        with self._lock:
            elapsed_ms = (now - self._last_press_time) * 1000
            if elapsed_ms < self._debounce_ms:
                return  # Debounce: ignorar disparo muito próximo
            self._last_press_time = now
            cb = self._callback

        if cb is not None:
            cb(self)

    def poll(self) -> PinState:
        """Lê o estado atual do botão por polling."""
        return self._gpio.read(self._pin)

    def cleanup(self) -> None:
        """Remove detecção de evento deste botão."""
        self._gpio.remove_event_detect(self._pin)
