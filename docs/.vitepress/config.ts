import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'es-ES',
  title: 'Node-RED · Sistemas Industriales',
  description: 'Módulo de Node-RED de la asignatura Sistemas Industriales: 7 sesiones sobre el invernadero del laboratorio',
  // Publicado en GitHub Pages: https://matrox1000.github.io/curso-node-red/
  base: '/curso-node-red/',
  cleanUrls: true,
  lastUpdated: true,
  // Enlaces a los servicios del entorno Docker del alumno (Node-RED, InfluxDB...)
  ignoreDeadLinks: [/^https?:\/\/localhost/],

  themeConfig: {
    nav: [
      { text: 'Inicio', link: '/' },
      { text: 'Temario', link: '/temario' },
      { text: 'Sesiones', link: '/sesiones/01-fundamentos', activeMatch: '/sesiones/' },
      { text: 'Evaluación', link: '/evaluacion/informe', activeMatch: '/evaluacion/' }
    ],

    sidebar: [
      {
        text: 'Curso',
        items: [
          { text: 'Temario general', link: '/temario' }
        ]
      },
      {
        text: 'Sesiones',
        items: [
          { text: '1. Fundamentos y flujos de control', link: '/sesiones/01-fundamentos' },
          { text: '2. Integración con APIs externas', link: '/sesiones/02-apis-externas' },
          { text: '3. MQTT e IoT en el invernadero', link: '/sesiones/03-mqtt-iot' },
          { text: '4. Paneles de monitorización', link: '/sesiones/04-dashboards' },
          { text: '5. Persistencia de datos', link: '/sesiones/05-persistencia' },
          { text: '6. Eventos y notificaciones', link: '/sesiones/06-eventos-notificaciones' },
          { text: '7. Agentes de IA y cierre', link: '/sesiones/07-ia-y-cierre' }
        ]
      },
      {
        text: 'Evaluación',
        items: [
          { text: 'Informe de sesiones', link: '/evaluacion/informe' },
          { text: 'Rúbrica', link: '/evaluacion/rubrica' }
        ]
      }
    ],

    outline: { level: [2, 3], label: 'En esta página' },
    docFooter: { prev: 'Anterior', next: 'Siguiente' },
    lastUpdatedText: 'Última actualización',
    darkModeSwitchLabel: 'Tema',
    sidebarMenuLabel: 'Menú',
    returnToTopLabel: 'Volver arriba',
    search: { provider: 'local' }
  }
})
