/* Panel de aceptación — totals, axis test, latest load_batch, issues, Revalidar.
 * Uses relative URLs only (v1/...). Numbers formatted es-CO via T4E.fmt. */
(function () {
  'use strict';
  var root = null;
  var alive = false;
  var seq = 0;

  function $(sel) { return root ? root.querySelector(sel) : null; }
  function esc(s) { return T4E.esc(s); }
  function fmt(v) { return T4E.fmt(v); }
  function raw(s) { return '<span class="raw-name">' + esc(s) + '</span>'; }
  function fmtDate(v) {
    if (!v) return '—';
    var d = new Date(v);
    if (isNaN(d.getTime())) return esc(v);
    return d.toLocaleString('es-CO', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'America/Bogota' });
  }
  function signed(n) {
    if (n === null || n === undefined || isNaN(Number(n))) return '—';
    n = Number(n);
    return (n > 0 ? '+' : '') + fmt(n);
  }
  function deltaCls(n) { n = Number(n); return n > 0 ? 'delta-up' : (n < 0 ? 'delta-down' : 'delta-flat'); }
  function delta(n) { return '<span class="delta ' + deltaCls(n) + '">' + signed(n) + '</span>'; }
  function statePill(ok) {
    return '<span class="check-dot ' + (ok ? 'ok' : 'fail') + '" aria-hidden="true"></span>' +
      (ok ? '<span class="pill pill-success">OK</span>' : '<span class="pill pill-error">Falla</span>');
  }
  function batchPill(status) {
    if (status === 'validated') return '<span class="pill pill-success">Validado</span>';
    if (status === 'failed') return '<span class="pill pill-error">Fallido</span>';
    if (status === 'running') return '<span class="pill pill-warning pill-warn">En curso</span>';
    return '<span class="pill">' + esc(status || '—') + '</span>';
  }
  function live(msg) { var p = $('#acc-live'); if (p) p.textContent = msg; }
  function showError(msg) {
    var el = $('#acc-error');
    if (!el) return;
    if (!msg) { el.hidden = true; el.textContent = ''; return; }
    el.hidden = false;
    el.innerHTML = '<b>No se pudo completar la operación.</b> ' + esc(msg);
  }

  /* ---------- renderers ---------- */
  function renderSub(batch) {
    var el = $('#acc-sub');
    if (!el) return;
    if (!batch) { el.textContent = 'Todavía no hay ningún lote cargado.'; return; }
    el.innerHTML = 'Último lote ' + raw('#' + batch.id) +
      ' · terminado ' + fmtDate(batch.finished_at) + ' (COT)' +
      ' · última validación <span data-last-validation>' + fmtDate(batch.last_validation) + '</span>';
  }

  function renderVerdict(a) {
    var el = $('#acc-verdict');
    var failed = a.checks.filter(function (c) { return !c.ok; });
    var ok = !!a.all_green;
    el.classList.toggle('fail', !ok);
    el.classList.toggle('ok', ok);
    var title = ok
      ? 'Aceptación aprobada: ' + a.passed + ' de ' + a.total + ' comprobaciones superadas'
      : 'Aceptación rechazada: ' + a.passed + ' de ' + a.total + ' comprobaciones superadas';
    var parts = [];
    if (failed.length) {
      parts.push('Falla: ' + failed.map(function (c) {
        return raw(c.table) + ' — ' + esc(c.label) + (c.difference !== null ? ' (' + signed(c.difference) + ', tolerancia ' + esc(c.tolLabel) + ')' : '');
      }).join('; ') + '.');
    }
    parts.push('La prueba del eje de Bogotá ' + (a.axis_test.ok ? 'pasa' : '<b>falla</b>') + '.');
    if (a.missing_sources && a.missing_sources.length) {
      parts.push('Tablas sin fuente/año en ' + raw('meta_sources') + ': ' + a.missing_sources.map(raw).join(', ') + '.');
    } else {
      parts.push('Todas las tablas tienen fuente y año en ' + raw('meta_sources') + '.');
    }
    var b = a.batch;
    el.innerHTML =
      '<span class="check-dot ' + (ok ? 'ok' : 'fail') + '" aria-hidden="true"></span>' +
      '<div class="acc-verdict-body"><b>' + esc(title) + '</b><p>' + parts.join(' ') + '</p></div>' +
      '<div class="acc-verdict-meta"><b>' + (ok ? 'Lote aceptado' : 'Lote no aceptado') + '</b>' +
      'Calculado <span data-last-validation>' + fmtDate(a.computed_at) + '</span>' +
      (b ? '<br>Estado del lote: ' + esc(b.status) : '') + '</div>';
  }

  function renderStats(a, issues) {
    var v1 = a.checks.filter(function (c) { return c.group === 'v1'; }).length;
    var v2 = a.checks.length - v1;
    var failed = a.checks.filter(function (c) { return !c.ok; });
    var nErr = issues ? issues.counts.error : 0;
    var nInfo = issues ? issues.counts.info : 0;
    $('#acc-stats').innerHTML =
      '<div class="card"><span class="stat-label">Comprobaciones</span><div class="stat-value">' + fmt(a.total) + '</div>' +
        '<div class="stat-meta">' + v1 + ' totales v1 · ' + v2 + ' integridad v2 · + eje</div></div>' +
      '<div class="card"><span class="stat-label">Superadas</span><div class="stat-value">' + fmt(a.passed) + '</div>' +
        '<div><span class="delta ' + (failed.length ? 'delta-flat' : 'delta-up') + '">' + (failed.length ? 'pendiente' : 'todas en verde') + '</span></div>' +
        '<div class="stat-meta">Eje de Bogotá: ' + (a.axis_test.ok ? 'OK' : 'FALLA') + '</div></div>' +
      '<div class="card"><span class="stat-label">Fallidas</span><div class="stat-value">' + fmt(failed.length) + '</div>' +
        '<div><span class="delta ' + (failed.length ? 'delta-down' : 'delta-flat') + '">' + (failed.length ? 'fuera de tolerancia' : 'ninguna') + '</span></div>' +
        '<div class="stat-meta">' + (failed.length ? failed.map(function (c) { return raw(c.table); }).join(' ') : '—') + '</div></div>' +
      '<div class="card"><span class="stat-label">Incidencias abiertas</span><div class="stat-value">' + fmt(nErr) + '</div>' +
        '<div class="stat-meta">' + fmt(nErr) + ' errores · ' + fmt(nInfo) + ' excepciones aprobadas</div></div>';
  }

  function checkRow(c) {
    var check = esc(c.label) + (c.detail ? '<div class="acc-detail">' + esc(c.detail) + '</div>' : '');
    return '<tr class="' + (c.ok ? '' : 'acc-failrow') + '">' +
      '<td>' + raw(c.table) + '</td>' +
      '<td class="acc-check">' + check + '</td>' +
      '<td class="num">' + fmt(c.expected) + '</td>' +
      '<td class="num">' + fmt(c.actual) + '</td>' +
      '<td class="acc-tol">' + esc(c.tolLabel) + '</td>' +
      '<td class="num">' + delta(c.difference) + '</td>' +
      '<td class="acc-state">' + statePill(c.ok) + '</td></tr>';
  }
  function subRow(s) {
    var label = esc(s.label) + (s.filter ? ' ' + raw(s.filter) : '') +
      (s.maxPerPersona !== undefined ? '<div class="acc-detail">máx. por persona ' + signed(s.maxPerPersona) + (s.worst ? ' (' + esc(s.worst) + ')' : '') + '</div>' : '') +
      (s.codes && s.codes.length ? '<div class="acc-detail">códigos: ' + s.codes.slice(0, 12).map(raw).join(', ') + '</div>' : '');
    return '<tr class="row-sub"><td>↳</td><td class="acc-check">' + label + '</td>' +
      '<td class="num">' + fmt(s.expected) + '</td><td class="num">' + fmt(s.actual) + '</td>' +
      '<td class="acc-tol"></td><td class="num">' + delta(s.difference) + '</td>' +
      '<td class="acc-state">' + (s.ok ? '<span class="check-dot ok" aria-hidden="true"></span>' : '<span class="check-dot fail" aria-hidden="true"></span>') + '</td></tr>';
  }

  function renderTotals(a) {
    var groups = [
      { id: 'v1', title: 'Totales de carga', tag: 'v1' },
      { id: 'v2', title: 'Integridad geográfica', tag: 'v2' }
    ];
    var html = '';
    groups.forEach(function (g) {
      var list = a.checks.filter(function (c) { return c.group === g.id; });
      if (!list.length) return;
      html += '<tr class="acc-group"><td colspan="7">' + g.title + ' <small>' + g.tag + ' · ' + list.length + ' comprobaciones</small></td></tr>';
      list.forEach(function (c) {
        html += checkRow(c);
        (c.sub || []).forEach(function (s) { html += subRow(s); });
      });
    });
    var allOk = a.passed === a.total;
    html += '<tr class="row-total"><td colspan="2">Total comprobaciones superadas</td>' +
      '<td class="num">' + fmt(a.total) + '</td><td class="num">' + fmt(a.passed) + '</td><td class="acc-tol">todas</td>' +
      '<td class="num">' + delta(a.passed - a.total) + '</td><td class="acc-state">' + statePill(allOk) + '</td></tr>';
    $('#acc_totals_table tbody').innerHTML = html;
  }

  function renderAxis(ax) {
    var body = $('#acc-axis-body');
    body.classList.remove('acc-empty');
    var act = ax.actual;
    var sql = ax.sql || "SELECT ST_Latitude(point), ST_Longitude(point) FROM geo_municipality WHERE municipality_code = '11001'";
    body.innerHTML =
      '<pre class="acc-code">' + esc(sql) + '</pre>' +
      '<dl class="acc-dl">' +
        '<dt>Lugar</dt><dd>' + esc(ax.name || 'Bogotá, D.C.') + ' ' + raw('11001') + '</dd>' +
        '<dt>Esperado</dt><dd>lat ' + T4E.fmt(ax.expected.lat, 2) + ' · lon ' + T4E.fmt(ax.expected.lon, 2) + ' (±' + T4E.fmt(ax.expected.tolerance, 2) + ')</dd>' +
        '<dt>Real</dt><dd>' + (act ? 'lat ' + act.lat.toFixed(4).replace('.', ',') + ' · lon ' + act.lon.toFixed(4).replace('.', ',') : esc(ax.message || 'sin punto')) + '</dd>' +
        '<dt>SRID</dt><dd>' + (act ? esc(act.srid) : '—') + '</dd>' +
        '<dt>Orden de ejes</dt><dd>' + (ax.ok ? 'long-lat correcto' : '¿invertido?') + '</dd>' +
      '</dl>' +
      '<div class="acc-axis-result">' + statePill(ax.ok) + ' <span class="acc-detail" style="display:inline">' +
        (ax.ok ? 'El punto de Bogotá coincide con lat 4,31 / lon −74,18.' : 'El punto de Bogotá NO coincide: revise axis-order=long-lat.') + '</span></div>';
  }

  function renderBatch(b) {
    var body = $('#acc-batch-body');
    var pill = $('#acc-batch-pill');
    if (!b) { body.innerHTML = 'Todavía no hay ningún lote.'; pill.innerHTML = ''; return; }
    body.classList.remove('acc-empty');
    pill.innerHTML = batchPill(b.status);
    var dur = '';
    if (b.started_at && b.finished_at) {
      var s = Math.max(0, Math.round((new Date(b.finished_at) - new Date(b.started_at)) / 1000));
      dur = s >= 60 ? Math.floor(s / 60) + ' min ' + (s % 60) + ' s' : s + ' s';
    }
    body.innerHTML =
      '<div class="acc-batch-figs">' +
        '<div><span class="stat-label">Filas cargadas</span><div class="fig">' + fmt(b.rows_loaded) + '</div></div>' +
        '<div><span class="stat-label">Errores</span><div class="fig">' + fmt(b.errors) + '</div></div>' +
        '<div><span class="stat-label">Excepciones</span><div class="fig">' + fmt(b.infos) + ' <small>info</small></div></div>' +
      '</div>' +
      '<dl class="acc-dl">' +
        '<dt>Lote</dt><dd>' + raw('#' + b.id) + ' · ' + esc(b.country_code || '') + '</dd>' +
        '<dt>Origen</dt><dd>' + raw(b.source_file || '—') + '</dd>' +
        '<dt>Inicio</dt><dd>' + fmtDate(b.started_at) + '</dd>' +
        '<dt>Fin</dt><dd>' + fmtDate(b.finished_at) + (dur ? ' · ' + esc(dur) : '') + '</dd>' +
        '<dt>Estado</dt><dd>' + batchPill(b.status) + '</dd>' +
        (b.previous ? '<dt>Lote anterior</dt><dd>' + raw('#' + b.previous.id) + ' · ' + esc(b.previous.status) + '</dd>' : '') +
        (b.notes ? '<dt>Notas</dt><dd class="acc-notes">' + esc(b.notes) + '</dd>' : '') +
      '</dl>';
  }

  function issueItem(i) {
    var isErr = i.severity === 'error';
    var meta = [raw(i.issue_type)];
    if (i.table_name) meta.push(raw(i.table_name + (i.column_name ? '.' + i.column_name : '')));
    if (i.code_value) meta.push('código ' + raw(i.code_value));
    if (i.expected_value !== null && i.expected_value !== undefined) meta.push('esperado ' + esc(i.expected_value));
    if (i.actual_value !== null && i.actual_value !== undefined) meta.push((isErr ? 'real ' : 'filas ') + esc(i.actual_value));
    return '<li class="acc-issue">' +
      (isErr ? '<span class="pill pill-error">Error</span>' : '<span class="pill pill-info">Sin geografía</span>') +
      '<div><div class="acc-issue-msg">' + esc(i.message) + '</div><div class="acc-issue-meta">' + meta.join(' · ') + '</div></div>' +
      '<span class="acc-issue-meta">' + fmtDate(i.created_at) + '</span></li>';
  }

  function renderIssues(res) {
    var errs = res.issues.filter(function (i) { return i.severity === 'error'; });
    var infos = res.issues.filter(function (i) { return i.severity !== 'error'; });
    $('#acc-issues-errors').innerHTML = errs.length ? errs.map(issueItem).join('')
      : '<li class="acc-empty"><span class="check-dot ok" aria-hidden="true"></span> Sin errores en el lote #' + esc(res.batch_id || '—') + '.</li>';
    $('#acc-issues-infos').innerHTML = infos.length ? infos.map(issueItem).join('')
      : '<li class="acc-empty">Sin excepciones registradas. Pulse «Revalidar» para registrarlas.</li>';
    $('#acc-err-count').textContent = fmt(res.counts.error) + ' errores';
    $('#acc-info-count').textContent = fmt(res.counts.info) + ' excepciones aprobadas (severity info)';
    $('#acc-issues-note').textContent = 'Lote #' + (res.batch_id || '—') + ' · las excepciones aprobadas no bloquean la aceptación.';
  }

  /* ---------- data ---------- */
  function refresh() {
    var my = ++seq;
    showError(null);
    return Promise.all([
      T4E.api('v1/acceptance'),
      T4E.api('v1/issues').catch(function () { return { batch_id: null, issues: [], counts: { error: 0, info: 0 } }; })
    ]).then(function (r) {
      if (!alive || my !== seq) return;
      var a = r[0]; var issues = r[1];
      renderSub(a.batch);
      renderVerdict(a);
      renderStats(a, issues);
      renderTotals(a);
      renderAxis(a.axis_test);
      renderBatch(a.batch);
      renderIssues(issues);
      var ft = $('#acc-foot-time');
      if (ft) ft.textContent = 'Calculado ' + fmtDate(a.computed_at) + ' (COT)';
      live(a.all_green ? 'Aceptación aprobada' : 'Aceptación rechazada: ' + a.passed + ' de ' + a.total);
    }).catch(function (e) {
      if (!alive || my !== seq) return;
      showError(e.message);
      var v = $('#acc-verdict');
      if (v) {
        v.classList.add('fail');
        v.innerHTML = '<span class="check-dot fail" aria-hidden="true"></span><div class="acc-verdict-body"><b>No se pudieron calcular las comprobaciones</b><p>' + esc(e.message) + '</p></div>';
      }
    });
  }

  /* ---------- busy state shared by Revalidar / Recargar CSV ---------- */
  var BTN_LABELS = { '#acc-btn-revalidate': 'Revalidar', '#acc-btn-reload': 'Recargar CSV' };
  function isBusy() {
    var a = $('#acc-btn-revalidate'); var b = $('#acc-btn-reload');
    return (a && a.disabled) || (b && b.disabled);
  }
  function setBusy(activeSel, label) {
    var page = $('#acc-page') || root;
    Object.keys(BTN_LABELS).forEach(function (sel) {
      var b = $(sel);
      if (!b) return;
      b.disabled = true;
      if (sel === activeSel) {
        b.classList.add('is-busy');
        b.setAttribute('aria-busy', 'true');
        var l = b.querySelector('.lbl');
        if (l) l.textContent = label;
      }
    });
    if (page) page.classList.add('is-running');
  }
  function clearBusy() {
    if (!alive) return;
    var page = $('#acc-page') || root;
    Object.keys(BTN_LABELS).forEach(function (sel) {
      var b = $(sel);
      if (!b) return;
      b.disabled = false;
      b.classList.remove('is-busy');
      b.removeAttribute('aria-busy');
      var l = b.querySelector('.lbl');
      if (l) l.textContent = BTN_LABELS[sel];
    });
    if (page) page.classList.remove('is-running');
  }

  function revalidate() {
    if (!$('#acc-btn-revalidate') || isBusy()) return;
    setBusy('#acc-btn-revalidate', 'Validando…');
    live('Revalidando el último lote…');
    showError(null);
    T4E.api('v1/validate', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: '{}' })
      .then(function (r) {
        live('Lote #' + r.batch_id + ' revalidado: ' + r.status + ', ' + r.errors + ' errores, ' + r.infos + ' excepciones');
        return refresh();
      })
      .catch(function (e) { showError(e.message); })
      .then(clearBusy);
  }

  /* ---------- Recargar CSV (POST v1/load) ---------- */
  function hideReload() {
    var el = $('#acc-reload');
    if (el) { el.hidden = true; el.innerHTML = ''; }
  }
  function renderReload(r, secs) {
    var el = $('#acc-reload');
    if (!el) return;
    var tables = r.tables || [];
    var empty = tables.filter(function (t) { return Number(t.inserted) === 0; });
    var noted = tables.filter(function (t) { return t.note; });
    var v = r.validation;
    var tRow = function (t) {
      return '<li>' + raw(t.table) + ' <span class="acc-detail" style="display:inline">CSV ' + fmt(t.csv_rows) +
        ' · insertadas ' + fmt(t.inserted) + (t.note ? ' · ' + esc(t.note) : '') + '</span></li>';
    };
    el.innerHTML =
      '<div class="acc-card-head"><div><span class="overline">POST v1/load · flow_load</span>' +
        '<h2 class="card-title" id="acc-reload-title"><i class="fa-solid fa-circle-check acc-reload-ok" aria-hidden="true"></i> Recarga completada · lote ' + raw('#' + r.batch_id) + '</h2></div>' +
        '<button type="button" class="btn btn-secondary btn-sm acc-reload-close" aria-label="Cerrar resumen"><i class="fa-solid fa-xmark" aria-hidden="true"></i></button></div>' +
      '<div class="acc-batch-figs">' +
        '<div><span class="stat-label">Tablas</span><div class="fig">' + fmt(tables.length) + '</div></div>' +
        '<div><span class="stat-label">Filas cargadas</span><div class="fig">' + fmt(r.rows_loaded) + '</div></div>' +
        '<div><span class="stat-label">Duración</span><div class="fig">' + fmt(secs) + ' <small>s</small></div></div>' +
      '</div>' +
      '<dl class="acc-dl">' +
        '<dt>Validación</dt><dd>' + (v
          ? batchPill(v.status) + ' · ' + fmt(v.passed) + ' de ' + fmt(v.total) + ' comprobaciones · ' + fmt(v.errors) + ' errores · ' + fmt(v.infos) + ' excepciones'
          : '<span class="pill pill-warning pill-warn">Sin validación</span>') + '</dd>' +
        '<dt>Tablas con 0 filas</dt><dd>' + (empty.length ? fmt(empty.length) : 'ninguna') + '</dd>' +
        '<dt>Tablas con notas</dt><dd>' + (noted.length ? fmt(noted.length) : 'ninguna') + '</dd>' +
      '</dl>' +
      (empty.length ? '<div class="acc-reload-list"><h4>Tablas con 0 filas</h4><ul>' + empty.map(tRow).join('') + '</ul></div>' : '') +
      (noted.length ? '<div class="acc-reload-list"><h4>Tablas con notas</h4><ul>' + noted.map(tRow).join('') + '</ul></div>' : '');
    el.hidden = false;
    var close = el.querySelector('.acc-reload-close');
    if (close) close.addEventListener('click', hideReload);
  }

  function reload() {
    if (!$('#acc-btn-reload') || isBusy()) return;
    var ok = window.confirm('¿Recargar los 27 CSV en MySQL?\n\nSe reemplazan los datos de las tablas con el contenido de data/geodb-v2/csv, se crea un nuevo load_batch y se valida. Puede tardar un par de minutos.');
    if (!ok) return;
    setBusy('#acc-btn-reload', 'Recargando…');
    live('Recargando los CSV en MySQL…');
    showError(null);
    hideReload();
    var t0 = Date.now();
    T4E.api('v1/load', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: '{}' })
      .then(function (r) {
        if (!alive) return;
        var secs = Math.round((Date.now() - t0) / 1000);
        renderReload(r, secs);
        live('Lote #' + r.batch_id + ' cargado: ' + r.rows_loaded + ' filas' +
          (r.validation ? ', validación ' + r.validation.status + ' (' + r.validation.errors + ' errores)' : ''));
        return refresh();
      })
      .catch(function (e) { showError(e.message); })
      .then(clearBusy);
  }

  window.T4EAcceptancePanel = {
    init: function (r) {
      root = r;
      alive = true;
      var btn = $('#acc-btn-revalidate');
      if (btn) btn.addEventListener('click', revalidate);
      var rbtn = $('#acc-btn-reload');
      if (rbtn) rbtn.addEventListener('click', reload);
      return refresh();
    },
    destroy: function () { alive = false; root = null; seq++; },
    refresh: function () { return refresh(); }
  };
})();