#!/usr/bin/env bash
# Instala y configura el broker central del invernadero en la Raspberry Pi.
# Uso:  sudo ./instalar.sh
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Ejecuta con sudo: sudo ./instalar.sh" >&2
  exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Instalando Mosquitto"
apt-get update
apt-get install -y mosquitto mosquitto-clients

echo "==> Copiando configuracion"
install -m 0644 "$DIR/mosquitto/conf.d/invernadero.conf" /etc/mosquitto/conf.d/invernadero.conf
install -m 0640 -o root -g mosquitto "$DIR/mosquitto/acl" /etc/mosquitto/acl

echo "==> Creando usuarios (profesor y alumno)"
read -r -s -p "Contrasena para 'profesor': " PASS_PROF; echo
read -r -s -p "Contrasena para 'alumno':   " PASS_ALUM; echo
rm -f /etc/mosquitto/passwd
touch /etc/mosquitto/passwd
mosquitto_passwd -b /etc/mosquitto/passwd profesor "$PASS_PROF"
mosquitto_passwd -b /etc/mosquitto/passwd alumno "$PASS_ALUM"
chown root:mosquitto /etc/mosquitto/passwd
chmod 0640 /etc/mosquitto/passwd

echo "==> Reiniciando Mosquitto"
systemctl enable mosquitto
systemctl restart mosquitto
sleep 2
systemctl --no-pager --lines=0 status mosquitto

echo
echo "Listo. Comprueba los datos con:"
echo "  mosquitto_sub -h localhost -u profesor -P '<contrasena>' -v -t 'invernadero/#'"
