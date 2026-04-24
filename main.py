import argparse
import signal
import threading

import gpio_modulo as gpio
from modelo1 import Modelo1
from modelo2 import Modelo2


def main():
    parser = argparse.ArgumentParser(
        description="Controle de Semaforos - Entrega 1 (FSE 2026/1)"
    )
    parser.add_argument(
        "--modo",
        choices=["ambos", "modelo1", "modelo2"],
        default="ambos",
        help="Qual modelo executar (padrao: ambos)",
    )
    args = parser.parse_args()

    m1 = None
    m2 = None

    if args.modo in ("ambos", "modelo1"):
        m1 = Modelo1()
        m1.iniciar()

    if args.modo in ("ambos", "modelo2"):
        m2 = Modelo2()
        m2.iniciar()

    print("Sistema iniciado. Pressione Ctrl+C para encerrar.")

    encerrar = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: encerrar.set())
    signal.signal(signal.SIGTERM, lambda *_: encerrar.set())

    try:
        while not encerrar.is_set():
            encerrar.wait(timeout=1.0)
    except KeyboardInterrupt:
        pass

    print("\nEncerrando...")
    if m1 is not None:
        m1.parar()
    if m2 is not None:
        m2.parar()
    gpio.limpar()
    print("Encerrado.")


if __name__ == "__main__":
    main()
