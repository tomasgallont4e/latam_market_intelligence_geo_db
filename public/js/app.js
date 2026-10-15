/* think4ever · Geo DB Colombia — shell + router
 * load_page('page_id') fetches pages/{id}.html into #page-main, attaches the
 * optional page stylesheet css/pages/{id}.css, loads js/pages/{id}.js once and
 * calls the page's init(root). Pages register via registerPage(id, {init, destroy}).
 * All URLs are RELATIVE (the app is served behind /run/<projectId>/).
 */
(function () {
  'use strict';

  var PAGES = {
    map_view: 'Mapa',
    compare_view: 'Comparar',
    acceptance_panel: 'Panel de aceptación',
    table_explorer: 'Explorador de tablas'
  };
  var DEFAULT_PAGE = 'map_view';
  var registry = {};        // id -> {init, destroy}
  var scriptLoads = {};     // id -> Promise
  // The map module has country-specific behaviour. Keep it out of a stale
  // browser cache after deploying a new mapping build.
  var pageAssetVersion = 'peru-map-20261014-8';
  var current = null;
  var loadSeq = 0;

  /* ---------- helpers shared with pages ---------- */
  var nf0 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
  var nf1 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 });
  var nf2 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 });

  window.T4E = {
    fmt: function (v, digits) {
      if (v === null || v === undefined || v === '' || isNaN(Number(v))) return '—';
      var n = Number(v);
      if (digits === 2) return nf2.format(n);
      if (digits === 1) return nf1.format(n);
      return nf0.format(n);
    },
    esc: function (s) {
      return String(s === null || s === undefined ? '' : s)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    },
    api: function (url, opts) {
      // url must be relative, e.g. 'api/map/departments'
      return fetch(url.replace(/^\/+/, ''), Object.assign({ headers: { Accept: 'application/json' } }, opts || {}))
        .then(function (r) {
          if (!r.ok) return r.text().then(function (t) { throw new Error('HTTP ' + r.status + ' ' + url + (t ? ': ' + t.slice(0, 200) : '')); });
          return r.json();
        });
    },
    isDark: function () {
      var t = document.documentElement.getAttribute('data-theme');
      if (t) return t === 'dark';
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
  };

  window.registerPage = function (id, def) {
    registry[id] = def || {};
  };

  function loadScriptOnce(id) {
    if (registry[id]) return Promise.resolve();
    if (scriptLoads[id]) return scriptLoads[id];
    scriptLoads[id] = new Promise(function (resolve) {
      var s = document.createElement('script');
      s.src = 'js/pages/' + id + '.js' + (id === 'map_view' ? '?v=' + pageAssetVersion : '');
      s.async = true;
      s.onload = function () { resolve(); };
      s.onerror = function () { delete scriptLoads[id]; resolve(); }; // page may be static-only
      document.body.appendChild(s);
    });
    return scriptLoads[id];
  }

  function setActive(id) {
    var items = document.querySelectorAll('.main-sidebar .nav-item[data-page]');
    for (var i = 0; i < items.length; i++) {
      var on = items[i].getAttribute('data-page') === id;
      items[i].classList.toggle('active', on);
      if (on) items[i].setAttribute('aria-current', 'page');
      else items[i].removeAttribute('aria-current');
    }
  }

  function renderError(main, id, err) {
    main.innerHTML =
      '<div class="page-pad"><div class="empty-state">' +
      '<i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>' +
      '<h2>' + T4E.esc(PAGES[id] || id) + '</h2>' +
      '<p>No se pudo cargar esta página.</p>' +
      '<small class="raw-name">' + T4E.esc(err && err.message ? err.message : String(err)) + '</small>' +
      '</div></div>';
  }

  window.load_page = function (id) {
    if (!PAGES[id]) id = DEFAULT_PAGE;
    var seq = ++loadSeq;
    var main = document.getElementById('page-main');

    // tear down the previous page (e.g. Leaflet maps)
    if (current && registry[current] && typeof registry[current].destroy === 'function') {
      try { registry[current].destroy(); } catch (e) { console.warn('destroy', current, e); }
    }
    current = id;
    setActive(id);
    document.title = (PAGES[id] || id) + ' · LATAM Market Intelligence · think4ever';
    if (location.hash !== '#' + id) {
      try { history.replaceState(null, '', '#' + id); } catch (e) { /* ignore */ }
    }

    var css = document.getElementById('page-css');
    if (css) css.setAttribute('href', 'css/pages/' + id + '.css');

    main.setAttribute('aria-busy', 'true');
    main.innerHTML = '<div class="page-loading"><span><i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>Cargando…</span></div>';

    return fetch('pages/' + id + '.html', { cache: 'no-cache' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status + ' pages/' + id + '.html');
        return r.text();
      })
      .then(function (html) {
        if (seq !== loadSeq) return;
        main.innerHTML = html;
        return loadScriptOnce(id).then(function () {
          if (seq !== loadSeq) return;
          var def = registry[id];
          if (def && typeof def.init === 'function') {
            return def.init(main);
          }
        });
      })
      .catch(function (err) {
        if (seq !== loadSeq) return;
        console.error(err);
        renderError(main, id, err);
      })
      .then(function () {
        if (seq === loadSeq) main.removeAttribute('aria-busy');
      });
  };

  /* ---------- theme ---------- */
  function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem('t4e-theme'); } catch (e) { /* ignore */ }
    if (saved === 'dark' || saved === 'light') document.documentElement.setAttribute('data-theme', saved);
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.addEventListener('click', function () {
      var next = T4E.isDark() ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('t4e-theme', next); } catch (e) { /* ignore */ }
      document.dispatchEvent(new CustomEvent('t4e:theme', { detail: { theme: next } }));
    });
  }

  function boot() {
    initTheme();
    var fromHash = (location.hash || '').replace(/^#/, '');
    load_page(PAGES[fromHash] ? fromHash : DEFAULT_PAGE);
    window.addEventListener('hashchange', function () {
      var h = (location.hash || '').replace(/^#/, '');
      if (PAGES[h] && h !== current) load_page(h);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
