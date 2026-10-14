/* think4ever · Geo DB Colombia — Mapa (map_view)
 * 3 groups of layers (Departamentos / Ciudades / Bogotá por localidad), persona filter,
 * quintile legend (rule_quintile_legend), tooltip and place card.
 * Read-only API: api/map/departments, api/map/municipalities, api/map/localidades, api/personas.
 * All URLs are relative (app served behind /run/<projectId>/).
 */
(function () {
  'use strict';

  // ---------- design constants ----------
  var RAMP = ['#E9EEF7', '#B9C7E3', '#7F98C9', '#3F5E9E', '#11255A'];
  var NODATA = '#DDDDDD';
  var POLY_BASE = { color: '#fff', weight: 0.8, opacity: 1, fillOpacity: 0.85 };
  var HOVER = { color: '#11255A', weight: 2 };
  var SELECTED = { color: '#E8772E', weight: 2.5 };
  var CIRCLE = { fillColor: '#3F5E9E', fillOpacity: 0.55, color: '#11255A', weight: 1, opacity: 1 };
  var CIRCLE_EVENT = { color: '#E8772E', weight: 2.5 };
  var CIRCLE_MAX_R = 26;
  var CIRCLE_MIN_R = 2.5;
  var INITIAL_VIEW = [4.6, -74.1];
  var INITIAL_ZOOM = 5;
  var NO_POINT_MUNI = '27493';
  var HIDDEN_IN_SELECTOR = { contracts_2025: true, tech_events: true }; // shown in the place card only
  var OSM_ATTR = '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';

  var GROUPS = {
    dept: { label: 'Departamentos', api: 'api/map/departments', personaAware: true, placeLabel: 'departamentos' },
    city: { label: 'Ciudades', api: 'api/map/municipalities', personaAware: true, placeLabel: 'ciudades' },
    bog: { label: 'Ciudades por zona', api: 'api/map/localidades', personaAware: true, placeLabel: 'zonas' }
  };
  var GROUP_ORDER = ['dept', 'city', 'bog'];

  // Indicators whose value depends on the persona filter, per layer group.
  var PERSONA_KEYS = {
    dept: { personas: true },
    city: { personas_metro: true },
    bog: { personas13: true, personas13_per_1000_employed: true }
  };
  var PERSONA_DEFAULT_KEY = { dept: 'personas', city: 'personas_metro', bog: 'personas13' };
  var PERSONA_COVERAGE = {
    dept: 'los 33 departamentos',
    city: 'las áreas metropolitanas con dato en <span class="raw-name">fact_persona_metro</span>',
    bog: 'solo las localidades de Bogotá (Encuesta Multipropósito 2021)'
  };
  var BOGOTA_MUNI = '11001';
  var PERSONA_ICON = '<i class="fa-solid fa-user lo-persona" style="margin-left:6px;color:#E8772E;font-size:11px" title="Depende del filtro por persona" aria-label="Depende del filtro por persona"></i>';
  function isPersonaKey(group, key) { return !!(PERSONA_KEYS[group] && PERSONA_KEYS[group][key]); }

  var nf = [
    new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }),
    new Intl.NumberFormat('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 1 }),
    new Intl.NumberFormat('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  ];

  var S = null; // page state

  // ---------- helpers ----------
  function esc(s) {
    if (window.T4E && T4E.esc) return T4E.esc(s);
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function api(url) {
    if (window.T4E && T4E.api) return T4E.api(url);
    return fetch(url).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url); return r.json(); });
  }
  function isNum(v) { return v !== null && v !== undefined && v !== '' && !isNaN(Number(v)); }
  function digitsFor(ind) {
    if (!ind) return 0;
    if (ind.key === 'secop_value_bn') return 2;
    if (ind.unit === '%' || ind.key === 'personas13_per_1000_employed') return 1;
    return 0;
  }
  function fmtVal(ind, v) {
    if (!isNum(v)) return null;
    var s = nf[digitsFor(ind)].format(Number(v));
    if (ind && ind.unit === '%') s += ' %';
    return s;
  }
  function fmtNum(ind, v) { return isNum(v) ? nf[digitsFor(ind)].format(Number(v)) : 'n.a.'; }
  function fmtDate(d) {
    if (!d) return '';
    var m = String(d).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return String(d);
    var dt = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
    return dt.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });
  }
  function $(sel) { return S.root.querySelector(sel); }

  // ---------- quintiles (rule_quintile_legend) ----------
  function quantile(sorted, p) {
    if (!sorted.length) return null;
    var pos = (sorted.length - 1) * p;
    var lo = Math.floor(pos), hi = Math.ceil(pos);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
  }
  function computeQuintiles(values) {
    var arr = values.filter(isNum).map(Number).sort(function (a, b) { return a - b; });
    if (!arr.length) return null;
    return {
      min: arr[0],
      max: arr[arr.length - 1],
      n: arr.length,
      breaks: [quantile(arr, 0.2), quantile(arr, 0.4), quantile(arr, 0.6), quantile(arr, 0.8)]
    };
  }
  function classOf(q, v) {
    if (!q || !isNum(v)) return 0; // 0 = sin datos
    v = Number(v);
    for (var i = 0; i < 4; i++) if (v <= q.breaks[i]) return i + 1;
    return 5;
  }
  function colorFor(q, v) {
    var c = classOf(q, v);
    return c ? RAMP[c - 1] : NODATA;
  }

  // ---------- data access ----------
  function dataUrl(group) {
    var g = GROUPS[group];
    if (g.personaAware && S.persona) return g.api + '?persona=' + encodeURIComponent(S.persona);
    return g.api;
  }
  function places(group) {
    var d = S.data[group];
    if (!d) return [];
    if (group === 'city') {
      return (d.municipalities || []).filter(function (m) {
        return m.municipality_code !== NO_POINT_MUNI && isNum(m.lat) && isNum(m.lon);
      }).map(function (m) {
        return { id: String(m.municipality_code), name: m.name, raw: m, values: m.values || {} };
      });
    }
    return (d.features || []).filter(function (f) { return f && f.geometry; }).map(function (f) {
      var p = f.properties || {};
      var id = group === 'dept' ? p.department_code : p.zone_id;
      return { id: String(id), name: p.name, raw: p, feature: f, values: p.values || {} };
    });
  }
  function placeById(group, id) {
    var list = places(group);
    for (var i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
    return null;
  }
  function indicators(group) {
    var d = S.data[group];
    return (d && d.indicators) || [];
  }
  function selectable(group) {
    return indicators(group).filter(function (i) { return !HIDDEN_IN_SELECTOR[i.key]; });
  }
  function activeIndicator() {
    var list = indicators(S.group);
    for (var i = 0; i < list.length; i++) if (list[i].key === S.key) return list[i];
    return list[0] || null;
  }

  // ---------- panel: layer selector ----------
  function renderLayerOptions() {
    var total = 0;
    GROUP_ORDER.forEach(function (g) {
      var box = $('[data-group-list="' + g + '"]');
      if (!box) return;
      var list = selectable(g);
      total += list.length;
      var html = '<span class="layer-group-title" id="lg-' + g + '">' + esc(GROUPS[g].label) + '</span>';
      list.forEach(function (ind) {
        var on = S.group === g && S.key === ind.key;
        var id = 'lo-' + g + '-' + ind.key;
        html += '<label class="layer-option' + (on ? ' active' : '') + '" for="' + id + '">' +
          '<input type="radio" name="map-layer" id="' + id + '" value="' + g + ':' + esc(ind.key) + '"' + (on ? ' checked' : '') + '>' +
          '<span class="lo-text"><span class="lo-name">' + esc(ind.label) + (isPersonaKey(g, ind.key) ? PERSONA_ICON : '') + '</span>' +
          '<span class="lo-raw raw-name">' + esc(ind.table) + ' · ' + esc(ind.column) + '</span></span></label>';
      });
      if (!list.length) html += '<p class="legend-note">Sin indicadores disponibles.</p>';
      box.innerHTML = html;
    });
    var c = $('#layer-count');
    if (c) c.textContent = total + ' indicadores';
  }

  function onLayerChange(e) {
    var t = e.target;
    if (!t || t.name !== 'map-layer') return;
    var parts = t.value.split(':');
    var prevGroup = S.group;
    S.group = parts[0];
    S.key = parts[1];
    if (prevGroup !== S.group) S.selected = null;
    var opts = S.root.querySelectorAll('.layer-option');
    for (var i = 0; i < opts.length; i++) {
      var inp = opts[i].querySelector('input');
      opts[i].classList.toggle('active', !!(inp && inp.checked));
    }
    draw(prevGroup !== S.group);
  }

  // ---------- panel: persona filter ----------
  function renderPersonaOptions(list) {
    var sel = $('#map_persona_filter');
    var html = '<option value="">Todas</option>';
    (list || []).forEach(function (p) {
      html += '<option value="' + esc(p.persona) + '">' + esc(p.persona) + (p.ring ? ' (' + esc(p.ring) + ')' : '') + '</option>';
    });
    sel.innerHTML = html;
    sel.value = S.persona || '';
  }

  function renderPersonaNote() {
    var note = $('#persona-note');
    if (!note) return;
    note.className = 'persona-note';
    var icon = '<i class="fa-solid fa-user" style="color:#E8772E" aria-hidden="true"></i>';
    if (!S.persona) {
      note.innerHTML = 'Mostrando <b>Todas</b> las 13 personas. Los indicadores marcados con ' + icon + ' dependen de este filtro.';
      return;
    }
    var html;
    if (isPersonaKey(S.group, S.key)) {
      html = 'El indicador actual muestra solo <b>' + esc(S.persona) + '</b>. Cobertura: ' + PERSONA_COVERAGE[S.group] + '.';
    } else {
      html = 'El indicador actual <b>no depende</b> de la persona. Elija uno marcado con ' + icon + ' para ver <b>' + esc(S.persona) + '</b> (' + PERSONA_COVERAGE[S.group] + ').';
    }
    if (S.group === 'bog') {
      html += ' Medellín, Cali, Barranquilla y Bucaramanga no tienen dato por zona (se ven en gris).';
    }
    note.innerHTML = html;
  }

  function onPersonaChange() {
    var val = $('#map_persona_filter').value;
    S.persona = val;
    // Make the effect visible: jump to the persona indicator of the current layer.
    if (val && !isPersonaKey(S.group, S.key)) S.key = PERSONA_DEFAULT_KEY[S.group];
    var refit = S.group === 'bog';
    renderPersonaNote();
    var seq = ++S.seq;
    setLoading(true);
    Promise.all([api(dataUrl('dept')), api(dataUrl('city')), api(dataUrl('bog'))]).then(function (res) {
      if (!S || seq !== S.seq) return;
      S.data.dept = res[0];
      S.data.city = res[1];
      S.data.bog = res[2];
      renderLayerOptions();
      draw(false, refit);
    }).catch(function (err) {
      if (!S || seq !== S.seq) return;
      showError(err);
    }).then(function () {
      if (S && seq === S.seq) setLoading(false);
    });
  }

  // ---------- map ----------
  function setLoading(on, msg) {
    var el = $('#map-loading');
    if (!el) return;
    if (msg) el.innerHTML = '<span>' + msg + '</span>';
    el.hidden = !on;
  }
  function showError(err) {
    console.error(err);
    setLoading(true, '<i class="fa-solid fa-triangle-exclamation" aria-hidden="true"></i>No se pudieron cargar los datos del mapa. <small class="raw-name">' + esc(err && err.message) + '</small>');
  }

  function setAttribution(group) {
    var ctl = S.map.attributionControl;
    S.extraAttr.forEach(function (a) { ctl.removeAttribution(a); });
    S.extraAttr = [];
    var d = S.data[group];
    var list = (d && d.attribution) || [];
    list.forEach(function (a) {
      if (/OpenStreetMap/i.test(a)) return; // tile layer already carries it
      ctl.addAttribution(a);
      S.extraAttr.push(a);
    });
  }

  function polygonStyle(id, value) {
    var st = {
      fillColor: colorFor(S.q, value),
      color: POLY_BASE.color, weight: POLY_BASE.weight, opacity: POLY_BASE.opacity, fillOpacity: POLY_BASE.fillOpacity
    };
    if (S.selected === id) { st.color = SELECTED.color; st.weight = SELECTED.weight; }
    return st;
  }

  function circleStyle(place) {
    var v = place.values[S.key];
    var st = {
      fillColor: isNum(v) && Number(v) > 0 ? CIRCLE.fillColor : NODATA,
      fillOpacity: CIRCLE.fillOpacity, color: CIRCLE.color, weight: CIRCLE.weight, opacity: CIRCLE.opacity
    };
    if (place.raw.has_event) { st.color = CIRCLE_EVENT.color; st.weight = CIRCLE_EVENT.weight; }
    if (S.selected === place.id) { st.color = SELECTED.color; st.weight = SELECTED.weight + 0.5; }
    return st;
  }

  function radiusFor(v) {
    if (!isNum(v) || Number(v) <= 0 || !S.cmax) return null;
    return Math.max(CIRCLE_MIN_R, CIRCLE_MAX_R * Math.sqrt(Number(v) / S.cmax));
  }

  function tooltipHtml(place, ind) {
    var v = fmtVal(ind, place.values[S.key]);
    return '<b>' + esc(place.name) + '</b><br>' +
      '<span class="tnum" style="font-variant-numeric:tabular-nums">' + (v ? esc(v) + (ind && ind.unit && ind.unit !== '%' ? ' ' + esc(ind.unit) : '') : 'Sin datos') + '</span>' +
      (S.group === 'city' && place.raw.has_event ? '<br><span style="color:#E8772E">● evento tech 2026</span>' : '');
  }

  function restyle(id) {
    if (!id || !S.byId[id]) return;
    var entry = S.byId[id];
    entry.layer.setStyle(entry.styleFn());
  }

  function bogotaBounds() {
    var b = null;
    Object.keys(S.byId).forEach(function (id) {
      var e = S.byId[id];
      if (!e || !e.place || String(e.place.raw.municipality_code) !== BOGOTA_MUNI || !e.layer.getBounds) return;
      var lb = e.layer.getBounds();
      if (!lb.isValid()) return;
      if (b) b.extend(lb); else b = L.latLngBounds(lb.getSouthWest(), lb.getNorthEast());
    });
    return b;
  }

  function draw(groupChanged, refit) {
    if (!S || !S.map) return;
    var ind = activeIndicator();
    if (ind) S.key = ind.key;
    if (S.layer) { S.map.removeLayer(S.layer); S.layer = null; }
    S.byId = {};
    var list = places(S.group);

    if (S.group === 'city') {
      var vals = list.map(function (p) { return p.values[S.key]; }).filter(function (v) { return isNum(v) && Number(v) > 0; }).map(Number);
      S.cmax = vals.length ? Math.max.apply(null, vals) : 0;
      S.q = computeQuintiles(vals);
      // draw big circles first so small ones stay clickable
      var drawn = list.filter(function (p) { return radiusFor(p.values[S.key]) || p.raw.has_event; })
        .sort(function (a, b) { return (Number(b.values[S.key]) || 0) - (Number(a.values[S.key]) || 0); });
      var group = L.featureGroup();
      drawn.forEach(function (p) {
        var r = radiusFor(p.values[S.key]) || 4;
        var styleFn = function () { return circleStyle(p); };
        var m = L.circleMarker([Number(p.raw.lat), Number(p.raw.lon)], Object.assign({ radius: r }, styleFn()));
        m.bindTooltip(tooltipHtml(p, ind), { className: 't4e-tip', sticky: true, direction: 'top', opacity: 1 });
        m.on('mouseover', function () { if (S.selected !== p.id) m.setStyle(HOVER); });
        m.on('mouseout', function () { m.setStyle(styleFn()); });
        m.on('click', function () { selectPlace(p.id, false); });
        S.byId[p.id] = { layer: m, styleFn: styleFn, place: p };
        group.addLayer(m);
      });
      S.drawnCount = drawn.length;
      S.layer = group.addTo(S.map);
    } else {
      S.q = computeQuintiles(list.map(function (p) { return p.values[S.key]; }));
      S.cmax = 0;
      var byFeature = {};
      list.forEach(function (p) { byFeature[p.id] = p; });
      S.layer = L.geoJSON({ type: 'FeatureCollection', features: list.map(function (p) { return p.feature; }) }, {
        style: function (f) {
          var id = String(S.group === 'dept' ? f.properties.department_code : f.properties.zone_id);
          return polygonStyle(id, (f.properties.values || {})[S.key]);
        },
        onEachFeature: function (f, layer) {
          var id = String(S.group === 'dept' ? f.properties.department_code : f.properties.zone_id);
          var p = byFeature[id];
          var styleFn = function () { return polygonStyle(id, p.values[S.key]); };
          layer.bindTooltip(tooltipHtml(p, ind), { className: 't4e-tip', sticky: true, direction: 'top', opacity: 1 });
          layer.on('mouseover', function () {
            if (S.selected !== id) { layer.setStyle(HOVER); layer.bringToFront(); }
          });
          layer.on('mouseout', function () {
            layer.setStyle(styleFn());
            if (S.selected && S.byId[S.selected] && S.byId[S.selected].layer.bringToFront) S.byId[S.selected].layer.bringToFront();
          });
          layer.on('click', function () { selectPlace(id, false); });
          S.byId[id] = { layer: layer, styleFn: styleFn, place: p };
        }
      }).addTo(S.map);
      S.drawnCount = list.length;
    }

    if (S.selected && S.byId[S.selected] && S.byId[S.selected].layer.bringToFront) S.byId[S.selected].layer.bringToFront();

    setAttribution(S.group);

    if (groupChanged || S.firstDraw || refit) {
      var bb = S.group === 'bog' && S.persona ? bogotaBounds() : null;
      if (bb && bb.isValid()) {
        S.map.fitBounds(bb, { padding: [24, 24] });
      } else if (S.group === 'bog' && S.layer.getBounds && S.layer.getBounds().isValid()) {
        S.map.fitBounds(S.layer.getBounds(), { padding: [24, 24] });
      } else if (groupChanged && S.lastGroup === 'bog') {
        S.map.setView(INITIAL_VIEW, INITIAL_ZOOM);
      }
      S.firstDraw = false;
    }
    S.lastGroup = S.group;

    var mapEl = $('#map');
    if (mapEl && ind) mapEl.setAttribute('aria-label', 'Mapa de Colombia con la capa ' + GROUPS[S.group].label + ' — ' + ind.label);

    renderOverlay(ind);
    renderLegend(ind);
    renderFooter(ind);
    renderPersonaNote();
    renderGeoNote();
    renderJump();
    renderPlace();
  }

  function selectPlace(id, zoom) {
    var prev = S.selected;
    S.selected = id;
    if (prev && prev !== id) restyle(prev);
    restyle(id);
    var entry = S.byId[id];
    if (entry && entry.layer.bringToFront) entry.layer.bringToFront();
    if (zoom && entry) {
      if (entry.layer.getBounds) S.map.fitBounds(entry.layer.getBounds(), { padding: [40, 40], maxZoom: S.group === 'bog' ? 13 : 8 });
      else if (entry.layer.getLatLng) S.map.setView(entry.layer.getLatLng(), Math.max(S.map.getZoom(), 8));
    }
    var jump = $('#place-jump');
    if (jump) jump.value = id || '';
    renderPlace();
  }

  function clearSelection() {
    var prev = S.selected;
    S.selected = null;
    restyle(prev);
    var jump = $('#place-jump');
    if (jump) jump.value = '';
    renderPlace();
  }

  // ---------- overlay / legend / footer / notes ----------
  function renderOverlay(ind) {
    var el = $('#map-overlay');
    if (!el || !ind) return;
    var list = places(S.group);
    var withData = list.filter(function (p) { return isNum(p.values[S.key]); }).length;
    el.innerHTML = '<span class="overline">' + esc(GROUPS[S.group].label) + (S.persona && GROUPS[S.group].personaAware ? ' · ' + esc(S.persona) : '') + '</span>' +
      '<div class="mo-title">' + esc(ind.label) + '</div>' +
      '<div class="mo-meta">' + nf[0].format(withData) + ' de ' + nf[0].format(list.length) + ' ' + GROUPS[S.group].placeLabel + ' con datos · ' + esc(ind.unit || '') + '</div>';
  }

  function legendRange(ind, a, b) {
    return '<span class="tnum">' + esc(fmtNum(ind, a)) + ' – ' + esc(fmtNum(ind, b)) + '</span>';
  }

  function renderLegend(ind) {
    var el = $('#map_legend_body');
    if (!el || !ind) return;
    var html = '<div class="legend-head">' + esc(ind.label) + '</div>' +
      '<div class="legend-unit">' + esc(ind.unit || '') + ' · <span class="raw-name">' + esc(ind.table) + '.' + esc(ind.column) + '</span></div>';

    if (S.group === 'city') {
      if (S.cmax > 0) {
        var steps = [S.cmax, S.cmax / 4, S.cmax / 16];
        html += '<div class="legend-sizes" aria-label="Tamaño del círculo proporcional a la raíz cuadrada del valor">';
        steps.forEach(function (v) {
          var r = radiusFor(v);
          var d = Math.ceil(r * 2 + 4);
          html += '<figure><svg width="' + d + '" height="' + d + '" aria-hidden="true"><circle cx="' + (d / 2) + '" cy="' + (d / 2) + '" r="' + r.toFixed(1) +
            '" fill="#3F5E9E" fill-opacity="0.55" stroke="#11255A" stroke-width="1"/></svg><figcaption>' + esc(fmtNum(ind, Math.round(v))) + '</figcaption></figure>';
        });
        html += '</div>';
      }
      html += '<div class="legend-item"><span class="swatch city" aria-hidden="true"></span><span>Ciudad (radio ∝ √valor)</span></div>' +
        '<div class="legend-item"><span class="swatch city-event" aria-hidden="true"></span><span>Ciudad con evento en <span class="raw-name">fact_tech_events</span></span></div>' +
        '<div class="legend-item"><span class="swatch nd" aria-hidden="true"></span><span>Sin datos</span></div>' +
        '<p class="legend-note">El tamaño del círculo es proporcional a la raíz cuadrada del valor. El municipio 27493 (sin punto) y "Rest of the country" no se dibujan.</p>';
    } else {
      if (S.q) {
        var lo = [S.q.min, S.q.breaks[0], S.q.breaks[1], S.q.breaks[2], S.q.breaks[3]];
        var hi = [S.q.breaks[0], S.q.breaks[1], S.q.breaks[2], S.q.breaks[3], S.q.max];
        for (var i = 0; i < 5; i++) {
          html += '<div class="legend-item"><span class="swatch r' + (i + 1) + '" aria-hidden="true"></span>' + legendRange(ind, lo[i], hi[i]) + '</div>';
        }
      }
      html += '<div class="legend-item"><span class="swatch nd" aria-hidden="true"></span><span>Sin datos</span></div>' +
        '<p class="legend-note">5 clases por quintiles' + (S.q ? ' (' + nf[0].format(S.q.n) + ' lugares con datos)' : '') + '.</p>';
    }
    el.innerHTML = html;
  }

  function renderFooter(ind) {
    var el = $('#map_source_footer');
    if (!el) return;
    var src = (ind && ind.source) || {};
    var html = '';
    if (ind) {
      html += 'Fuente: <b>' + esc(src.source_name || 'sin fuente registrada') + '</b>, ' + esc(src.year || 's. f.') +
        ' <span class="mf-raw raw-name">meta_sources · ' + esc(ind.table) + '</span><br>';
    }
    html += 'Todas las cifras son agregados; no hay datos personales.';
    el.innerHTML = html;
  }

  function renderGeoNote() {
    var el = $('#map-geo-note');
    if (!el) return;
    var txt = '';
    if (S.group === 'bog') txt = 'Zonas con límites: localidades de Bogotá (Sumapaz, rural, no se dibuja), comunas y corregimientos de Medellín, comunas de Cali, localidades de Barranquilla y comunas y corregimientos de Bucaramanga (BUC-C1..C3 con códigos provisionales). Polígonos de Medellín, Cali, Barranquilla y Bucaramanga: solo uso interno. Personas por zona: solo Bogotá. Población, ocupados y empresas tienen fuente y año distintos por ciudad (ver ficha); el tamaño de empresa de Cali se mide por ingresos y no es comparable con Bogotá. El contexto GEIH 2025 de Medellín A.M. y Cali–Yumbo aparece en la ficha y nunca colorea las comunas. BOG-00 (Sin localidad) queda fuera del mapa.';
    else if (S.group === 'city') txt = 'El municipio 27493 (sin punto) y "Rest of the country" no se dibujan.';
    if (txt) { el.textContent = txt; el.hidden = false; } else { el.hidden = true; el.textContent = ''; }
  }

  function renderJump() {
    var sel = $('#place-jump');
    if (!sel) return;
    var list = places(S.group).filter(function (p) { return S.byId[p.id]; })
      .sort(function (a, b) { return String(a.name).localeCompare(String(b.name), 'es'); });
    var html = '<option value="">— Ir a un lugar (' + GROUPS[S.group].placeLabel + ') —</option>';
    list.forEach(function (p) { html += '<option value="' + esc(p.id) + '">' + esc(p.name) + ' · ' + esc(p.id) + '</option>'; });
    sel.innerHTML = html;
    sel.value = S.selected && S.byId[S.selected] ? S.selected : '';
    var c = $('#jump-count');
    if (c) c.textContent = nf[0].format(list.length) + ' en el mapa';
  }

  // ---------- Medellín / Cali context (paquete think4ever personas) ----------
  var CTX_SOURCE = {
    MEDELLIN_ECV_2025: 'Alcaldía de Medellín, Encuesta de Calidad de Vida',
    CALI_ASIS_2021_DANE_DAP: 'ASIS Cali, Tabla 2 (DANE / DAP)'
  };
  var COMPANIES_SOURCE = {
    '05001': 'Medellín 2022 · datos.gov.co pb3w-3vmc (por actividad)',
    '76001': 'Cali 2025 · Cámara de Comercio de Cali (tamaño por ingresos, no comparable con Bogotá, que se mide por activos)'
  };
  function fmtInt(v) { return isNum(v) ? nf[0].format(Number(v)) : 'n.a.'; }
  function fmtDec(v) { return isNum(v) ? nf[1].format(Number(v)) : 'n.a.'; }

  function metroHtml(m) {
    var rows = [
      ['Ocupados del área metropolitana', m.employed],
      [m.persona ? m.persona : 'Personas de las 13 personas', m.persona ? m.persona_employed : m.personas13],
      ['TI núcleo', m.core_it]
    ];
    var html = '<span class="place-sub">Contexto metropolitano GEIH ' + esc(m.survey_year || 2025) + ' · ' + esc(m.metro_area) +
      ' · <span class="raw-name">fact_geih2025_metro_summary</span></span><table class="place-table"><tbody>';
    rows.forEach(function (r) {
      html += '<tr><td>' + esc(r[0]) + '</td><td class="num">' + esc(fmtInt(r[1])) + '</td></tr>';
    });
    html += '</tbody></table><p class="legend-note">Total del área metropolitana (DANE GEIH 2025). No se reparte por comuna y no colorea el mapa.</p>';
    return html;
  }

  function zoneContextHtml(r) {
    var muni = String(r.municipality_code || '');
    var html = '<span class="place-sub">Fuente y año por dato</span>';
    if (r.context) {
      var what = isNum((r.values || {}).employed_residents) ? 'Población, ocupados y conectividad' : 'Población';
      html += '<p class="legend-note">' + what + ': <b>' + esc(CTX_SOURCE[r.context.source_id] || r.context.source_id) + '</b>, ' +
        esc(r.context.reference_year) + ' <span class="raw-name">fact_zone_context</span></p>';
    }
    if (COMPANIES_SOURCE[muni]) {
      html += '<p class="legend-note">Empresas: <b>' + esc(COMPANIES_SOURCE[muni]) + '</b> <span class="raw-name">fact_companies_zone</span></p>';
    }
    html += '<p class="legend-note">Personas por zona: sin datos. Solo Bogotá tiene conteos por localidad (Encuesta Multipropósito 2021).</p>';
    if (r.metro_context) html += metroHtml(r.metro_context);
    return html;
  }

  function profileHtml(g) {
    var prof = g.profile || [];
    var html = '<span class="place-sub">Perfil GEIH ' + esc(g.survey_year || 2025) + ' · ' + esc(g.metro_area) +
      ' · <span class="raw-name">fact_persona_profile_metro_2025</span></span>';
    var s = g.summary;
    if (s) {
      html += '<p class="legend-note">' + esc(fmtInt(s.employed)) + ' ocupados; ' + esc(fmtInt(s.personas13)) + ' en las 13 personas (' +
        esc(fmtDec(s.personas13_per_1000_employed)) + ' por 1.000 ocupados).</p>';
    }
    if (!prof.length) return html + '<p class="legend-note">Sin perfil para esta selección.</p>';
    var small = false;
    html += '<table class="place-table" style="font-size:11px"><thead><tr><th scope="col">Persona</th><th scope="col" class="num">Ocupados</th>' +
      '<th scope="col" class="num">Edad</th><th scope="col" class="num">Ingreso (mill.)</th><th scope="col" class="num">% muj.</th>' +
      '<th scope="col" class="num">% univ.</th></tr></thead><tbody>';
    prof.forEach(function (x) {
      var warn = x.sample_flag && /below_30/.test(x.sample_flag);
      if (warn) small = true;
      html += '<tr><td>' + esc(x.persona) +
        (warn ? ' <i class="fa-solid fa-triangle-exclamation" style="color:#E8772E" title="Muestra menor a 30 registros: usar con precaución" aria-label="Muestra pequeña"></i>' : '') +
        '<span class="ind-raw raw-name">n = ' + esc(fmtInt(x.sample_records)) + '</span></td>' +
        '<td class="num">' + esc(fmtInt(x.employed)) + '</td><td class="num">' + esc(fmtDec(x.median_age)) + '</td>' +
        '<td class="num">' + esc(isNum(x.median_income_cop) ? fmtDec(Number(x.median_income_cop) / 1e6) : 'n.a.') + '</td>' +
        '<td class="num">' + esc(fmtDec(x.pct_women)) + '</td><td class="num">' + esc(fmtDec(x.pct_university)) + '</td></tr>';
    });
    html += '</tbody></table>';
    html += '<p class="legend-note">Ingreso: mediana de ingresos positivos, millones de COP. ' +
      (small ? '<i class="fa-solid fa-triangle-exclamation" style="color:#E8772E" aria-hidden="true"></i> Muestra menor a 30 registros: usar con precaución. ' : '') +
      'Fuente: DANE GEIH 2025, área metropolitana.</p>';
    return html;
  }

  // ---------- place card ----------
  function renderPlace() {
    var el = $('#map_place_info');
    if (!el) return;
    var p = S.selected ? placeById(S.group, S.selected) : null;
    if (!p) {
      el.innerHTML = '<div class="place-empty"><i class="fa-regular fa-hand-pointer" aria-hidden="true"></i>Haga clic en un lugar del mapa' +
        '<small>También puede elegirlo en la lista de arriba.</small></div>';
      return;
    }
    var r = p.raw;
    var meta;
    if (S.group === 'dept') meta = 'department_code <b>' + esc(p.id) + '</b>';
    else if (S.group === 'city') meta = 'municipality_code <b>' + esc(p.id) + '</b>' + (r.department_name ? ' · ' + esc(r.department_name) : '') +
      (r.metro_area ? '<br>metro_area <b>' + esc(r.metro_area) + '</b>' : '');
    else meta = 'zone_id <b>' + esc(p.id) + '</b> · zone_code <b>' + esc(r.zone_code) + '</b>';

    var html = '<div class="mo-title">' + esc(p.name) + '</div><div class="place-meta">' + meta + '</div>';
    html += '<table class="place-table"><thead><tr><th scope="col">Indicador</th><th scope="col" class="num">Valor</th><th scope="col" class="num">Año</th></tr></thead><tbody>';
    indicators(S.group).forEach(function (ind) {
      var v = fmtVal(ind, p.values[ind.key]);
      var active = ind.key === S.key || (S.key === 'secop_value_bn' && ind.key === 'contracts_2025');
      html += '<tr' + (active ? ' class="is-active"' : '') + '><td>' + esc(ind.label) +
        '<span class="ind-raw raw-name">' + esc(ind.table) + '.' + esc(ind.column) + '</span></td>' +
        '<td class="num">' + (v ? esc(v) : '<span class="na">n.a.</span>') + '</td>' +
        '<td class="num">' + (ind.source && ind.source.year ? esc(ind.source.year) : '<span class="na">n.a.</span>') + '</td></tr>';
    });
    html += '</tbody></table>';

    if (S.group === 'city') {
      var ev = r.events || [];
      html += '<span class="place-sub">Eventos tech 2026 · <span class="raw-name">fact_tech_events</span></span>';
      if (ev.length) {
        html += '<ul class="event-list">';
        ev.forEach(function (e) {
          html += '<li><span>' + esc(e.name) + (e.size ? ' <span class="raw-name">' + esc(e.size) + '</span>' : '') + '</span><span class="ev-date">' + esc(fmtDate(e.date_2026)) + '</span></li>';
        });
        html += '</ul>';
      } else {
        html += '<p class="legend-note" style="margin-top:4px">Sin eventos registrados.</p>';
      }
    }
    if (S.group === 'bog' && r.municipality_code && r.municipality_code !== '11001') {
      html += zoneContextHtml(r);
    }
    if (S.group === 'city' && r.geih2025) {
      html += profileHtml(r.geih2025);
    }

    html += '<div class="place-actions">' +
      '<button type="button" class="btn-navy btn-sm" data-action="compare"><i class="fa-solid fa-code-compare" aria-hidden="true"></i> Comparar este lugar</button>' +
      '<button type="button" class="btn-outline-navy btn-sm" data-action="clear">Quitar selección</button></div>';
    el.innerHTML = html;
  }

  function onPlaceAction(e) {
    var btn = e.target.closest ? e.target.closest('[data-action]') : null;
    if (!btn) return;
    var action = btn.getAttribute('data-action');
    if (action === 'clear') { clearSelection(); return; }
    if (action === 'compare') {
      var p = placeById(S.group, S.selected);
      if (!p) return;
      var seed = {
        level: S.group === 'dept' ? 'department' : (S.group === 'city' ? 'municipality' : 'localidad'),
        code: p.id,
        name: p.name,
        persona: S.persona || null
      };
      window.T4E = window.T4E || {};
      window.T4E.compareSeed = seed;
      try { sessionStorage.setItem('t4e-compare-seed', JSON.stringify(seed)); } catch (_) { /* ignore */ }
      if (typeof window.load_page === 'function') window.load_page('compare_view');
    }
  }

  // ---------- lifecycle ----------
  function init(root) {
    destroy();
    S = {
      root: root, map: null, layer: null, byId: {}, group: 'dept', key: 'personas', persona: '',
      data: { dept: null, city: null, bog: null }, selected: null, extraAttr: [], q: null, cmax: 0,
      seq: 0, firstDraw: true, lastGroup: 'dept', drawnCount: 0
    };
    if (typeof L === 'undefined') { showError(new Error('Leaflet no está disponible')); return; }

    var mapEl = $('#map');
    S.map = L.map(mapEl, { zoomControl: true, minZoom: 4, maxZoom: 17, worldCopyJump: false }).setView(INITIAL_VIEW, INITIAL_ZOOM);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: OSM_ATTR }).addTo(S.map);

    S.onResize = function () { if (S && S.map) S.map.invalidateSize(); };
    window.addEventListener('resize', S.onResize);
    if (window.ResizeObserver) {
      S.ro = new ResizeObserver(S.onResize);
      S.ro.observe($('#map_leaflet'));
    }
    setTimeout(S.onResize, 60);

    S.onLayerChange = onLayerChange;
    S.onPersona = onPersonaChange;
    S.onJump = function () { var v = $('#place-jump').value; if (v) selectPlace(v, true); else clearSelection(); };
    S.onPlaceAction = onPlaceAction;
    $('#map_layer_select').addEventListener('change', S.onLayerChange);
    $('#map_persona_filter').addEventListener('change', S.onPersona);
    $('#place-jump').addEventListener('change', S.onJump);
    $('#map_place_info').addEventListener('click', S.onPlaceAction);

    renderPersonaNote();
    var seq = ++S.seq;
    var mine = S;
    setLoading(true);
    return Promise.all([
      api('api/personas'),
      api(dataUrl('dept')),
      api(dataUrl('city')),
      api(dataUrl('bog'))
    ]).then(function (res) {
      if (S !== mine || seq !== S.seq) return;
      renderPersonaOptions(res[0] && res[0].personas);
      S.data.dept = res[1];
      S.data.city = res[2];
      S.data.bog = res[3];
      var first = selectable('dept')[0];
      if (first) S.key = first.key;
      renderLayerOptions();
      draw(false);
      setLoading(false);
      S.onResize();
    }).catch(function (err) {
      if (S !== mine) return;
      showError(err);
    });
  }

  function destroy() {
    if (!S) return;
    try {
      window.removeEventListener('resize', S.onResize);
      if (S.ro) S.ro.disconnect();
      if (S.map) S.map.remove();
    } catch (e) { /* ignore */ }
    S = null;
  }

  window.T4EMapView = {
    init: init,
    destroy: destroy,
    // exposed for tests
    _computeQuintiles: computeQuintiles,
    _classOf: classOf,
    RAMP: RAMP,
    NODATA: NODATA
  };
})();