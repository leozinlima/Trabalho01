import threading
import time

import gpio_modulo as gpio
from botao import Botao

BIT0 = 24
BIT1 = 8
BIT2 = 7
BOTAO_PRINCIPAL = 25
BOTAO_CRUZAMENTO = 22

VERDE_PRINC_MIN = 10.0
VERDE_PRINC_MAX = 20.0
VERDE_CRUZ_MIN = 5.0
VERDE_CRUZ_MAX = 10.0
T_AMARELO = 2.0
T_VERMELHO_TOTAL = 2.0

SEQUENCIA = (1, 2, 4, 5, 6, 4)

NOMES = {
    1: "Principal VERDE / Cruzamento VERMELHO",
    2: "Principal AMARELO / Cruzamento VERMELHO",
    4: "VERMELHO TOTAL",
    5: "Principal VERMELHO / Cruzamento VERDE",
    6: "Principal VERMELHO / Cruzamento AMARELO",
}


class Modelo2:
    def __init__(self):
        gpio.configurar_saida(BIT0)
        gpio.configurar_saida(BIT1)
        gpio.configurar_saida(BIT2)

        self._codigo = 0
        self._pedido_principal = threading.Event()
        self._pedido_cruzamento = threading.Event()
        self._acordar = threading.Event()
        self._rodando = False
        self._thread = None

        self._btn_principal = Botao(
            BOTAO_PRINCIPAL, "Principal", self._apertou_principal
        )
        self._btn_cruzamento = Botao(
            BOTAO_CRUZAMENTO, "Cruzamento", self._apertou_cruzamento
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
        self._escrever(0)
        gpio.desligar(BIT0)
        gpio.desligar(BIT1)
        gpio.desligar(BIT2)

    def _apertou_principal(self, _botao):
        codigo = self._codigo
        print(f"[Modelo 2] Botao Principal pressionado (codigo atual: {codigo})")
        if codigo == 1:
            self._pedido_principal.set()
            self._acordar.set()
            print("[Modelo 2] -> pedido via Principal registrado")
        else:
            print("[Modelo 2] -> sem efeito")

    def _apertou_cruzamento(self, _botao):
        codigo = self._codigo
        print(f"[Modelo 2] Botao Cruzamento pressionado (codigo atual: {codigo})")
        if codigo == 5:
            self._pedido_cruzamento.set()
            self._acordar.set()
            print("[Modelo 2] -> pedido via Cruzamento registrado")
        else:
            print("[Modelo 2] -> sem efeito")

    def _escrever(self, codigo):
        gpio.escrever(BIT0, codigo & 1)
        gpio.escrever(BIT1, (codigo >> 1) & 1)
        gpio.escrever(BIT2, (codigo >> 2) & 1)
        self._codigo = codigo

    def _esperar(self, segundos):
        if segundos <= 0:
            return
        self._acordar.clear()
        self._acordar.wait(timeout=segundos)

    def _anunciar(self, codigo):
        nome = NOMES.get(codigo, "?")
        print(f"[Modelo 2] {nome} (codigo {codigo})")

    def _fase_verde(self, codigo, minimo, maximo, evento):
        self._escrever(codigo)
        evento.clear()
        self._anunciar(codigo)

        inicio = time.monotonic()
        while self._rodando:
            restante = minimo - (time.monotonic() - inicio)
            if restante <= 0:
                break
            self._esperar(restante)
        if not self._rodando:
            return

        if evento.is_set():
            evento.clear()
            print("[Modelo 2] antecipando amarelo (pedestre apos minimo)")
            return

        restante = maximo - (time.monotonic() - inicio)
        if restante > 0:
            self._esperar(restante)
            if evento.is_set():
                evento.clear()
                print("[Modelo 2] antecipando amarelo (pedestre no restante)")

    def _fase_fixa(self, codigo, duracao):
        self._escrever(codigo)
        self._anunciar(codigo)
        self._esperar(duracao)

    def _loop(self):
        print("[Modelo 2] iniciado")
        while self._rodando:
            for codigo in SEQUENCIA:
                if not self._rodando:
                    break
                if codigo == 1:
                    self._fase_verde(
                        1,
                        VERDE_PRINC_MIN,
                        VERDE_PRINC_MAX,
                        self._pedido_principal,
                    )
                elif codigo == 5:
                    self._fase_verde(
                        5,
                        VERDE_CRUZ_MIN,
                        VERDE_CRUZ_MAX,
                        self._pedido_cruzamento,
                    )
                elif codigo in (2, 6):
                    self._fase_fixa(codigo, T_AMARELO)
                elif codigo == 4:
                    self._fase_fixa(codigo, T_VERMELHO_TOTAL)
        print("[Modelo 2] encerrado")
