#!/usr/bin/env python3
"""Render the new sect building PNGs in an isolated v79 Chromium test world.

This temporary draw override does not modify game files, saves, renderer code,
building registries, or elevated navigation. Landmarks without a game slot are
shown in the art sheet instead of being mistaken for installed world objects.
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
ROOT = Path(__file__).resolve().parents[1] / "planned-three"
FIXTURE = (REPO / "game/tests/fixtures/v79-world.json").read_text()


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_: object) -> None:
        pass


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(REPO)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    seed = {"savedAt": int(time.time() * 1000), "revision": 4,
            "time": 0, "paused": True, "speed": 1, "snapshot": FIXTURE}
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True,
                                                 executable_path="/usr/bin/chromium",
                                                 args=["--disable-dev-shm-usage"])
            context = browser.new_context(viewport={"width": 1440, "height": 1000},
                                          device_scale_factor=1)
            context.add_init_script("localStorage.setItem('tinyworld-current-session-v1',JSON.stringify(" + json.dumps(seed) + ")); ")
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base + "/game/dist/Tiny-World-v79-Modular.html", wait_until="load", timeout=120000)
            page.wait_for_function("typeof Session !== 'undefined' && Session.phase === 'ready'", timeout=60000)
            names = ["citadel-hall-a", "sky-monastery-hall-a", "iron-foundry-hall-a",
                     "citadel-gatehouse", "iron-foundry-workshop"]
            result = page.evaluate("""async data => {
              tw52Speed(0); G.uiHide=true; CIV.follow=0;
              const images={};
              for(const name of data.names){
                const image=new Image();
                image.src=data.base+'/art-production/sect-architecture/planned-three/assets/'+name+'.png';
                await image.decode();images[name]=image;
              }
              let site=null;
              for(let y=10;y<G.H-15&&!site;y++)for(let x=10;x<G.W-24&&!site;x++){
                let good=true;
                for(let yy=y;yy<y+12&&good;yy++)for(let xx=x;xx<x+22;xx++){
                  const i=yy*G.W+xx;if(!G.walk(xx,yy)||G.bld.has(i)){good=false;break}
                }
                if(good)site=[x,y];
              }
              if(!site)throw Error('No clear terrain patch');
              const [x,y]=site,placement=[
                ['citadel-hall-a','sectHall',x+3,y+5],
                ['sky-monastery-hall-a','sectHall',x+10,y+5],
                ['iron-foundry-hall-a','sectHall',x+17,y+5],
                ['citadel-gatehouse','sectGate',x+4,y+10],
                ['iron-foundry-workshop','blacksmith',x+17,y+10]
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
              window.__threeSectProbe={site,placement};
              return {site,placement,loaded:Object.fromEntries(Object.entries(images).map(([k,v])=>[k,[v.width,v.height]]))};
            }""", {"base": base, "names": names})
            for zoom in (16, 32):
                page.evaluate("""zoom=>{
                  const [x,y]=window.__threeSectProbe.site;
                  cam.z=zoom;cam.x=x-2;cam.y=y-2;clampCam();draw(performance.now());
                }""", zoom)
                page.locator("#cv").screenshot(path=str(ROOT / "previews" / f"v79-in-memory-{zoom}px.png"))
            record = {"status": "temporary browser rendering probe", "gameSourceChanged": False,
                      "persistentSavesChanged": False, "integrationClaim": False,
                      "landmarksPlacedInGame": False, "elevatedNavigationVerified": False,
                      "browser": browser.version, "site": result["site"],
                      "loadedCanvasSizes": result["loaded"],
                      "placedGameSlotBuildings": [item[0] for item in result["placement"]],
                      "images": [f"previews/v79-in-memory-{zoom}px.png" for zoom in (16, 32)],
                      "pageErrors": errors, "passed": not errors and len(result["loaded"]) == len(names),
                      "note": "Building PNGs were drawn at existing PLOTS dimensions through an in-memory raceBuilding override. This proves rendering and scale only; landmarks and routes are not installed."}
            (ROOT / "browser-probe.json").write_text(json.dumps(record, indent=2) + "\n")
            context.close()
            browser.close()
            print(json.dumps({"passed": record["passed"], "site": record["site"],
                              "pageErrors": errors}))
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
