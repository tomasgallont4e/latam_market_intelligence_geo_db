/* Router shim: the shell loads js/pages/{id}.js; the module lives in js/acceptance_panel.js. */
(function () {
  'use strict';
  var loading = null;
  function load() {
    if (window.T4EAcceptancePanel) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = 'js/acceptance_panel.js';
      s.onload = function () { resolve(); };
      s.onerror = function () { loading = null; reject(new Error('No se pudo cargar js/acceptance_panel.js')); };
      document.body.appendChild(s);
    });
    return loading;
  }
  window.registerPage('acceptance_panel', {
    init: function (root) { return load().then(function () { return window.T4EAcceptancePanel.init(root); }); },
    destroy: function () { if (window.T4EAcceptancePanel) window.T4EAcceptancePanel.destroy(); }
  });
})();