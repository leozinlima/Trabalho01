import threading
import time

from semaforo.gpio import modulo as gpio
from semaforo.entrada.botao import Botao

LED_VERDE = 17
LED_AMARELO = 18
LED_VERMELHO = 23
BOTAO_PRINCIPAL = 1
BOTAO_CRUZAMENTO = 12

T_VERDE = 10.0
T_VERDE_MIN = 5.0
T_AMARELO = 2.0
T_VERMELHO = 10.0


class Modelo1:
    def __init__(self):
        gpio.configurar_saida(LED_VERDE)
        gpio.configurar_saida(LED_AMARELO)
        gpio.configurar_saida(LED_VERMELHO)

        self._estado = "VERDE"
        self._pedido = threading.Event()
        self._acordar = threading.Event()
        self._rodando = False
        self._thread = None

        self._btn_principal = Botao(
            BOTAO_PRINCIPAL, "Principal", self._apertou
        )
        self._btn_cruzamento = Botao(
            BOTAO_CRUZAMENTO, "Cruzamento", self._apertou
        )

    def iniciar(self):
        if self._rodando:
            return
        self._rodando = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def parar(self):
        self._rodando = False
        self._acordar.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        self._btn_principal.liberar()
        self._btn_cruzamento.liberar()
        gpio.desligar(LED_VERDE)
        gpio.desligar(LED_AMARELO)
        gpio.desligar(LED_VERMELHO)

    def _apertou(self, botao):
        estado = self._estado
        print(f"[Modelo 1] Botao {botao.nome} pressionado (estado: {estado})")
        if estado == "VERDE":
            self._pedido.set()
            self._acordar.set()
            print("[Modelo 1] -> pedido de pedestre registrado")
        else:
            print("[Modelo 1] -> sem efeito")

    def _acender(self, verde, amarelo, vermelho):
        gpio.escrever(LED_VERDE, verde)
        gpio.escrever(LED_AMARELO, amarelo)
        gpio.escrever(LED_VERMELHO, vermelho)

    def _esperar(self, segundos):
        if segundos <= 0:
            return
        self._acordar.clear()
        self._acordar.wait(timeout=segundos)

    def _fase_verde(self):
        self._estado = "VERDE"
        self._pedido.clear()
        self._acender(1, 0, 0)
        print("[Modelo 1] VERDE")

        inicio = time.monotonic()
        while self._rodando:
            restante = T_VERDE_MIN - (time.monotonic() - inicio)
            if restante <= 0:
                break
            self._esperar(restante)
        if not self._rodando:
            return

        if self._pedido.is_set():
            self._pedido.clear()
            print("[Modelo 1] antecipando amarelo (pedestre apos minimo)")
            return

        restante = T_VERDE - (time.monotonic() - inicio)
        if restante > 0:
            self._esperar(restante)
            if self._pedido.is_set():
                self._pedido.clear()
                print("[Modelo 1] antecipando amarelo (pedestre no restante)")

    def _loop(self):
        print("[Modelo 1] iniciado")
        while self._rodando:
            self._fase_verde()
            if not self._rodando:
                break

            self._estado = "AMARELO"
            self._acender(0, 1, 0)
            print("[Modelo 1] AMARELO")
            self._esperar(T_AMARELO)
            if not self._rodando:
                break

            self._estado = "VERMELHO"
            self._acender(0, 0, 1)
            print("[Modelo 1] VERMELHO")
            self._esperar(T_VERMELHO)
        print("[Modelo 1] encerrado")
