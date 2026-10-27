#!/usr/bin/env python3
"""Reproducible offline build. The uploaded v79 and Cursor pack are never edited."""
from pathlib import Path
import base64, hashlib, json, re

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'baseline/Tiny-World-v79-original.html'
SHA='83bc95867919490989d76beeea785a542f7af6496eef2f952a15fb05431de3eb'
def build():
    raw=SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==SHA, 'Authoritative baseline changed'
    html=raw.decode('utf-8')
    changes=[]
    def replace(before,after,label):
        nonlocal html
        assert html.count(before)==1, f'Patch drift: {label}'
        html=html.replace(before,after);changes.append(label)
    replace("if(!localStorage.getItem(WIPE_FLAG)){","if(false && !localStorage.getItem(WIPE_FLAG)){",'Disable active one-time world wipe')
    replace("if(localStorage.getItem(TW_V14_RESET)!=='1'){","if(false && localStorage.getItem(TW_V14_RESET)!=='1'){",'Disable active v14 world wipe')
    start=html.index('async function resumeWorldOrCreate(){')
    end=html.index('\nconst persistentApply=apply;',start)
    html=html[:start]+(ROOT/'src/session-resume.js').read_text().rstrip()+html[end:]
    changes.append('Resume the newest valid persisted session; stop saving on unreadable data')
    replace("function install(){\n  if(typeof G==='undefined'||!G.creatures)","function install(){\n  if(window.TinyWorldVisuals?.installed)return;\n  if(typeof G==='undefined'||!G.creatures)",'Stop competing legacy renderer reinstall after modular adapter')
    replace("function install(){lock(G,'sprite',renderPerson);","function install(){if(window.TinyWorldVisuals?.installed)return;lock(G,'sprite',renderPerson);",'Stop competing v79 renderer reinstall after modular adapter')
    replace('<title>Tiny World v78 - Clean Asset Replacement</title>','<title>Tiny World v79 — Modular Development Build</title>','Correct stale document title')
    fontline=next(line for line in html.splitlines() if line.startswith("<link rel='preconnect'"))
    replace(fontline,'<!-- Offline build uses the existing system-font fallbacks. -->','Remove optional remote font dependency')
    pack=ROOT/'vendor/kingdom-sprites'
    manifest=json.loads((pack/'manifest.json').read_text())
    assets={}
    for path,meta in manifest['sheets'].items():
        data=(pack/path).read_bytes()
        assert hashlib.sha256(data).hexdigest()==meta['sha256'],path
        assets[path]='data:image/png;base64,'+base64.b64encode(data).decode()
    def js(text):
        assert '</script' not in text.lower(),'Unsafe inline script termination'
        return '<script>\n'+text+'\n</script>'
    registry=json.loads((ROOT/'reports/sect-registry.json').read_text())
    addition=[js('window.KINGDOM_MANIFEST='+json.dumps(manifest,separators=(',',':'))+';'),
              js('window.KINGDOM_PNGS='+json.dumps(assets,separators=(',',':'))+';'),
              js('window.TinyWorldSectReference='+json.dumps(registry,separators=(',',':'))+';')]
    for path in ['kingdom-compositor.js','anatomy-contract.js','tiny-world-visual-adapter.js']:
        addition.append(js((ROOT/'src'/path).read_text()))
    assert html.count('</body>')==1
    html=html.replace('</body>','\n'.join(addition)+'\n</body>')
    out=ROOT/'dist';out.mkdir(exist_ok=True)
    target=out/'Tiny-World-v79-Modular.html';target.write_text(html)
    report={'baseline':SOURCE.name,'baselineSHA256':SHA,'baselineBytes':len(raw),'build':target.name,
            'buildSHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'buildBytes':target.stat().st_size,
            'pngSheets':len(assets),'patches':changes,'freeToolsOnly':True,'artStatus':'provisional',
            'blenderAssetsIncluded':False,'gameplayRegistriesChanged':False}
    (ROOT/'reports/build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':build()
