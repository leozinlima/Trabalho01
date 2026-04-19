"""
Camada de abstração de GPIO.

Provê interfaces e implementações para input/output digital e PWM,
permitindo troca de backend (RPi.GPIO real vs mock para testes).
"""

from src.gpio.base import GPIOBackend, PinMode, PinState, Edge
from src.gpio.rpi_backend import RpiGPIOBackend
from src.gpio.mock_backend import MockGPIOBackend

__all__ = [
    "GPIOBackend",
    "PinMode",
    "PinState",
    "Edge",
    "RpiGPIOBackend",
    "MockGPIOBackend",
]
