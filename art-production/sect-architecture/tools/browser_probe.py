#!/usr/bin/env python3
"""Capture an isolated, temporary v79 rendering probe of Canopy PNGs.

This script changes only its in-memory browser test world. It does not patch the
HTML, game files, user saves, or game's architecture registry. Its images are
visual scale checks, not evidence of finished paths or integrated gameplay.
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import time

from playwright.sync_api import sync_playwright


REPO = Path(__file__).resolve().parents[3]
ROOT = Path(__file__).resolve().parents[1] / "canopy-village"
FIXTURE = (REPO / "game/tests/fixtures/v79-world.json").read_text()


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(REPO)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    seed = {"savedAt": int(time.time() * 1000), "revision": 4, "time": 0,
            "paused": True, "speed": 1, "snapshot": FIXTURE}
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium",
                                                  args=["--disable-dev-shm-usage"])
            context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
            context.add_init_script("localStorage.setItem('tinyworld-current-session-v1',JSON.stringify(" + json.dumps(seed) + ")); ")
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base + "/game/dist/Tiny-World-v79-Modular.html", wait_until="load", timeout=120000)
            page.wait_for_function("typeof Session !== 'undefined' && Session.phase === 'ready'", timeout=60000)
            assets = {
                "hall-a": "sectHall", "hall-b": "sectHall", "house-a": "house",
                "house-b": "house", "tree-shrine": "sectAltar", "root-gate": "sectGate",
            }
            info = page.evaluate("""async data => {
              tw52Speed(0); G.uiHide=true; CIV.follow=0;
              const list=Object.entries(data.assets);
              const images={};
              for (const [name] of list) {
                const image=new Image(); image.src=data.base+'/art-production/sect-architecture/canopy-village/assets/'+name+'.png';
                await image.decode(); images[name]=image;
              }
              let site=null;
              for(let y=10;y<G.H-15&&!site;y++)for(let x=10;x<G.W-20&&!site;x++) {
                let good=true;
                for(let yy=y;yy<y+12&&good;yy++)for(let xx=x;xx<x+18;xx++) {
                  const i=yy*G.W+xx;
                  if(!G.walk(xx,yy)||G.bld.has(i)){good=false;break}
                }
                if(good)site=[x,y];
              }
              if(!site)throw Error('No clear terrain patch for probe');
              const [x,y]=site, placement=[
                ['hall-a','sectHall',x+3,y+5],['hall-b','sectHall',x+10,y+5],
                ['house-a','house',x+1,y+10],['house-b','house',x+6,y+10],
                ['tree-shrine','sectAltar',x+11,y+10],['root-gate','sectGate',x+15,y+10]
              ];
              const mapping=new Map();
              for(const [name,type,xx,yy] of placement){const i=yy*G.W+xx;G.bld.set(i,type);mapping.set(i,name)}
              const old=raceBuilding;
              raceBuilding=function(pen,type,i,z){
                const name=mapping.get(i);if(!name)return old(pen,type,i,z);
                const [w,d,h]=PLOTS[type], xx=i%G.W, yy=i/G.W|0;
                pen.imageSmoothingEnabled=false;
                pen.drawImage(images[name],(xx+.5-w/2)*z,(yy+1-h)*z,w*z,h*z);
              };
              window.__canopyProbe={site,placement,images,mapping};
              return {site,placement,loaded:Object.fromEntries(Object.entries(images).map(([k,v])=>[k,[v.width,v.height]]))};
            }""", {"base": base, "assets": assets})
            for zoom in (16, 32):
                page.evaluate("""zoom=>{
                  const [x,y]=window.__canopyProbe.site;
                  cam.z=zoom;cam.x=x-2;cam.y=y-2;clampCam();draw(performance.now());
                }""", zoom)
                page.locator("#cv").screenshot(path=str(ROOT / "previews" / f"v79-in-memory-{zoom}px.png"))
            result = {"status": "temporary visual probe", "gameSourceChanged": False,
                      "persistentSavesChanged": False, "elevatedNavigationVerified": False,
                      "images": [f"previews/v79-in-memory-{zoom}px.png" for zoom in (16, 32)],
                      "note": "Browser-only draw override uses the existing plot footprint and y-sort; house-b is wider than its slot and drawn compressed by the current width. This is not an integration or gameplay test.",
                      "site": info["site"], "loadedCanvasSizes": info["loaded"],
                      "pageErrors": errors, "passed": not errors and len(info["loaded"]) == len(assets)}
            (ROOT / "browser-probe.json").write_text(json.dumps(result, indent=2) + "\n")
            context.close()
            browser.close()
            print(json.dumps({"passed": result["passed"], "site": info["site"], "pageErrors": errors}))
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
