const $ = s => document.querySelector(s),
    $$ = s => [...document.querySelectorAll(s)];
const token = $('meta[name="demo-token"]').content;
let catalog, state, selected, record, filter = '',
    page = 1,
    query = '',
    timer, resetManifest;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
} [c]));
const money = n => new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2
}).format(n / 100);

function toast(s) {
    $('#toast').textContent = s;
    $('#toast').style.display = 'block';
    clearTimeout(timer);
    timer = setTimeout(() => $('#toast').style.display = 'none', 6500)
}
async function api(path, method = 'GET', body) {
    const r = await fetch('/api/' + path, {
        method,
        headers: {
            'X-Demo-Token': token,
            'Content-Type': 'application/json'
        },
        body: body === undefined ? undefined : JSON.stringify(body)
    });
    const d = await r.json();
    if (!r.ok) throw Error(typeof d.detail === 'string' ? d.detail : JSON.stringify(d.detail));
    return d
}

function act(fn) {
    return async () => {
        try {
            await fn()
        } catch (e) {
            toast(e.message)
        }
    }
}

function view(name) {
    $('.breadcrumb').textContent='Employee workspace / '+({workspace:'Procurement home',research:'Policy & research',architecture:'Connected workflow',lab:'Integration lab'}[name]);
    $$('.view').forEach(e => e.classList.toggle('hidden', e.id !== name));
    $$('nav button').forEach(e => e.classList.toggle('active', e.dataset.view === name))
}
$$('[data-view]').forEach(b => b.onclick = () => view(b.dataset.view));
async function refresh() {
    state = await api(`state?kind=${encodeURIComponent(filter)}&q=${encodeURIComponent(query)}&page=${page}`);
    $('#stat-count').textContent = state.count.toLocaleString();
    $('#stat-delivered').textContent = state.delivered.toLocaleString();
    $('#queue-count').textContent = state.filtered + ' records';
    $('#page-label').textContent = `${state.page} / ${state.pages}`;
    $('#previous').disabled = page <= 1;
    $('#next').disabled = page >= state.pages;
    $('#seed').disabled = state.count > 0;
    $('#reset').disabled = !state.count;
    $('#records').innerHTML = state.records.length ? state.records.map(r => `<button class="record ${r.id===selected?'active':''}" data-id="${esc(r.id)}"><small>${esc(r.id)} · ${esc(r.department)}</small><strong>${esc(r.title)}</strong><em class="${r.evaluation.ready?'good':''}">${r.status==='review'?(r.evaluation.ready?'Ready for review':r.evaluation.blockers.length+' review items'):esc(r.status)}</em></button>`).join('') : '<p class="muted">No records. Generate a corpus below, or clear the filter.</p>';
    $$('.record').forEach(b => b.onclick = act(() => select(b.dataset.id)));
    $('#audit').innerHTML = state.audit.map(a => `<div class="audit-row"><time>${esc(new Date(a.time).toLocaleString())}</time><b>${esc(a.subject)}</b><span>${esc(a.event)}</span></div>`).join('') || '<p class="muted">Your first action will appear here.</p>';
    if (selected) {
        try {
            record = await api('records/' + selected);
            renderDetail()
        } catch (e) {
            selected = null;
            $('#detail').innerHTML = '<div class="empty"><h2>Choose another case.</h2><p>Generate or select a fixture to continue.</p></div>'
        }
    }
}
async function select(id) {
    selected = id;
    record = await api('records/' + id);
    renderDetail();
    $$('.record').forEach(b => b.classList.toggle('active', b.dataset.id === id))
}
const metric = (label, value, alert = false) => `<div class="metric ${alert?'alert':''}"><small>${label}</small><b>${esc(value)}</b></div>`;

function input(label, key, value, type = 'number', step = '1') {
    return `<label>${label}<input data-input="${key}" type="${type}" step="${step}" value="${esc(value)}" min="0"></label>`
}

function renderDetail() {
    const r = record,
        e = r.evaluation,
        m = e.metrics,
        x = r.inputs;
    let metrics = '',
        inputs = '';
    if (r.kind === 'pricing') {
        metrics = metric('Reviewed basis', money(m.expected_cents)) + metric('Submitted price', money(m.submitted_cents)) + metric('Variance', money(m.variance_cents), m.variance_cents !== 0);
        inputs = input('Submitted index', 'submitted_index', x.submitted_index, 'number', '.01') + `<p class="muted">Base $120,000 × coefficient 1.04 × index. Demo reviewed index: <strong>1.08</strong>. Fictional values, not a licensed unit price book.</p>`
    }
    if (r.kind === 'invoice') {
        metrics = metric('Accepted, unpaid', money(m.available_cents)) + metric('Invoice', money(m.invoice_cents)) + metric('Contract remainder', money(m.remaining_contract_cents));
        inputs = input('Invoice amount (cents)', 'invoice_cents', x.invoice_cents) + `<p class="muted">Accepted to date: $84,000. Previously paid: $36,000. Contract ceiling: $120,000. Synthetic ledger.</p>`
    }
    if (r.kind === 'emergency') {
        metrics = metric('CPO contact · 8h', m.contact_hour.status, ['late', 'overdue'].includes(m.contact_hour.status)) + metric('Form · 24h', m.form_hour.status, ['late', 'overdue'].includes(m.form_hour.status)) + metric('Demo estimate', money(r.amount_cents));
        inputs = input('Elapsed incident hours', 'elapsed_hours', x.elapsed_hours) + input('Actual contact hour (blank = missing)', 'contact_hour', x.contact_hour ?? '') + input('Actual form hour (blank = missing)', 'form_hour', x.form_hour ?? '')
    }
    if (r.kind === 'renewal') {
        metrics = metric('Notice deadline', m.notice_deadline) + metric('Days to notice', m.days_to_notice, m.days_to_notice < 0) + metric('Annual demo value', money(r.amount_cents));
        inputs = input('Illustrative notice interval (days)', 'notice_days', x.notice_days) + `<p class="muted">Contract end: ${esc(x.end_date)}. Fixed demonstration date: ${esc(x.as_of)}. Review the actual clause before making a decision.</p>`
    }
    const p = r.plans.find(p => !['stale'].includes(p.state));
    $('#detail').innerHTML = `<div class="case-header"><span class="pill">${esc(r.id)} · VERSION ${r.version} · ${esc(r.status.toUpperCase())}</span><h2>${esc(r.title)}</h2><p class="muted">${esc(r.supplier)} · ${esc(r.owner)} · <strong>SYNTHETIC</strong></p></div><div class="metrics">${metrics}</div><h3>Review the inputs</h3><div class="edit-grid">${inputs}</div><h3>Evidence checklist</h3><p class="muted">These switches simulate a reviewer’s recorded evidence. They do not verify documents or grant real authority.</p><div class="checks">${Object.entries(r.evidence).map(([k,v])=>`<label class="check"><input data-evidence="${k}" type="checkbox" ${v?'checked':''}>${esc(catalog.evidence_labels[k])}</label>`).join('')}</div><div class="button-row"><button id="save" ${['delivered','unknown'].includes(r.status)?'disabled':''}>Save review inputs</button><button id="prepare" class="primary" ${!e.ready||p||r.status!=='review'?'disabled':''}>Prepare handoff</button></div>${e.ready?`<p class="ready">Evidence gates satisfied in the simulation. ${p?'See the reviewed handoff state below.':'Separate demo approval is still required.'}</p>`:`<div class="blockers"><strong>Before preparation</strong><ul>${e.blockers.map(b=>`<li>${esc(b)}</li>`).join('')}</ul></div>`}${e.warnings.map(w=>`<div class="warning">${esc(w)}</div>`).join('')}${p?planHTML(p):''}<details><summary>Inspect the record JSON</summary><pre>${esc(JSON.stringify(r,null,2))}</pre></details>`;
    $('#api-preview').textContent = JSON.stringify(r, null, 2);
    $('#save').onclick = act(saveReview);
    $('#prepare').onclick = act(async () => {
        await api('plans', 'POST', {
            record_id: r.id
        });
        await refresh();
        toast('Command prepared. Review the payload, then approve the simulated handoff.')
    });
    $$('[data-action]').forEach(b => b.onclick = act(async () => {
        await api('plans/' + p.id + '/' + b.dataset.action, 'POST', b.dataset.action === 'execute' ? {
            lose_response: $('#lose-response')?.checked ?? false
        } : undefined);
        await refresh();
        toast(b.dataset.action === 'reconcile' ? 'Existing receipt reconciled; no second write.' : 'Local action recorded.')
    }));
}

function planHTML(p) {
    return `<section class="plan"><p class="eyebrow">REVIEWED HANDOFF / ${esc(p.id)}</p><h3>${esc(p.state.toUpperCase())}</h3><div class="steps"><span class="done">1 Prepared</span><span class="${p.state!=='prepared'?'done':''}">2 Demo approved</span><span class="${['delivered','unknown'].includes(p.state)?'done':''}">3 Inbox accepted</span><span class="${p.state==='delivered'?'done':''}">4 Receipt verified</span></div><p class="muted">Destination: local procurement inbox. This is a review packet, never a purchase order or payment instruction.</p><details><summary>Inspect immutable command</summary><pre>${esc(JSON.stringify(JSON.parse(p.payload),null,2))}</pre><p class="muted">SHA-256: ${esc(p.digest)}</p></details><div class="button-row">${p.state==='prepared'?'<button data-action="approve" class="primary">Approve as demo reviewer</button>':''}${p.state==='approved'?'<label class="check"><input type="checkbox" id="lose-response">Simulate lost response</label><button data-action="execute" class="primary">Deliver to local inbox</button>':''}${p.state==='unknown'?'<button data-action="reconcile" class="primary">Reconcile existing receipt</button>':''}${['unknown','delivered'].includes(p.state)?'<button data-action="execute">Replay same command</button>':''}</div></section>`
}
async function saveReview() {
    const b = {
        version: record.version,
        evidence: {}
    };
    $$('[data-evidence]').forEach(e => b.evidence[e.dataset.evidence] = e.checked);
    $$('[data-input]').forEach(e => b[e.dataset.input] = e.value === '' ? null : e.dataset.input === 'submitted_index' ? e.value : Number(e.value));
    await api('records/' + record.id + '/review', 'PUT', b);
    await refresh();
    toast('Saved; earlier prepared approvals for this record are invalidated.')
}
$('#search').oninput = () => {
    clearTimeout($('#search').searchTimer);
    $('#search').searchTimer = setTimeout(act(async () => {
        query = $('#search').value;
        page = 1;
        await refresh()
    }), 250)
};
$('#previous').onclick = act(async () => {
    page--;
    await refresh()
});
$('#next').onclick = act(async () => {
    page++;
    await refresh()
});
$('#all-filter').onclick = act(async () => {
    filter = '';
    page = 1;
    query = '';
    $('#search').value = '';
    $$('.scenario').forEach(b => b.classList.remove('selected'));
    await refresh()
});
$('#count').oninput = () => $('#count-label').textContent = Number($('#count').value).toLocaleString();
$('#seed').onclick = act(async () => {
    await api('seed', 'POST', {
        count: Number($('#count').value)
    });
    await refresh();
    if (state.records.length) await select(state.records[0].id);
    toast('Synthetic corpus generated. No provider requests made.')
});
$('#export').onclick = act(async () => {
    const data = await api('export');
    const u = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json'
    }));
    const a = document.createElement('a');
    a.href = u;
    a.download = 'municipal-demo-evidence.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(u), 1000);
    toast('Local evidence export downloaded.')
});
$('#reset').onclick = act(async () => {
    resetManifest = await api('reset-manifest');
    $('#reset-summary').textContent = `Remove ${resetManifest.record_count} synthetic records and their local command receipts from ${resetManifest.cohort}. No external data is affected.`;
    $('#reset-prompt').textContent = 'Type RESET ' + resetManifest.cohort;
    $('#reset-confirm').value = '';
    $('#reset-dialog').showModal()
});
$('#cancel-reset').onclick = () => $('#reset-dialog').close();
$('#confirm-reset').onclick = act(async () => {
    await api('reset', 'POST', {
        cohort: resetManifest.cohort,
        manifest_hash: resetManifest.manifest_hash,
        confirmation: $('#reset-confirm').value
    });
    $('#reset-dialog').close();
    await refresh();
    toast('Owned fixture cohort removed; audit retained.')
});
$('#copy-token').onclick = act(async () => {
    await navigator.clipboard.writeText(token);
    toast('Local token copied. Paste into Swagger Authorize.')
});
async function boot() {
    catalog = await api('catalog');
    const descriptions = ['Catch an index mismatch before a work-order review.', 'Match accepted work to an evidence-backed invoice.', 'Track the 8h / 24h evidence intervals.', 'Bring notice terms and performance into one review.'];
    $('#scenario-cards').innerHTML = Object.entries(catalog.scenarios).map(([k, s], i) => `<button class="scenario" data-kind="${k}"><span class="idx">0${i+1} / ${esc(s.source)}</span><strong>${esc(s.label)}</strong><small>${descriptions[i]}</small></button>`).join('');
    $$('.scenario').forEach(b => b.onclick = act(async () => {
        filter = b.dataset.kind;
        page = 1;
        $$('.scenario').forEach(e => e.classList.toggle('selected', e === b));
        await refresh();
        if (state.records.length) await select(state.records[0].id)
    }));
    $('#sources').innerHTML = catalog.sources.map(s => `<article class="panel source"><div class="meta">${esc(s.id)} · ${esc(s.classification)} · ${esc(s.date)}</div><h3>${esc(s.title)}</h3><p>${esc(s.finding)}</p><p class="muted">Demo implication: ${esc(s.implication)}</p><a href="${esc(s.url)}" target="_blank" rel="noopener">Read source ↗</a></article>`).join('');
    await refresh();
    if (state.records.length) await select(state.records[0].id)
}
boot().catch(e => toast(e.message));
