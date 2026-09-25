# Broker central del invernadero (Raspberry Pi)

La Raspberry Pi ejecuta **Mosquitto** como broker central. Cada ESP32 del invernadero sigue teniendo su propio broker embebido. Mosquitto abre un **puente** (*bridge*) con cada uno, recoge sus mensajes y los publica con una jerarquía común `invernadero/...`.

Los alumnos se conectan **solo a la RPi**, con un único nodo de configuración MQTT en Node-RED.

```text
 ESP32 DHT11  192.168.0.122 ─┐
 ESP32 DHT22  192.168.0.123 ─┤
 ESP32 balanza 192.168.0.121 ┤   puentes MQTT    ┌──────────────┐   1883 (usuario + ACL)
 ESP32 HC-SR04 192.168.0.120 ┼─────────────────▶ │ RPi Mosquitto│ ◀──────────────────── Node-RED de cada alumno
 ESP32 suelo  192.168.0.130 ─┤                   └──────────────┘
 ESP32 TDS    192.168.0.140 ─┤
 ESP32 actuador 192.168.0.100┘ ◀── comandos a los Shelly (out)
```

## Contenido

| Fichero | Destino en la RPi |
|---------|-------------------|
| `mosquitto/conf.d/invernadero.conf` | `/etc/mosquitto/conf.d/invernadero.conf`: listener, puentes y remapeo de topics |
| `mosquitto/acl` | `/etc/mosquitto/acl`: permisos de `profesor` y `alumno` |
| `instalar.sh` | Instala Mosquitto, copia la configuración y crea los usuarios |

## Requisitos

- Raspberry Pi OS (Bookworm o posterior) conectada al router del invernadero (`192.168.0.0/24`).
- **IP fija** para la RPi. Se propone `192.168.0.10`, fuera de las IPs de los ESP32. Con NetworkManager (Bookworm):

  ```bash
  nmcli con show                       # nombre de la conexión, p. ej. "preconfigured"
  sudo nmcli con mod "preconfigured" ipv4.method manual \
       ipv4.addresses 192.168.0.10/24 ipv4.gateway 192.168.0.1 ipv4.dns 192.168.0.1
  sudo nmcli con up "preconfigured"
  ```

  Otra opción es reservar la IP en el DHCP del router.

## Instalación

```bash
# Copiar la carpeta rpi/ a la Raspberry Pi, por ejemplo:
scp -r rpi/ pi@192.168.0.10:~/rpi-invernadero
ssh pi@192.168.0.10
cd ~/rpi-invernadero
chmod +x instalar.sh
sudo ./instalar.sh        # pide las contraseñas de 'profesor' y 'alumno'
```

## Jerarquía de topics resultante

Los payloads no cambian: son números en texto plano, tal como los publican los ESP32.

| Topic en la RPi | Origen (ESP32) | Payload |
|-----------------|----------------|---------|
| `invernadero/dht11/temperatura` | `sensorTHbroker/temperatura` | `23.4` (ºC) |
| `invernadero/dht11/humedad` | `sensorTHbroker/humedad` | `58.2` (%) |
| `invernadero/dht22/temperatura` | `sensorTH22broker/temperatura` | ºC |
| `invernadero/dht22/humedad` | `sensorTH22broker/humedad` | % |
| `invernadero/balanza/peso` | `balanzaHXbroker/peso` | `534.2` (g) |
| `invernadero/ultrasonidos/distancia` | `hcSr04broker/distancia` | `12.3` (cm) |
| `invernadero/suelo/humedad` | `sueloCAPbroker/humedad` | `42.5` (%) |
| `invernadero/suelo/lectura` | `sueloCAPbroker/lectura` | `2350` (ADC) |
| `invernadero/tds/tds` | `tdsMeterbroker/tds` | `367.5` (ppm) |
| `invernadero/tds/voltaje` | `tdsMeterbroker/voltaje` | `1.023` (V) |
| `invernadero/shelly/<id>/relay/0` | `shellies/<id>/relay/0` | `on` / `off` |
| `invernadero/shelly/<id>/relay/0/power` | `shellies/<id>/relay/0/power` | W |
| `invernadero/shelly/<id>/relay/0/energy` | `shellies/<id>/relay/0/energy` | W·min |
| `invernadero/shelly/<id>/online` | `shellies/<id>/online` | `true` / `false` |
| `invernadero/shelly/<id>/relay/0/command` → | `shellies/<id>/relay/0/command` | `on` / `off` / `toggle` |
| `invernadero/shelly/command` → | `shellies/command` | `update` |
| `invernadero/<nodo>/online` | *(generado por la RPi)* | `1` si el puente está conectado, `0` si no |

`<nodo>` es `dht11`, `dht22`, `balanza`, `ultrasonidos`, `suelo`, `tds` o `actuador`.

> **Nota:** `invernadero/<nodo>/online` indica si **la RPi alcanza el ESP32**. Si el ESP32 sigue conectado pero su sensor falla, el nodo deja de publicar y `online` sigue a `1`. Esa situación se detecta en Node-RED con un *watchdog*, que se trabaja en la sesión 3.

## Usuarios y permisos

| Usuario | Permisos |
|---------|----------|
| `profesor` | Lectura y escritura en todo |
| `alumno` | Lectura de `invernadero/#` y `$SYS/#`; escritura solo en los comandos de los Shelly; lectura y escritura en `alumnos/#` para pruebas propias |

Todos los alumnos comparten el usuario `alumno`. Cada uno debe usar un **Client ID distinto** en Node-RED para no expulsarse entre sí.

## Verificación

En la propia RPi:

```bash
# Estado de los puentes (1 = conectado)
mosquitto_sub -h localhost -u profesor -P '<pass>' -v -t 'invernadero/+/online'

# Todos los datos
mosquitto_sub -h localhost -u profesor -P '<pass>' -v -t 'invernadero/#'

# Encender un Shelly (sustituye <id>, p. ej. shellyplug-s-84CCA8XXXXXX)
mosquitto_pub -h localhost -u profesor -P '<pass>' -t 'invernadero/shelly/<id>/relay/0/command' -m on

# Log del broker
journalctl -u mosquitto -f
```

Desde un PC del aula, lo mismo con `-h 192.168.0.10 -u alumno`.

## Problemas conocidos

- **Un puente no conecta** (`invernadero/<nodo>/online` = `0`). Comprueba que el ESP32 responde a `ping` en su IP fija y que su broker acepta conexiones (`mosquitto_sub -h 192.168.0.122 -t '#' -v`).
- **El puente conecta pero no llegan datos del Shelly.** Los patrones del actuador usan el wildcard `+`. Si el broker embebido no resuelve bien los wildcards, sustituye `+` por los IDs concretos de los dos Shelly en `invernadero.conf`.
- **Límite de clientes del ESP32.** El puente ocupa una conexión en cada broker embebido. Si los alumnos siguen conectándose directamente a los ESP32 (práctica anterior), puede agotarse.
