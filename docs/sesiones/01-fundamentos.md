---
title: "Sesión 1 · Fundamentos de Node-RED y flujos de control"
outline: [2, 3]
---

# Sesión 1 · Fundamentos de Node-RED y flujos de control

## Objetivos de la sesión

- Levantar el entorno del curso con `docker compose up` y acceder al editor de Node-RED.
- Explicar la programación basada en flujos y la estructura del objeto `msg`.
- Construir flujos con los nodos `inject`, `debug`, `change`, `switch` y `function`.
- Recibir por MQTT una magnitud del invernadero (real o simulada) y convertirla a un valor numérico.
- Programar una decisión de control basada en umbrales guardados en el contexto de flujo.

## Conexión con el sistema del invernadero

Esta sesión construye la **lógica de procesado**: la pieza que recibe una lectura, la interpreta y decide qué hacer. En las sesiones siguientes esa decisión se enriquecerá con la previsión meteorológica (S2), actuará sobre la bomba real (S3), se verá en el panel (S4), quedará registrada (S5) y generará alertas (S6).

```text
[sensor] ──▶ ■ lógica de control (S1) ──▶ decisión: regar / no regar
```

## Conceptos clave

### Programación basada en flujos

En Node-RED un programa es un **flujo**: un grafo de **nodos** unidos por **cables**. Cada nodo recibe un mensaje, hace una cosa y pasa uno o más mensajes al siguiente. No hay un bucle principal: el motor (Node.js) ejecuta cada nodo cuando le llega un mensaje.

Ya conoces la idea desde Python:

| Script Python con `paho-mqtt` | Flujo de Node-RED |
|-------------------------------|-------------------|
| `client.connect(...)` y `loop_forever()` | Nodo de configuración `mqtt-broker`: Node-RED mantiene la conexión |
| `client.subscribe("invernadero/suelo/humedad")` | Nodo `mqtt in` con ese topic |
| Callback `on_message(client, userdata, msg)` | Todo lo que cuelga del cable de salida del `mqtt in` |
| `if valor < umbral: ...` | Nodo `switch` |
| `print(...)` | Nodo `debug` |

La diferencia está en lo que viene después: en Node-RED añadir un panel, una base de datos o un bot de Telegram es añadir nodos al mismo flujo, no reescribir el script.

### El mensaje `msg`

Todo lo que circula por un cable es un objeto JavaScript llamado `msg`:

| Propiedad | Contenido |
|-----------|-----------|
| `msg.payload` | El dato principal. Con MQTT, el contenido del mensaje: `"42.5"` |
| `msg.topic` | El topic MQTT o una etiqueta libre: `"invernadero/suelo/humedad"` |
| `msg._msgid` | Identificador único que asigna Node-RED |
| *cualquier otra* | Puedes añadir las tuyas: `msg.estado`, `msg.unidad`… |

Documentación: [Working with messages](https://nodered.org/docs/user-guide/messages).

### Nodos de esta sesión

| Nodo | Para qué |
|------|----------|
| `inject` | Genera un mensaje: al pulsar, al desplegar o periódicamente |
| `debug` | Muestra el mensaje en la barra lateral de depuración |
| `change` | Modifica propiedades sin escribir código: asignar, borrar, mover, expresiones JSONata |
| `switch` | Enruta el mensaje a una salida u otra según reglas |
| `function` | Código JavaScript con acceso a `msg`, al contexto y al estado del nodo |
| `mqtt in` | Suscripción a un topic MQTT |

Documentación: [Core nodes](https://nodered.org/docs/user-guide/nodes) y [Writing functions](https://nodered.org/docs/user-guide/writing-functions).

### Contexto

Los mensajes no se acuerdan de nada. Para guardar estado entre mensajes (el último valor, unos umbrales, un contador) Node-RED ofrece el **contexto** en tres ámbitos: **nodo** (`context`), **flujo** (`flow`, compartido por los nodos de la pestaña) y **global** (`global`, todo Node-RED). Documentación: [Working with context](https://nodered.org/docs/user-guide/context).

## Práctica guiada paso a paso

### Paso 0 · Preparar el entorno (20 min)

1. Descarga la carpeta `docker/` del repositorio del curso y abre una terminal en ella.
2. Crea tu fichero de configuración:

   ```bash
   cp .env.example .env
   ```

3. Edita `.env` y deja activo el bloque que corresponda:

   ::: code-group

   ```ini [.env · laboratorio]
   # Broker central de la Raspberry Pi
   COMPOSE_PROFILES=
   MQTT_HOST=192.168.0.10
   ```

   ```ini [.env · casa (simulador)]
   # Broker local + simulador del invernadero
   COMPOSE_PROFILES=casa
   MQTT_HOST=mosquitto
   ```

   :::

4. Arranca el entorno (la primera vez tarda unos minutos en construir las imágenes):

   ```bash
   docker compose up -d --build
   docker compose ps
   ```

5. Abre el editor en [http://localhost:1880](http://localhost:1880).

::: warning En el laboratorio
Tu PC tiene que estar conectado a la **Wi-Fi del router del invernadero**, no a la red de la universidad. Si no, Node-RED no alcanza la Raspberry Pi.
:::

::: tip En casa
El simulador publica los mismos topics que el invernadero real. `SIM_VELOCIDAD=60` hace que un minuto real equivalga a una hora simulada: verás secarse el suelo en pocos minutos. Mira qué publica con `docker compose logs -f simulador`.
:::

### Paso 1 · Primer flujo: `inject` → `debug` (10 min)

1. Arrastra un `inject` y un `debug` al lienzo y únelos.
2. Pulsa **Deploy** (arriba a la derecha).
3. Pulsa el botón del `inject` y abre la pestaña de depuración (icono del insecto): aparece un *timestamp*.

Nada se ejecuta hasta que despliegas. Cada cambio en el editor requiere un nuevo **Deploy**.

### Paso 2 · Anatomía de `msg` (15 min)

1. En el `inject`, cambia `msg.payload` a tipo *string* con valor `42.5` y `msg.topic` a `invernadero/suelo/humedad`.
2. En el `debug`, cambia *Output* a **complete msg object**. Despliega y pulsa: verás `payload`, `topic` y `_msgid`.
3. Inserta un `change` entre ambos con la regla *Set* `msg.unidad` = `%`. Comprueba que el mensaje llega con la nueva propiedad.

### Paso 3 · Conectar con el invernadero: `mqtt in` (30 min)

1. Arrastra un `mqtt in`. En **Server**, pulsa el lápiz para crear el nodo de configuración del broker:

   | Campo | Valor |
   |-------|-------|
   | Name | `Broker invernadero` |
   | Server | `${MQTT_HOST}` |
   | Port | `${MQTT_PORT}` |
   | Client ID | vacío (Node-RED genera uno aleatorio) |
   | Security → Username | `alumno` |
   | Security → Password | la contraseña del laboratorio |

   `${MQTT_HOST}` se sustituye por la variable de entorno del contenedor. Así el mismo flujo funciona en el laboratorio y en casa: solo cambia el `.env`.

2. En el `mqtt in`: **Topic** `invernadero/suelo/humedad`, **QoS** 0, **Output** *a UTF-8 string*.
3. Conéctalo a un `debug`, despliega y comprueba que bajo el nodo aparece **connected** y que llegan lecturas cada pocos segundos.

Topics disponibles (todos con payload numérico en texto):

| Topic | Magnitud |
|-------|----------|
| `invernadero/suelo/humedad` | Humedad del suelo (%) |
| `invernadero/dht22/temperatura` · `invernadero/dht11/temperatura` | Temperatura ambiente (ºC) |
| `invernadero/dht22/humedad` · `invernadero/dht11/humedad` | Humedad ambiente (%) |
| `invernadero/ultrasonidos/distancia` | Distancia al agua del depósito (cm) |
| `invernadero/balanza/peso` | Peso (g) |
| `invernadero/tds/tds` | Sólidos disueltos en el agua (ppm) |

::: warning `disconnected` bajo el `mqtt in`
- En el laboratorio: comprueba la Wi-Fi y el usuario y la contraseña de la pestaña *Security*.
- En casa: comprueba que `MQTT_ALUMNO_PASS` del `.env` coincide con la contraseña que has puesto en Node-RED, y que el perfil `casa` está activo (`docker compose ps` debe mostrar `mosquitto` y `simulador`).
:::

::: info Los topics llevan *retain*
Al suscribirte recibes enseguida el último valor, aunque el sensor no haya publicado todavía.
:::

### Paso 4 · De texto a número con `change` (15 min)

Los ESP32 publican **texto**: `"42.5"`, no `42.5`. Compararlo con un umbral numérico sin convertirlo es una fuente clásica de errores.

1. Añade un `change` después del `mqtt in` con nombre `texto → número`.
2. Regla: *Set* `msg.payload` a la expresión (tipo **J:** JSONata) `$number(payload)`.
3. Con el `debug` comprueba que el valor aparece ahora en azul (número) y no entre comillas (texto).

### Paso 5 · Probar sin sensores (10 min)

Para probar la lógica con valores concretos, sin depender de lo que marque el sensor en ese momento, añade tres `inject` con payload *string* `20.0`, `30.0` y `50.0` y conéctalos a la entrada del `change`. Son tus **casos de prueba**: los usarás en los pasos siguientes y en el entregable.

### Paso 6 · Umbrales en el contexto de flujo (20 min)

Los umbrales no deben estar escritos a fuego dentro de los nodos: se cargan una vez en el contexto de flujo y todos los nodos los leen de ahí.

1. Añade un `inject` llamado `cargar umbrales`, con **Inject once after 0.1 seconds** activado y payload JSON:

   ```json
   { "suelo": { "critico": 25, "aviso": 35 } }
   ```

2. Conéctalo a un `change` con la regla *Set* `flow.umbrales` = `msg.payload`.
3. Despliega y abre la pestaña **Context Data** de la barra lateral. Pulsa refrescar en *Flow* y comprueba que `umbrales` está guardado.

### Paso 7 · Clasificar con `switch` (20 min)

1. Añade un `switch` llamado `clasificar` sobre `msg.payload` con tres reglas:

   | Regla | Valor | Salida |
   |-------|-------|--------|
   | `<` | `flow.umbrales.suelo.critico` | 1 |
   | `<` | `flow.umbrales.suelo.aviso` | 2 |
   | *otherwise* | | 3 |

   Elige el tipo **flow.** en el desplegable del valor. Abajo, selecciona **stopping after first match**: sin esa opción, un 20 % cumpliría las dos primeras reglas y saldría por ambas.

2. En cada salida, un `change` que asigne `msg.estado` = `crítico`, `aviso` o `normal`.
3. Prueba con los tres `inject` y comprueba que cada valor sale por la salida esperada.

### Paso 8 · Decidir con `function` (25 min)

Une las tres salidas en un `function` llamado `decidir riego`:

```js
// Guarda el último estado en el contexto de flujo y decide la acción
const anterior = flow.get("estadoSuelo");
flow.set("estadoSuelo", msg.estado);
flow.set("ultimaHumedadSuelo", msg.payload);

const accion = msg.estado === "crítico" ? "regar" : "no regar";

msg.payload = {
    humedad: msg.payload,
    estado: msg.estado,
    accion: accion,
    cambio: msg.estado !== anterior   // true solo cuando cambia el estado
};

node.status({
    fill: msg.estado === "normal" ? "green" : msg.estado === "aviso" ? "yellow" : "red",
    shape: "dot",
    text: `${msg.payload.humedad} % → ${accion}`
});
return msg;
```

- `flow.get`/`flow.set` leen y escriben el contexto de flujo.
- `node.status` muestra un indicador bajo el nodo: útil para ver el estado sin abrir la depuración.
- `cambio` servirá en la sesión 6 para avisar solo cuando el estado cambia, no con cada lectura.

Conecta la salida a un `debug` y prueba con los `inject` y con los datos reales.

Si te atascas, puedes descargar el flujo de referencia de la práctica guiada: <a href="/flows/s1-control-riego.json" download>s1-control-riego.json</a>. Impórtalo con **Menú → Import**, abre el nodo `Broker invernadero` y escribe el usuario y la contraseña: las credenciales nunca se exportan.

### Paso 9 · Ver reaccionar al invernadero (solo en casa, 10 min)

Con el simulador puedes encender la bomba de riego (Shelly `shellyplug-s-SIM001`) y ver cómo sube la humedad del suelo y cambia la decisión:

```bash
docker compose exec mosquitto mosquitto_pub -u alumno -P alumno \
  -t invernadero/shelly/shellyplug-s-SIM001/relay/0/command -m on
```

Cambia `on` por `off` para apagarla. Si has cambiado `MQTT_ALUMNO_PASS`, usa tu contraseña.

::: danger No actúes sobre el invernadero real en esta sesión
En el laboratorio los Shelly son compartidos y controlan equipos reales. El envío de comandos se trabaja en la sesión 3.
:::

## Node-RED como plataforma

### Contexto: dónde vive el estado

- La pestaña **Context Data** muestra el contexto de nodo, flujo y global. Úsala para depurar.
- Por defecto el contexto está **en memoria**: se pierde al reiniciar Node-RED. Por eso los umbrales se cargan con un `inject` *once*.
- Usa `flow` para lo que comparten los nodos de una pestaña y `global` solo para lo que necesiten varias pestañas.

### `link in` / `link out`: cables invisibles

Cuando un flujo crece, los cables largos lo hacen ilegible. Un `link out` envía el mensaje a uno o varios `link in`, incluso en otra pestaña.

**Ejercicio:** conecta la salida de `decidir riego` a un `link out` y crea en otra zona del lienzo un `link in` → `debug`. En la sesión 3 usarás este patrón para separar la "lógica" de las "salidas".

### Organizar el flujo

- **Nombres**: cada nodo con un nombre que diga qué hace (`texto → número`, no `change`).
- **Comentarios**: nodos `comment` como títulos de sección. Su pestaña *info* admite Markdown.
- **Grupos**: selecciona varios nodos y pulsa **Ctrl+Shift+G** para agruparlos con un marco y un título.

### Importar y exportar

- **Ctrl+E** exporta la selección, la pestaña o todos los flujos a JSON. **Ctrl+I** importa.
- El JSON incluye los nodos de configuración (el broker) pero **no las credenciales**: por eso puedes compartir flujos sin filtrar contraseñas.
- Exportar es la forma de entregar tu trabajo y de guardar copias: hazlo al final de cada sesión.

## Entregable y evidencias para el informe

### Qué debe funcionar

Amplía el flujo de la práctica guiada para que controle también la **temperatura**:

1. Suscríbete además a `invernadero/dht22/temperatura` y conviértela a número.
2. Añade al `inject` de umbrales los de temperatura, por ejemplo:

   ```json
   {
     "suelo":       { "critico": 25, "aviso": 35 },
     "temperatura": { "aviso": 30, "critico": 35 }
   }
   ```

3. Clasifica cada temperatura como `normal`, `aviso` o `crítico`. Cuidado: aquí el peligro está en los valores **altos**.
4. Una única función de decisión que, con la **última lectura de cada sensor** guardada en el contexto, produzca:

   ```json
   { "regar": true, "ventilar": false, "suelo": "crítico", "temperatura": "normal" }
   ```

   Criterio mínimo: regar si el suelo está en estado crítico y ventilar si la temperatura está en aviso o crítico.

5. Casos de prueba con `inject` que cubran los tres estados de cada magnitud.

### Cómo se comprueba

- Con los `inject` de prueba, cada combinación produce la decisión esperada.
- Con datos reales o simulados, la decisión se actualiza al llegar cada lectura.
- Cambiar un umbral en el `inject` y volver a pulsarlo cambia el comportamiento sin tocar ningún otro nodo.

**Criterios de calidad:** umbrales solo en el contexto (ningún número "mágico" dentro de `switch` o `function`), nodos con nombre y flujo organizado con comentarios o grupos.

### Evidencias que debes guardar

- [ ] Captura del flujo completo.
- [ ] Captura de la depuración con al menos un caso de cada estado para cada magnitud.
- [ ] Captura de **Context Data** con los umbrales y los últimos valores guardados.
- [ ] Flujo exportado: `s1-<tu-apellido>.json`.
- [ ] En el informe, respuesta breve a:
  - ¿Qué ventajas e inconvenientes ves frente a tu script Python de la práctica anterior?
  - ¿Por qué hay que convertir el payload a número y qué pasaría si no lo hicieras?
  - ¿Por qué el `switch` debe detenerse en la primera coincidencia?

## Recursos adicionales

- [Node-RED — Getting started with Docker](https://nodered.org/docs/getting-started/docker)
- [Node-RED — Using environment variables](https://nodered.org/docs/user-guide/environment-variables)
- [Node-RED Cookbook](https://cookbook.nodered.org/)
- [JSONata — Documentación](https://docs.jsonata.org/overview)
