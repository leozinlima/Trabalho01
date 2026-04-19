"""
Definição centralizada de pinos GPIO e parâmetros de temporização.

Este módulo concentra TODA a configuração de hardware e timing do sistema,
facilitando ajustes sem alterar a lógica de negócio.
"""

from dataclasses import dataclass, field
from enum import IntEnum, auto


# ============================================================================
# Modelo 1 — 3 LEDs Individuais (Cruzamento 1)
# ============================================================================

@dataclass(frozen=True)
class Model1Pins:
    """Pinos GPIO do Modelo 1 (LEDs individuais)."""
    led_green: int = 17
    led_yellow: int = 18
    led_red: int = 23
    button_pedestrian_main: int = 1
    button_pedestrian_cross: int = 12


@dataclass(frozen=True)
class Model1Timing:
    """Temporização do Modelo 1 em segundos."""
    green_duration: float = 10.0
    yellow_duration: float = 2.0
    red_duration: float = 10.0
    green_min_time: float = 5.0  # Tempo mínimo antes de aceitar pedestre


# ============================================================================
# Modelo 2 — Cruzamento Completo (3 bits, Cruzamento 2)
# ============================================================================

@dataclass(frozen=True)
class Model2Pins:
    """Pinos GPIO do Modelo 2 (código de 3 bits)."""
    bit0: int = 24
    bit1: int = 8
    bit2: int = 7
    button_pedestrian_main: int = 25
    button_pedestrian_cross: int = 22


class CrossingState(IntEnum):
    """
    Estados do cruzamento completo (Modelo 2).
    O valor numérico é o código de 3 bits enviado à ESP32.
    """
    MAIN_GREEN_CROSS_RED = 1    # Via Principal verde / Via Cruzamento vermelho
    MAIN_YELLOW_CROSS_RED = 2   # Via Principal amarelo / Via Cruzamento vermelho
    ALL_RED = 4                 # Vermelho total (transição)
    MAIN_RED_CROSS_GREEN = 5    # Via Principal vermelho / Via Cruzamento verde
    MAIN_RED_CROSS_YELLOW = 6   # Via Principal vermelho / Via Cruzamento amarelo


# Sequência de estados do Modelo 2
# 1 -> 2 -> 4 -> 5 -> 6 -> 4 -> 1 -> ...
CROSSING_STATE_SEQUENCE: list[CrossingState] = [
    CrossingState.MAIN_GREEN_CROSS_RED,     # 1
    CrossingState.MAIN_YELLOW_CROSS_RED,    # 2
    CrossingState.ALL_RED,                  # 4
    CrossingState.MAIN_RED_CROSS_GREEN,     # 5
    CrossingState.MAIN_RED_CROSS_YELLOW,    # 6
    CrossingState.ALL_RED,                  # 4
]


@dataclass(frozen=True)
class Model2Timing:
    """Temporização do Modelo 2 em segundos."""
    main_green_min: float = 10.0
    main_green_max: float = 20.0
    cross_green_min: float = 5.0
    cross_green_max: float = 10.0
    yellow_duration: float = 2.0
    all_red_duration: float = 2.0


# ============================================================================
# Configurações Gerais
# ============================================================================

@dataclass(frozen=True)
class ButtonConfig:
    """Configurações de debounce para os botões."""
    debounce_ms: int = 300          # Debounce em milissegundos
    pulse_duration_ms: int = 200    # Duração esperada do pulso (referência)


# Instâncias globais de configuração (imutáveis)
MODEL1_PINS = Model1Pins()
MODEL1_TIMING = Model1Timing()
MODEL2_PINS = Model2Pins()
MODEL2_TIMING = Model2Timing()
BUTTON_CONFIG = ButtonConfig()
