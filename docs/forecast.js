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
 * ctx = { make, model, year, yrMin, yrMax, lat, lng, radiusMi, where }.
 * yrMin/yrMax null = any year; `year` is used as a one-year span only when
 * yrMin and yrMax are both left out (undefined). `where` (a place name or
 * ZIP) is added to the line as "within R mi of <where>".
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
    var r = s.radiusMi, where = q.where ? ' of ' + q.where : '';
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
    return { subject: subject(q), headline: headline, facts: facts, most: most, label: LABEL, alt: alt };
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function render(el, s, w) {
    var max = Math.max.apply(null, s.weeks.concat([1]));
    var showBars = s.status === 'ok';
    var bars = '';
    if (showBars) {
      bars = '<div class="ysf-bars" role="img" aria-label="' + esc(w.alt) + '">' +
        s.weeks.map(function (c) {
          var h = c ? Math.max(8, Math.round(100 * c / max)) : 0;
          return '<div class="ysf-bar" aria-hidden="true"><div class="ysf-bar-track">' +
            '<div class="ysf-bar-fill' + (c ? '' : ' ysf-zero') + '" style="height:' + h + '%"></div></div>' +
            '<span class="ysf-bar-n">' + c + '</span></div>';
        }).join('') + '</div>' +
        '<div class="ysf-axis" aria-hidden="true"><span>8 weeks ago</span><span>last week</span></div>';
    }
    el.innerHTML = '<div class="ysf" data-ysf-status="' + esc(s.status) + '">' +
      '<div class="ysf-subject">' + esc(w.subject) + '</div>' +
      '<p class="ysf-headline">' + esc(w.headline) + '</p>' +
      bars +
      '<p class="ysf-facts">' + esc(w.facts) + '</p>' +
      (w.most ? '<p class="ysf-most">' + esc(w.most) + '</p>' : '') +
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

  function mount(el, ctx) {
    if (!el) return Promise.resolve(null);
    var token = {};
    el._ysfToken = token;
    var clear = function () { if (el._ysfToken === token) el.innerHTML = ''; return null; };
    try {
      var q = query(ctx || {});
      if (!q.make || !q.model) return Promise.resolve(clear());
      if (summary({}, q).status === 'no place') return Promise.resolve(clear());
      return load(q.make).then(function (data) {
        if (el._ysfToken !== token) return null;   // a newer mount owns el
        if (!data) return clear();
        var s = summary(data, q);
        var w = words(s, q);
        if (!w) return clear();
        render(el, s, w);
        return s.status;
      }).catch(clear);
    } catch (e) {
      return Promise.resolve(clear());
    }
  }

  root.YSForecast = { summary: summary, words: words, mount: mount, _milesBetween: milesBetween };
})(typeof window !== 'undefined' ? window : globalThis);
