[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/Uh9jPYwa)

*Leonardo de Melo Lima - 222037700*
*Joao Victor Marques Reis de Miranda - 200058576*

# Controle de Semaforos - Entrega 1 (FSE 2026/1)

Implementacao em Python da Entrega 1 do Trabalho 1 da disciplina
**Fundamentos de Sistemas Embarcados (2026/1)**.

O programa controla, simultaneamente, dois modelos de semaforo
independentes em uma Raspberry Pi:

- **Modelo 1 (Cruzamento 1):** 3 LEDs individuais ligados diretamente em
  3 pinos GPIO.
- **Modelo 2 (Cruzamento 2):** cruzamento completo controlado por um
  codigo binario de 3 bits em 3 pinos GPIO.

Cada modelo possui dois botoes de pedestre independentes com tratamento
de debounce e log imediato no terminal.

## Estrutura

```
.
├── README.md
├── requirements.txt
└── semaforo/                   # pacote principal
    ├── __init__.py
    ├── __main__.py             # permite: python -m semaforo
    ├── main.py                 # ponto de entrada + CLI
    ├── gpio/                   # pacote — modulo GPIO
    │   ├── __init__.py
    │   └── modulo.py           # entrada/saida, interrupcao, PWM
    ├── entrada/                # pacote — entradas
    │   ├── __init__.py
    │   └── botao.py            # botao com debounce
    └── modelos/                # pacote — maquinas de estado
        ├── __init__.py
        ├── modelo1.py          # semaforo de 3 LEDs
        └── modelo2.py          # cruzamento em 3 bits
```

## Pinos (numeracao BCM)

### Modelo 1 - Cruzamento 1

| Componente            | GPIO |
|-----------------------|:----:|
| LED Verde             | 17   |
| LED Amarelo           | 18   |
| LED Vermelho          | 23   |
| Botao Pedestre Princ. | 1    |
| Botao Pedestre Cruz.  | 12   |

### Modelo 2 - Cruzamento 2

| Componente            | GPIO |
|-----------------------|:----:|
| Bit 0 (LSB)           | 24   |
| Bit 1                 | 8    |
| Bit 2 (MSB)           | 7    |
| Botao Pedestre Princ. | 25   |
| Botao Pedestre Cruz.  | 22   |

## Temporizacao

### Modelo 1

| Fase            | Duracao |
|-----------------|:-------:|
| Verde           | 10 s    |
| Verde (minimo)  | 5 s     |
| Amarelo         | 2 s     |
| Vermelho        | 10 s    |

### Modelo 2

| Fase                             | Duracao |
|----------------------------------|:-------:|
| Via Principal verde (min - max)  | 10 - 20 s |
| Via Cruzamento verde (min - max) | 5 - 10 s  |
| Amarelo                          | 2 s      |
| Vermelho total                   | 2 s      |

Sequencia: `1 -> 2 -> 4 -> 5 -> 6 -> 4 -> 1 -> ...`

## Comportamento dos botoes

- Sinal normalmente em baixa; ativo em alta por ~200 ms.
- Debounce de 300 ms (bouncetime do RPi.GPIO + debounce em software).
- A mensagem do botao e impressa imediatamente no terminal.

### Modelo 1

- Em VERDE, se ja se passaram 5 s: antecipa o amarelo.
- Em VERDE, se passaram menos de 5 s: aguarda completar o minimo e
  entao antecipa.
- Em AMARELO ou VERMELHO: apenas registra o aperto (sem efeito).

### Modelo 2

- Botao **Principal** no codigo 1 (via principal verde): antecipa o
  amarelo da via principal respeitando o minimo de 10 s.
- Botao **Cruzamento** no codigo 5 (via cruzamento verde): antecipa o
  amarelo da via de cruzamento respeitando o minimo de 5 s.
- Nos demais estados: apenas registra o aperto.

## Instalacao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Em algumas versoes do Raspberry Pi OS, instalar via APT
(`sudo apt install python3-rpi.gpio`) ou executar com `sudo` para ter
acesso a GPIO.

## Execucao

```bash
# Ambos os modelos (padrao)
python -m semaforo

# Apenas o Modelo 1
python -m semaforo --modo modelo1

# Apenas o Modelo 2
python -m semaforo --modo modelo2
```

Use **Ctrl+C** para encerrar. O sistema para as threads, libera as
interrupcoes dos botoes e desliga todas as saidas em LOW.

> **Atencao:** o codigo **nao** chama `GPIO.cleanup()` no encerramento.
> `cleanup()` reverte todos os pinos para `INPUT` em alta impedancia,
> deixando-os flutuantes. Isso faz o Dashboard do ThingsBoard "piscar"
> porque ele passa a ler valores aleatorios das GPIOs. Em vez disso,
> as saidas sao desligadas explicitamente em LOW pelos `parar()` de cada
> modelo, e as entradas seguem com `pull-down` configurado.
