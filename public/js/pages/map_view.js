/* Router shim: the shell loads js/pages/{id}.js; the Mapa module lives in js/map_view.js. */
(function () {
  'use strict';
  var loading = null;
  function load() {
    if (window.T4EMapView) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = 'js/map_view.js';
      s.onload = function () { resolve(); };
      s.onerror = function () { loading = null; reject(new Error('No se pudo cargar js/map_view.js')); };
      document.body.appendChild(s);
    });
    return loading;
  }
  window.registerPage('map_view', {
    init: function (root) { return load().then(function () { return window.T4EMapView.init(root); }); },
    destroy: function () { if (window.T4EMapView) window.T4EMapView.destroy(); }
  });
})();