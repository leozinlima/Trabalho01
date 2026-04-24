import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

_pwms = {}


def configurar_saida(pino):
    GPIO.setup(pino, GPIO.OUT)
    GPIO.output(pino, GPIO.LOW)


def configurar_entrada(pino, pull="down"):
    if pull == "up":
        GPIO.setup(pino, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    elif pull == "down":
        GPIO.setup(pino, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    else:
        GPIO.setup(pino, GPIO.IN)


def escrever(pino, valor):
    GPIO.output(pino, GPIO.HIGH if valor else GPIO.LOW)


def ligar(pino):
    GPIO.output(pino, GPIO.HIGH)


def desligar(pino):
    GPIO.output(pino, GPIO.LOW)


def ler(pino):
    return 1 if GPIO.input(pino) else 0


def registrar_interrupcao(pino, callback, debounce_ms=200):
    GPIO.add_event_detect(
        pino,
        GPIO.RISING,
        callback=callback,
        bouncetime=debounce_ms,
    )


def remover_interrupcao(pino):
    try:
        GPIO.remove_event_detect(pino)
    except Exception:
        pass


def iniciar_pwm(pino, frequencia, duty=0):
    pwm = GPIO.PWM(pino, frequencia)
    pwm.start(duty)
    _pwms[pino] = pwm


def alterar_duty_pwm(pino, duty):
    if pino in _pwms:
        _pwms[pino].ChangeDutyCycle(duty)


def alterar_frequencia_pwm(pino, frequencia):
    if pino in _pwms:
        _pwms[pino].ChangeFrequency(frequencia)


def parar_pwm(pino):
    if pino in _pwms:
        _pwms[pino].stop()
        del _pwms[pino]


def limpar():
    for pino in list(_pwms.keys()):
        parar_pwm(pino)
    GPIO.cleanup()
