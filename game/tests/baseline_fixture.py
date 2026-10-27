#!/usr/bin/env python3
"""Generate a small regression world through untouched v79's native game APIs.

Uses Python's standard-library HTTP server and the free Playwright/Chromium
installed in the execution environment. It never reads a normal browser profile.
"""
from __future__ import annotations

import argparse
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright


GAME = Path(__file__).resolve().parents[1]
BASELINE = GAME / "baseline" / "Tiny-World-v79-original.html"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    args = parser.parse_args()
    handler = partial(SimpleHTTPRequestHandler, directory=str(GAME))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, executable_path=args.chromium,
                args=["--disable-dev-shm-usage"],
            )
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            # Resettable random stream, installed before the baseline captures R.
            page.add_init_script("""
                window.fixtureRandomState = 0x79a55e;
                Math.random = () => {
                  let s = window.fixtureRandomState >>> 0;
                  s ^= s << 13; s ^= s >>> 17; s ^= s << 5;
                  window.fixtureRandomState = s >>> 0;
                  return (s >>> 0) / 4294967296;
                };
            """)
            page.goto(
                f"http://127.0.0.1:{server.server_port}/baseline/{BASELINE.name}",
                wait_until="load",
            )
            page.wait_for_function("window.TW79_GAME && TW79_GAME.map")
            result = page.evaluate("""() => {
              const g = TW79_GAME;
              tw52Speed(0);
              window.fixtureRandomState = 0x79a55e;
              Object.assign(g.opts, {w:96,h:64,seed:'v79-regression',diversity:false});
              g.opts.pop = Object.fromEntries(Object.keys(g.creatures).map(k => [k,0]));
              g.newWorld();
              tw52Speed(0);
              const sites = [];
              for (let y=12;y<g.H-12;y++) for (let x=12;x<g.W-12;x++) {
                if (!stableFoundation(x,y) || !buildFits('hall',x,y)) continue;
                sites.push({x,y,d:Math.hypot(x-g.W/2,y-g.H/2)});
              }
              sites.sort((a,b)=>a.d-b.d);
              if (!sites.length) throw Error('Fixture seed has no native settlement site');
              const home = sites[0], town = foundTown(home.x,home.y);
              if (!town) throw Error('Native foundTown failed');
              const citizens = [];
              const races = ['human','elf','dwarf','orc'];
              for (let n=0;n<races.length;n++) {
                const race = races[n];
                const site = sites.find(s=>s.x>home.x+3+n*2 && Math.abs(s.y-home.y)<7)
                  || sites[Math.min(n+1,sites.length-1)];
                let c;
                if (race==='human') c=g.spawn('human',site.x,site.y,true);
                else {
                  const previous = g.cre.length;
                  g.powers.find(p=>p.key==='spawn-'+race).use(g,site.x,site.y,true);
                  c=g.cre.slice(previous).find(c=>c.type==='human');
                }
                if (!c) throw Error('Native race spawn failed: '+race);
                const p=g.person(c);
                c.age=adultAge(c)+100; c.rx=c.x; c.ry=c.y;
                p.name='Regression '+race[0].toUpperCase()+race.slice(1);
                joinTown(c,town);
                setClass(c,p,n===0?'warrior':n===1?'mage':n===2?'tank':'archer');
                p.tier=n===0?4:2;
                p.spec=n===0?'knight':n===1?'wizard':n===2?'guardian':'sniper';
                p.preferredSpec=p.spec;
                p.roots=[['Water','Wood','Metal','Fire'][n]];
                p.tw69Root=p.roots[0].toLowerCase();
                p.tw69Path=['control','spirit','offense','offense'][n];
                p.cultStage=3+n; p.cultFoundation=1+n*.02;
                derive(c,p); tw74.initHuman(p,c); TW79.identity(p);
                citizens.push(c);
              }
              // Native mentoring and sect foundation, without fabricating a sect.
              g.time=120;
              g.systems.find(s=>s.key==='cultivationExtras').tick(g);
              const beasts=[];
              for (const [n,type] of ['wolf','deer','dragon'].entries()) {
                const site=sites[Math.min(12+n*5,sites.length-1)];
                const c=g.spawn(type,site.x,site.y,true);
                c.age=1000;c.rx=c.x;c.ry=c.y;
                tw74.initBeast(c,g);
                if(type!=='dragon') TW79.beastIdentity(c);
                beasts.push(c);
              }
              g.paused=true;
              const snapshot=g.snapshot(), data=JSON.parse(snapshot);
              const people=Object.fromEntries(citizens.map(c=>{
                const p=g.person(c);
                return [c.id,{name:p.name,race:p.race,cls:p.cls,spec:p.spec,
                  preferredSpec:p.preferredSpec,roots:p.roots,tw69Root:p.tw69Root,
                  tw69Path:p.tw69Path,tier:p.tier,cultStage:p.cultStage,
                  cultFoundation:p.cultFoundation,genome:p.genome,gear:p.gear,
                  tw79:p.tw79,tw74:p.tw74}];
              }));
              const expected={W:data.W,H:data.H,time:data.time,people,
                beasts:beasts.map(c=>({uid:c.uid,type:c.type,
                  tw74Beast:c.tw74Beast,tw79Beast:c.tw79Beast||null})),
                sects:data.state.sects||{},buildings:data.bld,
                notes:['Generated using native spawning, race powers, class setup, town foundation and mentoring.',
                  'Dragon has no baseline TW79.beastIdentity entry; its tw74Beast remains authoritative.',
                  'Derived combat stats and rarity may be recomputed by baseline restoration.']};
              return {snapshot,expected};
            }""")
            browser.close()
        if errors:
            raise RuntimeError("Baseline browser exceptions: " + "; ".join(errors))
        fixtures = GAME / "tests" / "fixtures"
        fixtures.mkdir(exist_ok=True, parents=True)
        (fixtures / "v79-world.json").write_text(result["snapshot"], encoding="utf-8")
        result["expected"]["baselineSha256"] = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
        result["expected"]["fixtureSha256"] = hashlib.sha256(
            (fixtures / "v79-world.json").read_bytes()).hexdigest()
        (fixtures / "v79-world.expected.json").write_text(
            json.dumps(result["expected"], indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"fixture":str(fixtures / "v79-world.json"),
                          "bytes":len(result["snapshot"]),
                          "people":len(result["expected"]["people"]),
                          "beasts":len(result["expected"]["beasts"]),
                          "sects":list(result["expected"]["sects"]),
                          "pageErrors":errors}, indent=2))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
