/* YardScout arrival forecast: "How often does my car land near me?"
 *
 * Reads the arrivals history the scan publishes (docs/data/arrivals/, written
 * by scraper/junkyard_scraper.py _write_arrivals_json; definitions there and
 * in ops/data.md) and turns it into one honest line, a facts line and eight
 * weekly bars. Past weeks only: never a promise, never a percentage.
 *
 *   YSForecast.summary(data, q)   pure; data = { index, file } (index.json and
 *                                 the make's file), q = { make, model, yrMin,
 *                                 yrMax, lat, lng, radiusMi }
 *   YSForecast.words(s, q)        the sentences for a summary
 *   YSForecast.mount(el, ctx)     loads the files (once / on demand) and
 *                                 renders into el; resolves to the status, or
 *                                 null when it rendered nothing. Never throws.
 *
 * ctx = { make, model, year, yrMin, yrMax, lat, lng, radiusMi, where, place,
 * compact }. compact = true renders the small block (watch rows, see render).
 * yrMin/yrMax null = any year; `year` is used as a one-year span only when
 * yrMin and yrMax are both left out (undefined). `place` (a place name or
 * ZIP, optional) is added to the line as "within R mi of <place>". `where`
 * is the surface that mounts the forecast ('parts' in the Parts card, 'cars'
 * in the Cars watch strip); it is never shown (hub, 2026-11-19: the app
 * passes where: 'parts', which once read "within 100 mi of parts").
 *
 * Data comes from the same place as the app's other data: app.js's global
 * DATA_BASE ('' on the web, 'https://yardscout.io/' in the native shells).
 * The service worker is network-first for these files. */
(function (root) {
  'use strict';

  var WEEKS = 8;
  var MIN_COVERED_WEEKS = 2;
  var LABEL = 'From set-out dates YardScout has recorded. Past weeks, not a promise.';

  function toRad(d) { return d * Math.PI / 180; }
  function milesBetween(lat1, lng1, lat2, lng2) {
    var dLat = toRad(lat2 - lat1), dLng = toRad(lng2 - lng1);
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return 3958.8 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }
  function num(v) { return typeof v === 'number' && isFinite(v) ? v : null; }

  function modelRows(file, model) {
    var models = (file && file.models) || {};
    if (Object.prototype.hasOwnProperty.call(models, model)) return models[model];
    var low = String(model || '').toLowerCase();
    for (var k in models) if (Object.prototype.hasOwnProperty.call(models, k) && k.toLowerCase() === low) return models[k];
    return [];
  }

  /* Pure. Sums the model's weekly arrivals over the yards within radiusMi,
   * skipping stale yards (list not updating) and yards with fewer than
   * MIN_COVERED_WEEKS covered weeks (new to YardScout). Rate = sum over the
   * counted yards of (that yard's arrivals / its covered weeks). */
  function summary(data, q) {
    q = q || {};
    if (wider(q)) return summarySpecs(data, q);
    var lat = num(q.lat), lng = num(q.lng), radius = num(q.radiusMi);
    var out = {
      status: 'ok', weeks: [0, 0, 0, 0, 0, 0, 0, 0], total: 0, rate: 0,
      yardsCounted: 0, skipped: { stale: 0, newYard: 0 }, top: [],
      radiusMi: radius, yrMin: num(q.yrMin), yrMax: num(q.yrMax),
    };
    if (lat === null || lng === null || radius === null || radius <= 0) { out.status = 'no place'; return out; }
    var index = data && data.index;
    if (!index || !Array.isArray(index.yards)) { out.status = 'no data'; return out; }
    var near = {};
    index.yards.forEach(function (y, i) {
      var ylat = num(y[1]), ylng = num(y[2]);
      if (ylat === null || ylng === null) return;
      if (milesBetween(lat, lng, ylat, ylng) > radius) return;
      if (y[4]) { out.skipped.stale++; return; }
      if (!(y[3] >= MIN_COVERED_WEEKS)) { out.skipped.newYard++; return; }
      near[i] = { name: y[0], covered: y[3], n: 0 };
      out.yardsCounted++;
    });
    if (!out.yardsCounted) { out.status = 'no counted yard'; return out; }
    var lo = out.yrMin, hi = out.yrMax;
    modelRows(data.file, q.model).forEach(function (r) {
      var y = near[r[0]];
      if (!y) return;
      if ((lo !== null || hi !== null) && !(r[1] > 0)) return;
      if (lo !== null && r[1] < lo) return;
      if (hi !== null && r[1] > hi) return;
      for (var w = 0; w < WEEKS; w++) {
        var c = r[2 + w] || 0;
        out.weeks[w] += c;
        y.n += c;
        out.total += c;
      }
    });
    var top = [];
    Object.keys(near).forEach(function (i) {
      var y = near[i];
      out.rate += y.n / y.covered;
      if (y.n > 0) top.push([y.name, y.n]);
    });
    top.sort(function (a, b) { return b[1] - a[1] || (a[0] < b[0] ? -1 : 1); });
    out.top = top;
    return out;
  }

  /* ---- donor models (the Parts card, 2026-11-19) ----
   * q.specs = [{make, model, yrMin, yrMax}]: the vehicle specs the Parts
   * list's own matching accepts for the search. A spec's make may be
   * "Toyota|Lexus" (one spec per make) and its model may end in "*" (every
   * model whose letters and digits start with the stem: the app's own
   * pfAppMatches rule for those rows); otherwise a model matches as modelRows
   * does (the same name, any case). Overlapping or touching year ranges of
   * the same make and model are merged first, and a history row is counted
   * at most once even when several specs match it. Rows with no model year
   * are not counted (every spec has years). */
  function alnum(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
  function mergeSpecs(specs) {
    var by = {};
    var keys = [];
    (specs || []).forEach(function (sp) {
      if (!sp) return;
      var lo = num(sp.yrMin), hi = num(sp.yrMax), model = String(sp.model || '').trim();
      if (lo === null || hi === null || lo > hi || !model) return;
      String(sp.make || '').split('|').forEach(function (mk) {
        mk = mk.trim();
        if (!mk) return;
        var k = mk.toLowerCase() + '\u0001' + model.toLowerCase();
        if (!by[k]) { by[k] = { make: mk, model: model, ranges: [] }; keys.push(k); }
        by[k].ranges.push([lo, hi]);
      });
    });
    var out = [];
    keys.sort().forEach(function (k) {
      var e = by[k];
      e.ranges.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
      var cur = null;
      e.ranges.forEach(function (r) {
        if (cur && r[0] <= cur.yrMax + 1) { if (r[1] > cur.yrMax) cur.yrMax = r[1]; return; }
        cur = { make: e.make, model: e.model, yrMin: r[0], yrMax: r[1] };
        out.push(cur);
      });
    });
    return out;
  }
  function specModelMatches(sp, name) {
    if (sp.model.charAt(sp.model.length - 1) === '*') {
      var stem = alnum(sp.model.slice(0, -1));
      return !!stem && alnum(name).indexOf(stem) === 0;
    }
    return String(name).toLowerCase() === sp.model.toLowerCase();
  }
  /* The specs say more than the own model: anything but nothing or exactly
   * the own make, model and year span (that reads as today, byte for byte). */
  function wider(q) {
    if (!q || !Array.isArray(q.specs) || !q.specs.length) return false;
    var m = mergeSpecs(q.specs);
    if (!m.length) return false;
    return !(m.length === 1 && m[0].make.toLowerCase() === String(q.make || '').toLowerCase()
      && m[0].model.toLowerCase() === String(q.model || '').toLowerCase()
      && m[0].yrMin === num(q.yrMin) && m[0].yrMax === num(q.yrMax));
  }
  function makesOf(specs) {
    var seen = {}, out = [];
    specs.forEach(function (sp) { var k = sp.make.toLowerCase(); if (!seen[k]) { seen[k] = 1; out.push(sp.make); } });
    return out;
  }
  // The yards within radius that count (the same rules as summary).
  function nearYards(index, lat, lng, radius, out) {
    var near = {};
    index.yards.forEach(function (y, i) {
      var ylat = num(y[1]), ylng = num(y[2]);
      if (ylat === null || ylng === null) return;
      if (milesBetween(lat, lng, ylat, ylng) > radius) return;
      if (y[4]) { out.skipped.stale++; return; }
      if (!(y[3] >= MIN_COVERED_WEEKS)) { out.skipped.newYard++; return; }
      near[i] = { name: y[0], covered: y[3], n: 0 };
      out.yardsCounted++;
    });
    return near;
  }
  /* Pure. data = { index, files: { <make lowercased>: make file, or null when
   * the index has no such make (none recorded: counts 0) } }. A make with no
   * entry in files at all is missing: status 'no data'. */
  function summarySpecs(data, q) {
    var lat = num(q.lat), lng = num(q.lng), radius = num(q.radiusMi);
    var specs = mergeSpecs(q.specs);
    var out = {
      status: 'ok', weeks: [0, 0, 0, 0, 0, 0, 0, 0], total: 0, rate: 0,
      yardsCounted: 0, skipped: { stale: 0, newYard: 0 }, top: [],
      radiusMi: radius, yrMin: null, yrMax: null,
      specs: specs.map(function (sp) { return { make: sp.make, model: sp.model, yrMin: sp.yrMin, yrMax: sp.yrMax, n: 0 }; }),
    };
    if (lat === null || lng === null || radius === null || radius <= 0) { out.status = 'no place'; return out; }
    var index = data && data.index;
    var files = data && data.files;
    if (!index || !Array.isArray(index.yards) || !files || !specs.length) { out.status = 'no data'; return out; }
    var makes = makesOf(specs);
    for (var m = 0; m < makes.length; m++) {
      if (!Object.prototype.hasOwnProperty.call(files, makes[m].toLowerCase())) { out.status = 'no data'; return out; }
    }
    var near = nearYards(index, lat, lng, radius, out);
    if (!out.yardsCounted) { out.status = 'no counted yard'; return out; }
    makes.forEach(function (mk) {
      var file = files[mk.toLowerCase()];
      var models = (file && file.models) || {};
      var mine = out.specs.filter(function (sp) { return sp.make.toLowerCase() === mk.toLowerCase(); });
      Object.keys(models).forEach(function (name) {
        var cands = mine.filter(function (sp) { return specModelMatches(sp, name); });
        if (!cands.length) return;
        models[name].forEach(function (r) {
          var y = near[r[0]];
          if (!y || !(r[1] > 0)) return;
          var sp = null;
          for (var c = 0; c < cands.length; c++) if (r[1] >= cands[c].yrMin && r[1] <= cands[c].yrMax) { sp = cands[c]; break; }
          if (!sp) return;   // one row, counted once, under the first spec it matches
          for (var w = 0; w < WEEKS; w++) {
            var c2 = r[2 + w] || 0;
            out.weeks[w] += c2;
            y.n += c2;
            sp.n += c2;
            out.total += c2;
          }
        });
      });
    });
    var top = [];
    Object.keys(near).forEach(function (i) {
      var y = near[i];
      out.rate += y.n / y.covered;
      if (y.n > 0) top.push([y.name, y.n]);
    });
    top.sort(function (a, b) { return b[1] - a[1] || (a[0] < b[0] ? -1 : 1); });
    out.top = top;
    return out;
  }
  // "2003-09 4Runner"; "1998-2004 Tacoma"; "2005 Tundra"; a "*" model reads as its stem.
  function specLabel(sp) {
    var lo = sp.yrMin, hi = sp.yrMax;
    var yrs = lo === hi ? String(lo)
      : Math.floor(lo / 100) === Math.floor(hi / 100) ? lo + '-' + String(hi).slice(2) : lo + '-' + hi;
    return yrs + ' ' + sp.model.replace(/\s*\*$/, '');
  }
  var MODELS_SHOWN = 3;
  var CAVEAT = 'The 8-week counts include every car of these models and years, whatever its engine or options.';
  /* The calibration line (hub, 2026-11-19): today's lot, counted by the app
   * with its own matching. lot = { donors, cars }: cars = lot cars in range
   * of the specs in use, each once; donors = the rows the list shows among
   * them. Nothing when cars is 0, a number is missing, or donors > cars. */
  function lotLine(lot, within) {
    if (!lot) return '';
    var d = lot.donors, c = lot.cars;
    if (typeof d !== 'number' || typeof c !== 'number' || !isFinite(d) || !isFinite(c)) return '';
    if (c < 1 || d < 0 || d > c || Math.floor(d) !== d || Math.floor(c) !== c) return '';
    return 'On lots ' + within + ' now: ' + d + ' of ' + c + ' ' + plural(c, 'car', 'cars') +
      ' of these models ' + (d === 1 ? 'is a donor' : 'are donors') + ' for this part.';
  }

  function plural(n, one, many) { return n === 1 ? one : many; }

  function subject(q) {
    var lo = num(q.yrMin), hi = num(q.yrMax), m = String(q.model || '');
    if (lo !== null && hi !== null) return (lo === hi ? String(lo) : lo + '-' + hi) + ' ' + m;
    if (lo !== null) return lo + '+ ' + m;
    if (hi !== null) return 'up to ' + hi + ' ' + m;
    return m + ', any year';
  }

  /* The sentences. Order: no counted yard, none, exactly one, then the rate. */
  function words(s, q) {
    q = q || {};
    if (!s || s.status === 'no place' || s.status === 'no data') return null;
    var r = s.radiusMi, where = q.place ? ' of ' + q.place : '';
    var within = 'within ' + r + ' mi' + where;
    var headline;
    if (s.status === 'no counted yard') headline = 'Not enough history near you yet';
    else if (s.total === 0) headline = 'None landed ' + within + ' in the last 8 weeks';
    else if (s.total === 1) headline = 'Rare here: 1 landed ' + within + ' in the last 8 weeks';
    else if (s.rate >= 1.5) headline = 'About ' + Math.round(s.rate) + ' a week land ' + within;
    else if (s.rate >= 0.75) headline = 'About one a week lands ' + within;
    // 1 / rate rounds to 1 for rates just under 0.75; say 2 (the rarer side).
    else headline = 'About one every ' + Math.max(2, Math.round(1 / s.rate)) + ' weeks lands ' + within;
    var facts = s.total + ' in the last 8 weeks at ' + s.yardsCounted + ' ' + plural(s.yardsCounted, 'yard', 'yards');
    var k = s.skipped.stale + s.skipped.newYard;
    if (k) {
      var why = [];
      if (s.skipped.stale) why.push(plural(s.skipped.stale, 'list not updating', 'lists not updating'));
      if (s.skipped.newYard) why.push('new to YardScout');
      facts += ' (' + k + ' ' + plural(k, 'yard', 'yards') + ' not counted: ' + why.join(' / ') + ')';
    }
    var most = '';
    if (s.total >= 3 && s.top.length) {
      most = 'Most land at: ' + s.top.slice(0, 2).map(function (t) { return t[0] + ' (' + t[1] + ')'; }).join(', ');
    }
    var alt = 'Arrivals per week, oldest to newest: ' + s.weeks.join(', ');
    var w = { subject: subject(q), headline: headline, facts: facts, most: most, label: LABEL, alt: alt };
    if (s.specs) {
      var ord = s.specs.slice().sort(function (a, b) {
        var la = specLabel(a), lb = specLabel(b);
        return b.n - a.n || (la < lb ? -1 : la > lb ? 1 : 0);
      }).map(specLabel);
      w.subject = 'Cars of the donor models';
      w.lot = lotLine(q.lotNow, r !== null && r !== undefined ? within : 'in range');
      w.models = ord.slice(0, MODELS_SHOWN);
      w.modelsMore = ord.slice(MODELS_SHOWN);
      w.caveat = CAVEAT;
    }
    return w;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* compact (the Alerts tab's watch rows): the same subject, headline, facts
   * and label, and the eight bars small (no per-bar numbers; the bars keep the
   * same text alternative); no "Most land at" line. Nothing new is said. */
  // A year span never breaks at its hyphen ("2003-" / "09 4Runner").
  function labelHtml(l) {
    var m = /^(\S+) (.*)$/.exec(l);
    return m ? '<span class="ysf-yrs">' + esc(m[1]) + '</span> ' + esc(m[2]) : esc(l);
  }
  function modelsHtml(w) {
    var line = w.models.map(labelHtml).join(', ');
    if (!w.modelsMore.length) return '<p class="ysf-models">' + line + '</p>';
    var all = w.modelsMore.join(', ');
    return '<details class="ysf-models ysf-models-more"><summary title="' + esc(all) + '">' + line +
      ' <span class="ysf-more">and ' + w.modelsMore.length + ' more</span></summary>' +
      '<p class="ysf-models-rest">' + w.modelsMore.map(labelHtml).join(', ') + '</p></details>';
  }
  function render(el, s, w, compact) {
    var max = Math.max.apply(null, s.weeks.concat([1]));
    var showBars = s.status === 'ok';
    var bars = '';
    if (showBars) {
      bars = '<div class="ysf-bars" role="img" aria-label="' + esc(w.alt) + '">' +
        s.weeks.map(function (c) {
          var h = c ? Math.max(8, Math.round(100 * c / max)) : 0;
          return '<div class="ysf-bar" aria-hidden="true"><div class="ysf-bar-track">' +
            '<div class="ysf-bar-fill' + (c ? '' : ' ysf-zero') + '" style="height:' + h + '%"></div></div>' +
            (compact ? '' : '<span class="ysf-bar-n">' + c + '</span>') + '</div>';
        }).join('') + '</div>' +
        '<div class="ysf-axis" aria-hidden="true"><span>8 weeks ago</span><span>last week</span></div>';
    }
    el.innerHTML = '<div class="ysf' + (compact ? ' ysf-compact' : '') + '" data-ysf-status="' + esc(s.status) + '"' +
      (s.specs ? ' data-ysf-kind="donor-models"' : '') + '>' +
      '<div class="ysf-subject">' + esc(w.subject) + '</div>' +
      '<p class="ysf-headline">' + esc(w.headline) + '</p>' +
      (w.lot ? '<p class="ysf-lot">' + esc(w.lot) + '</p>' : '') +
      (w.models ? modelsHtml(w) : '') +
      bars +
      '<p class="ysf-facts">' + esc(w.facts) + '</p>' +
      (w.most && !compact ? '<p class="ysf-most">' + esc(w.most) + '</p>' : '') +
      (w.caveat ? '<p class="ysf-caveat">' + esc(w.caveat) + '</p>' : '') +
      '<p class="ysf-label">' + esc(w.label) + '</p>' +
      '</div>';
  }

  // ---- loading: index once, make files on demand, both kept in memory ----
  function base() {
    try { if (typeof DATA_BASE === 'string') return DATA_BASE; } catch (e) { /* not defined */ }
    var cap = root.Capacitor;
    return cap && cap.isNativePlatform && cap.isNativePlatform() ? 'https://yardscout.io/' : '';
  }
  var indexP = null;
  var files = {};
  function getJSON(path) {
    return fetch(base() + path).then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); });
  }
  function loadIndex(fresh) {
    if (!indexP || fresh) {
      indexP = getJSON('data/arrivals/index.json').then(function (d) {
        if (!d || !Array.isArray(d.yards) || !d.makes) throw new Error('bad index');
        return d;
      });
      indexP.catch(function () { indexP = null; });   // a failure is retried on the next mount
    }
    return indexP;
  }
  function loadFile(slug) {
    if (!files[slug]) {
      files[slug] = getJSON('data/arrivals/' + encodeURIComponent(slug) + '.json');
      files[slug].catch(function () { delete files[slug]; });
    }
    return files[slug];
  }
  function findMake(index, make) {
    var m = index.makes || {};
    if (Object.prototype.hasOwnProperty.call(m, make)) return m[make][0];
    var low = String(make || '').toLowerCase();
    for (var k in m) if (Object.prototype.hasOwnProperty.call(m, k) && k.toLowerCase() === low) return m[k][0];
    return null;
  }
  // Yard indices are per build: a make file only reads against the index of
  // the same build. On a mismatch the index is fetched again once.
  function load(make) {
    return loadIndex(false).then(function (index) {
      var slug = findMake(index, make);
      if (!slug) return null;   // make not in the history: say nothing rather than "none"
      return loadFile(slug).then(function (file) {
        if (file.builtAt === index.builtAt) return { index: index, file: file };
        delete files[slug];
        return loadIndex(true).then(function (ix2) {
          return loadFile(slug).then(function (f2) {
            return f2.builtAt === ix2.builtAt ? { index: ix2, file: f2 } : null;
          });
        });
      });
    });
  }

  function query(ctx) {
    var q = {};
    for (var k in ctx) if (Object.prototype.hasOwnProperty.call(ctx, k)) q[k] = ctx[k];
    if (q.yrMin === undefined && q.yrMax === undefined && num(q.year) !== null) { q.yrMin = q.year; q.yrMax = q.year; }
    if (q.yrMin === undefined) q.yrMin = null;
    if (q.yrMax === undefined) q.yrMax = null;
    return q;
  }

  /* All of the specs' make files (at most MAX_MAKES, each fetched once and
   * cached), read against one index; null when that cannot be had in full:
   * the caller then shows the own model. A make the index does not list had
   * no arrivals recorded at all and counts 0. */
  var MAX_MAKES = 4;
  function loadSpecs(specs) {
    var makes = makesOf(mergeSpecs(specs));
    if (!makes.length || makes.length > MAX_MAKES) return Promise.resolve(null);
    return loadIndex(false).then(function (index) {
      return Promise.all(makes.map(function (mk) {
        var slug = findMake(index, mk);
        return slug ? loadFile(slug) : null;
      })).then(function (list) {
        var files = {};
        for (var i = 0; i < makes.length; i++) {
          if (list[i] && list[i].builtAt !== index.builtAt) return null;   // another build: never a partial or mixed sum
          files[makes[i].toLowerCase()] = list[i];
        }
        return { index: index, files: files };
      });
    }).catch(function () { return null; });
  }
  function ownQuery(q) {
    var o = {};
    for (var k in q) if (Object.prototype.hasOwnProperty.call(q, k) && k !== 'specs') o[k] = q[k];
    return o;
  }

  function mount(el, ctx) {
    if (!el) return Promise.resolve(null);
    var token = {};
    el._ysfToken = token;
    var clear = function () { if (el._ysfToken === token) el.innerHTML = ''; return null; };
    try {
      var q = query(ctx || {});
      if (!q.make || !q.model) return Promise.resolve(clear());
      if (summary({}, ownQuery(q)).status === 'no place') return Promise.resolve(clear());
      if (wider(q) && !q.compact) {
        return loadSpecs(q.specs).then(function (data) {
          if (el._ysfToken !== token) return null;
          var s = data ? summary(data, q) : null;
          if (!s || s.status === 'no data') return ownMount(el, ownQuery(q), token, clear);
          var w = words(s, q);
          if (!w) return ownMount(el, ownQuery(q), token, clear);
          render(el, s, w, false);
          return s.status;
        }).catch(clear);
      }
      return ownMount(el, ownQuery(q), token, clear);
    } catch (e) {
      return Promise.resolve(clear());
    }
  }
  function ownMount(el, q, token, clear) {
    try {
      return load(q.make).then(function (data) {
        if (el._ysfToken !== token) return null;   // a newer mount owns el
        if (!data) return clear();
        var s = summary(data, q);
        var w = words(s, q);
        if (!w) return clear();
        render(el, s, w, !!q.compact);
        return s.status;
      }).catch(clear);
    } catch (e) {
      return Promise.resolve(clear());
    }
  }

  root.YSForecast = { summary: summary, words: words, mount: mount, _milesBetween: milesBetween, _mergeSpecs: mergeSpecs };
})(typeof window !== 'undefined' ? window : globalThis);
