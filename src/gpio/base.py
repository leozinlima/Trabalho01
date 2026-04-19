"""
Interface abstrata para a camada GPIO.

Define o contrato que todos os backends (real e mock) devem seguir.
Suporta:
  - Output digital (liga/desliga)
  - Input por polling
  - Input por interrupção (callback)
  - PWM (preparado para uso futuro)
"""

from abc import ABC, abstractmethod
from enum import IntEnum, auto
from typing import Callable, Optional


class PinMode(IntEnum):
    """Modo de configuração de um pino GPIO."""
    INPUT = auto()
    OUTPUT = auto()


class PinState(IntEnum):
    """Estado lógico de um pino GPIO."""
    LOW = 0
    HIGH = 1


class Edge(IntEnum):
    """Tipo de borda para detecção de interrupção."""
    RISING = auto()
    FALLING = auto()
    BOTH = auto()


class GPIOBackend(ABC):
    """
    Interface abstrata para operações GPIO.

    Todas as implementações (RPi.GPIO, mock, etc.) devem herdar
    desta classe e implementar todos os métodos abstratos.
    """

    @abstractmethod
    def setup_pin(self, pin: int, mode: PinMode, pull_up_down: Optional[str] = None) -> None:
        """
        Configura um pino GPIO.

        Args:
            pin: Número do pino GPIO (BCM).
            mode: INPUT ou OUTPUT.
            pull_up_down: 'up', 'down' ou None para sem pull.
        """
        ...

    @abstractmethod
    def write(self, pin: int, state: PinState) -> None:
        """
        Escreve um estado lógico em um pino de saída.

        Args:
            pin: Número do pino GPIO (BCM).
            state: HIGH ou LOW.
        """
        ...

    @abstractmethod
    def read(self, pin: int) -> PinState:
        """
        Lê o estado atual de um pino de entrada (polling).

        Args:
            pin: Número do pino GPIO (BCM).

        Returns:
            Estado atual do pino (HIGH ou LOW).
        """
        ...

    @abstractmethod
    def add_event_detect(
        self,
        pin: int,
        edge: Edge,
        callback: Callable[[int], None],
        debounce_ms: int = 200,
    ) -> None:
        """
        Registra detecção de evento por interrupção em um pino de entrada.

        Args:
            pin: Número do pino GPIO (BCM).
            edge: Tipo de borda (RISING, FALLING, BOTH).
            callback: Função chamada ao detectar o evento. Recebe o pino como argumento.
            debounce_ms: Tempo de debounce em milissegundos.
        """
        ...

    @abstractmethod
    def remove_event_detect(self, pin: int) -> None:
        """
        Remove a detecção de evento de um pino.

        Args:
            pin: Número do pino GPIO (BCM).
        """
        ...

    @abstractmethod
    def pwm_start(self, pin: int, frequency: float, duty_cycle: float) -> None:
        """
        Inicia PWM em um pino de saída.

        Args:
            pin: Número do pino GPIO (BCM). Deve estar configurado como OUTPUT.
            frequency: Frequência do PWM em Hz.
            duty_cycle: Ciclo de trabalho (0.0 a 100.0).
        """
        ...

    @abstractmethod
    def pwm_change_duty_cycle(self, pin: int, duty_cycle: float) -> None:
        """
        Altera o duty cycle de um PWM ativo.

        Args:
            pin: Número do pino GPIO (BCM).
            duty_cycle: Novo ciclo de trabalho (0.0 a 100.0).
        """
        ...

    @abstractmethod
    def pwm_change_frequency(self, pin: int, frequency: float) -> None:
        """
        Altera a frequência de um PWM ativo.

        Args:
            pin: Número do pino GPIO (BCM).
            frequency: Nova frequência em Hz.
        """
        ...

    @abstractmethod
    def pwm_stop(self, pin: int) -> None:
        """
        Para o PWM em um pino.

        Args:
            pin: Número do pino GPIO (BCM).
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """
        Libera todos os recursos GPIO.
        Deve ser chamado ao encerrar o programa.
        """
        ...
