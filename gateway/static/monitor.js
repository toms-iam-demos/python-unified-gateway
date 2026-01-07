  const API_LATEST = "/events/latest?limit=80&include_body=1&include_json_obj=1";
  const API_EVENT  = (id) => `/events/${encodeURIComponent(id)}?include_body=1&include_json_obj=1`;
  const SSE_URL    = "/webhooks/monitor/stream";

  const els = {
    status:  document.getElementById("status"),
    mode:    document.getElementById("mode"),
    src:     document.getElementById("src"),
    list:    document.getElementById("list"),
    sel:     document.getElementById("sel"),
    json:    document.getElementById("json"),
    headers: document.getElementById("headers"),
    raw:     document.getElementById("raw"),
    refresh: document.getElementById("refresh"),
    clear:   document.getElementById("clear"),
  };
  // --- DIAGNOSTIC: prove JS is executing (shows on-page) ---
  try {
    els.status.textContent = "JS loaded (boot)";
    els.status.className = "pill ok";
  } catch (e) {
    // If even this fails, DOM ids are mismatched or script isn't running.
  }

  function showFatal(msg) {
    try {
      els.status.textContent = "JS error: " + msg;
      els.status.className = "pill bad";
    } catch (e) {}
  }

  window.addEventListener("error", (ev) => {
    showFatal(ev.message || "window error");
  });

  window.addEventListener("unhandledrejection", (ev) => {
    showFatal((ev.reason && ev.reason.message) ? ev.reason.message : String(ev.reason));
  });


  const seen = new Set();
  const cache = new Map(); // id -> full event object (from /events/latest)

  let pollTimer = null;

  function setStatus(text, cls) {
    els.status.textContent = text;
    els.status.className = "pill " + (cls || "warn");
  }

  function setMode(text) {
    els.mode.textContent = text;
  }

  function pretty(obj) {
    try { return JSON.stringify(obj, null, 2); }
    catch { return String(obj); }
  }

  function addEvent(evt) {
    const id = evt.event_id || evt.id || evt.correlation_id || "(no-id)";
    cache.set(id, evt);
    if (seen.has(id)) return;
    seen.add(id);

    const li = document.createElement("li");
    li.innerHTML = `
      <div class="meta">
        <span><code>${evt.source || "unknown"}</code></span>
        <span>${evt.timestamp || ""}</span>
      </div>
      <div class="title">${id}</div>
      <div class="meta"><span>${evt.status || "ok"}</span><span>click to view</span></div>
    `;
    li.onclick = () => loadOne(id);
    els.list.prepend(li);
  }

  async function loadLatest() {
    const res = await fetch(API_LATEST, { cache: "no-store" });
    if (!res.ok) throw new Error("latest HTTP " + res.status);
    const data = await res.json();
    const events = Array.isArray(data) ? data : (data.events || data.items || []);
    for (const evt of events) addEvent(evt);
  }

  async function loadOne(id) {
    els.sel.textContent = id;

    // Use cached full event object from /events/latest (work-safe).
    const evt = cache.get(id);
    if (!evt) {
      els.src.textContent = "unknown";
      els.headers.textContent = pretty({ error: "event not in cache", id });
      els.raw.textContent = "";
      els.json.textContent = "{}";
      return;
    }

    els.src.textContent = evt.source || "unknown";

    // Headers: backend stores JSON string in headers_json
    let headersObj = {};
    try {
      headersObj = evt.headers_json ? JSON.parse(evt.headers_json) : {};
    } catch (e) {
      headersObj = { _parse_error: String(e), _raw: evt.headers_json };
    }

    els.headers.textContent = pretty(headersObj);
    els.raw.textContent = evt.body_raw || "";
    els.json.textContent = pretty(evt.json_obj || {});
  }

  function startPolling() {
    if (pollTimer) return;
    setMode("polling");
    setStatus("Polling (work-safe)", "warn");
    pollTimer = setInterval(loadLatest, 2500);
  }

  async function connect() {
    setMode("initial");
    setStatus("Loading history…", "warn");
    await loadLatest();
    setStatus("History loaded", "ok");

    setMode("sse");
    setStatus("Connecting…", "warn");

    const es = new EventSource(SSE_URL);
    let gotFirst = false;

    const silentFallback = setTimeout(() => {
      if (!gotFirst) {
        es.close();
        startPolling();
      }
    }, 4000);

    es.onmessage = (e) => {
      gotFirst = true;
      clearTimeout(silentFallback);
      setStatus("Connected (live)", "ok");
      try { addEvent(JSON.parse(e.data)); } catch {}
    };

    es.onerror = () => {
      es.close();
      startPolling();
    };
  }

  els.refresh.onclick = loadLatest;
  els.clear.onclick = () => {
    els.list.innerHTML = "";
    seen.clear();
    els.sel.textContent = "none";
    els.json.textContent = "{}";
    els.headers.textContent = "{}";
    els.raw.textContent = "";
  };

  connect();
