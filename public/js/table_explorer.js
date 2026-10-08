/* Explorador de tablas — catalog (GET v1/tables) + paginated row preview
 * (GET v1/tables/:table/rows?page=&q=). All URLs relative. */
(function () {
  'use strict';
  var PAGE = 25;
  var st = null;

  function $(id) { return document.getElementById(id); }
  function esc(s) { return T4E.esc(s); }
  function fmt(n) { return T4E.fmt(n); }

  function pagerHtml(page, pages, total, kind) {
    if (!total) return '<span class="pager-info">Mostrando 0 de 0</span>';
    var from = (page - 1) * PAGE + 1, to = Math.min(page * PAGE, total);
    var h = '<span class="pager-info">Mostrando ' + fmt(from) + '–' + fmt(to) + ' de ' + fmt(total) + '</span>';
    h += '<div class="pager-btns" role="group" aria-label="Paginación">';
    h += '<button type="button" data-' + kind + '-page="' + (page - 1) + '"' + (page <= 1 ? ' disabled' : '') + ' aria-label="Página anterior"><i class="fa-solid fa-chevron-left" aria-hidden="true"></i></button>';
    var set = {}, list = [1, pages, page - 1, page, page + 1].filter(function (p) { return p >= 1 && p <= pages && !set[p] && (set[p] = 1); }).sort(function (a, b) { return a - b; });
    var prev = 0;
    list.forEach(function (p) {
      if (p - prev > 1) h += '<span class="gap">…</span>';
      h += '<button type="button" data-' + kind + '-page="' + p + '"' + (p === page ? ' class="active" aria-current="page"' : '') + '>' + p + '</button>';
      prev = p;
    });
    h += '<button type="button" data-' + kind + '-page="' + (page + 1) + '"' + (page >= pages ? ' disabled' : '') + ' aria-label="Página siguiente"><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></button>';
    return h + '</div>';
  }

  /* ---------------- catalog ---------------- */
  function filtered() {
    var q = st.tq.toLowerCase();
    return st.tables.filter(function (t) {
      if (st.filter === 'geo' && !t.has_geo) return false;
      if (st.filter === 'nogeo' && t.has_geo) return false;
      if (!q) return true;
      return [t.table_name, t.source_name, t.year, t.geo_level].join(' ').toLowerCase().indexOf(q) >= 0;
    });
  }

  function renderStats(d) {
    var t = d.totals;
    $('st-tables').textContent = fmt(t.tables);
    $('st-tables-meta').innerHTML = fmt(t.with_source_year) + ' con fuente y año en <span class="raw-name">meta_sources</span>';
    $('st-rows').textContent = fmt(t.rows);
    $('st-sources').textContent = fmt(t.sources);
    $('st-nogeo').textContent = fmt(t.no_geo);
    $('st-nogeo-meta').innerHTML = '<span class="tag-nogeo">sin geografía</span> fuera del Mapa y de Comparar';
    var tabs = st.root.querySelectorAll('.tab-rail .tab');
    var counts = { all: t.tables, geo: t.with_geo, nogeo: t.no_geo };
    for (var i = 0; i < tabs.length; i++) tabs[i].querySelector('.tc').textContent = counts[tabs[i].getAttribute('data-filter')];
  }

  function renderTables() {
    var list = filtered();
    var pages = Math.max(1, Math.ceil(list.length / PAGE));
    if (st.tpage > pages) st.tpage = pages;
    var slice = list.slice((st.tpage - 1) * PAGE, st.tpage * PAGE);
    var body = $('exp-tables-body');
    if (!slice.length) {
      body.innerHTML = '<tr class="exp-empty"><td colspan="6">Ninguna tabla coincide con la búsqueda.</td></tr>';
    } else {
      body.innerHTML = slice.map(function (t) {
        var geo = t.has_geo
          ? '<span class="exp-geo"><span class="tag-geo">' + esc(t.geo_columns[0]) + '</span><span class="lvl">' + esc(t.geo_level) + '</span></span>'
          : '<span class="exp-geo"><span class="tag-nogeo">sin geografía</span>' + (t.kind === 'system' ? '<span class="lvl">sistema</span>' : '') + '</span>';
        return '<tr tabindex="0" data-table="' + esc(t.table_name) + '"' + (t.table_name === st.sel ? ' class="is-selected" aria-selected="true"' : '') + '>' +
          '<td><span class="raw-name">' + esc(t.table_name) + '</span></td>' +
          '<td class="num">' + fmt(t.rows) + '</td>' +
          '<td class="exp-src">' + (t.source_name ? esc(t.source_name) : '<span class="null-val">sin registro en meta_sources</span>') + '</td>' +
          '<td class="num">' + (t.year ? esc(t.year) : '<span class="null-val">—</span>') + '</td>' +
          '<td>' + geo + '</td>' +
          '<td class="num"><i class="fa-solid fa-chevron-right exp-open" aria-hidden="true"></i></td></tr>';
      }).join('');
    }
    $('exp-list-count').textContent = fmt(list.length) + ' de ' + fmt(st.tables.length) + ' tablas';
    $('exp-tables-pager').innerHTML = pagerHtml(st.tpage, pages, list.length, 't');
  }

  /* ---------------- row preview ---------------- */
  function openTable(name) {
    st.sel = name;
    st.rq = '';
    st.rpage = 1;
    $('exp-row-search').value = '';
    renderTables();
    $('exp-preview').hidden = false;
    loadRows(true);
  }

  function loadRows(scroll) {
    var seq = ++st.rseq;
    var name = st.sel;
    $('exp-rows-body').innerHTML = '<tr class="exp-empty"><td colspan="99">Cargando…</td></tr>';
    T4E.api('v1/tables/' + encodeURIComponent(name) + '/rows?page=' + st.rpage + '&q=' + encodeURIComponent(st.rq))
      .then(function (d) {
        if (!st || seq !== st.rseq) return;
        st.rows = d;
        renderRows(d);
        if (scroll) $('exp-preview').scrollIntoView({ behavior: 'smooth', block: 'start' });
      })
      .catch(function (e) {
        if (!st || seq !== st.rseq) return;
        $('exp-rows-body').innerHTML = '<tr class="exp-empty"><td colspan="99">Error: ' + esc(e.message) + '</td></tr>';
      });
  }

  function cell(v, col) {
    if (v === null || v === undefined) return '<td><span class="null-val">NULL</span></td>';
    var cls = (col.kind === 'num') ? ' class="num"' : (col.kind === 'geom' || col.kind === 'long' || String(v).length > 60) ? ' class="wrap"' : '';
    var txt = col.kind === 'geom' ? '<span class="raw-name">' + esc(v) + '</span>' : esc(v);
    return '<td' + cls + '>' + txt + '</td>';
  }

  function renderRows(d) {
    var meta = (st.tables.filter(function (t) { return t.table_name === d.table; })[0]) || {};
    $('exp-prev-name').textContent = d.table;
    $('exp-prev-meta').innerHTML =
      '<span><b>' + fmt(d.total) + '</b> filas' + (d.q ? ' (filtradas)' : '') + '</span>' +
      '<span>Fuente: <b>' + esc(meta.source_name || '—') + '</b></span>' +
      '<span>Año: <b>' + esc(meta.year || '—') + '</b></span>' +
      '<span>Geografía: <b>' + esc(d.has_geo ? d.geo_level + ' (' + d.geo_columns.join(', ') + ')' : 'sin geografía') + '</b></span>' +
      (d.exceptions_on_page ? '<span><span class="tag-nogeo">sin geografía</span> ' + d.exceptions_on_page + ' en esta página</span>' : '');
    var note = $('exp-prev-note');
    if (d.note) { note.hidden = false; note.innerHTML = '<i class="fa-solid fa-circle-info" aria-hidden="true"></i><span>' + esc(d.note) + '</span>'; }
    else note.hidden = true;
    $('exp-btn-map').hidden = !d.has_geo;

    $('exp-rows-head').innerHTML = '<tr><th scope="col">#</th>' + d.columns.map(function (c) {
      return '<th scope="col"' + (c.kind === 'num' ? ' class="num"' : '') + ' title="' + esc(c.type) + '">' + esc(c.name) + '</th>';
    }).join('') + '<th scope="col">Geografía</th></tr>';

    var base = (d.page - 1) * d.page_size;
    $('exp-rows-body').innerHTML = d.rows.length ? d.rows.map(function (r, i) {
      return '<tr' + (r.__is_exception ? ' class="is-exc"' : '') + '><td class="num">' + (base + i + 1) + '</td>' +
        d.columns.map(function (c) { return cell(r[c.name], c); }).join('') +
        '<td>' + (r.__is_exception ? '<span class="tag-nogeo" title="' + esc(r.__exception_reason) + '">sin geografía</span> <span class="lvl">' + esc(r.__exception_reason) + '</span>' : (d.has_geo ? '' : '<span class="null-val">—</span>')) + '</td></tr>';
    }).join('') : '<tr class="exp-empty"><td colspan="99">Sin filas' + (d.q ? ' para «' + esc(d.q) + '»' : '') + '.</td></tr>';

    var sample = $('exp-sample');
    var bits = [];
    if (d.truncated_columns.length) bits.push('Columnas abreviadas (ST_AsText / texto largo, truncado): ' + d.truncated_columns.join(', ') + '.');
    if (d.q) bits.push('Búsqueda LIKE en: ' + (d.search_columns.join(', ') || 'ninguna columna de texto') + '.');
    sample.hidden = !bits.length;
    sample.textContent = bits.join(' ');
    $('exp-rows-pager').innerHTML = pagerHtml(d.page, d.pages, d.total, 'r');
  }

  function downloadCsv() {
    var d = st && st.rows;
    if (!d) return;
    var names = d.columns.map(function (c) { return c.name; });
    var q = function (v) { if (v === null || v === undefined) return ''; var s = String(v); return /[",\n;]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    var lines = [names.concat(['sin_geografia']).join(',')].concat(d.rows.map(function (r) {
      return names.map(function (n) { return q(r[n]); }).concat([r.__is_exception ? '1' : '']).join(',');
    }));
    var blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = d.table + '_p' + d.page + '.csv';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }

  /* ---------------- events ---------------- */
  function debounce(fn, ms) { var t; return function () { var a = arguments; clearTimeout(t); t = setTimeout(function () { fn.apply(null, a); }, ms); }; }

  function onKey(e) {
    if (e.key === '/' && document.activeElement && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) {
      var i = $('exp-table-search'); if (i) { e.preventDefault(); i.focus(); }
    }
  }

  function bind(root) {
    $('exp-table-search').addEventListener('input', function (e) { st.tq = e.target.value.trim(); st.tpage = 1; renderTables(); });
    root.querySelector('.tab-rail').addEventListener('click', function (e) {
      var b = e.target.closest('.tab'); if (!b) return;
      var tabs = root.querySelectorAll('.tab-rail .tab');
      for (var i = 0; i < tabs.length; i++) { var on = tabs[i] === b; tabs[i].classList.toggle('active', on); tabs[i].setAttribute('aria-selected', on ? 'true' : 'false'); }
      st.filter = b.getAttribute('data-filter'); st.tpage = 1; renderTables();
    });
    var body = $('exp-tables-body');
    body.addEventListener('click', function (e) { var tr = e.target.closest('tr[data-table]'); if (tr) openTable(tr.getAttribute('data-table')); });
    body.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var tr = e.target.closest('tr[data-table]'); if (tr) { e.preventDefault(); openTable(tr.getAttribute('data-table')); }
    });
    $('exp-tables-pager').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-t-page]'); if (!b || b.disabled) return;
      st.tpage = Number(b.getAttribute('data-t-page')); renderTables();
    });
    $('exp-rows-pager').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-r-page]'); if (!b || b.disabled) return;
      st.rpage = Number(b.getAttribute('data-r-page')); loadRows(false);
    });
    $('exp-row-search').addEventListener('input', debounce(function (e) {
      if (!st || !st.sel) return;
      st.rq = e.target.value.trim(); st.rpage = 1; loadRows(false);
    }, 300));
    $('exp-btn-csv').addEventListener('click', downloadCsv);
    document.addEventListener('keydown', onKey);
  }

  window.T4ETableExplorer = {
    init: function (root) {
      st = { root: root, tables: [], filter: 'all', tq: '', tpage: 1, sel: null, rq: '', rpage: 1, rseq: 0, rows: null };
      bind(root);
      return Promise.all([
        T4E.api('v1/tables'),
        T4E.api('v1/batches/latest').catch(function () { return null; })
      ]).then(function (res) {
        if (!st) return;
        var d = res[0], b = res[1];
        st.tables = d.tables;
        $('exp-sub').innerHTML = (b ? 'Último lote <b>#' + esc(b.id) + '</b> · ' + esc(b.status) + (b.finished_at ? ' · cargado el ' + esc(b.finished_at) : '') + ' · ' : '') +
          'catálogo según <span class="raw-name">meta_sources</span>';
        if (b) $('st-rows-meta').textContent = 'Suma de todas las tablas · lote #' + b.id;
        renderStats(d);
        renderTables();
      }).catch(function (e) {
        var el = $('exp-error'); if (el) { el.hidden = false; el.textContent = 'No se pudo cargar el catálogo: ' + e.message; }
        $('exp-tables-body').innerHTML = '<tr class="exp-empty"><td colspan="6">Error al cargar.</td></tr>';
      });
    },
    destroy: function () {
      document.removeEventListener('keydown', onKey);
      st = null;
    }
  };
})();