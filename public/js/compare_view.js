/* Comparar lugares — calls api/compare (relative URLs only). */
(function () {
  'use strict';

  var MAX = 4;
  var DEFAULT_SEL = { department: ['11', '05'] };
  var LEVEL_LABEL = { department: 'Departamentos', municipality: 'Ciudades', localidad: 'Localidades de Bogotá' };
  var S = null;

  function $(sel) { return S.root.querySelector(sel); }
  function esc(s) { return window.T4E.esc(s); }
  function norm(s) { return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }

  function digitsFor(ind) {
    var u = String(ind.unit || '');
    if (u.indexOf('miles de millones') >= 0) return 2;
    if (u === '%' || u.indexOf('por 1.000') >= 0) return 1;
    return 0;
  }
  function fmtVal(v, ind) {
    if (v === null || v === undefined) return '<span class="na">n.a.</span>';
    return esc(window.T4E.fmt(v, digitsFor(ind)));
  }

  function placeById(id) {
    var list = (S.places[S.level] || {}).places || [];
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return null;
  }
  function placeLabel(p) { return p.parent ? p.name + ' (' + p.parent + ')' : p.name; }

  /* ---------- panel ---------- */
  function renderOptions() {
    var ul = $('#cmp_places');
    var list = (S.places[S.level] || {}).places || [];
    var q = norm(S.search);
    var full = S.selected.length >= MAX;
    var shown = 0, html = '';
    for (var i = 0; i < list.length && shown < 200; i++) {
      var p = list[i];
      if (q && norm(p.name + ' ' + p.code + ' ' + (p.parent || '')).indexOf(q) < 0) continue;
      var sel = S.selected.indexOf(p.id) >= 0;
      var dis = full && !sel;
      html += '<li><button type="button" class="place-opt" role="option" data-id="' + esc(p.id) + '" aria-selected="' + sel + '"' +
        (dis ? ' aria-disabled="true"' : '') + '><span class="box">' + (sel ? '<i class="fa-solid fa-check"></i>' : '') + '</span>' +
        '<span>' + esc(placeLabel(p)) + '</span><span class="code">' + esc(p.code) + '</span></button></li>';
      shown++;
    }
    if (!shown) html = '<li class="place-empty-search">' + (list.length ? 'Sin resultados para la búsqueda.' : 'Cargando lugares…') + '</li>';
    ul.innerHTML = html;
  }

  function renderChips() {
    var html = '';
    S.selected.forEach(function (id) {
      var p = placeById(id);
      html += '<span class="place-chip">' + esc(p ? p.name : id) +
        '<button type="button" data-remove="' + esc(id) + '" aria-label="Quitar ' + esc(p ? p.name : id) + '">×</button></span>';
    });
    $('#cmpChips').innerHTML = html;
    var c = $('#cmpCount');
    c.textContent = S.selected.length + ' de ' + MAX + ' seleccionados';
    c.classList.toggle('is-low', S.selected.length < 2);
  }

  function renderSub() {
    var persona = S.persona || 'Todas';
    $('#cmpSub').textContent = LEVEL_LABEL[S.level] + ' · ' + S.selected.length + ' lugares · Persona: ' + persona;
    var pf = $('#cmp_persona_filter');
    pf.disabled = false;
    $('#cmpPersonaHelp').innerHTML = S.level === 'localidad'
      ? 'Aplica a «Personas» y «por 1.000 ocupados» de las localidades de Bogotá (Encuesta Multipropósito 2021, <span class="raw-name">fact_em2021_localidad_persona</span>). Sumapaz sin dato.'
      : 'Aplica a los indicadores de <span class="raw-name">fact_persona_profile</span>, igual que en el mapa.';
  }

  function showAlert(msg, kind) {
    var a = $('#cmpAlert');
    if (!msg) { a.hidden = true; return; }
    a.hidden = false;
    a.className = 'alert ' + (kind === 'danger' ? 'alert-danger' : 'alert-warning') + ' cmp-alert';
    a.querySelector('b').textContent = kind === 'danger' ? 'No se pudo comparar.' : 'Selección incompleta.';
    $('#cmpAlertMsg').textContent = msg;
  }

  function emptyTable(msg) {
    $('#cmp_table').innerHTML = '<tbody><tr><td><div class="cmp-empty-table"><i class="fa-solid fa-table-columns" aria-hidden="true"></i>' + esc(msg) + '</div></td></tr></tbody>';
    $('#cmpSummary').innerHTML = '';
    S.result = null;
  }

  /* ---------- results ---------- */
  function renderResult(res) {
    S.result = res;
    var places = res.places, inds = res.indicators;
    var head = '<thead><tr><th scope="col">Indicador</th>';
    places.forEach(function (p) {
      head += '<th scope="col" class="place-th num">' + esc(p.name) + '<small>' + esc(p.code) + '</small></th>';
    });
    head += '<th scope="col">Fuente y año</th></tr></thead>';
    var body = '<tbody>';
    inds.forEach(function (ind) {
      var max = null;
      ind.values.forEach(function (v) { if (v !== null && (max === null || v > max)) max = v; });
      var nonNull = ind.values.filter(function (v) { return v !== null; }).length;
      body += '<tr><td class="ind"><span class="ind-label">' + esc(ind.label) + '</span><span class="raw-name">' + esc(ind.table) + '</span></td>';
      ind.values.forEach(function (v) {
        var best = v !== null && v === max && nonNull > 1 && max !== 0;
        body += '<td class="num' + (best ? ' best' : '') + '">' + fmtVal(v, ind) + '</td>';
      });
      var src = ind.source || {};
      body += '<td class="src"><b>' + esc(src.source_name || 'n.a.') + '</b>' + esc(src.year || '') + '</td></tr>';
    });
    body += '</tbody>';
    $('#cmp_table').innerHTML = head + body;

    // summary strip: first indicator per place
    var first = inds[0];
    var sum = $('#cmpSummary');
    sum.style.setProperty('--cols', String(places.length));
    sum.innerHTML = places.map(function (p, i) {
      return '<div class="sum-card"><span class="overline">' + esc(res.level_label) + ' · ' + esc(p.code) + '</span>' +
        '<div class="sum-name">' + esc(placeLabel(p)) + '</div>' +
        '<div class="sum-fig">' + (first ? fmtVal(first.values[i], first) : '<span class="na">n.a.</span>') +
        (first ? '<small>' + esc(first.unit || '') + '</small>' : '') + '</div>' +
        (first ? '<div class="sum-class">' + esc(first.label) + '</div>' : '') + '</div>';
    }).join('');

    var fs = first && first.source ? first.source : null;
    $('#cmpFootSrc').innerHTML = fs ? 'Fuente: <b>' + esc(fs.source_name || 'n.a.') + '</b>, ' + esc(fs.year || '') : '';
    if (res.persona_note) $('#cmp_footer').textContent = res.note + ' ' + res.persona_note;
    else $('#cmp_footer').textContent = res.note;
  }

  function refresh() {
    renderChips();
    renderOptions();
    renderSub();
    var seq = ++S.seq;
    if (S.selected.length < 2) {
      showAlert('Seleccione al menos 2 lugares del mismo nivel.');
      emptyTable('Seleccione al menos 2 lugares del mismo nivel.');
      return;
    }
    showAlert(null);
    var url = 'api/compare?level=' + encodeURIComponent(S.level) +
      '&ids=' + encodeURIComponent(S.selected.join(',')) +
      (S.persona ? '&persona=' + encodeURIComponent(S.persona) : '');
    $('#cmp_table').innerHTML = '<tbody><tr><td><div class="cmp-empty-table"><i class="fa-solid fa-circle-notch fa-spin" aria-hidden="true"></i>Cargando…</div></td></tr></tbody>';
    return fetch(url, { headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (x) {
        if (!S || seq !== S.seq) return;
        if (!x.ok) { showAlert(x.j && x.j.error ? x.j.error : 'Error al comparar.', 'danger'); emptyTable('Sin datos.'); return; }
        renderResult(x.j);
      })
      .catch(function (e) {
        if (!S || seq !== S.seq) return;
        showAlert(e.message, 'danger');
        emptyTable('Sin datos.');
      });
  }

  function loadPlaces(level) {
    if (S.places[level]) return Promise.resolve(S.places[level]);
    return window.T4E.api('api/compare/places?level=' + level).then(function (res) {
      if (S) S.places[level] = res;
      var meta = S && S.root.querySelector('.opt-meta[data-level="' + level + '"]');
      if (meta) meta.textContent = window.T4E.fmt(res.count);
      return res;
    });
  }

  function setLevel(level, preselect) {
    S.level = level;
    S.selected = [];
    S.search = '';
    $('#cmpSearch').value = '';
    var opts = S.root.querySelectorAll('#cmp_level .layer-option');
    for (var i = 0; i < opts.length; i++) {
      var inp = opts[i].querySelector('input');
      opts[i].classList.toggle('active', inp.value === level);
      inp.checked = inp.value === level;
    }
    renderOptions();
    return loadPlaces(level).then(function () {
      if (!S || S.level !== level) return;
      if (preselect) S.selected = (DEFAULT_SEL[level] || []).filter(function (id) { return !!placeById(id); });
      return refresh();
    });
  }

  function exportCsv() {
    var res = S.result;
    if (!res) return;
    var q = function (s) { s = String(s === null || s === undefined ? '' : s); return '"' + s.replace(/"/g, '""') + '"'; };
    var lines = [['Indicador'].concat(res.places.map(function (p) { return p.name + ' (' + p.code + ')'; }), ['Fuente', 'Año']).map(q).join(',')];
    res.indicators.forEach(function (ind) {
      lines.push([ind.label].concat(ind.values.map(function (v) { return v === null ? 'n.a.' : v; }),
        [ind.source && ind.source.source_name, ind.source && ind.source.year]).map(q).join(','));
    });
    lines.push(q(res.note));
    var blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'comparar_' + res.level + '.csv';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  function bind() {
    $('#cmp_level').addEventListener('change', function (e) {
      if (e.target && e.target.name === 'cmp_level') setLevel(e.target.value, false);
    });
    $('#cmpSearch').addEventListener('input', function (e) { S.search = e.target.value; renderOptions(); });
    $('#cmp_places').addEventListener('click', function (e) {
      var b = e.target.closest('.place-opt');
      if (!b || b.getAttribute('aria-disabled') === 'true') return;
      var id = b.getAttribute('data-id');
      var i = S.selected.indexOf(id);
      if (i >= 0) S.selected.splice(i, 1);
      else if (S.selected.length < MAX) S.selected.push(id);
      refresh();
      var again = S.root.querySelector('.place-opt[data-id="' + id.replace(/"/g, '') + '"]');
      if (again) again.focus();
    });
    $('#cmpChips').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-remove]');
      if (!b) return;
      var i = S.selected.indexOf(b.getAttribute('data-remove'));
      if (i >= 0) { S.selected.splice(i, 1); refresh(); }
    });
    $('#cmpClear').addEventListener('click', function () { S.selected = []; refresh(); });
    $('#cmp_persona_filter').addEventListener('change', function (e) { S.persona = e.target.value || ''; refresh(); });
    $('#cmpExport').addEventListener('click', exportCsv);
  }

  window.T4ECompareView = {
    init: function (root) {
      S = { root: root, level: 'department', selected: [], search: '', persona: '', places: {}, seq: 0, result: null };
      bind();
      window.T4E.api('api/personas').then(function (res) {
        if (!S) return;
        var sel = $('#cmp_persona_filter');
        sel.innerHTML = '<option value="">Todas</option>' + res.personas.map(function (p) {
          return '<option value="' + esc(p.persona) + '">' + esc(p.persona) + '</option>';
        }).join('');
      }).catch(function () { /* filter stays at Todas */ });
      // load counts for the other levels in the background
      ['municipality', 'localidad'].forEach(function (l) { loadPlaces(l).catch(function () {}); });
      return setLevel('department', true).catch(function (e) { showAlert(e.message, 'danger'); });
    },
    destroy: function () { S = null; }
  };
})();