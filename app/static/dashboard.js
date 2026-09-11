'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const colors = {TRUSTED: '#54deb0', VERIFY: '#e9b76e', REJECT: '#f08089', INACTIVE: '#8d9eb2'};
  const statusNames = {TRUSTED: 'Trusted session', VERIFY: 'Identity verification needed', REJECT: 'Suspicious behavior', INACTIVE: 'Insufficient activity'};
  const decisions = {
    ALLOW: ['Allow access', 'Typing behavior is within the engine’s trusted score range.'],
    PROMPT_REAUTH: ['Verify identity', 'The engine recommends re-authentication for this session.'],
    LOCK_SESSION: ['Restrict access', 'The engine recommends locking this session.'],
    HOLD: ['Waiting for activity', 'At least 5 character presses are needed in a 10-second window.']
  };
  let history = [], mode = null, running = false, busy = false, timer = null;
  let origin = 0, events = [], pending = [], held = new Set(), signingKey = null, keyIds = new Map();
  let generation = 0, tabOwner = null;
  const monitorMarkup = $('monitor-button').innerHTML;
  const fmt = (value, digits = 0) => value == null ? '—' : Number(value).toFixed(digits);
  const timeLabel = seconds => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;

  async function api(path, data) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(path, {
        method: data === undefined ? 'GET' : 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
        body: data === undefined ? undefined : JSON.stringify(data), signal: controller.signal
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Unable to complete the request. Please try again.');
      return payload;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('The scoring engine took too long to respond. Please try again.');
      throw error;
    } finally { clearTimeout(timeout); }
  }
  function notify(message) { $('announcer').textContent = message; }
  function fail(error) {
    stop('Monitoring stopped');
    $('error-banner').textContent = error.message || 'Connection lost. Check the server and try again.';
    $('error-banner').hidden = false;
    $('system-label').textContent = 'Connection needs attention';
    $('system-dot').className = 'dot red';
  }
  function system(label, color) {
    $('system-label').textContent = label;
    $('system-dot').className = `dot ${color || ''}`;
  }
  function drawChart() {
    const svg = $('history-chart');
    const width = 720, left = 37, right = 663, top = 14, bottom = 191;
    const y = score => bottom - (bottom - top) * score / 100;
    const visible = history.slice(-40);
    const first = visible.length ? Math.max(0, visible[0].elapsed_seconds - 10) : 0;
    const span = Math.max(60, (visible.at(-1)?.elapsed_seconds || 60) - first);
    const step = Math.ceil(span / 6 / 10) * 10;
    const end = first + step * 6;
    const x = seconds => left + (right - left) * (seconds - first) / (end - first);
    let content = '<defs><linearGradient id="history-fill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#54deb0" stop-opacity=".17"/><stop offset="1" stop-color="#54deb0" stop-opacity="0"/></linearGradient></defs>';
    for (const score of [0, 20, 40, 60, 80, 100]) {
      content += `<line x1="${left}" y1="${y(score)}" x2="${right}" y2="${y(score)}" stroke="#2b3b4b" stroke-opacity=".52"/><text x="${left - 11}" y="${y(score) + 3}" fill="#8094a9" font-size="9" text-anchor="end">${score}</text>`;
    }
    for (const [score, color, label] of [[70, '#54deb0', 'Trusted'], [40, '#e9b76e', 'Verify']]) {
      content += `<line x1="${left}" y1="${y(score)}" x2="${right}" y2="${y(score)}" stroke="${color}" stroke-opacity=".5" stroke-dasharray="5 6"/><text x="${right + 8}" y="${y(score) + 3}" fill="${color}" opacity=".85" font-size="9">${label}</text>`;
    }
    for (let i = 0; i <= 6; i++) {
      const second = first + (end - first) * i / 6;
      content += `<text x="${x(second)}" y="216" fill="#8094a9" font-size="9" text-anchor="middle">${timeLabel(second)}</text>`;
    }
    const points = visible.filter(row => row.trust_score !== null);
    if (points.length) {
      const path = points.map((row, i) => `${i ? 'L' : 'M'}${x(row.elapsed_seconds).toFixed(2)},${y(row.trust_score).toFixed(2)}`).join(' ');
      content += `<path d="${path} L${x(points.at(-1).elapsed_seconds)},${bottom} L${x(points[0].elapsed_seconds)},${bottom} Z" fill="url(#history-fill)"/>`;
      for (let i = 1; i < points.length; i++) {
        const a = points[i - 1], b = points[i];
        content += `<line x1="${x(a.elapsed_seconds)}" y1="${y(a.trust_score)}" x2="${x(b.elapsed_seconds)}" y2="${y(b.trust_score)}" stroke="${colors[b.status]}" stroke-width="2.6" stroke-linecap="round" ${b.is_active ? '' : 'stroke-dasharray="4 4"'}/>`;
      }
      for (const row of points) {
        const color = colors[row.status] || colors.INACTIVE;
        content += `<circle cx="${x(row.elapsed_seconds)}" cy="${y(row.trust_score)}" r="3.5" fill="${color}" stroke="#16212e" stroke-width="2"><title>${timeLabel(row.elapsed_seconds)} · Trust ${fmt(row.trust_score, 1)} · ${row.is_active ? row.status : 'Idle, score held'}</title></circle>`;
      }
    }
    svg.innerHTML = content;
    svg.setAttribute('aria-label', points.length ? `Trust history: ${points.map(row => `${timeLabel(row.elapsed_seconds)}, score ${fmt(row.trust_score, 1)}`).join('; ')}` : 'No trust scores recorded yet');
    $('chart-empty').hidden = points.length > 0;
  }
  function render() {
    const last = history.at(-1);
    const color = last ? (colors[last.status] || colors.INACTIVE) : colors.TRUSTED;
    const score = last?.trust_score ?? null;
    $('gauge-container').style.setProperty('--accent', color);
    $('gauge-value').setAttribute('stroke-dasharray', `${score ?? 0} 100`);
    $('trust-score').textContent = fmt(score);
    $('gauge-svg').setAttribute('aria-label', score === null ? 'Trust score: awaiting keyboard data' : `Trust score ${fmt(score, 1)} out of 100`);
    $('gauge-caption').textContent = !last ? 'Waiting for keyboard data' : !last.is_active ? (score === null ? 'Waiting for enough activity' : 'Idle · previous score held') : {TRUSTED: 'Trusted · allow access', VERIFY: 'Verify · check identity', REJECT: 'Risk detected · restrict'}[last.status];
    $('status-badge').style.setProperty('--accent', last ? color : '#a4b5c8');
    $('status-badge').classList.toggle('neutral', !last);
    $('status-text').textContent = last ? statusNames[last.status] : 'Awaiting first window';
    $('status-description').textContent = !last ? 'Start monitoring to evaluate your typing behavior.' : !last.is_active ? 'Idle window. Insufficient typing does not lower trust.' : last.prediction === 1 ? 'The model identifies this keyboard window as an inlier.' : 'The model identifies an unusual keyboard pattern.';
    const decision = last ? decisions[last.decision] : ['Ready when you are', 'Your trust score determines the engine’s recommended response.'];
    $('decision-title').textContent = decision[0];
    $('decision-description').textContent = decision[1];
    document.querySelectorAll('.policy-row').forEach(row => row.classList.toggle('active', last && score !== null && row.dataset.band === last.status));
    const metrics = last?.metrics;
    $('cadence').textContent = fmt(metrics?.characters_per_second, 1);
    $('hold').textContent = fmt(metrics?.mean_hold_ms);
    $('flight').textContent = fmt(metrics?.mean_flight_ms);
    $('hold-std').textContent = `σ ${fmt(metrics?.std_hold_ms)} ms`;
    $('pauses').textContent = `${fmt(metrics?.pause_count)} ${metrics?.pause_count === 1 ? 'pause' : 'pauses'}`;
    $('history-source').textContent = mode === 'replay' ? 'RECORDED REPLAY' : mode === 'live' ? 'KEYBOARD SESSION' : 'THIS SESSION';
    $('event-count').textContent = history.length;
    if (history.length) {
      const list = $('event-list'); list.replaceChildren();
      for (const row of history.slice(-20).reverse()) {
        const event = document.createElement('div'); event.className = 'event';
        event.style.setProperty('--accent', colors[row.status] || colors.INACTIVE);
        const dot = document.createElement('i'); dot.className = 'dot'; dot.style.background = row.is_active ? colors[row.status] : colors.INACTIVE;
        const body = document.createElement('div'); body.className = 'event-body';
        const title = document.createElement('div'); title.className = 'event-title';
        const label = document.createElement('span'); label.textContent = row.is_active ? decisions[row.decision][0] : row.trust_score === null ? 'Waiting for activity' : 'Idle · trust maintained';
        const trust = document.createElement('b'); trust.textContent = `${fmt(row.trust_score, 1)}${row.trust_score === null ? '' : ' / 100'}`;
        title.append(label, trust);
        const detail = document.createElement('p');
        const time = document.createElement('span'); time.textContent = `Window ${String(row.number).padStart(2, '0')} · ${timeLabel(row.elapsed_seconds)}`;
        const tag = document.createElement('span'); tag.textContent = row.source === 'replay' ? 'Recorded replay' : new Date(row.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit', second: '2-digit'});
        detail.append(time, tag); body.append(title, detail); event.append(dot, body); list.append(event);
      }
    } else {
      $('event-list').innerHTML = '<div class="events-empty"><strong>No evaluations yet</strong><span>New decisions will be listed here.</span></div>';
    }
    $('events-footer').textContent = last ? `${history.length} window${history.length === 1 ? '' : 's'} evaluated · ${mode === 'replay' ? 'recorded data' : 'this session'}` : 'Waiting for the first evaluation';
    drawChart();
  }
  function stop(label = 'Monitoring paused') {
    running = false; generation++;
    clearInterval(timer); timer = null;
    events = []; pending = []; held.clear(); keyIds.clear(); signingKey = null;
    $('typing-area').disabled = true;
    $('monitor-button').innerHTML = monitorMarkup;
    $('monitor-button').disabled = false;
    $('replay-button').disabled = false;
    $('window-progress').style.width = '0%';
    $('capture-label').textContent = label;
    system(label);
    notify(label);
    if (tabOwner) { tabOwner(); tabOwner = null; }
  }
  async function submitWindow(batch, token) {
    const response = await api('/api/window', {events: batch});
    if (token !== generation) return;
    if (response.result) {
      history.push(response.result); history = history.slice(-120); render();
      notify(`Window ${response.result.number}. ${response.result.is_active ? statusNames[response.result.status] : 'Idle window'}. Trust score ${fmt(response.result.trust_score, 1)}.`);
    }
    if (response.done && mode === 'replay') stop('Replay complete');
  }
  async function tick(token) {
    if (!running || busy || token !== generation) return;
    const elapsed = performance.now() - origin;
    if (mode === 'live') {
      $('window-progress').style.width = `${Math.min(100, elapsed / 100)}%`;
      $('capture-label').textContent = `Next evaluation in ${Math.max(0, Math.ceil((10000 - elapsed) / 1000))}s · ${events.filter(e => e.event === 'press' && e.key_type === 'character').length} characters`;
      if (elapsed < 10000) return;
    }
    busy = true;
    try {
      const batch = events, hashes = pending;
      events = []; pending = []; origin = performance.now();
      await Promise.all(hashes);
      await submitWindow(batch, token);
    } catch (error) { if (token === generation) fail(error); }
    finally { busy = false; }
  }
  async function begin(nextMode) {
    if (running || busy) return;
    $('monitor-button').disabled = true; $('replay-button').disabled = true;
    $('error-banner').hidden = true;
    try {
      // A single collector per browser avoids mixing two tabs into one server session.
      if (navigator.locks) {
        let resolveAcquired;
        const acquired = new Promise(resolve => { resolveAcquired = resolve; });
        navigator.locks.request('aca-keyboard-session', {ifAvailable: true}, async lock => {
          if (!lock) { resolveAcquired(false); return; }
          await new Promise(resolve => { tabOwner = resolve; resolveAcquired(true); });
        });
        if (!await acquired) throw new Error('A session is already running in another tab. Stop it there before starting here.');
      }
      if (nextMode === 'live') {
        if (!crypto.subtle) throw new Error('Keyboard privacy requires localhost or HTTPS. Open the dashboard at http://127.0.0.1:5000.');
        signingKey = await crypto.subtle.generateKey({name: 'HMAC', hash: 'SHA-256'}, false, ['sign']);
      }
      await api('/api/start', {mode: nextMode});
      history = []; mode = nextMode; running = true; events = []; pending = []; held.clear(); keyIds.clear();
      const token = ++generation;
      render(); origin = performance.now();
      $('typing-area').value = '';
      $('typing-area').disabled = mode !== 'live';
      $('monitor-button').textContent = 'Ⅱ  Stop session';
      $('monitor-button').disabled = false;
      $('replay-button').disabled = true;
      $('window-label').textContent = mode === 'live' ? 'Evaluated every 10 seconds' : 'Recorded 10-second windows';
      $('capture-note').textContent = mode === 'live' ? 'Only this area is monitored. HMAC-SHA256 key IDs; your text is never sent or saved.' : 'Recorded keyboard session · accelerated playback. No keyboard capture.';
      $('capture-label').textContent = mode === 'live' ? 'Collecting first window…' : 'Replaying recorded windows…';
      system(mode === 'live' ? 'Monitoring active' : 'Recorded replay', mode === 'live' ? 'green' : 'amber');
      if (mode === 'live') $('typing-area').focus();
      timer = setInterval(() => tick(token), mode === 'live' ? 100 : 1000);
      if (mode === 'replay') await tick(token);
    } catch (error) { fail(error); }
  }
  function record(event, type) {
    if (!running || mode !== 'live' || event.isComposing) return;
    if (type === 'press') {
      if (event.repeat || held.has(event.code)) return;
      held.add(event.code);
    } else {
      if (!held.has(event.code)) return;
      held.delete(event.code);
    }
    const elapsed = performance.now() - origin;
    if (elapsed >= 10000 || events.length + pending.length >= 4000) return;
    const batch = events;
    const keyType = event.key.length === 1 && event.code !== 'Space' ? 'character' : 'special';
    if (!keyIds.has(event.code)) {
      keyIds.set(event.code, crypto.subtle.sign('HMAC', signingKey, new TextEncoder().encode(event.code)).then(buffer => Array.from(new Uint8Array(buffer), b => b.toString(16).padStart(2, '0')).join('')));
    }
    const promise = keyIds.get(event.code).then(keyId => batch.push({elapsed_ms: elapsed, event: type, key_id: keyId, key_type: keyType}));
    pending.push(promise);
  }
  $('typing-area').addEventListener('keydown', event => record(event, 'press'));
  $('typing-area').addEventListener('keyup', event => record(event, 'release'));
  $('typing-area').addEventListener('blur', () => held.clear());
  $('monitor-button').addEventListener('click', () => running ? stop(mode === 'replay' ? 'Replay paused' : 'Monitoring paused · partial window discarded') : begin('live'));
  $('replay-button').addEventListener('click', () => begin('replay'));
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && running) stop('Paused while tab is hidden · partial window discarded');
  });
  document.querySelectorAll('.nav-item').forEach(link => link.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('selected', item === link));
  }));
  api('/api/state').then(data => {
    history = data.history; mode = data.mode; render();
    if (history.length) { system('Session paused'); $('capture-label').textContent = 'Previous results restored · start a new session to continue'; }
  }).catch(fail);
})();
