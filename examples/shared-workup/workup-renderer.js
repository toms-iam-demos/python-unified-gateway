/* Shared, dependency-free workup presentation. Content is supplied by each example. */
(function(root){
  'use strict';
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const tones=new Set(['native','fixture','design','retained','implemented']);
  const tone=value=>tones.has(value)?value:'design';
  const badge=(label,state)=>`<span class="wu-badge wu-${tone(state)}">${esc(label)}</span>`;
  function validate(data){
    if(!data||typeof data.title!=='string'||!data.title.trim()||!data.summary||!data.status||!data.basis)throw Error('Workup needs a title, summary, status and evidence basis');
    if(!Array.isArray(data.workflows)||!data.workflows.length)throw Error('Workup needs an illustrated workflow');
    for(const flow of data.workflows){
      if(!flow.title||!flow.description||!flow.outcome||!Array.isArray(flow.steps)||flow.steps.length<2)throw Error('Workflow needs a description, ordered steps and an outcome');
      for(const step of [...flow.steps,...(flow.branches||[])])if(!step.title||!step.description||!step.label||!tones.has(step.tone))throw Error('Every workflow step needs a description and explicit evidence state');
    }
    for(const key of ['evidence','systems','acceptance'])if(!Array.isArray(data[key])||data[key].length<2)throw Error('Workup needs '+key);
    for(const item of data.evidence)if(!item.title||!item.description||!item.source||!item.label||!tones.has(item.tone))throw Error('Evidence needs a source and explicit state');
    for(const item of data.systems)if(!item.title||!item.description||!item.boundary)throw Error('System boundary is missing');
    for(const item of data.acceptance)if(!item.title||!item.description)throw Error('Acceptance gate is missing');
    return data;
  }
  function assertCoverage(entries,workups){
    const ids=entries.map(e=>typeof e==='string'?e:e.id);
    if(new Set(ids).size!==ids.length)throw Error('Duplicate example ID');
    for(const id of ids){if(!Object.prototype.hasOwnProperty.call(workups,id))throw Error('Missing workup: '+id);validate(workups[id]);}
    return ids.length;
  }
  function flowMarkup(flow,index,prefix){
    const cols=flow.steps.length===3?3:flow.steps.length<=4?flow.steps.length:4;
    return `<article class="wu-story" id="${prefix}-flow-${index+1}"><header class="wu-story-head"><div><span class="wu-kicker">WORKFLOW ${String(index+1).padStart(2,'0')}</span><h4>${esc(flow.title)}</h4><p>${esc(flow.description)}</p></div>${badge(flow.label,flow.tone)}</header><div class="wu-diagram"><ol class="wu-flow wu-cols-${cols}" aria-label="${esc(flow.title)}">${flow.steps.map((step,i)=>`<li class="wu-step wu-step-${tone(step.tone)}"><span class="wu-number">${String(i+1).padStart(2,'0')}</span>${badge(step.label,step.tone)}<h5>${esc(step.title)}</h5><p>${esc(step.description)}</p>${step.detail?`<details><summary>Inspect this step</summary><p>${esc(step.detail)}</p></details>`:''}</li>`).join('')}</ol>${flow.branches?.length?`<div class="wu-branch-label"><span aria-hidden="true">↳</span> Outcomes and decision branches</div><div class="wu-branches">${flow.branches.map(branch=>`<div class="wu-branch wu-step-${tone(branch.tone)}">${badge(branch.label,branch.tone)}<h5>${esc(branch.title)}</h5><p>${esc(branch.description)}</p></div>`).join('')}</div>`:''}<div class="wu-outcome"><span aria-hidden="true">↳</span><p>${esc(flow.outcome)}</p></div></div></article>`;
  }
  function render(data,options={}){
    validate(data);
    const id=options.id||'workup';
    if(!/^[a-z][a-z0-9-]*$/.test(id))throw Error('Invalid workup anchor');
    const diagrams=data.workflows.map((flow,index)=>flowMarkup(flow,index,id)).join('');
    if(options.workflowOnly)return `<section class="pug-workup wu-embedded" id="${id}" aria-labelledby="${id}-title"><div class="wu-heading"><span class="wu-kicker">WORKFLOW PROOF / THE FULL STORY</span><h3 id="${id}-title">${esc(data.title)}</h3><p>${esc(data.summary)}</p><div class="wu-basis">${badge(data.status,data.tone)}<span>${esc(data.basis)}</span></div></div>${diagrams}</section>`;
    return `<section class="pug-workup" id="${id}" aria-labelledby="${id}-title"><div class="wu-heading"><span class="wu-kicker">DESIGN WORKUP / PROCESS, PROOF AND DELIVERY</span><h2 id="${id}-title">${esc(data.title)}</h2><p>${esc(data.summary)}</p><div class="wu-basis">${badge(data.status,data.tone)}<span>${esc(data.basis)}</span></div></div><nav class="wu-jump" aria-label="Workup chapters"><a href="#${id}-workflow">Workflow illustrations</a><a href="#${id}-evidence">Evidence</a><a href="#${id}-systems">Implementation</a><a href="#${id}-acceptance">Acceptance gates</a></nav><div id="${id}-workflow" class="wu-chapter">${diagrams}</div><div id="${id}-evidence" class="wu-chapter"><span class="wu-kicker">THE EVIDENCE</span><h3>What exists. What it establishes.</h3><div class="wu-evidence">${data.evidence.map(e=>`<article>${badge(e.label,e.tone)}<h4>${esc(e.title)}</h4><p>${esc(e.description)}</p><small>Basis: ${esc(e.source)}</small></article>`).join('')}</div></div><div id="${id}-systems" class="wu-chapter"><span class="wu-kicker">THE IMPLEMENTATION</span><h3>Each system has a clear responsibility.</h3><div class="wu-systems">${data.systems.map((s,i)=>`<article><span class="wu-number">${String(i+1).padStart(2,'0')}</span><h4>${esc(s.title)}</h4><p>${esc(s.description)}</p><div class="wu-boundary">${esc(s.boundary)}</div></article>`).join('')}</div></div><div id="${id}-acceptance" class="wu-chapter"><span class="wu-kicker">THE NEXT ACCEPTANCE GATES</span><h3>What must be true before we go further.</h3><ol class="wu-gates">${data.acceptance.map(a=>`<li><h4>${esc(a.title)}</h4><p>${esc(a.description)}</p></li>`).join('')}</ol></div><p class="wu-footnote">Workflow illustrations explain this example's recorded or proposed behavior. Evidence labels identify the difference. Opening this workup performs no provider operation.</p></section>`;
  }
  const api={validate,assertCoverage,render};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.PUGWorkup=api;
})(typeof window==='object'?window:globalThis);
