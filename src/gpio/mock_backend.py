"""
Backend GPIO mock para testes sem hardware Raspberry Pi.

Simula as operações de GPIO em software, imprimindo no terminal
cada mudança de estado e permitindo simular botões via teclado.
"""

import threading
from typing import Callable, Optional

from src.gpio.base import GPIOBackend, PinMode, PinState, Edge
from src.utils.logger import get_logger

logger = get_logger("MockGPIO")


class MockGPIOBackend(GPIOBackend):
    """
    Backend GPIO simulado para desenvolvimento e testes locais.

    Mantém estado interno dos pinos e imprime mudanças no terminal.
    Callbacks de interrupção podem ser disparados manualmente via
    simulate_button_press().
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pin_modes: dict[int, PinMode] = {}
        self._pin_states: dict[int, PinState] = {}
        self._callbacks: dict[int, tuple[Edge, Callable[[int], None], int]] = {}
        self._pwm_active: dict[int, tuple[float, float]] = {}  # pin -> (freq, duty)
        logger.info("MockGPIOBackend inicializado (modo simulação)")

    def setup_pin(self, pin: int, mode: PinMode, pull_up_down: Optional[str] = None) -> None:
        with self._lock:
            self._pin_modes[pin] = mode
            self._pin_states[pin] = PinState.LOW
            direction = "INPUT" if mode == PinMode.INPUT else "OUTPUT"
            pull = f" (pull_{pull_up_down})" if pull_up_down else ""
            logger.debug(f"Pin {pin:>2} configurado como {direction}{pull}")

    def write(self, pin: int, state: PinState) -> None:
        with self._lock:
            old_state = self._pin_states.get(pin, PinState.LOW)
            self._pin_states[pin] = state
        if old_state != state:
            state_str = "HIGH" if state == PinState.HIGH else "LOW"
            logger.debug(f"Pin {pin:>2} <- {state_str}")

    def read(self, pin: int) -> PinState:
        with self._lock:
            return self._pin_states.get(pin, PinState.LOW)

    def add_event_detect(
        self,
        pin: int,
        edge: Edge,
        callback: Callable[[int], None],
        debounce_ms: int = 200,
    ) -> None:
        with self._lock:
            self._callbacks[pin] = (edge, callback, debounce_ms)
            logger.debug(f"Pin {pin:>2} evento registrado (edge={edge.name}, debounce={debounce_ms}ms)")

    def remove_event_detect(self, pin: int) -> None:
        with self._lock:
            self._callbacks.pop(pin, None)
            logger.debug(f"Pin {pin:>2} evento removido")

    def pwm_start(self, pin: int, frequency: float, duty_cycle: float) -> None:
        with self._lock:
            self._pwm_active[pin] = (frequency, duty_cycle)
            logger.debug(f"Pin {pin:>2} PWM iniciado (freq={frequency}Hz, duty={duty_cycle}%)")

    def pwm_change_duty_cycle(self, pin: int, duty_cycle: float) -> None:
        with self._lock:
            if pin in self._pwm_active:
                freq, _ = self._pwm_active[pin]
                self._pwm_active[pin] = (freq, duty_cycle)

    def pwm_change_frequency(self, pin: int, frequency: float) -> None:
        with self._lock:
            if pin in self._pwm_active:
                _, duty = self._pwm_active[pin]
                self._pwm_active[pin] = (frequency, duty)

    def pwm_stop(self, pin: int) -> None:
        with self._lock:
            self._pwm_active.pop(pin, None)
            logger.debug(f"Pin {pin:>2} PWM parado")

    def cleanup(self) -> None:
        with self._lock:
            self._pwm_active.clear()
            self._callbacks.clear()
            self._pin_states.clear()
            self._pin_modes.clear()
        logger.info("MockGPIOBackend cleanup realizado")

    # ---- Métodos exclusivos do mock para simulação ----

    def simulate_button_press(self, pin: int) -> None:
        """
        Simula o pressionamento de um botão (borda de subida).
        Dispara o callback registrado, se existir.

        Args:
            pin: Número do pino GPIO do botão.
        """
        with self._lock:
            entry = self._callbacks.get(pin)

        if entry is not None:
            edge, callback, _ = entry
            if edge in (Edge.RISING, Edge.BOTH):
                # Dispara callback em thread separada (simula comportamento RPi.GPIO)
                threading.Thread(
                    target=callback,
                    args=(pin,),
                    daemon=True,
                    name=f"mock-callback-pin{pin}",
                ).start()
        else:
            logger.warning(f"Pin {pin}: nenhum callback registrado para simular botão")

    def get_pin_state(self, pin: int) -> PinState:
        """Retorna o estado atual de um pino (para inspeção em testes)."""
        with self._lock:
            return self._pin_states.get(pin, PinState.LOW)

    def get_output_pins_snapshot(self) -> dict[int, PinState]:
        """Retorna snapshot de todos os pinos de saída e seus estados."""
        with self._lock:
            return {
                pin: state
                for pin, state in self._pin_states.items()
                if self._pin_modes.get(pin) == PinMode.OUTPUT
            }
