"""
Implementação real do backend GPIO usando RPi.GPIO.

Este módulo só deve ser importado e usado em uma Raspberry Pi com
o pacote RPi.GPIO instalado.
"""

from typing import Callable, Optional

from src.gpio.base import GPIOBackend, PinMode, PinState, Edge


class RpiGPIOBackend(GPIOBackend):
    """Backend GPIO usando a biblioteca RPi.GPIO."""

    def __init__(self) -> None:
        try:
            import RPi.GPIO as GPIO  # type: ignore[import-untyped]
        except ImportError as e:
            raise RuntimeError(
                "RPi.GPIO não está disponível. "
                "Execute em uma Raspberry Pi ou use o backend mock (--mock)."
            ) from e

        self._GPIO = GPIO
        self._GPIO.setmode(GPIO.BCM)
        self._GPIO.setwarnings(False)
        self._pwm_instances: dict[int, object] = {}

    def setup_pin(self, pin: int, mode: PinMode, pull_up_down: Optional[str] = None) -> None:
        gpio_mode = self._GPIO.OUT if mode == PinMode.OUTPUT else self._GPIO.IN

        pud = self._GPIO.PUD_OFF
        if pull_up_down == "up":
            pud = self._GPIO.PUD_UP
        elif pull_up_down == "down":
            pud = self._GPIO.PUD_DOWN

        if mode == PinMode.INPUT:
            self._GPIO.setup(pin, gpio_mode, pull_up_down=pud)
        else:
            self._GPIO.setup(pin, gpio_mode)

    def write(self, pin: int, state: PinState) -> None:
        self._GPIO.output(pin, self._GPIO.HIGH if state == PinState.HIGH else self._GPIO.LOW)

    def read(self, pin: int) -> PinState:
        value = self._GPIO.input(pin)
        return PinState.HIGH if value else PinState.LOW

    def add_event_detect(
        self,
        pin: int,
        edge: Edge,
        callback: Callable[[int], None],
        debounce_ms: int = 200,
    ) -> None:
        edge_map = {
            Edge.RISING: self._GPIO.RISING,
            Edge.FALLING: self._GPIO.FALLING,
            Edge.BOTH: self._GPIO.BOTH,
        }
        gpio_edge = edge_map[edge]
        self._GPIO.add_event_detect(
            pin,
            gpio_edge,
            callback=callback,
            bouncetime=debounce_ms,
        )

    def remove_event_detect(self, pin: int) -> None:
        try:
            self._GPIO.remove_event_detect(pin)
        except ValueError:
            pass  # Pino não tinha evento registrado

    def pwm_start(self, pin: int, frequency: float, duty_cycle: float) -> None:
        pwm = self._GPIO.PWM(pin, frequency)
        pwm.start(duty_cycle)
        self._pwm_instances[pin] = pwm

    def pwm_change_duty_cycle(self, pin: int, duty_cycle: float) -> None:
        pwm = self._pwm_instances.get(pin)
        if pwm is not None:
            pwm.ChangeDutyCycle(duty_cycle)  # type: ignore[union-attr]

    def pwm_change_frequency(self, pin: int, frequency: float) -> None:
        pwm = self._pwm_instances.get(pin)
        if pwm is not None:
            pwm.ChangeFrequency(frequency)  # type: ignore[union-attr]

    def pwm_stop(self, pin: int) -> None:
        pwm = self._pwm_instances.pop(pin, None)
        if pwm is not None:
            pwm.stop()  # type: ignore[union-attr]

    def cleanup(self) -> None:
        for pin in list(self._pwm_instances.keys()):
            self.pwm_stop(pin)
        self._GPIO.cleanup()
