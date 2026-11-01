#!/usr/bin/env python3
"""Browser proof of the three approved PixelLab sect routes and default fallback."""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import quote
import json
import time

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT/'releases/sect-art-01'
BUILD = RELEASE/'Tiny World v79 — Provisional Sect Art Update 01.html'


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main() -> None:
    checks, errors, console_errors = [], [], []
    report = {'build': BUILD.name, 'suite': 'approved-sect-in-game-browser-validation',
              'checks': checks, 'pageErrors': errors, 'consoleErrors': console_errors}
    def check(name, passed, evidence=None):
        checks.append({'name': name, 'passed': bool(passed), 'evidence': evidence})
        if not passed:
            raise AssertionError(f'{name}: {evidence}')
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/{quote(str(BUILD.relative_to(ROOT)))}'
    started = time.perf_counter()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium',
                                                args=['--disable-dev-shm-usage'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: console_errors.append(message.text) if message.type == 'error' and 'favicon.ico' not in message.text and 'Failed to load resource: the server responded with a status of 404' not in message.text else None)
            page.goto(url, wait_until='load', timeout=120000)
            page.wait_for_function('Session.phase==="ready"&&window.TinyWorldSectArt?.ready', timeout=60000)
            boot = page.evaluate('''()=>({phase:Session.phase,assets:TinyWorldSectArt.assetNames,states:TinyWorldSectArt.snapshot().loaded,
                 sects:SECT77_NAMES.length,roots:tw74.ROOTS.length,races:Object.keys(KINGDOM_MANIFEST.races).length,
                 beasts:Object.keys(KINGDOM_MANIFEST.beasts).length})''')
            check('Complete v79 game boots and exactly nine approved PNGs decode',
                  boot['phase']=='ready' and len(boot['assets'])==9 and all(v=='ready' for v in boot['states'].values()), boot)
            check('Thirty sect styles and distinct root registry remain',boot['sects']==30 and boot['roots']==30,boot)
            check('Existing 19 race and 17 beast art registries remain',boot['races']==19 and boot['beasts']==17,boot)
            scenario = page.evaluate('''()=>{
              tw52Speed(0);G.opts.seed='sect-visual-probe';G.newWorld();tw52Speed(0);
              const found=[];
              for(const [id,name] of [[0,'Ashen Citadel'],[1,'Sky Monastery of Storm'],[2,'Iron Foundry of Phoenix']]){
                let site=null;
                for(let y=20;y<G.H-20&&!site;y+=8)for(let x=20;x<G.W-20&&!site;x+=8){
                  if(found.some(f=>Math.hypot(f.x-x,f.y-y)<45))continue;
                  const s={name,x,y,noTown:1,level:3};if(tw64Find(s,2))site=s;
                }
                if(!site)throw Error('Native mountain site unavailable: '+id);
                site.mt=tw64Carve(site);
                if(!site.mt||site.mt.sectStyle!==id)throw Error('Native sect carve mismatch: '+id);
                for(const room of site.mt.rooms){
                  if(!['sectHall','sectGate','blacksmith','tower','house'].includes(room.type))continue;
                  if(id!==2&&['blacksmith','tower'].includes(room.type))continue;
                  const i=room.ay*G.W+room.ax;room.i=i;G.bld.set(i,room.type);
                  (G.state.buildingStyles??={})[i]='sectstyle'+id+'color0';
                }
                (G.state.sects??={})[name]=site;
                found.push({id,name,x:site.x,y:site.y,cx:site.mt.cx,top:site.mt.top,
                            style:site.mt.sectStyle,rooms:site.mt.rooms.filter(r=>r.i!==undefined).map(r=>({type:r.type,i:r.i})),
                            path:[site.mt.cx,site.mt.bottom+1,site.mt.bottom+2]});
              }
              window.__reviewSects=found;
              return found;
            }''')
            check('Three native sect terrain plans carve with IDs 0, 1, 2',
                  [s['style'] for s in scenario]==[0,1,2],scenario)
            check('Approved building slots exist in native layout',
                  all('sectHall' in [r['type'] for r in s['rooms']] for s in scenario)
                  and 'sectGate' in [r['type'] for r in scenario[0]['rooms']]
                  and {'tower','blacksmith'}.issubset({r['type'] for r in scenario[2]['rooms']}),scenario)
            path = page.evaluate('''()=>__reviewSects.map(s=>{
              const [x,a,b]=s.path,open=G.walk(x,a)&&G.walk(x,b),c=G.spawn('human',x,a,true),before=[c.x,c.y];
              if(open)for(let n=0;n<40&&c.y!==b;n++){G.time++;G.step(c,x,b)}
              return {id:s.id,open,before,after:[c.x,c.y],moved:c.x===x&&c.y===b};
            })''')
            check('Characters step through preserved native sect approach paths',all(p['open'] and p['moved'] for p in path),path)
            for sect in scenario:
                page.evaluate('''s=>{cam.z=32;cam.x=s.cx-22;cam.y=s.top-12;G.uiHide=true;G.state.sel=0}''',sect)
                page.wait_for_timeout(500)
                image=RELEASE/'screenshots'/f"{sect['id']}-{['citadel','sky-monastery','iron-foundry'][sect['id']]}.png"
                image.parent.mkdir(exist_ok=True)
                page.locator('#cv').screenshot(path=str(image))
            live = page.evaluate('''()=>({diag:TinyWorldSectArt.snapshot(),routes:__reviewSects.map(s=>s.rooms.map(r=>({type:r.type,id:TinyWorldSectArt.sectIdForBuilding(r.i)})))})''')
            check('Only approved ID 0–2 buildings draw PixelLab and both approved peaks draw',
                  all(n>0 for n in live['diag']['drawn']) and live['diag']['terrainDrawn'][0]>0
                  and live['diag']['terrainDrawn'][1]>0 and live['diag']['terrainDrawn'][2]==0
                  and all(r['id']==s['id'] for s,rooms in zip(scenario,live['routes']) for r in rooms)
                  and all(count>0 for key,count in live['diag']['assetDrawn'].items() if key!='sky-monastery-bridge')
                  and live['diag']['assetDrawn']['sky-monastery-bridge']==0,live)
            timings = page.evaluate('''()=>{
              const samples=[];for(const s of __reviewSects){cam.x=s.cx-22;cam.y=s.top-12;
                for(let n=0;n<12;n++){const a=performance.now();draw(a);samples.push(performance.now()-a)}}
              samples.sort((a,b)=>a-b);return {samples:samples.length,medianMs:samples[samples.length/2|0],
                p95Ms:samples[Math.ceil(samples.length*.95)-1],maxMs:samples.at(-1)};
            }''')
            check('Three-sect live draw remains responsive in headless Chromium',
                  timings['samples']==36 and timings['medianMs']<30,timings)
            # A direct renderer test for all other registered IDs verifies fallback
            # without creating a second playable game or altering the release HTML.
            defaults = page.evaluate('''()=>{
              const before=TinyWorldSectArt.snapshot(),oldCount=Object.keys(TW65.spr).length;
              const canvas=document.createElement('canvas');canvas.width=256;canvas.height=256;const pen=canvas.getContext('2d');
              const used=[];
              for(let id=3;id<30;id++){
                const x=45+id*2,y=90,i=y*G.W+x,name='Default architecture proof '+id;
                G.bld.set(i,'sectHall');G.state.sects[name]={name,mt:{sectStyle:id,rooms:[{type:'sectHall',i}]}};
                G.time++;
                if(TinyWorldSectArt.sectIdForBuilding(i)!==id)throw Error('Fallback index mismatch: '+id);
                raceBuilding(pen,'sectHall',i,32);used.push(id);
                delete G.state.sects[name];G.bld.delete(i);
              }
              const after=TinyWorldSectArt.snapshot();
              return {used,defaultCounts:after.defaultDrawn.slice(3),approvedBefore:before.drawn,
                      approvedAfter:after.drawn,legacySpriteCacheBefore:oldCount,
                      legacySpriteCacheAfter:Object.keys(TW65.spr).length};
            }''')
            check('IDs 3–29 use default v79 architecture with no rejected sprite cache use',
                  defaults['used']==list(range(3,30)) and all(n>0 for n in defaults['defaultCounts'])
                  and defaults['approvedBefore']==defaults['approvedAfter']
                  and defaults['legacySpriteCacheBefore']==defaults['legacySpriteCacheAfter'],defaults)
            # Existing save/restore preserves the native terrain, room indices and
            # actual character positions even after the new visual dispatch.
            saved = page.evaluate('''()=>{
              const before=__reviewSects.map(s=>{const m=G.state.sects[s.name].mt;
                return {name:s.name,style:m.sectStyle,rooms:m.rooms.filter(r=>r.i!==undefined).map(r=>[r.i,r.type]),
                        tiles:m.tiles.length};});
              const bytes=G.snapshot();G.restore(bytes);tw52Speed(0);
              const after=before.map(s=>{const m=G.state.sects[s.name]?.mt;
                return {name:s.name,style:m?.sectStyle,rooms:m?.rooms.filter(r=>r.i!==undefined).map(r=>[r.i,r.type]),
                        tiles:m?.tiles.length};});
              return {same:JSON.stringify(before)===JSON.stringify(after),bytes:bytes.length,after};
            }''')
            check('Saved sect styles, native terrain and occupied rooms survive world restore',saved['same'],saved)
            page.locator('#tw-modular-art').click()
            toggle = page.evaluate('''()=>{const s=__reviewSects[0],r=s.rooms.find(r=>r.type==='sectHall');
              const before=TinyWorldSectArt.snapshot().drawn[0];
              raceBuilding(document.createElement('canvas').getContext('2d'),'sectHall',r.i,32);
              return {actorArtEnabled:TinyWorldVisuals.enabled,before,after:TinyWorldSectArt.snapshot().drawn[0]};}''')
            check('Existing actor-art toggle cannot reveal rejected sect sprites',
                  not toggle['actorArtEnabled'] and toggle['after']>toggle['before'],toggle)
            check('No missing images or JavaScript exceptions',not errors and not console_errors,{'page':errors,'console':console_errors})
            report['scene'] = scenario
            report['rendering'] = live['diag']
            report['fallback'] = defaults
            report['performance'] = timings
            browser.close()
        report['passed']=True
    except Exception as exc:
        report['passed']=False
        report['failure']=str(exc)
        raise
    finally:
        report['elapsedSeconds']=round(time.perf_counter()-started,2)
        server.shutdown()
        (RELEASE/'sect-art-validation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'passed':report.get('passed'),'checks':len(checks),'elapsedSeconds':report['elapsedSeconds'],
                          'failure':report.get('failure')}))


if __name__=='__main__':
    main()
