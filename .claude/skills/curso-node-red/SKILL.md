---
name: curso-node-red
description: Especificación del curso de Node-RED (módulo de la asignatura Sistemas Industriales, 7 sesiones de 4h, escenario invernadero con ESP32 + MQTT). Úsala siempre que se generen o editen materiales del curso -temario, apuntes de sesión, ejercicios, guía del informe, rúbricas, docker-compose del entorno, simulador- para mantener estructura, formato y criterios consistentes.
---

# Curso Node-RED — Sistemas Industriales

Especificación de referencia para generar cualquier material de este curso. Antes de crear o editar contenido (temario, sesión, ejercicio, guía del informe, rúbrica), lee esta skill completa.

## Contexto y audiencia

- Módulo dentro de la asignatura **Sistemas Industriales** (grado de Ingeniería Informática).
- **7 sesiones de 4 horas** (7 semanas), no una asignatura completa independiente.
- Estudiantes que **ya programan** (JS/Python) y que **ya han usado MQTT desde Python** en sus PCs para comunicarse con los sensores del laboratorio. No conocen Node-RED ni la programación basada en flujos. No repasar programación básica ni "qué es MQTT" desde cero: partir de lo que ya hicieron en Python y mostrar qué aporta Node-RED (integración, visualización, persistencia, eventos).
- Enfoque pedagógico: **orientado a un sistema integrado**. Cada sesión aporta una pieza del sistema de monitorización del invernadero; evitar contenido "de relleno" que no vaya a usarse después.

## Escenario: el invernadero del laboratorio

Todas las prácticas guiadas usan el **invernadero** del laboratorio, que ya existe físicamente:

- **Router Wi-Fi** propio. Los alumnos tienen las credenciales.
- **Varios ESP32 ya programados**, cada uno con su **broker MQTT embebido**, que publican las lecturas de sus sensores: **temperatura/humedad ambiente (DHT11 y DHT22)**, **distancia (HC-SR04)**, **calidad del agua (TDS)**, **peso (HX711)** y **humedad del suelo**. Un ESP32 más hace de broker para **2 Shelly Plug S** (actuadores). No se programan los ESP32 en el curso.
- **Raspberry Pi** que actúa **solo como broker MQTT central** (Mosquitto con un *bridge* a cada ESP32, configuración en `rpi/`). No ejecuta Node-RED. Remapea todos los topics a `invernadero/<nodo>/<magnitud>`.
- Cada alumno ejecuta **su propio Node-RED en Docker en su PC**, conectado al broker de la RPi.

Los **topics, payloads, IPs y actuadores reales** (incluidos 2 Shelly Plug S) están en [`references/invernadero-mqtt.md`](references/invernadero-mqtt.md). Léelo antes de escribir cualquier práctica o el simulador; no inventes topics.

## Entorno técnico

- Node-RED se ejecuta con **Docker / docker-compose** en el PC del alumno, nunca con `npm install -g node-red`. Servicios del stack:
  - `node-red` con **Dashboard 2.0** (`@flowfuse/node-red-dashboard`) preinstalado. **No usar** `node-red-dashboard` (1.0, obsoleto).
  - `mosquitto`: broker local para trabajar **fuera del laboratorio**. En el laboratorio se usa el broker de la RPi.
  - `influxdb`: series temporales. Alternativa SQL si se justifica.
  - `simulador`: publica por MQTT **los mismos topics y payloads** que los ESP32 del invernadero, para trabajar en casa sin hardware.
- Cada ejercicio debe funcionar tanto contra el **invernadero real** (broker RPi) como contra el **simulador** (broker local), indicando qué cambia: normalmente solo el host del broker en el nodo de configuración MQTT.

## Estructura de las 7 sesiones

No reordenar ni renombrar estas sesiones sin que el usuario lo pida explícitamente.

| # | Título | Contenido principal | Entregable de sesión |
|---|--------|---------------------|-----------------------|
| 1 | Fundamentos de Node-RED y flujos de control | Entorno Docker, FBP, objeto `msg`, nodos core (`inject`, `debug`, `function`, `change`, `switch`), contexto; flujos de control sobre datos de sensores (simulados o del invernadero vía un `mqtt in` básico) | Flujo con lógica condicional sobre datos de sensores |
| 2 | Integración con APIs externas | `http request`, APIs REST (p. ej. meteorología sin clave como Open-Meteo), parsing JSON, gestión de errores y timeouts; `http in`/`http response` para exponer datos propios | Flujo que combina una API externa con los datos del invernadero |
| 3 | MQTT e IoT en la red del invernadero | Conexión al broker de la RPi, topics y wildcards, QoS, retained, LWT, normalización de payloads de todos los sensores, comandos | Sistema que integra todos los sensores del invernadero por MQTT y reacciona a sus mensajes |
| 4 | Paneles de monitorización | Dashboard 2.0: páginas, grupos, gauges, charts, controles; diseño tipo HMI | Panel de monitorización en tiempo real del invernadero |
| 5 | Persistencia de datos | InfluxDB (o SQL) desde Node-RED, escritura y consulta de históricos, gráficas de tendencia en el panel | Histórico consultable + gráfica de tendencia |
| 6 | Eventos y notificaciones | Modelado de eventos y alarmas (umbrales, histéresis, antirrebote con `trigger`), notificaciones por Telegram (WhatsApp opcional) | Sistema de alertas que notifica ante una condición definida |
| 7 | Agentes de IA y cierre | Llamada a LLM/agente desde un flujo, function calling simple sobre el estado/histórico del invernadero, integración final | Sistema integrado con asistente de IA |

**Node-RED como plataforma** (punto 8 del usuario): cada sesión incluye un bloque breve con aspectos de la plataforma ligados a la práctica del día. Reparto:
- S1: contexto, `link in/out`, organización de flujos, importar/exportar.
- S2: `catch`/`status`/`complete`, variables de entorno.
- S3: nodos de configuración y subflujos.
- S4: Dashboard 2.0 (sustituto de 1.0).
- S5: `filter` (RBE), `join`/`batch`, limitación de frecuencia.
- S6: credenciales, `settings.js` (`adminAuth`, `credentialSecret`).
- S7: modo Projects (git), gestión de la paleta, despliegue.

El **sistema integrado** es la monitorización del invernadero: ESP32 (o simulador) → MQTT (RPi) → Node-RED → InfluxDB/SQL → panel → alertas por Telegram → asistente de IA, con datos de APIs externas (meteorología) como contexto. Cada sesión debe dejar claro qué pieza del sistema se acaba de construir.

## Evaluación: informe de sesiones

- La evaluación se hace **mediante un informe de las sesiones**. No hay examen.
- Estructura por sesión: **objetivos**, **desarrollo** (qué se ha hecho y cómo), **evidencias** (capturas del flujo y del panel, salida de `debug`, flow exportado `.json`), **problemas encontrados y soluciones**, **conclusiones**. Al final, un capítulo del **sistema integrado**.
- El informe se **entrega una sola vez, al final del módulo**, y se acompaña de una **presentación breve** del sistema integrado. El alumno lo va redactando sesión a sesión: cada página de sesión termina indicando **qué evidencias debe recoger** para su informe.
- Pendiente de confirmar con el usuario: pesos de informe y presentación, y duración de la presentación.
- Criterios de corrección breves y objetivos por sesión (funciona / no funciona + 1-2 matices de calidad), no listas extensas.

## Formato de los materiales: sitio VitePress

El curso se publica como un **sitio VitePress** (no como ficheros Markdown sueltos). Antes de tocar `.vitepress/config.ts`, frontmatter, contenedores (`::: tip`, `::: warning`, `::: code-group`), rutas dinámicas o cualquier otra característica de VitePress, consulta la skill **`vitepress`** (`.claude/skills/vitepress/SKILL.md` y sus `references/`), que es la fuente técnica de verdad para esa parte.

Todo el contenido se redacta en **Markdown**, en **español**, con tono para estudiantes de ingeniería (directo, técnico, sin infantilizar).

Estructura de directorios del repositorio:

```
docs/
  .vitepress/
    config.ts        # nav + sidebar (una entrada por sesión, ver abajo)
    theme/            # solo si se necesita personalización (ver skill vitepress)
  index.md            # portada del curso
  temario.md          # temario general
  sesiones/
    01-fundamentos.md
    02-apis-externas.md
    03-mqtt-iot.md
    04-dashboards.md
    05-persistencia.md
    06-eventos-notificaciones.md
    07-ia-y-cierre.md
  evaluacion/
    informe.md        # guía y plantilla del informe
    rubrica.md
  public/
    flows/            # .json exportados de Node-RED, servidos tal cual por VitePress
docker/
  docker-compose.yml
rpi/                   # broker central de la Raspberry Pi (Mosquitto + bridges + ACL); no forma parte del sitio
package.json           # dependencia `vitepress`
```

- El **sidebar** de `.vitepress/config.ts` debe reflejar siempre las 7 sesiones en orden, más una sección de evaluación; cualquier página nueva se añade también aquí, no solo como fichero suelto.
- Los flujos Node-RED exportados van en `public/flows/` (VitePress los sirve como asset estático) y se enlazan desde la página de la sesión con un enlace de descarga, no se pegan como JSON gigante en el cuerpo del Markdown. El sitio se publica en GitHub Pages con `base: '/curso-node-red/'`, y VitePress no añade la base a los enlaces a ficheros de `public/`: usa rutas **relativas**, p. ej. `[s1-control-riego.json](../flows/s1-control-riego.json){download}`.
- Usa contenedores VitePress donde aporten (`::: tip` para atajos, `::: warning` para errores comunes de Node-RED/MQTT, `::: code-group` para mostrar el mismo paso contra el invernadero real vs. el simulador). Ver `references/core-markdown.md` y `references/features-code-blocks.md` de la skill vitepress.
- El sitio no debe tener enlaces rotos (`vitepress build` falla con ellos): no enlazar páginas que aún no existen.

### Imágenes, diagramas y gráficos

**Usa o genera imágenes siempre que sean la mejor forma de explicar algo.** No es decoración: si un concepto se entiende antes viéndolo que leyéndolo, la página debe incluir la imagen. Antes de dar por terminada una página, repasa cada sección y pregúntate: "¿esto se entendería mejor con un dibujo?".

Casos en los que la imagen es casi siempre mejor que el texto:

| Qué explicar | Tipo de imagen |
|--------------|----------------|
| Arquitectura del sistema, qué pieza se añade en la sesión, red del invernadero | Diagrama de bloques (SVG) |
| Recorrido de un mensaje: sensor → broker → Node-RED → salida; publicación/suscripción; bridges de la RPi | Diagrama de flujo o de secuencia (SVG) |
| Estructura de un flujo de Node-RED que el alumno tiene que construir | Captura del editor (PNG) o esquema de nodos (SVG) |
| Dónde está una opción en el editor (Deploy, Context Data, pestaña Security…) | Captura del editor recortada y señalada (PNG) |
| Resultado esperado del entregable (panel, salida de debug, mensaje de Telegram) | Captura del resultado (PNG) |
| Comportamiento de los datos: umbrales, histéresis, antirrebote, ciclo diario, tendencia | Gráfica (SVG) con los datos del invernadero o del simulador |
| Estados y transiciones: alarma activa/reconocida/cerrada, watchdog | Diagrama de estados (SVG) |

Reglas:

- **Formato.** Diagramas y gráficas en **SVG** escrito a mano o generado por script, que es ligero, nítido y se puede versionar. Capturas en **PNG**. No uses arte ASCII para diagramas que sean clave para entender la sesión: pásalo a SVG. El ASCII solo vale como apoyo rápido dentro de un bloque de código.
- **Ubicación y enlaces.** Guarda las imágenes junto a la página, en `docs/<sección>/img/sNN-<descripcion>.svg|png` (p. ej. `docs/sesiones/img/s03-bridges-rpi.svg`), y enlázalas con una ruta relativa: `![texto alternativo](./img/s03-bridges-rpi.svg)`. Vite las procesa y respeta la `base` de GitHub Pages.
- **Tema claro y oscuro.** El sitio tiene los dos temas. Cada SVG debe leerse bien en ambos: cajas con relleno propio y texto oscuro sobre relleno claro (el contraste lo da la caja, no el fondo de la página), y trazos y flechas en tonos medios. Evita el negro o el blanco puro sobre fondo transparente.
- **Accesibilidad.** Texto alternativo descriptivo siempre. Si la imagen transmite información que no está en el texto, añade debajo una frase que la resuma.
- **Coherencia visual.** Mismos colores para los mismos elementos en todo el curso. Nombres, topics y valores deben coincidir con los reales (`references/invernadero-mqtt.md`). Paleta (relleno / borde); referencia: `docs/sesiones/img/s02-arquitectura.svg`:

  | Elemento | Relleno | Borde |
  |----------|---------|-------|
  | ESP32 / sensores | `#dcfce7` | `#16a34a` |
  | RPi / broker MQTT | `#ede9fe` | `#7c3aed` |
  | Node-RED (contenedor) | `#fff1f2` | `#e11d48` (título `#9f1239`) |
  | Nodo dentro de Node-RED | `#ffffff` | `#cbd5e1` |
  | Contexto (flow/global), trazo discontinuo | `#fefce8` | `#ca8a04` |
  | Servicios externos (APIs, Telegram, LLM) | `#dbeafe` | `#2563eb` |
  | Actuadores (Shelly) | `#fef3c7` | `#d97706` |
  | Clientes / usuario | `#f1f5f9` | `#64748b` |

  Texto `#1e293b` (secundario `#475569`), cables y etiquetas de flecha `#64748b`, tipografía `system-ui`. Incluye `<title>` y `<desc>` en cada SVG.
- **Gráficas de datos.** Antes de dibujar una gráfica, consulta la skill **`dataviz`**. Usa datos plausibles del invernadero o generados con el simulador, con ejes y unidades rotulados.
- **Capturas del editor.** Si hay un Node-RED en marcha, genera las capturas reales (p. ej. con la skill `claude-in-chrome`). Si no se pueden generar en ese momento, deja un marcador visible y avísalo al usuario:

  ```md
  ::: info Captura pendiente
  Editor con el flujo del paso 7: switch `clasificar` con sus tres salidas.
  :::
  ```

- **Proporción.** Cada imagen debe responder a una necesidad concreta de explicación. No pongas imágenes genéricas ni de relleno.

Plantilla obligatoria para la página de cada sesión (`docs/sesiones/0N-slug.md`), con frontmatter mínimo `title` y `outline`:

1. **Objetivos de la sesión** (3-5 bullets, verbos en infinitivo, medibles)
2. **Conexión con el sistema del invernadero** (qué pieza se añade)
3. **Conceptos clave** (breve, con enlaces a documentación oficial de Node-RED cuando aplique)
4. **Práctica guiada paso a paso** (instrucciones reproducibles sobre el entorno Docker, contra el invernadero y el simulador)
5. **Node-RED como plataforma** (el bloque de la sesión, ver reparto arriba)
6. **Entregable y evidencias para el informe** (qué debe funcionar, cómo se comprueba, qué evidencias recoger y enlace de descarga al flow en `public/flows/`)
7. **Recursos adicionales** (opcional)

## Qué evitar

- No generar contenido teórico extenso desconectado de un ejercicio práctico inmediato.
- No asumir instalación local sin Docker.
- No pedir a los alumnos que programen los ESP32: ya están programados.
- No usar `node-red-dashboard` 1.0.
- No añadir sesiones, protocolos o herramientas fuera de las 7 sesiones anteriores sin confirmarlo con el usuario primero.
- No diseñar la evaluación como examen: es un informe de sesiones con evidencias.
- No crear páginas de sesión sin darlas de alta en el sidebar de `.vitepress/config.ts`.
- No configurar o personalizar VitePress "a ojo": para config/theme/routing consulta primero la skill `vitepress`.
