# Controle de Semáforos — Entrega 1

**Fundamentos de Sistemas Embarcados (2026/1)**  
**Data de Entrega:** 27/04/2026

## Visão Geral

Sistema de controle de dois modelos independentes de semáforo para Raspberry Pi via GPIO. Ambos os modelos operam simultaneamente em threads separadas, com suporte a botões de pedestre com debounce por interrupção.

- **Modelo 1** (Cruzamento 1): 3 LEDs individuais (verde, amarelo, vermelho) com ciclo fixo e botões de pedestre.
- **Modelo 2** (Cruzamento 2): Cruzamento completo controlado por código de 3 bits, com dois semáforos (via principal e via de cruzamento) e botões de pedestre independentes.

## Estrutura do Projeto

```
trabalho-1-2026-1-main/
├── requirements.txt              # Dependência: RPi.GPIO
├── README_projeto.md             # Este arquivo
├── src/
│   ├── __init__.py               # Pacote raiz
│   ├── __main__.py               # Permite execução via python -m src
│   ├── main.py                   # Ponto de entrada, CLI, ciclo de vida
│   ├── config.py                 # Pinos GPIO e parâmetros de temporização
│   ├── io_abstractions.py        # DigitalOutput e ButtonInput de alto nível
│   ├── model1.py                 # Máquina de estados do Modelo 1
│   ├── model2.py                 # Máquina de estados do Modelo 2
│   ├── button_simulator.py       # Simulador de botões via teclado (modo mock)
│   ├── gpio/
│   │   ├── __init__.py           # Sub-pacote GPIO
│   │   ├── base.py               # Interface abstrata (ABC) para GPIO
│   │   ├── rpi_backend.py        # Implementação real com RPi.GPIO
│   │   └── mock_backend.py       # Implementação mock para testes locais
│   └── utils/
│       ├── __init__.py           # Sub-pacote utilitários
│       └── logger.py             # Logger centralizado com formatação
```

## Dependências

| Pacote | Versão | Observação |
|--------|--------|------------|
| `RPi.GPIO` | ≥ 0.7.0 | Necessário apenas na Raspberry Pi |
| Python | ≥ 3.10 | Usa type hints modernas (`list[...]`) |

No modo `--mock`, **nenhuma dependência externa** é necessária.

## Instalação

### Na Raspberry Pi

```bash
# Clonar o repositório
git clone <url-do-repositorio>
cd trabalho-1-2026-1-main

# Instalar dependências
pip install -r requirements.txt
```

### Em máquina local (para desenvolvimento/testes)

```bash
cd trabalho-1-2026-1-main
# Nenhuma instalação necessária — use --mock
```

## Execução

```bash
# Rodar ambos os modelos (Raspberry Pi — hardware real)
python3 -m src.main

# Rodar ambos em modo simulação (qualquer máquina)
python3 -m src.main --mock

# Rodar apenas o Modelo 1
python3 -m src.main --model modelo1

# Rodar apenas o Modelo 2
python3 -m src.main --model modelo2

# Rodar apenas o Modelo 1 em simulação
python3 -m src.main --mock --model modelo1

# Ver ajuda
python3 -m src.main --help
```

### Encerramento

Pressione **Ctrl+C** para encerrar o programa. O sistema faz cleanup automático da GPIO.

## Exemplos de CLI

### Modo mock com simulador de botões

```
$ python3 -m src.main --mock
18:32:00.303 | INFO  | Main     | Usando backend GPIO MOCK (simulação)
18:32:00.304 | INFO  | Main     | ╔══════════════════════════════════════════════════╗
18:32:00.304 | INFO  | Main     | ║   Controle de Semáforos — Entrega 1             ║
18:32:00.304 | INFO  | Main     | ║   Fundamentos de Sistemas Embarcados (2026/1)   ║
18:32:00.304 | INFO  | Main     | ╚══════════════════════════════════════════════════╝
...
18:32:00.305 | INFO  | Modelo1  | 🟢 Modelo 1: VERDE
18:32:00.305 | INFO  | Modelo2  | 🟢🔴 Modelo 2: Via Principal VERDE / Via Cruzamento VERMELHA (código=1)
```

No modo mock, pressione as teclas **1, 2, 3, 4** para simular botões de pedestre.

## Pinos GPIO

### Modelo 1 — Cruzamento 1 (LEDs individuais)

| Componente | GPIO | Direção |
|------------|:----:|:-------:|
| LED Verde | 17 | Saída |
| LED Amarelo | 18 | Saída |
| LED Vermelho | 23 | Saída |
| Botão Ped. Principal | 1 | Entrada |
| Botão Ped. Cruzamento | 12 | Entrada |

### Modelo 2 — Cruzamento 2 (3 bits)

| Componente | GPIO | Direção |
|------------|:----:|:-------:|
| Semáforo Bit 0 | 24 | Saída |
| Semáforo Bit 1 | 8 | Saída |
| Semáforo Bit 2 | 7 | Saída |
| Botão Ped. Principal | 25 | Entrada |
| Botão Ped. Cruzamento | 22 | Entrada |

## Observações sobre Raspberry Pi

1. **Modo BCM**: O sistema usa numeração BCM para os pinos GPIO.
2. **Permissões**: Pode ser necessário executar com `sudo` dependendo da configuração do sistema.
3. **Pull-down**: Os botões são configurados com pull-down interno (normalmente LOW).
4. **Cleanup**: A GPIO é limpa automaticamente ao encerrar (Ctrl+C ou SIGTERM).

## Como Testar

1. **Sem hardware**: Use `python3 -m src.main --mock` e pressione teclas 1-4 para simular botões.
2. **Com hardware**: Conecte LEDs e botões conforme as tabelas acima e execute `python3 -m src.main`.
3. **Modelo individual**: Use `--model modelo1` ou `--model modelo2` para testar isoladamente.

## Licença

Projeto acadêmico — Universidade de Brasília — FSE 2026/1.
