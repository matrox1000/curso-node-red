---
title: Temario general
outline: [2, 3]
---

# Temario general

Módulo de **Node-RED** de la asignatura **Sistemas Industriales**: **7 sesiones de 4 horas**, una por semana.

El hilo conductor es el **invernadero del laboratorio**. Cada sesión añade una pieza a un sistema de monitorización que al final del módulo recoge los datos de los sensores, los guarda, los muestra en un panel, avisa cuando algo va mal y permite consultarlos a un asistente de IA.

## Punto de partida

**Qué se da por sabido:**

- Programar con soltura en JavaScript o Python. Dentro de Node-RED se escribe JavaScript, en los nodos `function`.
- Comunicarse por MQTT con los sensores del invernadero desde un programa Python. Lo hiciste en las prácticas anteriores.
- Manejar JSON, HTTP y la línea de comandos a nivel básico.
- Tener Docker y Docker Compose instalados en el portátil.

**Qué aporta este módulo:**

- Programación basada en flujos (*flow-based programming*) con Node-RED.
- Pasar de "un script que lee un topic" a un sistema que integra sensores, APIs externas, base de datos, panel de operador, alarmas e IA.
- Conceptos propios de sistemas industriales: telemetría, series temporales, HMI, alarmas con histéresis y robustez ante fallos de dispositivos.

## El invernadero

| Elemento | Función |
|----------|---------|
| Router Wi-Fi | Red propia del invernadero. Tienes las credenciales. |
| ESP32 (varios) | Ya programados. Cada uno publica sus lecturas en su propio broker MQTT embebido. |
| Raspberry Pi | Broker MQTT central (Mosquitto). Recoge los datos de todos los ESP32 y los publica bajo `invernadero/...`. Es el único broker al que te conectas. |
| Tu PC | Ejecuta tu Node-RED en Docker, conectado al broker de la RPi. |

Magnitudes disponibles:

| Dispositivo | Magnitud | Uso en el sistema |
|-------------|----------|-------------------|
| DHT11 y DHT22 | Temperatura (ºC) y humedad ambiente (%) | Clima interior del invernadero |
| HC-SR04 | Distancia (cm) | Por ejemplo, nivel del depósito de agua |
| TDS Meter | Sólidos disueltos (ppm) | Calidad del agua de riego |
| HX711 | Peso (g) | Por ejemplo, reserva de agua o sustrato |
| Sensor capacitivo | Humedad del suelo (%) | Necesidad de riego |
| 2× Shelly Plug S | Relé on/off, potencia (W) | Actuadores: bomba de riego, ventilación o iluminación |

::: info Los ESP32 no se programan en este módulo
Los ESP32 ya publican sus datos. Todo el trabajo se hace en Node-RED.
:::

## Entorno de trabajo

Node-RED se ejecuta en tu PC con **docker-compose**. El entorno se entrega en la sesión 1 y crece hasta la sesión 7. No hay que instalar Node-RED en local.

| Servicio | Función | Se usa desde |
|----------|---------|--------------|
| `node-red` | Motor de flujos, con **Dashboard 2.0** preinstalado | Sesión 1 |
| `simulador` | Publica por MQTT los mismos topics y payloads que los ESP32 del invernadero | Sesión 1 |
| `mosquitto` | Broker local para trabajar fuera del laboratorio | Sesión 1 |
| `influxdb` | Base de datos de series temporales | Sesión 5 |

::: tip En el laboratorio o en casa
En el laboratorio, Node-RED se conecta al broker de la **Raspberry Pi** y recibe los datos reales. Fuera de él, se conecta al `mosquitto` local, donde publica el `simulador`. Los flujos son los mismos: solo cambia el host del broker en el nodo de configuración MQTT.
:::

## Arquitectura del sistema

```text
                                   ┌─────────────────── Tu PC (Docker) ─────────────────────┐
 ┌──────────┐   MQTT   ┌───────┐   │                                                        │
 │  ESP32   │ ───────▶ │  RPi  │ ─▶│  Node-RED: lógica de control (S1)                      │
 │ sensores │          │broker │   │     │  ◀── APIs externas: meteorología (S2)           │
 └──────────┘          └───────┘   │     │  ◀── integración MQTT de todos los sensores (S3)│
  (o simulador + mosquitto local)  │     ├──▶ panel de monitorización (S4)                  │
                                   │     ├──▶ InfluxDB: histórico (S5)                      │
                                   │     ├──▶ alertas por Telegram (S6)                     │
                                   │     └──▶ asistente de IA (S7)                          │
                                   └────────────────────────────────────────────────────────┘
```

## Planificación de sesiones

| # | Sesión | Pieza del sistema | Entregable |
|---|--------|-------------------|------------|
| 1 | Fundamentos de Node-RED y flujos de control | Lógica de procesado | Flujo con lógica condicional sobre datos de sensores |
| 2 | Integración con APIs externas | Datos de contexto externos | Flujo que combina una API externa con los datos del invernadero |
| 3 | MQTT e IoT en la red del invernadero | Capa de comunicaciones | Integración por MQTT de todos los sensores, con reacción a sus mensajes |
| 4 | Paneles de monitorización | Interfaz de operador (HMI) | Panel de monitorización en tiempo real |
| 5 | Persistencia de datos | Histórico | Histórico consultable y gráfica de tendencia |
| 6 | Eventos y notificaciones | Alarmas | Sistema de alertas que notifica ante una condición definida |
| 7 | Agentes de IA y cierre | Asistente e integración final | Sistema integrado con asistente de IA |

Estructura típica de una sesión de 4 horas:

| Bloque | Duración aprox. |
|--------|-----------------|
| Conceptos clave, siempre ligados a la práctica del día | 30–45 min |
| Práctica guiada paso a paso | 2 h – 2 h 30 min |
| Trabajo autónomo sobre el entregable y recogida de evidencias para el informe | 1 h – 1 h 30 min |

Cada sesión incluye además un bloque breve de **Node-RED como plataforma**: funciones del entorno que se usan en la práctica de ese día.

## Contenido por sesión

### [Sesión 1 — Fundamentos de Node-RED y flujos de control](/sesiones/01-fundamentos)

**Objetivos**

- Levantar el entorno con `docker compose up` y acceder al editor de Node-RED.
- Explicar el modelo de programación basada en flujos y la estructura del objeto `msg`.
- Construir flujos con los nodos core `inject`, `debug`, `function`, `change` y `switch`.
- Programar lógica de control sobre lecturas de sensores, simuladas o del invernadero.

**Contenidos**

- Qué es Node-RED y dónde encaja en la integración IT/OT y el *edge computing*.
- Editor, paleta, *deploy* y pestañas.
- El mensaje `msg`: `payload`, `topic` y propiedades propias.
- Transformación de datos con `change` y `function`, y enrutado con `switch`.
- Primera fuente de datos real: un `mqtt in` que recibe un sensor del invernadero, lo mismo que hacía tu script Python. En la sesión 3 se profundiza en MQTT.

**Node-RED como plataforma:** contexto de nodo, de flujo y global; `link in`/`link out`; organización con grupos y comentarios; importar y exportar flujos.

**Entregable:** flujo que clasifica las lecturas de humedad del suelo y temperatura como `normal`, `aviso` o `crítico` según umbrales configurables y decide si "regar" o "ventilar".

### [Sesión 2 — Integración con APIs externas](/sesiones/02-apis-externas)

**Objetivos**

- Consumir APIs REST con `http request` y procesar respuestas JSON.
- Combinar datos externos (previsión meteorológica) con los datos del invernadero en una decisión de control.
- Gestionar errores de red, timeouts y respuestas inesperadas.
- Exponer el estado del invernadero como API propia con `http in`/`http response`.

**Contenidos**

- Anatomía de una llamada REST: método, URL, parámetros, cabeceras y códigos de estado.
- API meteorológica sin clave (por ejemplo, [Open-Meteo](https://open-meteo.com/)): temperatura exterior, humedad exterior y evapotranspiración.
- Consulta periódica con `inject`, parsing y extracción de los campos útiles.
- Endpoint propio, por ejemplo `GET /api/invernadero/estado`, consultable desde tus programas Python o el navegador.

**Node-RED como plataforma:** gestión de errores con `catch`, `status` y `complete`; variables de entorno para URLs y parámetros.

**Entregable:** flujo que consulta la previsión meteorológica y la combina con los datos del invernadero, por ejemplo para ventilar solo si fuera hace más fresco que dentro. Además, un endpoint REST que devuelve el estado actual.

### Sesión 3 — MQTT e IoT en la red del invernadero

**Objetivos**

- Conectar Node-RED al broker de la Raspberry Pi y suscribirse a todos los sensores del invernadero.
- Usar *wildcards* (`+`, `#`) para procesar familias de topics con un solo flujo.
- Normalizar los payloads de los distintos sensores a un modelo de datos común.
- Aplicar QoS, mensajes *retained* y LWT, y detectar sensores que dejan de publicar.

**Contenidos**

- De Python a Node-RED: qué cambia al integrar varios sensores en un mismo sistema.
- Jerarquía de topics del invernadero y suscripciones con *wildcards*.
- Modelo de datos común del sistema: `sensor`, `magnitud`, `valor`, `unidad`, `ts`.
- QoS 0, 1 y 2, *retained* y *Last Will and Testament*.
- Publicación desde Node-RED: estados, consignas y comandos.
- Detección de sensores caídos (*watchdog*) cuando un ESP32 deja de publicar.

**Node-RED como plataforma:** nodos de configuración (broker compartido entre flujos) y subflujos para tratar todos los sensores con la misma lógica.

**Entregable:** sistema que integra por MQTT todos los sensores del invernadero en el modelo de datos común, reacciona a sus mensajes y detecta cuando un sensor deja de publicar.

### Sesión 4 — Paneles de monitorización

**Objetivos**

- Construir un panel con **Dashboard 2.0** usando *gauges*, gráficas, textos de estado y controles.
- Aplicar criterios de diseño HMI: jerarquía visual, colores de estado y agrupación por zona o magnitud.
- Modificar umbrales y consignas desde el panel.

**Contenidos**

- Estructura de Dashboard 2.0: páginas, grupos y *layouts*.
- Widgets de visualización y de control, y cómo alimentarlos desde el flujo.
- Principios básicos de interfaces de operador en entornos industriales.
- Umbrales editables desde el panel que realimentan la lógica de la sesión 1.

**Node-RED como plataforma:** Dashboard 2.0 frente a Dashboard 1.0 (obsoleto), temas, y cómo se sirve el panel desde el mismo Node-RED.

**Entregable:** panel en tiempo real del invernadero, con el estado de cada sensor (incluidos los caídos) y al menos un control que actúe sobre el sistema.

### Sesión 5 — Persistencia de datos

**Objetivos**

- Explicar por qué las series temporales requieren una base de datos específica.
- Escribir lecturas en InfluxDB desde Node-RED con *measurements*, *tags* y *fields* bien elegidos.
- Consultar históricos con filtros de tiempo y agregaciones.
- Mostrar gráficas de tendencia en el panel a partir del histórico.

**Contenidos**

- Modelo de datos de InfluxDB y su relación con el modelo común de la sesión 3.
- Escritura: individual frente a por lotes, y frecuencia de muestreo.
- Consultas: rango temporal, media, máximo, mínimo y *downsampling*.
- Alternativa SQL: cuándo tiene sentido y qué cambia.

**Node-RED como plataforma:** `filter` (RBE) para guardar solo cambios, `join`/`batch` para agrupar escrituras y limitación de frecuencia con `delay`.

**Entregable:** histórico consultable de las magnitudes del invernadero y una gráfica de tendencia en el panel con rango temporal seleccionable.

### Sesión 6 — Eventos y notificaciones

**Objetivos**

- Diferenciar eventos de estados y modelar alarmas con condición, histéresis, reconocimiento y cierre.
- Evitar tormentas de alertas con temporizadores re-disparables y limitación de frecuencia.
- Enviar notificaciones por Telegram ante eventos del invernadero.
- Explorar el envío por WhatsApp y sus limitaciones.

**Contenidos**

- Detección de flancos, histéresis y antirrebote con el nodo `trigger`.
- Alarmas típicas del invernadero: depósito bajo, suelo seco, temperatura extrema y sensor caído.
- Bot de Telegram: creación con @BotFather, obtención del `chatId` y envío de mensajes. Comandos básicos para consultar el estado desde el móvil.
- WhatsApp: opciones disponibles (API oficial de Meta, pasarelas de terceros) y por qué es más complejo que Telegram.

**Node-RED como plataforma:** credenciales y secretos (tokens fuera de los flujos exportados), `settings.js` con `adminAuth` y `credentialSecret`.

**Entregable:** sistema de alertas que notifica por Telegram ante al menos una condición definida, con histéresis o antirrebote para no repetir avisos.

### Sesión 7 — Agentes de IA y cierre

**Objetivos**

- Invocar un LLM desde un flujo de Node-RED para interpretar los datos del invernadero.
- Implementar *function calling* simple para que un agente consulte el estado o el histórico del sistema.
- Integrar y verificar todas las piezas del sistema.

**Contenidos**

- Qué es un sistema agéntico: modelo, herramientas y bucle de decisión.
- Llamada a un LLM vía API desde Node-RED: *prompt*, contexto y respuesta estructurada.
- *Function calling*: exponer 1–2 herramientas, como `leer_estado` o `consultar_historico`, que el agente puede invocar.
- Casos de uso: resumen diario del invernadero, explicación de una alarma, asistente accesible desde el bot de Telegram.
- Límites y riesgos: el agente propone, el sistema de control decide. Validación de acciones.

**Node-RED como plataforma:** modo Projects (control de versiones con git), gestión de la paleta y despliegue.

**Entregable:** sistema integrado del invernadero con un asistente de IA que responde consultas sobre su estado. Entrega del informe y presentación del sistema.

## Evaluación

La evaluación se hace mediante un **informe de las sesiones**, que se entrega **al final del módulo**, y una **presentación breve** del sistema. No hay examen.

Para cada sesión, el informe recoge:

| Apartado | Contenido |
|----------|-----------|
| Objetivos | Qué se pretendía conseguir en la sesión |
| Desarrollo | Qué has construido y cómo, con las decisiones de diseño |
| Evidencias | Capturas del flujo y del panel, salida de `debug` y flow exportado (`.json`) |
| Problemas y soluciones | Qué falló y cómo lo resolviste |
| Conclusiones | Qué has aprendido y qué mejorarías |

El informe termina con un capítulo del **sistema integrado**: arquitectura final, cómo encajan las piezas y una demostración de funcionamiento.

En la **presentación** se muestra el sistema funcionando sobre el invernadero y se explican las decisiones de diseño principales.

::: tip Recoge las evidencias durante la sesión
El informe se entrega al final, pero se escribe cada semana. Cada página de sesión indica qué evidencias debes guardar. Hacer las capturas y exportar el flujo al terminar cada práctica cuesta mucho menos que reconstruirlo en la semana 7.
:::

## Bibliografía y recursos

**Documentación oficial**

- [Node-RED — Documentación](https://nodered.org/docs/)
- [Node-RED — Cookbook](https://cookbook.nodered.org/)
- [FlowFuse Dashboard 2.0 — Documentación](https://dashboard.flowfuse.com/)
- [Mosquitto — Documentación](https://mosquitto.org/documentation/)
- [HiveMQ — MQTT Essentials](https://www.hivemq.com/mqtt/)
- [InfluxDB — Documentación](https://docs.influxdata.com/)
- [Open-Meteo — Documentación de la API](https://open-meteo.com/en/docs)

**Artículos y guías de apoyo**

- Charles Mahler (InfluxData): [IoT made easy with Node-RED and InfluxDB](https://www.influxdata.com/blog/iot-easy-node-red-influxdb/). Normalización de datos antes de persistir.
- Enrique Crespo (Aprendiendo Arduino): [Crea un bot de Telegram con Node-RED](https://aprendiendoarduino.wordpress.com/2020/04/11/crea-un-bot-de-telegram-con-node-red/).
- FlowFuse: [Migración de Dashboard 1.0 a 2.0](https://dashboard.flowfuse.com/user/migration.html).
- Ayuda Domótica: [Instalación y configuración de Node-RED y paletas esenciales](https://ayudadomotica.com/sistemas-domoticos/instalacion-configuracion-node-red-paletas-esenciales/). Incluye recomendaciones de seguridad.
