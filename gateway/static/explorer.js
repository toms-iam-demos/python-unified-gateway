"use strict";

(() => {
  const view = document.querySelector("#view");
  const detail = document.querySelector("#detail");
  const status = document.querySelector("#status");
  const refreshButton = document.querySelector("#refresh");
  const tabs = document.querySelector("#tabs");
  const modes = ["Architecture", "Request Trace", "Routes", "Data", "docusign", "Runtime"];
  let mode = modes[0];
  let generation = 0;
  let activeRequest = null;

  function inspect(value) {
    detail.textContent = JSON.stringify(value, null, 2);
  }

  function node(parent, label, value) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "node";
    button.textContent = label;
    button.addEventListener("click", () => inspect(value));
    parent.append(button);
    return button;
  }

  function paragraph(parent, text) {
    const element = document.createElement("p");
    element.textContent = text;
    parent.append(element);
  }

  function arrow(parent) {
    const element = document.createElement("div");
    element.className = "arrow";
    element.textContent = "↓";
    element.setAttribute("aria-hidden", "true");
    parent.append(element);
  }

  function routes(items) {
    const groups = new Map();
    for (const route of items) {
      const family = route.family.join(", ");
      if (!groups.has(family)) groups.set(family, []);
      groups.get(family).push(route);
    }
    for (const [family, items] of groups) {
      const heading = document.createElement("h2");
      heading.textContent = family;
      view.append(heading);
      for (const route of items) {
        node(view, `${route.methods.join(" / ")} ${route.path}`, route);
      }
    }
  }

  function architecture(flow) {
    const nodes = new Map(flow.map(item => [item.id, item]));
    function flowNode(parent, id) {
      const item = nodes.get(id);
      if (item) node(parent, item.name, item);
    }
    for (const id of ["ingress", "asgi", "framework", "validation", "handler"]) {
      flowNode(view, id);
      arrow(view);
    }
    const branches = document.createElement("div");
    branches.className = "branches";
    view.append(branches);
    for (const [label, ids] of [
      ["POST /webhooks/docusign", ["envelope", "ledger", "monitor"]],
      ["GET /docusign/jwt-test", ["oauth"]],
    ]) {
      const branch = document.createElement("section");
      const heading = document.createElement("h3");
      heading.textContent = label;
      branch.append(heading);
      branches.append(branch);
      ids.forEach((id, index) => {
        flowNode(branch, id);
        if (index < ids.length - 1) arrow(branch);
      });
    }
    paragraph(view, "Conceptual flow, not a discovered call graph. Framework substages are not separately measured. HMAC verification precedes ledger persistence.");
  }

  function requestTraces(result) {
    paragraph(view, "Completed requests in this worker. Streaming time includes waiting until disconnect; spans may overlap. Ingress, routing and validation timings are unavailable.");
    if (result.status !== "fulfilled") {
      node(view, "Trace telemetry unavailable", {status: "unavailable"});
      return;
    }
    if (!result.value.traces.length) {
      paragraph(view, "No completed requests yet. Visit /health, then refresh.");
    }
    for (const trace of result.value.traces) {
      node(view, `${trace.method} ${trace.path} · ${trace.status_code} · ${trace.duration_ms} ms`, trace);
      for (const span of trace.spans) {
        node(view, `↳ ${span.name} · ${span.duration_ms} ms (${span.status})`, span);
      }
    }
  }

  function ledger(data, result) {
    const envelope = data.flow.find(item => item.id === "envelope");
    node(view, "Envelope / idempotency", envelope);
    routes(data.routes.filter(route => route.path.startsWith("/events") || route.path.startsWith("/webhooks/monitor")));
    if (result.status !== "fulfilled") {
      node(view, "Ledger unavailable", {status: "unavailable", detail: result.reason.message});
      return;
    }
    const response = result.value;
    node(view, "Ledger status", {ready: response.ready, returned: response.returned});
    for (const event of response.events || []) {
      node(view, `${event.received_at} · ${event.source} · ${event.event_id}`, {
        event_id: event.event_id,
        source: event.source,
        path: event.path,
        received_at: event.received_at,
        verify_status: event.verify_status,
        timing_status: "historical timing unavailable",
      });
    }
  }

  async function get(path, signal) {
    const response = await fetch(path, {signal, cache: "no-store", credentials: "same-origin"});
    if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}`);
    return response.json();
  }

  async function refresh() {
    const requestId = ++generation;
    if (activeRequest) activeRequest.abort();
    const controller = new AbortController();
    activeRequest = controller;
    const timeout = setTimeout(() => controller.abort(), 8000);
    refreshButton.disabled = true;
    status.textContent = "Refreshing…";
    status.dataset.error = "false";
    try {
      const requests = [get("metadata", controller.signal), get("traces", controller.signal)];
      if (mode === "Data") requests.push(get("../events/latest?limit=20", controller.signal));
      const [metadata, traces, events] = await Promise.allSettled(requests);
      if (requestId !== generation) return;
      view.replaceChildren();
      if (metadata.status !== "fulfilled") {
        detail.textContent = "Explorer data is unavailable.";
        throw metadata.reason;
      }
      const data = metadata.value;
      switch (mode) {
        case "Architecture": architecture(data.flow); break;
        case "Routes": routes(data.routes); break;
        case "docusign": routes(data.routes.filter(route => route.path.includes("docusign"))); break;
        case "Runtime": node(view, "Worker runtime", data.runtime); break;
        case "Request Trace": requestTraces(traces); break;
        case "Data": ledger(data, events); break;
      }
      const unavailable = [];
      if (traces.status !== "fulfilled") unavailable.push("trace telemetry");
      if (events && events.status !== "fulfilled") unavailable.push("ledger");
      status.dataset.error = String(unavailable.length > 0);
      status.textContent = unavailable.length
        ? `Unavailable: ${unavailable.join(", ")}. Other views remain available.`
        : `Updated ${new Date().toLocaleTimeString()}. Samples are local to this worker.`;
    } catch (error) {
      if (requestId !== generation) return;
      status.dataset.error = "true";
      status.textContent = controller.signal.aborted
        ? "Explorer request timed out. Refresh to retry."
        : `Explorer unavailable: ${error.message}`;
    } finally {
      clearTimeout(timeout);
      if (requestId === generation) {
        activeRequest = null;
        refreshButton.disabled = false;
      }
    }
  }

  for (const name of modes) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = name;
    button.setAttribute("aria-pressed", String(name === mode));
    button.addEventListener("click", () => {
      mode = name;
      for (const tab of tabs.children) tab.setAttribute("aria-pressed", String(tab === button));
      detail.textContent = "Select a node, route, event or trace.";
      refresh();
    });
    tabs.append(button);
  }
  refreshButton.addEventListener("click", refresh);
  setInterval(() => {
    // Do not interrupt keyboard inspection or replace a focused route button.
    if (!document.hidden && !activeRequest && !view.contains(document.activeElement)) refresh();
  }, 10000);
  refresh();
})();
