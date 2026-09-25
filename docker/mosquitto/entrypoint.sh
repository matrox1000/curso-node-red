#!/bin/sh
# Genera el fichero de contraseñas a partir de las variables de entorno
# y arranca Mosquitto.
set -e

PW=/mosquitto/data/passwd
rm -f "$PW"
touch "$PW"
mosquitto_passwd -b "$PW" alumno    "${MQTT_ALUMNO_PASS:?falta MQTT_ALUMNO_PASS}"
mosquitto_passwd -b "$PW" profesor  "${MQTT_PROFESOR_PASS:?falta MQTT_PROFESOR_PASS}"
mosquitto_passwd -b "$PW" simulador "${MQTT_SIMULADOR_PASS:?falta MQTT_SIMULADOR_PASS}"
chown mosquitto:mosquitto "$PW"
chmod 0600 "$PW"

# La ACL se copia al volumen de datos para darle permisos restrictivos
# (un fichero montado desde Windows no los conserva).
cp /mosquitto/config/acl /mosquitto/data/acl
chown mosquitto:mosquitto /mosquitto/data/acl
chmod 0600 /mosquitto/data/acl

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
