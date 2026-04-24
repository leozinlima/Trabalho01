import threading
import time

import gpio_modulo as gpio


class Botao:
    def __init__(self, pino, nome, callback, debounce_ms=300):
        self.pino = pino
        self.nome = nome
        self._callback = callback
        self._debounce = debounce_ms / 1000.0
        self._ultimo = 0.0
        self._lock = threading.Lock()

        gpio.configurar_entrada(pino, pull="down")
        gpio.registrar_interrupcao(pino, self._borda, debounce_ms=debounce_ms)

    def _borda(self, _canal):
        agora = time.monotonic()
        with self._lock:
            if agora - self._ultimo < self._debounce:
                return
            self._ultimo = agora
        try:
            self._callback(self)
        except Exception as e:
            print(f"[Botao {self.nome}] erro no callback: {e}")

    def liberar(self):
        gpio.remover_interrupcao(self.pino)
