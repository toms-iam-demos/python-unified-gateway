/* Same-origin read-only requests. Event content is rendered only as text. */
(function () {
  'use strict';
  const secretKey = /authorization|cookie|password|passwd|secret|token|api.?key|signature|credential/i;
  const personalKey = /email|phone|address|remote_addr|name|recipient|signer|contact/i;
  function scrubText(value, personal) {
    let text = String(value).replace(/\b(Bearer|Basic)\s+[A-Za-z0-9+/=._~-]+/gi, '$1 [redacted]')
      .replace(/\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]+\b/g, '[redacted]')
      .replace(/((?:password|secret|token|api[_-]?key|signature|authorization|cookie)\s*[=:]\s*)[^\s&,;]+/gi, '$1[redacted]');
    if (personal) text = text.replace(/[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[email masked]')
      .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[IP masked]')
      .replace(/\b(?:\+?\d[\d ()-]{8,}\d)\b/g, '[number masked]');
    return text;
  }
  function redact(value, personal = true, depth = 0) {
    if (depth > 40) return '[nested data omitted]';
    if (typeof value === 'string') {
      try { return JSON.stringify(redact(JSON.parse(value), personal, depth + 1)); } catch (_) {
        // Incomplete JSON cannot be safely parsed: omit credential-bearing previews.
        for (const match of value.matchAll(/("(?:\\.|[^"\\])*")\s*:/g)) {
          let key;
          try { key = JSON.parse(match[1]); } catch (_) { return '[redacted] Unparseable JSON preview.'; }
          if (secretKey.test(key)) return '[redacted] Incomplete JSON preview contains credential fields.';
        }
        return scrubText(value, personal);
      }
    }
    if (Array.isArray(value)) return value.map(v => redact(v, personal, depth + 1));
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k,v]) => [k, secretKey.test(k) ? '[redacted]' : personal && personalKey.test(k) ? '[masked]' : redact(v, personal, depth + 1)]));
    return value;
  }
  function outcome(event) {
    const verify = String(event.verify_status || '').toLowerCase();
    if (/fail|invalid|reject|error/.test(verify)) return {key:'verification', label:'Verification issue'};
    if (Number(event.status_code) >= 400) return {key:'error', label:'HTTP ' + Number(event.status_code)};
    if (verify === 'verified') return {key:'received', label:'Verified receipt'};
    if (event.status_code != null && Number(event.status_code) >= 100) return {key:'received', label:'HTTP ' + Number(event.status_code)};
    return {key:'unknown', label:'No result recorded'};
  }
  function displayTime(value) {
    if (value == null || value === '') return 'Not recorded';
    const date = new Date(typeof value === 'number' ? (value < 1e12 ? value * 1000 : value) : value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toISOString().replace('T', ' ').replace('.000Z', ' UTC').replace('Z', ' UTC');
  }
  const helpers = {redact, outcome, displayTime};
  if (typeof module !== 'undefined' && module.exports) module.exports = helpers;
  if (typeof document === 'undefined') return;
  const root = document.getElementById('pug-event-preview');
  if (!root) return;
  const $ = selector => root.querySelector(selector);
  let records = [], selected = null, selectedId = '', view = 'json', busy = false, lastRefresh = 0;
  const node = (tag, text, cls) => {const el=document.createElement(tag); if (text != null) el.textContent=text; if(cls) el.className=cls; return el;};
  const badge = event => {const result=outcome(event);return node('span',result.label,'status '+result.key);};
  async function getJSON(path) {
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(path, {credentials:'same-origin', cache:'no-store', headers:{Accept:'application/json'}, signal:controller.signal});
      if (response.status === 401 || response.status === 403) throw new Error('Your operator session needs sign-in. Reload this page to sign in again.');
      if (response.status === 429) throw new Error('Refresh limit reached. Wait a few seconds, then refresh.');
      if (!response.ok) throw new Error('Events are unavailable (HTTP '+response.status+'). Try Refresh.');
      if (!(response.headers.get('content-type') || '').includes('application/json')) throw new Error('The server returned an unexpected response. Reload to check your sign-in.');
      const data = await response.json();
      if (data.ready !== true) throw new Error('The event store is not ready. Existing results may be stale; try Refresh.');
      return data;
    } catch (error) {
      if(error.name === 'AbortError') throw new Error('The request timed out. Existing results may be stale; try Refresh.');
      if(error instanceof TypeError) throw new Error('Cannot reach the event service. Check your connection, then try Refresh. Previous results may be stale.');
      throw error;
    }
    finally {clearTimeout(timeout);}
  }
  function renderPayload() {
    root.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
    if (!selected) return;
    const personal = $('#mask-fields').checked;
    let value;
    if (view === 'headers') {try {value=JSON.parse(selected.headers_json || '{}');} catch (_) {value=selected.headers_json || 'No headers recorded.';}}
    else if(view === 'raw') value=selected.body_raw == null ? 'No body recorded.' : selected.body_raw;
    else value=selected.json_obj != null ? selected.json_obj : selected.json_parsed || {message:'No parsed JSON available. Use Raw body for non-JSON payloads.'};
    const safe=redact(value,personal);
    $('#payload').textContent=typeof safe==='string'?safe:JSON.stringify(safe,null,2);
    const warnings=[];
    if(selected.body_truncated && view==='raw') warnings.push('Cached body preview truncated at 4,000 bytes; open the raw record for more.');
    if(selected.json_omitted && view==='json') warnings.push('Parsed JSON exceeds the bounded preview. Inspect the raw record if needed.');
    if(selected.headers_omitted && view==='headers') warnings.push('Headers exceed the safe preview size and were omitted.');
    $('#payload-notice').textContent=warnings.join(' ');
    $('#detail-summary').textContent=scrubText([selected.method,selected.path].filter(Boolean).join(' ') || 'No request path recorded.',personal);
    const reason = selected.verify_reason ? ' '+scrubText(selected.verify_reason,personal)+'.' : '';
    $('#event-result').textContent='Verification: '+(selected.verify_status || 'not recorded')+'.'+reason+' Receipt evidence does not confirm downstream completion.';
    $('#event-result').className='event-result '+outcome(selected).key;
  }
  function renderDetail() {
    if(!selected) return;
    $('#detail-source').textContent=selected.source || 'Unspecified source';
    $('#detail-status').replaceChildren(badge(selected));
    const providerType=selected.json_obj && (selected.json_obj.event || selected.json_obj.type);
    $('#detail-title').textContent=typeof providerType==='string'?providerType:(selected.kind || 'Event received');
    $('#detail-time').textContent=displayTime(selected.received_at);
    $('#detail-id').textContent=selected.event_id || 'Not recorded';
    $('#detail-correlation').textContent=selected.correlation_id || 'Not recorded';
    $('#raw-event').href='/events/'+encodeURIComponent(selected.event_id)+'?include_body=1&include_json_obj=1&body_max_chars=20000';
    $('#raw-event').hidden=false;
    renderPayload();
  }
  function choose(event) {
    selectedId=event.event_id;selected=event;renderList();renderDetail();
  }
  function renderList() {
    const query=$('#event-search').value.trim().toLowerCase(),source=$('#source-filter').value,result=$('#outcome-filter').value;
    const filtered=records.filter(e=>(!source||e.source===source)&&(!result||outcome(e).key===result)&&(!query||[e.event_id,e.kind,e.source,e.correlation_id,e.path].join(' ').toLowerCase().includes(query)));
    $('#event-count').textContent=filtered.length+' / '+records.length;
    const list=$('#event-list');list.replaceChildren();
    if(!filtered.length){list.append(node('div',records.length?'No matching events.':'No events returned.','empty'));return;}
    for(const event of filtered){const button=node('button',null,'event-row');button.type='button';button.setAttribute('aria-pressed',String(event.event_id===selectedId));const top=node('div',null,'row-top');top.append(node('span',event.source || 'Unspecified','source-name'),badge(event));const bottom=node('div',null,'row-bottom');bottom.append(node('span',event.event_id),node('span',displayTime(event.received_at)));button.append(top,node('div',event.kind || 'Event received','event-name'),bottom);button.onclick=()=>choose(event);list.append(button);}
  }
  async function refresh(force = false) {
    if(busy || Date.now()-lastRefresh<1500)return;
    busy=true;lastRefresh=Date.now();$('#refresh-events').disabled=true;
    try {
      const data=await getJSON('/events/ui/snapshot'+(force?'?refresh=true':''));
      if(!Array.isArray(data.events))throw new Error('The event response is incomplete. Try Refresh.');
      records=data.events;
      const selector=$('#source-filter'),old=selector.value;
      selector.replaceChildren(new Option('All sources',''),...Array.from(new Set(records.map(e=>e.source).filter(Boolean))).sort().map(s=>new Option(s,s)));
      selector.value=Array.from(selector.options).some(o=>o.value===old)?old:'';
      $('#feed-error').hidden=true;
      $('#connection-status').textContent='Cached snapshot · Captured '+displayTime(data.captured_at);
      renderList();
      if(records.length)choose(records.find(e=>e.event_id===selectedId)||records[0]);
      else {
        selected=null;selectedId='';$('#detail-source').textContent='CACHED SNAPSHOT';$('#detail-status').replaceChildren();
        $('#detail-title').textContent='No events in snapshot';$('#detail-summary').textContent='Refresh the snapshot when records are available.';
        for(const id of ['#detail-time','#detail-id','#detail-correlation'])$(id).textContent='—';
        $('#event-result').textContent='No receipt evidence in this snapshot.';$('#event-result').className='event-result unknown';
        $('#payload').textContent='No event selected.';$('#payload-notice').textContent='';$('#raw-event').hidden=true;
      }
    }catch(error){$('#feed-error').textContent=error.message;$('#feed-error').hidden=false;$('#connection-status').textContent=records.length?'Refresh failed · Keeping previous snapshot':'Snapshot unavailable';}
    finally{busy=false;setTimeout(()=>{$('#refresh-events').disabled=false;},1500);}
  }
  $('#refresh-events').onclick=()=>refresh(true);
  $('#event-search').oninput=renderList;$('#source-filter').onchange=renderList;$('#outcome-filter').onchange=renderList;
  $('#mask-fields').onchange=renderPayload;
  root.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view;renderPayload();});
  refresh();
})();
