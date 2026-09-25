# Red MQTT del invernadero (práctica anterior, versión desplegada)

Fuente: `.claude/documentacion practica 1/Apuntes_laboratorioPracticas2 (1).zip` → `mqtt-esp/` (sketches del 18-21 sep 2026). Es la versión desplegada. La carpeta `Homeassistant/` (firmware genérico `casa/<deviceId>/...` y el caso de uso teórico `invernadero/...`) es anterior y **no** está desplegada.

No copiar contraseñas (Wi-Fi, brokers) en los materiales publicados del curso: remitir a "credenciales del laboratorio".

## Arquitectura

- Cada ESP32 ejecuta **su propio broker MQTT embebido** (`sMQTTBroker`, MQTT 3.1.1, puerto 1883, sin usuario ni TLS) y publica sus lecturas en él.
- Modo AP+STA: cada nodo crea su propia Wi-Fi (broker en `192.168.4.1`) y además se une al router del aula (`192.168.0.0/24`) con IP fija.
- Uso "conjunto": el PC en la Wi-Fi del router alcanza todos los brokers por IP.
- **Decisión del curso:** la Raspberry Pi (IP propuesta `192.168.0.10`) ejecuta **Mosquitto como broker central** con un *bridge* a cada ESP32. Los alumnos se conectan **solo a la RPi** (usuario `alumno`, ACL) y usan la jerarquía **`invernadero/<nodo>/<magnitud>`**. Configuración en `rpi/` (ver `rpi/README.md`).
- **En todos los materiales del curso usa los topics `invernadero/...` de la tabla siguiente**, no los originales de los ESP32. El simulador publica exactamente estos topics.

## Topics del curso (broker de la RPi)

| Topic | Payload | Origen ESP32 |
|-------|---------|--------------|
| `invernadero/dht11/temperatura`, `invernadero/dht11/humedad` | ºC, % | `sensorTHbroker/...` |
| `invernadero/dht22/temperatura`, `invernadero/dht22/humedad` | ºC, % | `sensorTH22broker/...` |
| `invernadero/balanza/peso` | g | `balanzaHXbroker/peso` |
| `invernadero/ultrasonidos/distancia` | cm | `hcSr04broker/distancia` |
| `invernadero/suelo/humedad`, `invernadero/suelo/lectura` | %, ADC | `sueloCAPbroker/...` |
| `invernadero/tds/tds`, `invernadero/tds/voltaje` | ppm, V | `tdsMeterbroker/...` |
| `invernadero/shelly/<id>/relay/0` (`on`/`off`), `.../relay/0/power`, `.../relay/0/energy`, `invernadero/shelly/<id>/online` | | `shellies/<id>/...` |
| `invernadero/shelly/<id>/relay/0/command` ← `on`/`off`/`toggle`; `invernadero/shelly/command` ← `update` | | hacia `shellies/...` |
| `invernadero/<nodo>/online` | `1`/`0` (retained) | generado por la RPi: estado del puente |

`<nodo>` ∈ `dht11`, `dht22`, `balanza`, `ultrasonidos`, `suelo`, `tds`, `actuador`. `online` indica que la RPi alcanza el ESP32, **no** que el sensor funcione: el fallo del sensor se detecta por ausencia de mensajes (watchdog).

Permisos del usuario `alumno`: lectura de `invernadero/#` y `$SYS/#`; escritura solo en los comandos de los Shelly; lectura y escritura en `alumnos/#`. Cada alumno debe usar un Client ID único.

## Topics originales en los ESP32 (solo referencia)

Todos los payloads son **números en texto plano** (no JSON), 1 decimal salvo que se indique. Sensores: QoS 0, `retain=true`, sin LWT ni topic de estado, sin topics de comandos.

| Nodo | IP | Topic | Payload | Publicación |
|------|----|-------|---------|-------------|
| TH DHT11 (ESP32-S3) | 192.168.0.122 | `sensorTHbroker/temperatura` | `23.4` (ºC) | cada 5 s |
| | | `sensorTHbroker/humedad` | `58.2` (%) | cada 5 s |
| TH DHT22 (ESP32-S3) | 192.168.0.123 | `sensorTH22broker/temperatura` | `23.4` (ºC) | cada 5 s |
| | | `sensorTH22broker/humedad` | `58.2` (%) | cada 5 s |
| Balanza HX711 | 192.168.0.121 | `balanzaHXbroker/peso` | `534.2` (g) | Δ≥1 g o cada 5 s |
| Distancia HC-SR04 | 192.168.0.120 | `hcSr04broker/distancia` | `12.3` (cm, 2-450) | Δ≥1 cm o cada 5 s |
| Humedad suelo capacitivo v1.2 | 192.168.0.130 | `sueloCAPbroker/humedad` | `42.5` (%) | Δ≥1 % o cada 5 s |
| | | `sueloCAPbroker/lectura` | `2350` (ADC 0-4095, entero) | junto con humedad |
| Calidad agua TDS V1.0 | 192.168.0.140 | `tdsMeterbroker/tds` | `367.5` (ppm) | Δ≥2 ppm o cada 5 s |
| | | `tdsMeterbroker/voltaje` | `1.023` (V, 3 decimales) | junto con tds |

Si una lectura falla (NaN, sin eco, sensor desconectado) el nodo **no publica**: la caída solo se detecta por ausencia de mensajes (watchdog en Node-RED).

## Actuador: 2× Shelly Plug S (Gen1)

Broker embebido en el ESP32-S3 "Actuador" (`192.168.0.100`); los Shelly se conectan a él. `<id>` = `shellyplug-s-<HEX>` (HEX en mayúsculas en los topics).

| Topic | Publica | Payload |
|-------|---------|---------|
| `shellies/<id>/relay/0/command` | cliente (Node-RED) | `on` / `off` / `toggle` (QoS 0, sin retain) |
| `shellies/<id>/relay/0` | Shelly | `on` / `off` (retain) |
| `shellies/<id>/online` | Shelly | `true` / `false` (retain) |
| `shellies/<id>/relay/0/power` | Shelly | W, p. ej. `34.2` |
| `shellies/<id>/relay/0/energy` | Shelly | W·min, p. ej. `125.6` |
| `shellies/command`, `shellies/<id>/command` | ESP32 / cliente | `update` (pide estado completo; el ESP32 lo envía cada 30 s) |

## Lo que los alumnos ya saben (no repetir desde cero)

- Python con `paho-mqtt` ≥ 2.0 (`CallbackAPIVersion.VERSION2`): suscribirse, publicar, `loop_forever()`.
- Herramientas: `mosquitto_sub`/`mosquitto_pub`, MQTT Explorer/MQTTX, Wireshark.
- Teoría MQTT completa: pub/sub, topics y wildcards, QoS 0/1/2, retain, sesión y keepalive, LWT, estructura de paquetes, seguridad (ACL, TLS), 3.1.1 frente a 5.0.
- Existió una práctica de extensión **opcional** de Node-RED (+2 puntos): 2 `mqtt in` contra 2 brokers, `function` para unidades/timestamp, dashboard 1.0 (`ui_chart`, `ui_gauge`), CSV con `file`, bonus `ui_switch` → Shelly. Algunos alumnos pueden haberla hecho.

## Entorno Docker y simulador (`docker/`)

- `.env` elige el sitio: **laboratorio** (`COMPOSE_PROFILES=` vacío, `MQTT_HOST=192.168.0.10`) o **casa** (`COMPOSE_PROFILES=casa`, `MQTT_HOST=mosquitto`, arranca `mosquitto` local + `simulador`).
- El nodo de configuración MQTT de los flujos usa `${MQTT_HOST}` y `${MQTT_PORT}`: el mismo flujo sirve en ambos sitios. Usuario `alumno`; las credenciales no se exportan.
- El Mosquitto local replica usuarios y ACL de la RPi, y además deja al `alumno` escribir en `simulador/#`.
- El simulador (`docker/simulador/simulador.py`) publica los topics `invernadero/...` con la misma cadencia y formato que los ESP32. Shelly simulados: `shellyplug-s-SIM001` = **bomba de riego** (sube la humedad del suelo, vacía el depósito y sube el peso), `shellyplug-s-SIM002` = **ventilador** (baja la temperatura). `SIM_VELOCIDAD=60`: 1 min real = 1 h simulada.
- Control del simulador: `simulador/fallo/<nodo>` ← `ok` | `sensor` (deja de publicar; `online` sigue en `1`) | `desconectado` (deja de publicar y `online`=`0`); `simulador/deposito/rellenar` ← cualquier payload.
- Flujos exportados de referencia en `docs/public/flows/sN-<slug>.json`.
