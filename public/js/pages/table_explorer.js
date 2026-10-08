/* Router shim: the shell loads js/pages/{id}.js; the module lives in js/table_explorer.js. */
(function () {
  'use strict';
  var loading = null;
  function load() {
    if (window.T4ETableExplorer) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = 'js/table_explorer.js';
      s.onload = function () { resolve(); };
      s.onerror = function () { loading = null; reject(new Error('No se pudo cargar js/table_explorer.js')); };
      document.body.appendChild(s);
    });
    return loading;
  }
  window.registerPage('table_explorer', {
    init: function (root) { return load().then(function () { return window.T4ETableExplorer.init(root); }); },
    destroy: function () { if (window.T4ETableExplorer) window.T4ETableExplorer.destroy(); }
  });
})();