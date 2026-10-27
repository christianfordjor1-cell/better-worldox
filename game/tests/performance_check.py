#!/usr/bin/env python3
"""Bounded full-game draw benchmark in an isolated Chromium world."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
import json,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def run():
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));Thread(target=server.serve_forever,daemon=True).start()
 started=time.time();errors=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage'])
   context=browser.new_context(viewport={'width':1280,'height':900});page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(f'http://127.0.0.1:{server.server_port}/dist/Tiny-World-v79-Modular.html',wait_until='domcontentloaded',timeout=120000)
   page.wait_for_function('typeof Session!=="undefined"&&Session.phase==="ready"',timeout=60000)
   setup=page.evaluate('''()=>{tw52Speed(0);G.opts.w=96;G.opts.h=64;G.opts.seed='tiny-world-performance-v79';G.opts.pop=Object.fromEntries(Object.keys(G.creatures).map(k=>[k,0]));G.newWorld();tw52Speed(0);G.uiHide=true;const sites=[];for(let y=2;y<Math.min(G.H-2,40);y++)for(let x=2;x<Math.min(G.W-2,90);x++)if(G.walk(x,y)&&!G.bld.has(y*G.W+x))sites.push([x,y]);if(!sites.length)throw Error('No walkable benchmark sites');window.perfHumans=[];for(let i=0;i<100;i++){const [x,y]=sites[(i*13)%sites.length],c=G.spawn('human',x,y,true);c.age=adultAge(c)+100;const p=G.person(c);TW79.identity(p);perfHumans.push(c)}window.perfBeasts=[];const kinds=Object.keys(KINGDOM_MANIFEST.beasts).filter(t=>G.creatures[t]);for(let i=0;i<30;i++){const [x,y]=sites[(i*23+8)%sites.length],c=G.spawn(kinds[i%kinds.length],x,y,true);if(SPECIES[c.type])c.age=SPECIES[c.type].mature+100;perfBeasts.push(c)}cam.z=12;cam.x=0;cam.y=0;G.state.sel=0;CIV.follow=0;CIV.labels=false;G._ix=null;return {world:[G.W,G.H],seed:G.opts.seed,addedHumans:perfHumans.length,addedBeasts:perfBeasts.length,totalActors:G.cre.filter(c=>c.hp>0).length,camera:{...cam},logicalViewport:[VW,VH],actualCanvas:[cv.width,cv.height],pixelScale:G.px,visibleHumans:perfHumans.filter(c=>c.x<cam.x+VW/cam.z&&c.y<cam.y+VH/cam.z).length}}''')
   warm=page.evaluate('''async()=>{const start=performance.now();let ready=0;for(const c of perfHumans.slice(0,20)){const p=G.person(c),plan=TinyWorldVisuals.citizenPlan(p,c,TinyWorldVisuals.frame(c,G),'#729aab');const result=await KingdomSprites.preload(plan);if(result.ready)ready++;if(performance.now()-start>10000)break}return {ready,elapsedMs:performance.now()-start,stats:KingdomSprites.stats()}}''')
   def sample(enabled):
    return page.evaluate('''async enabled=>{TinyWorldVisuals.setEnabled(enabled);const times=[];const before=TinyWorldVisuals.diagnostics();for(let i=0;i<60;i++){const start=performance.now();draw(start);times.push(performance.now()-start);await new Promise(resolve=>setTimeout(resolve,0))}times.sort((a,b)=>a-b);const mean=times.reduce((a,b)=>a+b,0)/times.length;return {mode:enabled?'provisional PNG':'original v79',samples:times.length,meanDrawMs:mean,medianDrawMs:times[Math.floor(times.length*.5)],p95DrawMs:times[Math.floor(times.length*.95)],maxDrawMs:times.at(-1),drawOnlyFpsEquivalent:1000/mean,beforeCounters:before.counters,afterCounters:TinyWorldVisuals.diagnostics().counters,compositor:KingdomSprites.stats()}}''',enabled)
   original=sample(False);provisional=sample(True)
   simulation=page.evaluate('''()=>{TinyWorldVisuals.setEnabled(true);const before=G.time,start=performance.now();tw52Speed(1);let calls=0;while(G.time-before<100&&calls<120&&performance.now()-start<1000){advanceSimulation(60,14);calls++}tw52Speed(0);return {ticks:G.time-before,elapsedMs:performance.now()-start,calls,actors:G.cre.filter(c=>c.hp>0).length,targetTicks:100,budgetMs:1000}}''')
   # One additional draw catches delayed image failures and post-simulation renderer errors.
   page.evaluate('draw(performance.now())');page.wait_for_timeout(100)
   diagnostics=page.evaluate('TinyWorldVisuals.diagnostics()');stats=diagnostics['compositor']['stats']
   bounded=stats['cacheBytes']<=stats['maxCacheBytes'] and stats['rawRows']<=48 and stats['cells']<=384 and stats['composites']<=256
   result={'suite':'full-game-performance-smoke','build':'dist/Tiny-World-v79-Modular.html','browser':browser.version,'environment':'Headless system Chromium in the managed cloud CPU environment; no hardware-independent frame-rate guarantee.','setup':setup,'warmup':warm,'original':original,'provisional':provisional,'simulation':simulation,'retainedCanvasCachesBounded':bounded,'finalDiagnostics':diagnostics,'pageErrors':errors,'elapsedSeconds':round(time.time()-started,2),'passed':not errors and bounded and setup['addedHumans']==100 and setup['addedBeasts']==30 and simulation['ticks']>0,'limitations':['Draw timings measure synchronous draw() CPU time, not end-to-end display FPS.','Paused atlas actors use their actual idle poses; all walking frames and large-population animation are outside this benchmark.','The canvas cache estimate excludes embedded HTML/data strings, image decode buffers, browser overhead and last-complete actor snapshots.','A large cold population may use preserved original sprites while PNG rows load; counters disclose these fallbacks.','One native simulation batch is a smoke check, not long-run balance or speed-accuracy proof.']}
   (ROOT/'reports/performance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['passed','elapsedSeconds','retainedCanvasCachesBounded','pageErrors']}));print(json.dumps({'original':{k:original[k] for k in ['meanDrawMs','medianDrawMs','p95DrawMs']},'provisional':{k:provisional[k] for k in ['meanDrawMs','medianDrawMs','p95DrawMs']},'simulation':simulation}))
   browser.close()
   if not result['passed']:raise AssertionError('Performance functional smoke failed; see report')
 finally:server.shutdown()
if __name__=='__main__':run()
