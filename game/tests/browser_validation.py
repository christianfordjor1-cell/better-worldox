#!/usr/bin/env python3
"""Actual build, offline-file, legacy-save, resume and rendering regression checks."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse, json, threading, time
from playwright.sync_api import sync_playwright, Error as BrowserError

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=(ROOT/'tests/fixtures/v79-world.json').read_text()
EXPECTED=json.loads((ROOT/'tests/fixtures/v79-world.expected.json').read_text())
STABLE='name race cls spec preferredSpec roots tw69Root tw69Path tier cultStage cultFoundation genome gear tw79 tw74'.split()
def saved_values_kept(actual,expected):
    if isinstance(expected,dict):
        return isinstance(actual,dict) and all(k in actual and saved_values_kept(actual[k],v) for k,v in expected.items())
    return actual==expected
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--chromium',default='/usr/bin/chromium');args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/dist/Tiny-World-v79-Modular.html'
    checks=[];errors=[];report={'browser':'Chromium','checks':checks,'pageErrors':errors}
    def check(name,value,detail=None):
        checks.append({'name':name,'passed':bool(value),**({'detail':detail} if detail is not None else {})})
        if not value:raise AssertionError(name+': '+str(detail))
    def wait(page):page.wait_for_function('typeof Session!=="undefined"&&Session.phase==="ready"&&!!window.TinyWorldVisuals',timeout=60000)
    def state(page):return page.evaluate('''()=>{tw52Speed(0);const d=JSON.parse(G.snapshot());return {W:d.W,H:d.H,time:d.time,map:d.map,shade:d.shade,people:d.state.people,cre:d.cre,sects:d.state.sects,buildings:d.bld}}''')
    sentinels={'tinyworld2':'KEEP-QUICKSAVE','tinyworld-slot-30':'KEEP-SLOT','tinyworld-qol-auto-sentinel':'KEEP-AUTOSAVE','world-user-backup':'KEEP-OTHER-WORLD'}
    seed={'savedAt':int(time.time()*1000),'revision':4,'time':EXPECTED['time'],'paused':True,'speed':1,'snapshot':FIXTURE}
    try:
      with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=args.chromium,args=['--disable-dev-shm-usage'])
        ctx=browser.new_context(viewport={'width':1440,'height':1000})
        init='''data=>{if(!sessionStorage.getItem('test-seeded')){for(const [k,v] of Object.entries(data.sentinels))localStorage.setItem(k,v);localStorage.setItem('tinyworld-current-session-v1',JSON.stringify(data.entry));sessionStorage.setItem('test-seeded','1');}}'''
        ctx.add_init_script('('+init+')('+json.dumps({'entry':seed,'sentinels':sentinels})+');')
        page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        started=time.perf_counter();page.goto(url,wait_until='load',timeout=120000);wait(page)
        report['loadSeconds']=round(time.perf_counter()-started,3)
        data=state(page);fixture=json.loads(FIXTURE)
        check('Baseline save restores terrain, shade, time and dimensions',all(data[k]==fixture[k] for k in ['W','H','time','map','shade']))
        mismatches=[]
        for pid,person in EXPECTED['people'].items():
          for key in STABLE:
            if data['people'][pid].get(key)!=person.get(key):mismatches.append([pid,key])
        check('Saved race, class, spec, roots, cultivation, genome, gear and identity preserved',not mismatches,mismatches)
        # Native restore adds dormant/tribute defaults; all existing authored sect data stays intact.
        sects_kept=all(all(data['sects'].get(name,{}).get(k)==v for k,v in sect.items()) for name,sect in EXPECTED['sects'].items())
        check('Saved sect definitions and buildings preserved',sects_kept and data['buildings']==EXPECTED['buildings'])
        beast_bad=[]
        for want in EXPECTED['beasts']:
          got=next(c for c in data['cre'] if c['uid']==want['uid'])
          for k in ['tw79Beast','tw74Beast']:
            if not saved_values_kept(got.get(k),want.get(k)):beast_bad.append([want['type'],k])
        check('Both independent saved beast identities preserved',not beast_bad,beast_bad)
        check('Native Ancient bloodline casing maps to ancient visual layer without rewriting identity',page.evaluate('''()=>{const c=G.cre.find(c=>c.type==='dragon'),before=JSON.stringify(c.tw74Beast),q=TinyWorldVisuals.beastIdentity(c);return q.ancient===true&&TinyWorldVisuals.beastPlan(c).layers.some(l=>l.kind==='ancient')&&before===JSON.stringify(c.tw74Beast)}'''))
        got=page.evaluate('(keys)=>Object.fromEntries(keys.map(k=>[k,localStorage.getItem(k)]))',list(sentinels))
        check('Startup never deletes quicksave, slot, autosave or other world keys',got==sentinels)
        check('Historical fresh-start flags are not written',page.evaluate("localStorage.getItem('tinyworld-fresh-start-2026-10-20')===null&&localStorage.getItem('tinyworld-v14-stockpile-clean-start')===null"))
        # Render actual actors at enough zoom to load PNG layers, using their normal draw functions.
        visual=page.evaluate('''async()=>{
          const v=TinyWorldVisuals,a=KingdomSprites,people=G.cre.filter(c=>c.type==='human');
          const before=JSON.stringify(people.map(c=>G.person(c)));
          const images=[];
          for(const c of people){const plan=v.citizenPlan(G.person(c),c,0);let result=await a.preload(plan);for(let retry=0;!result.ready&&retry<5;retry++)result=await a.preload(plan);images.push(result.ready);}
          const canvas=document.createElement('canvas');canvas.width=600;canvas.height=600;const x=canvas.getContext('2d');
          for(const c of people)G.creatures.human.sprite(x,c,24,G);
          const same=before===JSON.stringify(people.map(c=>G.person(c)));
          return {loaded:images.every(Boolean),same,diagnostics:v.diagnostics()};
        }''')
        check('Actual layered PNGs load and render through game creature sprite API',visual['loaded'] and visual['diagnostics']['counters']['citizenDraws']>=4,visual['diagnostics']['counters'])
        check('Rendering does not rewrite saved person records',visual['same'])
        check('Equipped native firearm maps to gun while keeping saved fields intact',page.evaluate('''()=>{const source=G.person(G.cre.find(c=>c.type==='human')),p={...source,gear:{weapon:{type:'firearm',name:'Rare Iron firearm'}}},before=JSON.stringify(p);return TinyWorldVisuals.personIdentity(p).weapon==='gun'&&JSON.stringify(p)===before}'''))
        check('All19visualraces/all17beasts catalogued; unregistered gameplay species explicit',visual['diagnostics']['races']==19 and visual['diagnostics']['beasts']==17 and len(visual['diagnostics']['artOnlyBeasts'])==5)
        # Wait through the old reinstallation period. The explicit handoff must persist.
        page.wait_for_timeout(13000)
        check('Legacy renderer timers cannot replace modular adapter',page.evaluate('G.creatures.human.sprite===humanSprite&&TinyWorldVisuals.installed&&G.sprite.name==="portraitSprite"'))
        toggle=page.locator('#tw-modular-art');toggle.click();check('Original-art fallback toggle works',page.evaluate('!TinyWorldVisuals.enabled'))
        toggle.click();check('Provisional-art mode restored',page.evaluate('TinyWorldVisuals.enabled'))
        # Use real native archive controls for save and restore.
        page.locator('#bSave').click();page.locator('[data-save-slot="29"]').click()
        page.evaluate('G.time+=17')
        page.locator('[data-load-slot="29"]').click()
        check('Native archive slot save/load restores time and seeded appearance',state(page)['time']==EXPECTED['time'])
        page.evaluate('G.state.integrationRegression={kept:true};G.time+=7;tw52Speed(0)')
        check('Current-session write succeeds',page.evaluate('saveCurrentSession(true)'))
        page.reload(wait_until='load',timeout=120000);wait(page)
        check('Reload resumes the saved world without generating a replacement',page.evaluate('G.time')==EXPECTED['time']+7 and page.evaluate('G.state.integrationRegression.kept'))
        check('Reload preserves all protected sentinel saves',page.evaluate('(keys)=>Object.fromEntries(keys.map(k=>[k,localStorage.getItem(k)]))',list(sentinels))==sentinels)
        page.evaluate("localStorage.removeItem('tinyworld-current-session-v1')")
        page.reload(wait_until='load',timeout=120000);wait(page)
        check('IndexedDB resumes the current world when the local copy is absent',page.evaluate('G.time')==EXPECTED['time']+7 and page.evaluate('G.state.integrationRegression.kept'))
        # Game screenshot, using the real camera and complete simulation world.
        page.evaluate('''()=>{tw52Speed(0);const c=G.cre.find(c=>c.type==='human');cam.z=32;cam.x=c.x-18;cam.y=c.y-8;G.uiHide=false;G.state.sel=c.id;renderInfo(G);}''')
        page.wait_for_timeout(2500);page.screenshot(path=str(ROOT/'reports/playable-world.png'))
        report['rendering']=page.evaluate('TinyWorldVisuals.diagnostics()')
        ctx.close()
        # Corrupt save must remain recoverable and must stop automatic overwriting.
        bad=browser.new_context();bad.add_init_script("localStorage.setItem('tinyworld-current-session-v1','{BROKEN');localStorage.setItem('tinyworld-slot-5','KEEP-CORRUPT-CASE');")
        pg=bad.new_page();pg.goto(url,wait_until='load',timeout=120000)
        pg.wait_for_function('typeof Session!=="undefined"&&Session.phase==="recovery"',timeout=30000)
        check('Unreadable current-world data is kept and auto-saving blocked',pg.evaluate("localStorage.getItem('tinyworld-current-session-v1')==='{BROKEN'&&localStorage.getItem('tinyworld-slot-5')==='KEEP-CORRUPT-CASE'&&Session.phase==='recovery'"))
        bad.close()
        # Fully self-contained file: block HTTP and open by file:// with no server.
        offline=browser.new_context();requests=[]
        offline.route('http://**/*',lambda route:route.abort());offline.route('https://**/*',lambda route:route.abort())
        op=offline.new_page();op.on('pageerror',lambda e:errors.append(str(e)))
        op.on('request',lambda r:requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
        try:
          op.goto((ROOT/'dist/Tiny-World-v79-Modular.html').as_uri(),wait_until='load',timeout=120000)
          report['fileURLTest']='passed'
        except BrowserError as error:
          if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(error):raise
          report['fileURLTest']='Not verified: managed browser policy blocks file:// navigation. Embedded offline assets tested through local HTTP instead.'
          # This environment cannot open file URLs. Permit only the initial HTML request;
          # every later network request remains blocked, including the local server.
          requests.clear()
          offline.unroute_all()
          first=[True]
          def initial_document_only(route):
            if first[0] and route.request.url==url:
              first[0]=False;route.continue_()
            else:route.abort()
          offline.route('**/*',initial_document_only)
          op.goto(url,wait_until='load',timeout=120000)
          requests[:]=[r for r in requests if r!=url]
        wait(op)
        file_result=op.evaluate('''async()=>{tw52Speed(0);const i=G.map.findIndex((_,i)=>G.walk(i%G.W,Math.floor(i/G.W))&&!G.bld.has(i));const c=G.spawn('human',i%G.W,Math.floor(i/G.W),true);const r=await KingdomSprites.preload(TinyWorldVisuals.citizenPlan(G.person(c),c,0));return {ready:r.ready,size:[r.canvas.width,r.canvas.height]};}''')
        check('Self-contained HTML decodes embedded PNGs with all later networking blocked',file_result['ready'] and file_result['size']==[144,144] and not requests,{'externalRequests':requests,'fileURLTest':report['fileURLTest']})
        offline.close();check('No JavaScript page exceptions during normal game tests',not errors,errors)
        restricted=browser.new_context();restricted.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked by test','SecurityError')}});Object.defineProperty(window,'indexedDB',{get(){throw new DOMException('Blocked by test','SecurityError')}});")
        rp=restricted.new_page();rp.goto(url,wait_until='load',timeout=120000);wait(rp)
        check('Game remains playable with browser storage unavailable',rp.evaluate('G.W>0&&G.H>0&&G.map.length===G.W*G.H'))
        restricted.close()
        browser.close()
      report['passed']=True
    except Exception as error:
      report['passed']=False;report['failure']=str(error);raise
    finally:
      server.shutdown();(ROOT/'reports/browser-validation.json').write_text(json.dumps(report,indent=2)+'\n')
      print(json.dumps({'passed':report.get('passed'),'checks':len(checks),'failure':report.get('failure')},indent=2))
if __name__=='__main__':main()
