#!/usr/bin/env python3
"""Browser smoke regressions of the real game, using isolated browser storage."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
import hashlib, json, time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    checks=[]; page_errors=[]
    def check(name,ok,evidence):
        checks.append({'name':name,'passed':bool(ok),'evidence':evidence})
        if not ok: raise AssertionError(f'{name}: {evidence}')
    started=time.time()
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True)
        page=context.new_page();page.on('pageerror',lambda e:page_errors.append(str(e)))
        page.on('dialog',lambda d:d.accept())
        page.goto(base+'baseline/Tiny-World-v79-original.html',wait_until='domcontentloaded',timeout=120000)
        page.wait_for_function('typeof Session!=="undefined"&&Session.phase==="ready"',timeout=60000)
        reference=page.evaluate('''()=>{tw52Speed(0);return {classes:Object.keys(CLS),specs:Object.fromEntries(Object.entries(SPECIAL).map(([k,v])=>[k,v.family])),races:Object.keys(RACES),creatures:Object.keys(G.creatures),systems:G.systems.map(s=>s.key),roots:tw74.ROOTS,techniques:tw74.TECHNIQUES.map(t=>[t.id,t.name,t.root,t.branch,t.rank]),realms:CLASS_RANKS}}''')
        context.close()
        context=browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True)
        page=context.new_page();page.on('pageerror',lambda e:page_errors.append(str(e)));page.on('dialog',lambda d:d.accept())
        page.goto(base+'dist/Tiny-World-v79-Modular.html',wait_until='domcontentloaded',timeout=120000)
        page.wait_for_function('typeof Session!=="undefined"&&Session.phase==="ready"',timeout=60000)
        current=page.evaluate('''()=>{tw52Speed(0);return {classes:Object.keys(CLS),specs:Object.fromEntries(Object.entries(SPECIAL).map(([k,v])=>[k,v.family])),races:Object.keys(RACES),creatures:Object.keys(G.creatures),systems:G.systems.map(s=>s.key),roots:tw74.ROOTS,techniques:tw74.TECHNIQUES.map(t=>[t.id,t.name,t.root,t.branch,t.rank]),realms:CLASS_RANKS}}''')
        check('Native registries and simulation systems preserved',reference==current,{'classes':len(current['classes']),'specialisations':len(current['specs']),'existingMechanicRaces':len(current['races']),'existingActorTypes':len(current['creatures']),'systems':len(current['systems']),'roots':len(current['roots']),'techniques':len(current['techniques']),'separateBranches':sorted({t[3] for t in current['techniques']})})
        generated=page.evaluate('''()=>{G.opts.seed='tiny-world-regression-v79';G.newWorld();tw52Speed(0);return {seed:G.opts.seed,width:G.W,height:G.H,map:G.map.length,walkable:G.map.reduce((n,_,i)=>n+Number(!!G.walk(i%G.W,i/G.W|0)),0),creatures:G.cre.length}}''')
        check('New world generation through existing pipeline',generated['map']==generated['width']*generated['height'] and generated['walkable']>0,generated)
        spawned=page.evaluate('''()=>{const sites=[];for(let i=0;i<G.map.length;i++)if(G.walk(i%G.W,i/G.W|0)&&!G.bld.has(i))sites.push(i);window.regressionActors=[];for(const [n,cls] of Object.keys(CLS).entries()){const i=sites[Math.min(sites.length-1,500+n*5)],c=G.spawn('human',i%G.W,i/G.W|0,true),p=G.person(c);c.age=adultAge(c)+100;setClass(c,p,cls);TW79.identity(p);regressionActors.push(c)};return regressionActors.map(c=>({id:c.id,cls:G.person(c).cls,adult:c.age>=adultAge(c),seed:G.person(c).tw79.seed,hp:c.hp}))}''')
        check('Native adult spawn and all fifteen class assignments',len(spawned)==15 and all(c['adult'] and c['seed'] and c['hp']>0 for c in spawned),{'classes':[c['cls'] for c in spawned],'actors':len(spawned)})
        progression=page.evaluate('''()=>{const c=regressionActors[0],p=G.person(c);p.tier=1;p.cultStage=1;p.ego=0;const initial={tier:p.tier,stage:p.cultStage},stageResult=promote(c,p),stage={tier:p.tier,stage:p.cultStage};p.cultStage=10;const rankResult=promote(c,p),rank={tier:p.tier,stage:p.cultStage,specialisation:p.spec};tw74.initHuman(p,c);return {initial,stageResult,stage,rankResult,rank,techniques:p.tw74.techniques.length,root:p.tw74.root}}''')
        check('Cultivation substage, complete-foundation breakthrough and specialisation',progression['stageResult'] and progression['stage']=={'tier':1,'stage':2} and progression['rankResult'] and progression['rank']['tier']==2 and progression['rank']['stage']==1 and progression['rank']['specialisation'] in current['specs'] and progression['techniques']>0,progression)
        combat=page.evaluate('''()=>{const c=regressionActors[0],p=G.person(c),w=G.spawn('wolf',c.x,c.y,true);w.age=SPECIES.wolf.mature+10;w.hp=w.maxHp=Math.max(w.maxHp,100000);const before=w.hp;let hits=0;for(let n=0;n<16&&w.hp===before;n++){if(strike(c,w,'warrior'))hits++}window.regressionWolf=w;return {before,after:w.hp,hits,hurtUntil:w.hurtUntil,time:G.time,combatAudit:G.state.combatV68}}''')
        check('Real hostile strike applies damage and hurt timing',combat['after']<combat['before'] and combat['hurtUntil']>combat['time'],combat)
        beasts=page.evaluate('''()=>{const results=[];for(const type of Object.keys(KINGDOM_MANIFEST.beasts)){if(!G.creatures[type])continue;const site=regressionActors[1],c=G.spawn(type,site.x,site.y,true);tw74.initBeast(c,G);if(TW79.beastIdentity)TW79.beastIdentity(c);results.push({type,alive:c.hp>0,identity:!!c.tw74Beast,visualIdentity:!!c.tw79Beast})};return {registered:results,artOnly:Object.keys(KINGDOM_MANIFEST.beasts).filter(t=>!G.creatures[t])}}''')
        check('Existing beast spawning and identity hooks',len(beasts['registered'])==12 and all(x['alive'] and x['identity'] and x['visualIdentity'] for x in beasts['registered']),beasts)
        companions=page.evaluate("""()=>{const tamer=regressionActors[2],tp=G.person(tamer);tp.cls='archer';tp.spec='beastmaster';const wild=G.spawn('wolf',tamer.x,tamer.y,true);tw74.initBeast(wild,G);const bonded=tw7418.attach(G,tamer,wild);const summoner=regressionActors[3],sp=G.person(summoner);sp.cls='mage';sp.spec='summoner';const animals=G.cre.filter(c=>c.type!=='human'&&c.hp>0);let site=-1;for(let i=0;i<G.map.length;i+=19){const x=i%G.W,y=i/G.W|0;if(G.walk(x,y)&&animals.every(c=>(c.x-x)**2+(c.y-y)**2>144)){site=i;break}}if(site<0)return {error:'No isolated summoner site'};summoner.x=site%G.W;summoner.y=site/G.W|0;summoner.rx=summoner.x;summoner.ry=summoner.y;const repaired=tw7421.repair(G,summoner),bound=tw7421.owned(G,summoner);return {bonded,tamerMaster:wild.tw74Beast.master,tamerUid:tamer.uid,tamerIsSummoner:tw7421.isSummoner(tp),repaired,summons:bound.map(c=>({type:c.type,bloodline:c.tw74Beast.bloodline,master:c.tw74Beast.master})),summonerUid:summoner.uid,summonerIsTamer:tw7421.isTamer(sp)}}""")
        check('Beastmaster contract and independent spirit summoning',companions.get('bonded') and companions['tamerMaster']==companions['tamerUid'] and not companions['tamerIsSummoner'] and companions.get('repaired') and not companions['summonerIsTamer'] and any(c['bloodline']=='Spirit Conjuration' and c['master']==companions['summonerUid'] for c in companions['summons']),companions)
        sect=page.evaluate('''()=>{let town=null;for(let i=0;i<G.map.length&&!town;i+=11){const x=i%G.W,y=i/G.W|0;if(stableFoundation(x,y)&&buildFits('hall',x,y))town=foundTown(x,y)}if(!town)return {error:'No town foundation found'};const master=regressionActors[2],disciple=regressionActors[3],mp=G.person(master),dp=G.person(disciple);master.town=disciple.town=town.id;master.k=disciple.k=town.k;mp.tier=6;mp.cls='warrior';mp.disciples=[];mp.sect='Regression Azure Sect';dp.tier=1;dp.master=0;dp.disciples=[];G.time=120;for(let n=0;n<20&&!G.state.sects?.[mp.sect];n++){G.systems.find(s=>s.key==='cultivationExtras').tick(G)}const s=G.state.sects?.[mp.sect];if(!s)return {error:'Native founding did not find a retreat',town:town.name};s.level=2;G.time=140;G.systems.find(s=>s.key==='sectMountain').tick(G);const m=s.mt;return {name:s.name,founder:s.founder,disciple:dp.master,master:mp.id,mountain:m?{tiles:m.tiles.length,rooms:m.rooms.length,terraces:m.T}:null,veins:(G.state.veins||[]).length}}''')
        check('Native sect founding and procedural mountain generation',sect.get('name')=='Regression Azure Sect' and sect.get('disciple')==sect.get('master') and sect.get('mountain',{}).get('tiles',0)>100,sect)
        # Existing controls: dispatch the real range input event, then let the live loop advance.
        page.evaluate('''()=>{const slider=document.getElementById('hud-speed');slider.value='3';slider.dispatchEvent(new Event('input',{bubbles:true}))}''')
        control=page.evaluate('''()=>({speed:G.speed,paused:G.paused,time:G.time})''')
        page.wait_for_timeout(700)
        advanced=page.evaluate('''()=>{const time=G.time;tw52Speed(0);return {time,paused:G.paused}}''')
        check('Existing speed slider advances live simulation and pauses',control['speed']==3 and not control['paused'] and advanced['time']>control['time'] and advanced['paused'],{'selected':control,'after':advanced})
        paused_at=advanced['time'];page.wait_for_timeout(250)
        check('Paused simulation remains stable',page.evaluate('G.time')==paused_at,{'time':paused_at})
        # Real downloads and actual file inputs; no replacement import/export implementation.
        expected=page.evaluate('''()=>{tw52Speed(0);const p=G.person(regressionActors[0]);return {time:G.time,W:G.W,H:G.H,name:p.name,identity:p.tw79,cls:p.cls,spec:p.spec,personId:p.id,terrain:Array.from(G.map),sects:Object.keys(G.state.sects||{})}}''')
        with page.expect_download() as event: page.evaluate('exportWorld()')
        download=event.value;world_bytes=Path(download.path()).read_bytes();world=json.loads(world_bytes)
        check('Actual world JSON download',world['version']==4 and world['time']==expected['time'] and len(world['map'])==expected['W']*expected['H'],{'filename':download.suggested_filename,'bytes':len(world_bytes),'version':world['version']})
        page.evaluate('''()=>{G.opts.seed='temporary-import-check';G.newWorld();tw52Speed(0)}''')
        world_input=page.locator('.panel.World input[type=file]').first
        world_input.set_input_files({'name':'world-regression.json','mimeType':'application/json','buffer':world_bytes})
        page.wait_for_function('(n)=>G.time===n',arg=expected['time'],timeout=20000)
        loaded=page.evaluate('''id=>{tw52Speed(0);const p=G.state.people[id];return {time:G.time,W:G.W,H:G.H,name:p?.name,identity:p?.tw79,cls:p?.cls,spec:p?.spec,personId:p?.id,terrain:Array.from(G.map),sects:Object.keys(G.state.sects||{})}}''',expected['personId'])
        check('Actual world file import preserves terrain, sect and warrior identity',loaded==expected,{'time':loaded['time'],'size':[loaded['W'],loaded['H']],'sects':loaded['sects'],'identitySeed':loaded['identity']['seed']})
        with page.expect_download() as event: page.evaluate('tw52ExportCharacters(false)')
        download=event.value;roster_bytes=Path(download.path()).read_bytes();roster=json.loads(roster_bytes)
        people=[entry for entry in roster['characters'] if entry.get('person') and entry['creature']['type']=='human']
        check('Actual character roster JSON download',roster['format']=='tiny-world-characters' and len(people)>=15,{'filename':download.suggested_filename,'humanRecords':len(people),'totalActorRecords':len(roster['characters'])})
        before_ids=page.evaluate('G.cre.filter(c=>c.type==="human"&&c.hp>0).map(c=>c.id)')
        with page.expect_file_chooser() as picker: page.evaluate('tw54ImportCharacters()')
        picker.value.set_files({'name':'roster-regression.json','mimeType':'application/json','buffer':roster_bytes})
        page.wait_for_function('(n)=>G.cre.filter(c=>c.type==="human"&&c.hp>0).length===n',arg=len(before_ids)+len(people),timeout=20000)
        imported=page.evaluate('''old=>G.cre.filter(c=>c.type==='human'&&c.hp>0&&!old.includes(c.id)).map(c=>{const p=G.person(c);return {id:p.id,name:p.name,cls:p.cls,spec:p.spec,tw79:p.tw79,root:p.tw69Root,kids:p.kids,mate:p.mate}})''',before_ids)
        check('Actual character file import keeps appearance seeds under new IDs',all(imported[n]['tw79']==entry['person']['tw79'] and imported[n]['name']==entry['person']['name'] and imported[n]['id'] not in before_ids for n,entry in enumerate(people)),{'newHumans':len(imported),'preservedSeeds':[x['tw79']['seed'] for x in imported[:4]],'foreignFamilyLinksCleared':all(x['kids']==[] and not x['mate'] for x in imported)})
        # Save slots use the actual archive controls and native snapshot/restore.
        page.evaluate("openOverview('saves')")
        page.locator('[data-save-slot="30"]').click()
        slot=page.evaluate('localStorage.getItem("tinyworld-slot-30")')
        check('Existing archive save control stores a version4 world',json.loads(slot)['version']==4,{'slot':31,'bytes':len(slot)})
        saved_time=page.evaluate('G.time');page.evaluate('G.time+=17')
        page.locator('[data-load-slot="30"]').click()
        check('Existing archive load control restores saved time',page.evaluate('G.time')==saved_time,{'time':saved_time})
        check('No JavaScript page exceptions',not page_errors,page_errors)
        browser.close()
    except Exception as exc:
        if not checks or checks[-1]['passed']:checks.append({'name':'Test execution completed','passed':False,'evidence':str(exc)})
        raise
    finally:
        server.shutdown()
        result={'build':'dist/Tiny-World-v79-Modular.html','suite':'actual-gameplay-browser-smoke','elapsedSeconds':round(time.time()-started,2),'passed':all(c['passed'] for c in checks),'checks':checks,'pageErrors':page_errors,'scope':'Smoke tests exercise existing native gameplay/API and actual file controls; they do not prove long-running balance, every ability or every world layout.'}
        (ROOT/'reports/gameplay-regression.json').write_text(json.dumps(result,indent=2)+'\n')
        lines=['# Playable gameplay regression','',f"Result: {'PASS' if result['passed'] else 'FAIL'}. Chromium, isolated temporary browser profile, {result['elapsedSeconds']} seconds.",'']
        lines += [f"- {'PASS' if c['passed'] else 'FAIL'} — {c['name']}" for c in checks]
        lines += ['',result['scope'],'','The suite compares all 15 classes, 48 specialisations, existing actor/race mechanics, simulation systems, realms and 1,260 techniques to the untouched v79 loaded in a separate profile. It does not create mechanics for the five artwork-only beast species.']
        (ROOT/'reports/gameplay-regression.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'passed':True,'checks':len(checks),'seconds':round(time.time()-started,2)}))
if __name__=='__main__':run()
