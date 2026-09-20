const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() { this.children = []; this.textContent = ''; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes.flatMap(n => n.fragment ? n.children : [n]); }
  setAttribute() {}
}
const els = Object.fromEntries(['status','mode','src','list','sel','json','headers','raw','refresh','clear'].map(id => [id,new Element()]));
const calls = [], timers = new Map(); let serial = 0;
const context = {
  document: {hidden:false, getElementById:id=>els[id], createElement:()=>new Element(), createDocumentFragment:()=>Object.assign(new Element(),{fragment:true}), addEventListener(){}},
  window:{addEventListener(){}}, AbortController, Date,
  setTimeout:(fn,ms)=>{timers.set(++serial,{fn,ms});return serial;}, clearTimeout:id=>timers.delete(id),
  fetch:(url,options)=>new Promise(resolve=>calls.push({url,options,resolve}))
};
const finish = (call,data)=>call.resolve({ok:true,json:async()=>data});
const flush = ()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../gateway/static/monitor.js'),'utf8'),context);
  assert.equal(calls.length,1);
  assert.match(calls[0].url,/include_body=0&include_json_obj=0/);
  els.refresh.onclick(); assert.equal(calls.length,1,'no overlapping poll');
  finish(calls[0],{ready:true,events:Array.from({length:100},(_,i)=>({event_id:String(i),source:'docusign'}))}); await flush();
  assert.equal(els.list.children.length,80);
  assert.ok([...timers.values()].some(t=>t.ms===5000));
  const first = els.list.children[0].onclick();
  assert.match(calls[1].url,/body_max_chars=16000/);
  const second = els.list.children[1].onclick();
  assert.equal(calls[1].options.signal.aborted,true);
  finish(calls[2],{ready:true,event:{source:'docusign',headers_json:'{}',body_raw:'preview',body_truncated:true,json_omitted:true,json_bytes:2000000}}); await second;
  finish(calls[1],{ready:true,event:{body_raw:'stale',headers_json:'{}'}}); await first;
  assert.match(els.raw.textContent,/preview\n\[Preview truncated/);
  assert.match(els.json.textContent,/exceeds preview limit/);
  els.clear.onclick(); assert.equal(els.list.children.length,0); assert.equal(timers.size,0);
  console.log('PASS: summary polling, overlap prevention, row cap, bounded detail, stale selection, clear');
})().catch(error=>{console.error(error);process.exitCode=1;});
