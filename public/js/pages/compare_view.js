/* Router shim: the shell loads js/pages/{id}.js; the Comparar module lives in js/compare_view.js. */
(function () {
  'use strict';
  var loading = null;
  function load() {
    if (window.T4ECompareView) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = 'js/compare_view.js';
      s.onload = function () { resolve(); };
      s.onerror = function () { loading = null; reject(new Error('No se pudo cargar js/compare_view.js')); };
      document.body.appendChild(s);
    });
    return loading;
  }
  window.registerPage('compare_view', {
    init: function (root) { return load().then(function () { return window.T4ECompareView.init(root); }); },
    destroy: function () { if (window.T4ECompareView) window.T4ECompareView.destroy(); }
  });
})();