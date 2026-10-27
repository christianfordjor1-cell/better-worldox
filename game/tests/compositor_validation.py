#!/usr/bin/env python3
"""Validate real Cursor PNGs and the built v79 compositor in isolated Chromium.

Free dependencies: Python 3, Pillow, Playwright and Chromium. Run from any cwd:
python game/tests/compositor_validation.py
No normal browser profile, user save or game source is changed.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import shutil
import threading
import time
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

GAME = Path(__file__).resolve().parents[1]
PACK = GAME / 'vendor' / 'kingdom-sprites'
REPORT = GAME / 'reports' / 'compositor-validation.json'
CATALOG = GAME / 'reports' / 'provisional-sprite-catalog.png'


def validate_assets():
    manifest = json.loads((PACK / 'manifest.json').read_text())
    errors, ground_exceptions, edge_touching = [], [], []
    modes, alpha_values = Counter(), set()
    maximum_colours = neutral_sheets = body_rows = anchored = 0
    for path, sheet in manifest['sheets'].items():
        file = PACK / path
        if hashlib.sha256(file.read_bytes()).hexdigest() != sheet['sha256']:
            errors.append({'path':path,'check':'sha256'})
        with Image.open(file) as image:
            modes[image.mode] += 1
            if list(image.size) != sheet['size'] or image.width != 2016 or image.height != sheet['rows'] * 144:
                errors.append({'path':path,'check':'grid'})
            colours = image.getcolors(maxcolors=256)
            if colours is None:
                errors.append({'path':path,'check':'palette'}); continue
            palette, transparent = image.getpalette(), image.info.get('transparency')
            used = []
            for _, index in colours:
                if image.mode == 'P':
                    rgb = tuple(palette[index*3:index*3+3])
                    alpha = (0 if transparent == index else 255) if isinstance(transparent,int) else transparent[index] if isinstance(transparent,bytes) and index < len(transparent) else 255
                else:
                    rgb, alpha = index[:3], index[3] if len(index)>3 else 255
                used.append((rgb,alpha)); alpha_values.add(alpha)
            count = len(set(used)); maximum_colours = max(maximum_colours,count)
            if count != sheet['colors']: errors.append({'path':path,'check':'colour count'})
            if sheet['tintable']:
                if any(alpha and (rgb[0] != rgb[1] or rgb[1] != rgb[2]) for rgb,alpha in used):
                    errors.append({'path':path,'check':'neutral mask'})
                else: neutral_sheets += 1
            if any(alpha == 0 and rgb != (0,0,0) for rgb,alpha in used):
                errors.append({'path':path,'check':'transparent RGB'})
            # Indexed zero is transparent throughout this uploaded pack.
            if image.mode == 'P' and transparent == 0:
                for x in [0,image.width-1]+[v for n in range(1,14) for v in (n*144-1,n*144)]:
                    if image.crop((x,0,x+1,image.height)).getbbox():
                        edge_touching.append({'path':path,'axis':'x','coordinate':x}); break
                for y in [0,image.height-1]+[v for n in range(1,sheet['rows']) for v in (n*144-1,n*144)]:
                    if image.crop((0,y,image.width,y+1)).getbbox():
                        edge_touching.append({'path':path,'axis':'y','coordinate':y}); break
            if path.endswith('/body.png'):
                for row in range(sheet['rows']):
                    box = image.crop((0,row*144,144,(row+1)*144)).getbbox(); body_rows += 1
                    if box and box[3] == 131: anchored += 1
                    else: ground_exceptions.append({'path':path,'row':row,'bounds':box,'lowestVisibleY':box[3]-1 if box else None})
    return {'ok':not errors and alpha_values == {0,255} and not edge_touching,
        'sheets':len(manifest['sheets']),'logicalFrames':sum(x['rows']*14 for x in manifest['sheets'].values()),
        'modeCounts':dict(modes),'alphaValues':sorted(alpha_values),'maxColours':maximum_colours,
        'neutralTintSheets':neutral_sheets,'cellEdgeViolations':edge_touching,
        'idleBodyRowsChecked':body_rows,'idleRowsAtY130':anchored,'groundExceptions':ground_exceptions,
        'errors':errors}


BROWSER_CHECKS = r'''async ({stressSeconds}) => {
 const K=KingdomSprites,V=TinyWorldVisuals,M=K.manifest,g=TW79_GAME;
 if(typeof tw52Speed==='function')tw52Speed(0);g.paused=true;
 const hash=canvas=>{let h=2166136261;for(const value of canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data)h=Math.imul(h^value,16777619);return (h>>>0).toString(16).padStart(8,'0')};
 const pixels=canvas=>{const d=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n};
 const person={id:'compositor-warrior',name:'Compositor Warrior',race:'human',sex:'male',cls:'warrior',spec:'',tw79:{seed:7931,skin:2,hair:1,style:4,eyes:0,face:2,build:1,ornament:5,material:0,weapon:'sword'}};
 const report={manifest:K.validateManifest(),catalogPlanErrors:[],catalogPlanCount:0,frameHashes:[],channelChecks:[],beastBodies:[],artStatus:'provisional Cursor PNGs; not Blender artwork'};
 for(const race of Object.keys(M.races))for(const age of ['child','adult','elder'])for(let frame=0;frame<14;frame++){
  const plan=V.citizenPlan({...person,race},null,frame,'#729aab',age);report.catalogPlanCount++;
  for(const layer of plan.layers){const sheet=M.sheets[layer.path];if(!sheet||!Number.isInteger(layer.row)||layer.row<0||layer.row>=sheet.rows)report.catalogPlanErrors.push({race,age,frame,layer});}
 }
 const beforeIdentity=JSON.stringify(person);
 for(let frame=0;frame<14;frame++){
  const result=await K.preload(V.citizenPlan(person,null,frame,'#729aab','adult'));
  report.frameHashes.push({frame,pose:M.frameOrder[frame],ready:result.ready,hash:hash(result.canvas),visiblePixels:pixels(result.canvas)});
 }
 report.identityUnchanged=beforeIdentity===JSON.stringify(person);
 report.distinctFrameHashes=new Set(report.frameHashes.map(x=>x.hash)).size;
 report.walkDistinctHashes=new Set(report.frameHashes.filter(x=>x.frame>=1&&x.frame<=6).map(x=>x.hash)).size;
 report.duplicateFrameGroups=Object.values(Object.groupBy?Object.groupBy(report.frameHashes,x=>x.hash):report.frameHashes.reduce((out,x)=>{(out[x.hash]||=[]).push(x);return out},{})).filter(a=>a.length>1).map(a=>a.map(x=>x.frame));
 const basePlan=V.citizenPlan(person,null,0,'#729aab','adult'),baseResult=await K.preload(basePlan);
 for(const [field,value,allowed] of [['skin',5,['body','face']],['hair',6,['hair','beard']],['eyes',3,['eyes']],['material',3,['outfit','special']]]){
  const changed={...person,tw79:{...person.tw79,[field]:value}},plan=V.citizenPlan(changed,null,0,'#729aab','adult'),result=await K.preload(plan),changedLayers=[];
  for(const layer of basePlan.layers){const other=plan.layers.find(l=>l.kind===layer.kind);const a=K.cell(layer.path,layer.row,0,layer.tint),b=K.cell(other.path,other.row,0,other.tint);if(hash(a)!==hash(b))changedLayers.push(layer.kind);}
  report.channelChecks.push({field,changedLayers,wholeSpriteChanged:hash(baseResult.canvas)!==hash(result.canvas),independent:changedLayers.length>0&&changedLayers.every(k=>allowed.includes(k)),ready:result.ready});
 }
 for(const type of Object.keys(M.beasts)){
  const plan=K.beastLayers({id:'beast-'+type,type},'adult',0),body=plan.layers.find(l=>l.kind==='body'),result=await K.preload({layers:[body],frame:0});
  report.beastBodies.push({type,path:body.path,row:body.row,ready:result.ready,hash:hash(result.canvas),visiblePixels:pixels(result.canvas)});
 }
 report.distinctBeastBodyPaths=new Set(report.beastBodies.map(x=>x.path)).size;
 report.distinctBeastBodyHashes=new Set(report.beastBodies.map(x=>x.hash)).size;
 report.invalidManifestRejected=!K.validateManifest({...M,anchor:[0,0]}).ok;
 const samples=[['Human warrior',V.citizenPlan(person,null,0,'#729aab','adult')],['Wolffolk ranger',V.citizenPlan({...person,id:'wolf-ranger',race:'wolffolk',cls:'archer',tw79:{...person.tw79,seed:7922,hair:0,style:2,weapon:'bow'}},null,0,'#537a60','adult')],['Dragon',K.beastLayers({type:'dragon',id:7911,pattern:3,crest:2,tail:2,eye:1,accent:1},'adult',0)]];
 report.catalogImages=[];
 for(const [name,plan]of samples){const result=await K.preload(plan);report.catalogImages.push({name,ready:result.ready,data:result.canvas.toDataURL('image/png')});}
 // A real PNG error must use the game's preserved legacy renderer, not disappear.
 const failedPerson={...person,id:'missing-png',race:'dragonfolk',tw79:{...person.tw79,seed:7988,style:9}},failedPlan=V.citizenPlan(failedPerson,null,0,'#729aab','adult'),badPath=failedPlan.layers.find(l=>l.kind==='hair').path,original=KINGDOM_PNGS[badPath];
 KINGDOM_PNGS[badPath]='data:image/png;base64,broken-png';
 const failedResult=await K.preload(failedPlan),priorFallbacks=V.diagnostics().counters.failedFallbacks||0,portrait=g.sprite(failedPerson,1,0,'#729aab');
 report.pngFailureFallback={path:badPath,failed:failedResult.failed,ready:failedResult.ready,failures:failedResult.failures.map(x=>({path:x.path,code:x.code})),legacyPortrait:[portrait.width,portrait.height],visiblePixels:pixels(portrait),counterIncreased:(V.diagnostics().counters.failedFallbacks||0)>priorFallbacks};
 KINGDOM_PNGS[badPath]=original;report.pngFailureFallback.resetCount=K.resetFailures(badPath);
 report.pngFailureFallback.recovered=(await K.preload(failedPlan)).ready;
 report.stress=[];
 const actors=Array.from({length:20},(_,i)=>({id:8000+i,race:i<12?'human':Object.keys(M.races)[i-11],cls:M.classes[i%16],build:i%4,sex:i%2})),inflight=new Set(),start=performance.now();
 await new Promise(done=>{const timer=setInterval(()=>{const frame=1+Math.floor((performance.now()-start)/130)%6;let ready=0;const tick=performance.now();for(let i=0;i<actors.length;i++){const plan=K.citizenLayers(actors[i],'adult',frame),result=K.compose(plan),key=i+'|'+frame;if(result.ready)ready++;else if(!inflight.has(key)){inflight.add(key);K.preload(plan).finally(()=>inflight.delete(key));}}if(Math.floor((performance.now()-start)/1000)>report.stress.length)report.stress.push({seconds:Math.round((performance.now()-start)/1000),ready,compose20Ms:Math.round((performance.now()-tick)*1000)/1000,stats:K.stats(),loads:K.diagnostics().counters.loadsStarted||0});if(performance.now()-start>stressSeconds*1000){clearInterval(timer);done();}},40)});
 report.diagnostics=K.diagnostics();
 return report;
}'''


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass


def make_catalog(samples):
    image = Image.new('RGB',(1512,760),'#19202b'); draw = ImageDraw.Draw(image)
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
        small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    except OSError: font=small=ImageFont.load_default()
    draw.text((24,15),'TINY WORLD · PROVISIONAL CURSOR PNG ASSETS',fill='#f4dbb1',font=font)
    draw.text((24,44),'Actual 144 × 144 compositions above; exact 3× nearest-neighbour enlargement below.',fill='#c1ccd8',font=small)
    for n,sample in enumerate(samples):
        left=24+n*504
        sprite=Image.open(io.BytesIO(base64.b64decode(sample['data'].split(',',1)[1]))).convert('RGBA')
        draw.text((left,78),sample['name'],fill='#f4dbb1',font=font)
        for y0,size in [(112,144),(281,432)]:
            for y in range(y0,y0+size,12):
                for x in range(left,left+size,12):
                    draw.rectangle((x,y,min(x+11,left+size-1),min(y+11,y0+size-1)),fill='#48505c' if ((x-left)//12+(y-y0)//12)%2 else '#3c444f')
            shown=sprite if size==144 else sprite.resize((size,size),Image.Resampling.NEAREST)
            image.paste(shown,(left,y0),shown)
        draw.text((left,258),'144 × 144 native',fill='#c1ccd8',font=small)
    draw.text((24,732),'Preposed layered sprites. Independent anatomical articulation is not present. Blender prototype remains separate.',fill='#c1ccd8',font=small)
    image.save(CATALOG)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium',default='/usr/bin/chromium')
    parser.add_argument('--html',type=Path,default=GAME/'dist'/'Tiny-World-v79-Modular.html')
    parser.add_argument('--stress-seconds',type=int,default=15)
    args=parser.parse_args(); args.html=args.html.resolve(); started=time.time()
    result={'test':'compositor actual PNG and browser validation','html':str(args.html.relative_to(GAME)),
        'htmlSHA256':hashlib.sha256(args.html.read_bytes()).hexdigest(),
        'browser':'Chromium','firefoxAvailable':shutil.which('firefox') is not None,
        'dependencies':'Free Python, Pillow, Playwright and system Chromium',
        'assets':validate_assets(),'pageErrors':[]}
    handler=partial(QuietHandler,directory=str(GAME)); server=ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True,executable_path=args.chromium,args=['--disable-dev-shm-usage'])
            context=browser.new_context(viewport={'width':1280,'height':900});page=context.new_page()
            page.on('pageerror',lambda error:result['pageErrors'].append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/{args.html.relative_to(GAME).as_posix()}',wait_until='load',timeout=90000)
            page.wait_for_function('window.TinyWorldVisuals && window.KingdomSprites',timeout=90000)
            result['browserVersion']=browser.version
            result['browserChecks']=page.evaluate(BROWSER_CHECKS,{'stressSeconds':max(5,args.stress_seconds)})
            samples=result['browserChecks'].pop('catalogImages');make_catalog(samples)
            result['catalogSamples']=[{'name':s['name'],'ready':s['ready']}for s in samples]
            # Verify invalid manifest fail-closed in a clean realm, without altering the game.
            invalid=context.new_page();invalid.set_content('<!doctype html><script>globalThis.KINGDOM_MANIFEST={format:"wrong",cell:[1,1]};</script>')
            invalid.add_script_tag(path=str(GAME/'src'/'kingdom-compositor.js'))
            result['invalidManifestFailClosed']=invalid.evaluate('''()=>{const K=KingdomSprites,r=K.compose(K.citizenLayers({}));return !K.diagnostics().compatible&&r.failed&&!r.ready&&(K.diagnostics().counters.loadsStarted||0)===0}''')
            context.close();browser.close()
    finally:server.shutdown();server.server_close()
    checks=result['browserChecks'];last=checks['stress'][-1]
    result['assertions']={
        'assetStructure':result['assets']['ok'],'noJavaScriptExceptions':not result['pageErrors'],
        'manifestCompatible':checks['manifest']['ok'],'allRaceAgeFramePlansValid':checks['catalogPlanCount']==798 and not checks['catalogPlanErrors'],
        'identityReadOnly':checks['identityUnchanged'],'posesHaveActualDistinctPixels':checks['distinctFrameHashes']>=8 and checks['walkDistinctHashes']>=4,
        'allPosesReady':all(x['ready']and x['visiblePixels']>0 for x in checks['frameHashes']),
        'independentColourChannels':all(x['ready']and x['independent']and x['wholeSpriteChanged']for x in checks['channelChecks']),
        'allBeastBodyPlansDistinct':checks['distinctBeastBodyPaths']==17 and all(x['ready']and x['visiblePixels']>0 for x in checks['beastBodies']),
        'invalidManifestRejected':checks['invalidManifestRejected']and result['invalidManifestFailClosed'],
        'failedPNGHasVisibleLegacyFallback':checks['pngFailureFallback']['failed']and not checks['pngFailureFallback']['ready']and checks['pngFailureFallback']['visiblePixels']>0 and checks['pngFailureFallback']['counterIncreased'],
        'failedPNGCanRecoverExplicitly':checks['pngFailureFallback']['recovered'],
        'twentyActorWalkCacheWarm':last['ready']==20 and last['stats']['composites']>=120,
        'cacheBounds':all(x['stats']['rawRows']<=48 and x['stats']['cells']<=384 and x['stats']['composites']<=256 for x in checks['stress']),
        'allCatalogSamplesReady':all(s['ready']for s in result['catalogSamples'])}
    result['ok']=all(result['assertions'].values());result['seconds']=round(time.time()-started,2)
    REPORT.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'ok':result['ok'],'assertions':result['assertions'],'seconds':result['seconds'],'report':str(REPORT)},indent=2))
    if not result['ok']:raise SystemExit(1)

if __name__=='__main__':main()
