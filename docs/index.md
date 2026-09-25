---
layout: home

hero:
  name: Node-RED
  text: Sistemas Industriales
  tagline: De los sensores de un invernadero a un sistema de monitorización completo en 7 sesiones
  actions:
    - theme: brand
      text: Ver temario
      link: /temario
    - theme: alt
      text: Sesión 1
      link: /sesiones/01-fundamentos

features:
  - title: Un invernadero real
    details: Varios ESP32 publican por MQTT temperatura, humedad, distancia, calidad del agua, peso y humedad del suelo. Cada sesión añade una pieza al sistema que los monitoriza.
  - title: Entorno reproducible
    details: Node-RED, Mosquitto, InfluxDB y un simulador de sensores arrancan con docker compose up en tu PC.
  - title: En el laboratorio o en casa
    details: En el laboratorio te conectas al broker del invernadero. Fuera de él, el simulador publica los mismos topics.
---
