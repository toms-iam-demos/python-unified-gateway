const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { createHmac } = require('node:crypto');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const container = process.argv[2];
const throughTraefik = process.argv[3] === '--traefik';
const gatewayUrl = throughTraefik ? 'http://edge:8080' : 'http://127.0.0.1:8001';
function inside(code, ...args) {
  return execFileSync('docker', ['--context',process.env.PUG_REHEARSAL_CONTEXT || 'colima-pug-rehearsal','exec',container,'python','-c',code,...args], {encoding:'utf8'});
}
function request(path, headers={}, body=null) {
  return JSON.parse(inside(`
import base64,json,sys,urllib.request,urllib.error
path,headers,body=sys.argv[1:]
req=urllib.request.Request('${gatewayUrl}'+path, data=body.encode() if body else None, headers=json.loads(headers))
try: r=urllib.request.urlopen(req,timeout=4)
except urllib.error.HTTPError as e: r=e
with r: print(json.dumps([r.status,dict(r.headers),base64.b64encode(r.read()).decode()]))
`, path, JSON.stringify(headers), body || ''));
}
const origin = 'http://acceptance.invalid';
const credentials = 'Basic ' + Buffer.from('operator:synthetic-password').toString('base64');
const decode = ([status, , data]) => { assert.equal(status,200); return JSON.parse(Buffer.from(data,'base64')); };
(async () => {
  const body = JSON.stringify({event:'synthetic-acceptance',token:'SYNTHETIC_TOKEN_ONLY',padding:'x'.repeat(8000)});
  assert.equal(request('/webhooks/docusign', {'X-DocuSign-Signature-1':'invalid'},body)[0],401);
  const signature = createHmac('sha256','synthetic-only').update(body).digest('base64');
  for (const correlation of ['synthetic-original','synthetic-duplicate']) {
    assert.equal(decode(request('/webhooks/docusign', {'X-DocuSign-Signature-1':signature,'X-Correlation-Id':correlation,'Content-Type':'application/json'},body)).persisted,true);
  }
  const rows=JSON.parse(inside(`
import json,sqlite3
db=sqlite3.connect('file:/tmp/events.db?mode=ro',uri=True)
print(json.dumps(db.execute('SELECT event_id,correlation_id,verify_status,cast(body_raw as text) FROM events').fetchall()))
`));
  assert.equal(rows.length,1);
  const [[id, correlation, verified, storedBody]]=rows;
  assert.equal(storedBody,body);
  assert.equal(correlation,'synthetic-original');
  assert.equal(verified,'verified');
  const {events}=decode(request('/webhooks/monitor',{Authorization:credentials}));
  assert.equal(events.length,2);
  for(const event of events) {
    assert.equal(event.persistence.event_id,id);
    assert.equal(event.persistence.correlation_id,correlation);
  }
  console.log('PASS signed delivery and duplicate: HTTP 200, persisted, one verified row, stable IDs');
  const browser=await chromium.launch({executablePath:process.env.PUG_CHROME_PATH,args:['--disable-background-networking']});
  try {
    const context=await browser.newContext();
    await context.route('**/*',async route=>{
      const url=new URL(route.request().url());
      if(url.origin!==origin) return route.abort();
      if(!throughTraefik && route.request().headers().authorization!==credentials) {
        return route.fulfill({status:401,body:'Synthetic ingress denied'});
      }
      if(url.pathname.endsWith('/stream')) return route.abort();
      const [status,headers,data]=request(url.pathname+url.search, route.request().headers().authorization ? {Authorization:route.request().headers().authorization} : {});
      await route.fulfill({status,headers,body:Buffer.from(data,'base64')});
    });
    const page=await context.newPage();
    for(const path of ['/webhooks/monitor/ui','/events/ui']) {
      const denied = await page.goto(origin+path);
      assert.equal(denied.status(),401);
      if(throughTraefik) assert.match(denied.headers()['www-authenticate'], /^Basic /);
    }
    await context.setExtraHTTPHeaders({authorization:credentials});
    assert.equal((await page.goto(origin+'/webhooks/monitor/ui')).status(),200);
    await page.locator('#refresh').click();
    await page.waitForFunction(()=>document.querySelectorAll('#list li').length===1);
    assert.match(await page.locator('#list li').textContent(),new RegExp(id));
    assert.equal((await page.goto(origin+'/events/ui')).status(),200);
    await page.locator('.event-row').first().click();
    await page.waitForFunction(id=>document.querySelector('#detail-id').textContent===id,id);
    await page.locator('[data-view=raw]').click();
    const payload=await page.locator('#payload').textContent();
    assert.match(payload,/Incomplete JSON preview contains credential fields/);
    assert(!payload.includes('SYNTHETIC_TOKEN_ONLY'));
    console.log(`PASS browser: ${throughTraefik ? 'Traefik Basic Auth' : 'simulated ingress'} denial and operator access, monitor polling, matching event detail, truncated raw preview masked`);
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
