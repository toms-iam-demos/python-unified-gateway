(() => {
  'use strict';
  const ids = ['status','mode','src','list','sel','json','headers','raw','refresh','clear'];
  const els = Object.fromEntries(ids.map(id => [id, document.getElementById(id)]));
  const API_LATEST = '/events/latest?limit=80&include_body=0&include_json_obj=0';
  const API_EVENT = id => `/events/${encodeURIComponent(id)}?include_body=1&include_json_obj=1&body_max_chars=16000`;
  let timer, busy = false, stopped = false, failures = 0, selection = 0, detailController;
  const pretty = value => JSON.stringify(value, null, 2);
  function status(text, cls = 'warn') {
    els.status.textContent = text;
    els.status.className = 'pill ' + cls;
  }
  async function request(url, controller = new AbortController()) {
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, {cache: 'no-store', signal: controller.signal});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const data = await response.json();
      if (data.ready !== true) throw new Error('Event store unavailable');
      return data;
    } finally { clearTimeout(timeout); }
  }
  function clearDetail() {
    selection++;
    if (detailController) detailController.abort();
    els.sel.textContent = 'none';
    els.src.textContent = 'docusign';
    els.json.textContent = '{}';
    els.headers.textContent = '{}';
    els.raw.textContent = '';
  }
  async function loadOne(id) {
    clearDetail();
    const version = selection;
    detailController = new AbortController();
    els.sel.textContent = id;
    els.json.textContent = 'Loading preview...';
    try {
      const data = await request(API_EVENT(id), detailController);
      if (version !== selection) return;
      const evt = data.event;
      if (!evt) throw new Error('Event not found');
      els.src.textContent = evt.source || 'unknown';
      els.headers.textContent = evt.headers_omitted ? 'Headers exceed preview limit.' : pretty(JSON.parse(evt.headers_json || '{}'));
      els.raw.textContent = (evt.body_raw || '') + (evt.body_truncated ? '\n[Preview truncated; original retained in ledger.]' : '');
      els.json.textContent = evt.json_omitted
        ? `JSON exceeds preview limit (${evt.json_bytes} bytes). See bounded raw preview below.`
        : pretty(evt.json_obj ?? {});
    } catch (error) {
      if (version !== selection) return;
      els.json.textContent = 'Preview unavailable: ' + (error.name === 'AbortError' ? 'request timed out' : error.message);
    }
  }
  function render(events) {
    const fragment = document.createDocumentFragment();
    for (const evt of events.slice(0, 80)) {
      const id = evt.event_id;
      if (!id) continue;
      const item = document.createElement('li');
      const meta = document.createElement('div'); meta.className = 'meta';
      meta.textContent = `${evt.source || 'unknown'} · ${evt.received_at || ''}`;
      const title = document.createElement('div'); title.className = 'title'; title.textContent = id;
      const state = document.createElement('div'); state.className = 'meta';
      state.textContent = `${evt.verify_status || 'unknown'} · click to view`;
      item.append(meta, title, state);
      item.tabIndex = 0; item.setAttribute('role', 'button');
      item.onclick = () => loadOne(id);
      item.onkeydown = event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); loadOne(id); } };
      fragment.append(item);
    }
    els.list.replaceChildren(fragment);
  }
  async function poll() {
    if (busy || stopped || document.hidden) return;
    clearTimeout(timer);
    busy = true;
    try {
      const data = await request(API_LATEST);
      if (!Array.isArray(data.events)) throw new Error('Invalid event response');
      if (stopped) return;
      render(data.events);
      failures = 0;
      status(`Updated ${new Date().toLocaleTimeString()}`, 'ok');
    } catch (error) {
      failures++;
      status('List stale: ' + (error.name === 'AbortError' ? 'request timed out' : error.message), 'bad');
    } finally {
      busy = false;
      if (!stopped && !document.hidden) timer = setTimeout(poll, Math.min(60000, 5000 * 2 ** Math.min(failures, 4)));
    }
  }
  els.refresh.onclick = () => { stopped = false; poll(); };
  els.clear.onclick = () => {
    stopped = true; clearTimeout(timer); clearDetail(); els.list.replaceChildren();
    status('Cleared. Refresh to resume.');
  };
  document.addEventListener('visibilitychange', () => {
    clearTimeout(timer);
    if (!document.hidden) poll();
  });
  window.addEventListener('pagehide', () => {
    stopped = true; clearTimeout(timer); clearDetail();
  });
  els.mode.textContent = 'summary polling';
  status('Loading summaries...');
  poll();
})();
