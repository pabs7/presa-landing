// Landing de Presa: adapta el botón de socios al dispositivo y rellena el año del pie.
(function () {
  var body = document.body
  // Al desplegar, el contenedor sustituye los marcadores; si no, se usa la app en esta misma dirección.
  var appUrl = (body.dataset.appUrl || '').replace(/\/+$/, '')
  if (!appUrl || appUrl.indexOf('${') === 0) appUrl = ''

  var isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
    || (navigator.userAgent.indexOf('Macintosh') !== -1 && navigator.maxTouchPoints > 1)

  // En el móvil se abre la app con el aviso de instalar visible; en el ordenador, el login.
  var memberUrl = appUrl + (isMobile ? '/?install=1' : '/')

  document.querySelectorAll('[data-member-cta], [data-member-link]').forEach(function (link) {
    link.setAttribute('href', memberUrl)
  })

  var label = document.querySelector('[data-member-cta-label]')
  if (label) label.textContent = isMobile ? 'Descargar la app' : 'Entrar en la app'

  var note = document.querySelector('[data-member-note]')
  if (note) {
    note.textContent = isMobile
      ? 'Se instala desde el navegador, sin pasar por ninguna tienda.'
      : '¿Estás en el móvil? Desde allí puedes instalar la app.'
  }

  var year = document.querySelector('[data-year]')
  if (year) year.textContent = String(new Date().getFullYear())
})()
