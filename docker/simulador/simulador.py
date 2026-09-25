"""
Simulador del invernadero del laboratorio.

Publica por MQTT los mismos topics y payloads que el broker central de la
Raspberry Pi (jerarquía invernadero/<nodo>/<magnitud>, números en texto plano,
retain en los sensores) para poder trabajar fuera del laboratorio.

Modelo físico sencillo y acoplado:
  - la temperatura sigue un ciclo diario; el ventilador (Shelly 2) la baja
  - el suelo se seca con el tiempo; la bomba (Shelly 1) lo riega, vacía el
    depósito (sube la distancia del HC-SR04) y aumenta el peso de la maceta

Control del simulador (topics simulador/..., solo en el broker local):
  simulador/fallo/<nodo>       ok | sensor | desconectado
  simulador/deposito/rellenar  (cualquier payload) rellena el depósito
"""

import math
import os
import random
import signal
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USER = os.getenv("MQTT_USER", "simulador")
PASS = os.getenv("MQTT_PASS", "")
VELOCIDAD = float(os.getenv("SIM_VELOCIDAD", "60"))  # 60 -> 1 min real = 1 h simulada
SHELLY_BOMBA = os.getenv("SHELLY_BOMBA", "shellyplug-s-SIM001")
SHELLY_VENTILADOR = os.getenv("SHELLY_VENTILADOR", "shellyplug-s-SIM002")

P = "invernadero"
PERIODO_MAX = 5.0          # s: los ESP32 publican como mínimo cada 5 s
PERIODO_SHELLY = 30.0      # s: los Shelly Gen1 publican potencia cada 30 s
NODOS = ["dht11", "dht22", "balanza", "ultrasonidos", "suelo", "tds", "actuador"]


def log(texto):
    print(f"{datetime.now():%H:%M:%S} {texto}", flush=True)


class Invernadero:
    """Estado físico simulado."""

    def __init__(self):
        ahora = datetime.now()
        self.hora = ahora.hour + ahora.minute / 60   # hora simulada del día
        self.temp = 22.0
        self.hum_aire = 60.0
        self.hum_suelo = 55.0
        self.nivel = 0.8          # depósito: 0 vacío, 1 lleno
        self.voltaje_tds = 1.0
        self.bomba = False
        self.ventilador = False

    def paso(self, dt_real):
        dt_h = dt_real * VELOCIDAD / 3600          # horas simuladas
        self.hora = (self.hora + dt_h) % 24

        # Temperatura: exterior con ciclo diario + efecto invernadero
        exterior = 17 + 7 * math.sin(2 * math.pi * (self.hora - 9) / 24)
        sol = max(0.0, math.sin(math.pi * (self.hora - 7) / 12)) if 7 <= self.hora <= 19 else 0.0
        objetivo = exterior + 6 * sol - (6 if self.ventilador else 0)
        self.temp += (objetivo - self.temp) * min(1.0, dt_h / 0.5)

        # Humedad ambiente: baja cuando sube la temperatura
        objetivo_hum = max(25, min(95, 90 - 1.8 * (self.temp - 12) - (8 if self.ventilador else 0)))
        self.hum_aire += (objetivo_hum - self.hum_aire) * min(1.0, dt_h / 0.5)

        # Suelo: se seca más con calor; la bomba riega si hay agua
        secado = 1.2 * max(0.3, self.temp / 20)                    # %/h
        riego = 15.0 if (self.bomba and self.nivel > 0.02) else 0.0  # %/h
        self.hum_suelo = max(5.0, min(95.0, self.hum_suelo + (riego - secado) * dt_h))

        # Depósito: la bomba lo vacía
        if self.bomba:
            self.nivel = max(0.0, self.nivel - 0.10 * dt_h)

        # Calidad del agua: deriva lenta
        self.voltaje_tds = max(0.3, min(2.3, self.voltaje_tds + random.gauss(0, 0.002)))

    # --- Lecturas tal como las darían los sensores --------------------
    def dht22(self):
        return self.temp + random.gauss(0, 0.1), self.hum_aire + random.gauss(0, 0.3)

    def dht11(self):
        # Menos preciso: resolución de 1 unidad y pequeño sesgo
        return round(self.temp + 0.8), round(self.hum_aire - 2)

    def distancia(self):
        # Sensor en la tapa de un depósito de 40 cm: lleno -> 5 cm, vacío -> 40 cm
        return 5 + (1 - self.nivel) * 35 + random.gauss(0, 0.2)

    def peso(self):
        # Maceta: sustrato + agua retenida
        return 4200 + 12 * self.hum_suelo + random.gauss(0, 0.3)

    def suelo(self):
        # Calibración del firmware: seco = 3000, agua = 1400
        lectura = int(3000 - self.hum_suelo / 100 * 1600 + random.gauss(0, 4))
        humedad = max(0.0, min(100.0, (3000 - lectura) / 1600 * 100))
        return humedad, lectura

    def tds(self):
        # Fórmula DFRobot (25 ºC), la misma que usa el firmware
        v = self.voltaje_tds + random.gauss(0, 0.003)
        ppm = (133.42 * v ** 3 - 255.86 * v ** 2 + 857.39 * v) * 0.5
        return ppm, v


class Canal:
    """Publica un topic con la regla de los ESP32: si cambia >= delta o cada 5 s."""

    def __init__(self, topic, decimales=1, delta=None):
        self.topic = topic
        self.decimales = decimales
        self.delta = delta
        self.ultimo_valor = None
        self.ultimo_t = 0.0

    def debe_publicar(self, valor, ahora):
        if self.ultimo_valor is None or ahora - self.ultimo_t >= PERIODO_MAX:
            return True
        return self.delta is not None and abs(valor - self.ultimo_valor) >= self.delta

    def texto(self, valor):
        return f"{valor:.{self.decimales}f}" if self.decimales else str(int(valor))

    def marcar(self, valor, ahora):
        self.ultimo_valor = valor
        self.ultimo_t = ahora


class Simulador:
    def __init__(self):
        self.inv = Invernadero()
        self.fallo = {nodo: "ok" for nodo in NODOS}
        self.energia = {SHELLY_BOMBA: 0.0, SHELLY_VENTILADOR: 0.0}   # W·min
        self.ultimo_shelly = 0.0
        self.canales = {
            "dht11": [Canal(f"{P}/dht11/temperatura"), Canal(f"{P}/dht11/humedad")],
            "dht22": [Canal(f"{P}/dht22/temperatura"), Canal(f"{P}/dht22/humedad")],
            "balanza": [Canal(f"{P}/balanza/peso", delta=1.0)],
            "ultrasonidos": [Canal(f"{P}/ultrasonidos/distancia", delta=1.0)],
            "suelo": [Canal(f"{P}/suelo/humedad", delta=1.0), Canal(f"{P}/suelo/lectura", decimales=0)],
            "tds": [Canal(f"{P}/tds/tds", delta=2.0), Canal(f"{P}/tds/voltaje", decimales=3)],
        }

        self.cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="simulador-invernadero")
        if USER:
            self.cliente.username_pw_set(USER, PASS)
        self.cliente.on_connect = self.al_conectar
        self.cliente.on_message = self.al_recibir
        self.cliente.reconnect_delay_set(1, 30)

    # --- MQTT ---------------------------------------------------------
    def pub(self, topic, payload, retain=False):
        self.cliente.publish(topic, payload, qos=0, retain=retain)

    def al_conectar(self, cliente, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log(f"Conexión rechazada por el broker: {reason_code}")
            return
        log(f"Conectado a {HOST}:{PORT}")
        cliente.subscribe(f"{P}/shelly/+/relay/0/command")
        cliente.subscribe(f"{P}/shelly/command")
        cliente.subscribe("simulador/#")
        for nodo in NODOS:
            self.pub(f"{P}/{nodo}/online", "0" if self.fallo[nodo] == "desconectado" else "1", retain=True)
        self.publicar_shellies()

    def al_recibir(self, cliente, userdata, msg):
        texto = msg.payload.decode(errors="replace").strip().lower()
        partes = msg.topic.split("/")

        # invernadero/shelly/<id>/relay/0/command
        if msg.topic.endswith("/relay/0/command") and len(partes) == 6:
            self.comando_shelly(partes[2], texto)
        elif msg.topic == f"{P}/shelly/command" and texto == "update":
            self.publicar_shellies()
        elif partes[:2] == ["simulador", "fallo"] and len(partes) == 3:
            self.cambiar_fallo(partes[2], texto)
        elif msg.topic == "simulador/deposito/rellenar":
            self.inv.nivel = 1.0
            log("Depósito rellenado")

    # --- Actuadores -----------------------------------------------------
    def estado_shelly(self, sid):
        return self.inv.bomba if sid == SHELLY_BOMBA else self.inv.ventilador

    def comando_shelly(self, sid, orden):
        if sid not in self.energia or self.fallo["actuador"] != "ok":
            return
        actual = self.estado_shelly(sid)
        nuevo = {"on": True, "off": False, "toggle": not actual}.get(orden)
        if nuevo is None:
            return
        if sid == SHELLY_BOMBA:
            self.inv.bomba = nuevo
        else:
            self.inv.ventilador = nuevo
        log(f"{sid} -> {'on' if nuevo else 'off'}")
        self.publicar_shelly(sid)

    def potencia(self, sid):
        if not self.estado_shelly(sid):
            return 0.0
        base = 35.0 if sid == SHELLY_BOMBA else 22.0
        return base + random.gauss(0, 0.5)

    def publicar_shelly(self, sid):
        base = f"{P}/shelly/{sid}"
        self.pub(f"{base}/online", "true", retain=True)
        self.pub(f"{base}/relay/0", "on" if self.estado_shelly(sid) else "off", retain=True)
        self.pub(f"{base}/relay/0/power", f"{self.potencia(sid):.1f}")
        self.pub(f"{base}/relay/0/energy", f"{self.energia[sid]:.1f}")

    def publicar_shellies(self):
        if self.fallo["actuador"] != "ok":
            return
        for sid in self.energia:
            self.publicar_shelly(sid)

    # --- Fallos ---------------------------------------------------------
    def cambiar_fallo(self, nodo, modo):
        if nodo not in NODOS or modo not in ("ok", "sensor", "desconectado"):
            log(f"Fallo no válido: {nodo}={modo}")
            return
        self.fallo[nodo] = modo
        self.pub(f"{P}/{nodo}/online", "0" if modo == "desconectado" else "1", retain=True)
        log(f"Nodo {nodo}: {modo}")

    # --- Bucle principal ----------------------------------------------
    def lecturas(self):
        inv = self.inv
        return {
            "dht11": inv.dht11(),
            "dht22": inv.dht22(),
            "balanza": (inv.peso(),),
            "ultrasonidos": (inv.distancia(),),
            "suelo": inv.suelo(),
            "tds": inv.tds(),
        }

    def publicar_sensores(self, ahora):
        for nodo, valores in self.lecturas().items():
            if self.fallo[nodo] != "ok":
                continue
            canales = self.canales[nodo]
            # El primer canal decide; los demás se publican a la vez (como en el firmware)
            if not canales[0].debe_publicar(valores[0], ahora):
                continue
            for canal, valor in zip(canales, valores):
                self.pub(canal.topic, canal.texto(valor), retain=True)
                canal.marcar(valor, ahora)

    def ejecutar(self):
        while True:
            try:
                self.cliente.connect(HOST, PORT, keepalive=30)
                break
            except OSError as e:
                log(f"Esperando al broker {HOST}:{PORT} ({e})")
                time.sleep(3)
        self.cliente.loop_start()

        anterior = time.monotonic()
        while True:
            time.sleep(1)
            ahora = time.monotonic()
            dt = ahora - anterior
            anterior = ahora

            self.inv.paso(dt)
            for sid in self.energia:
                self.energia[sid] += self.potencia(sid) * dt / 60
            self.publicar_sensores(ahora)
            if ahora - self.ultimo_shelly >= PERIODO_SHELLY:
                self.publicar_shellies()
                self.ultimo_shelly = ahora

    def detener(self, *_):
        log("Deteniendo simulador")
        for nodo in NODOS:
            self.pub(f"{P}/{nodo}/online", "0", retain=True)
        time.sleep(0.5)
        self.cliente.loop_stop()
        self.cliente.disconnect()
        sys.exit(0)


if __name__ == "__main__":
    sim = Simulador()
    signal.signal(signal.SIGTERM, sim.detener)
    signal.signal(signal.SIGINT, sim.detener)
    log(f"Simulador del invernadero (velocidad x{VELOCIDAD:g}); bomba={SHELLY_BOMBA}, ventilador={SHELLY_VENTILADOR}")
    sim.ejecutar()
