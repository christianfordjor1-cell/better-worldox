/* Rendering only. Saved person, beast, cultivation and family records are never rewritten. */
(function(global){
'use strict';
const g=global.TW79_GAME, art=global.KingdomSprites;
if(!g||!art||!art.validateManifest().ok)return;
const manifest=art.manifest, legacyPerson=g.sprite, legacyHuman=humanSprite;
const legacyBeasts=new Map(), lastCitizen=new WeakMap(), lastBeast=new WeakMap(), pending=new WeakMap();
const counters={citizenDraws:0,beastDraws:0,pendingFallbacks:0,failedFallbacks:0,lodDraws:0};
let enabled=true;
try{enabled=localStorage.getItem('tinyworld-layered-art-v1')!=='legacy'}catch{}
const hash=art.hash, own=(o,k)=>Object.prototype.hasOwnProperty.call(o||{},k);
const index=(value,n,seed,key)=>Number.isFinite(Number(value))&&value!==null&&value!==''?((Math.trunc(Number(value))%n)+n)%n:hash(seed+':'+key)%n;
const canonical=new Map([...manifest.classes,...manifest.specialisations,...manifest.weapons,...manifest.roots,...manifest.branches].map(k=>[k.toLowerCase(),k]));
const key=value=>{const s=String(value||'').trim(),lower=s.toLowerCase();return lower==='firearm'?'gun':canonical.get(lower)||lower};
function personIdentity(p,c){
 const saved={...(p.tw79||{}),...(p.spriteIdentity||{}),...(p.visualIdentity||{})};
 const seed=saved.seed??p.tw746?.seed??hash('person:'+String(p.id??p.name??c?.uid??0));
 const q={...p,...saved,id:seed,seed,sex:p.sex,cls:p.cls||'civilian',spec:p.spec||p.specialization||p.specId||''};
 for(const [field,n] of Object.entries({skin:8,hair:8,style:10,eyes:4,face:4,build:4,ornament:6,material:4}))q[field]=index(saved[field]??p[field],n,seed,field);
 const form=String(p.speciesForm||'').toLowerCase().replace(/\s/g,'');
 const formRace=own(manifest.races,form)?form:form+'folk';
 const race=String(p.race||p.tw746?.race||c?.race||'human').toLowerCase();
 q.race=own(manifest.races,formRace)?formRace:own(manifest.races,race)?race:'human';
 q.speciesForm='';q.spec=key(q.spec);
 const item=p.gear?.weapon;
 const itemKind=typeof item?.type==='string'?key(item.type):typeof twItemInfo==='function'&&item?key(twItemInfo(item)?.type):null;
 q.weapon=manifest.weapons.includes(itemKind)?itemKind:saved.weapon==='none'||saved.weapon==='hoe'?'fists':saved.weapon;
 // Keep roots and the six branches separate from the sect architectural registry.
 q.root=key(p.tw69Root||p.elementRoot||p.root||p.roots?.[0]||p.tw74?.root);
 q.branch=key(p.branch||p.cultivation?.branch||p.tw74?.branch);
 q.cultivationTier=Math.max(1,Math.min(6,Number(p.tier)||1));
 // These are flattened copies: the compositor must not prefer unflattened nested data.
 delete q.spriteIdentity;delete q.visualIdentity;
 return q;
}
function beastIdentity(c){return {...c,...(c.tw79Beast||{}),id:c.tw79Beast?.seed??c.uid,uid:c.tw79Beast?.seed??c.uid,
 ancient:[c.tw79Beast?.bloodline,c.tw74Beast?.bloodline].some(value=>String(value||'').toLowerCase()==='ancient'),bloodline:c.tw79Beast?.bloodline};}
function age(p,c){return c?(c.age<adultAge(c)?'child':c.age>elderAge(c)?'elder':'adult'):'adult';}
function beastAge(c){return typeof SPECIES!=='undefined'&&SPECIES[c.type]&&c.age<SPECIES[c.type].mature?'baby':'adult';}
function frame(c,game=g){
 if(c.hp<=0)return 10;
 if(c.hurtUntil>game.time)return 9;
 const pose=typeof citizenActionPose==='function'&&c.type==='human'?citizenActionPose(c,game):null;
 if(c.attack||pose?.kind==='attack'||pose?.kind==='shoot')return 7;
 const clock=typeof ActionMotion!=='undefined'?ActionMotion.clock:game.time*120;
 const phase=Math.floor(clock/120+(c.uid||c.id||0));
 if(pose?.kind==='cast'||/cast|channel|meditat|cultivat/i.test(c.action||''))return 12+phase%2;
 if(pose?.kind==='work'||c.practice||/harvest|gather|quarr|chop|build|craft|repair/i.test(c.action||''))return 11+phase%3;
 const moving=pose?.kind==='walk'||pose?.kind==='carry'||Math.abs((c.rx??c.x)-c.x)+Math.abs((c.ry??c.y)-c.y)>.06;
 if(moving)return 1+phase%6;
 return Math.floor(clock/900+(c.uid||c.id||0))%5===0?8:0;
}
function citizenPlan(p,c,fr=0,color='#729aab',stage){return art.citizenLayers(personIdentity(p,c),stage||age(p,c),fr,color,c);}
function beastPlan(c,fr=0){return art.beastLayers(beastIdentity(c),beastAge(c),fr);}
function colorOf(p,c,game){return game.state.kings?.[c?.k]?.color||(typeof TUN!=='undefined'?TUN[p.tun]:null)||'#729aab';}
function lock(object,name,value){Object.defineProperty(object,name,{value,writable:false,configurable:true});}
function resultFor(plan,actor,cache){
 const result=art.compose(plan);
 // Avoid flicker as a new animation row is decoded. Do not show another identity after equipment/age changes.
 const signature=JSON.stringify(plan.layers.map(l=>[l.path,l.row,l.tint]));
 if(result.ready){cache.set(actor,{signature,canvas:result.canvas});return result.canvas;}
 counters[result.failed?'failedFallbacks':'pendingFallbacks']++;
 if(!result.failed&&!pending.has(actor)){
  const request=art.preload(plan).then(complete=>{if(complete.ready)cache.set(actor,{signature,canvas:complete.canvas});}).finally(()=>pending.delete(actor));
  pending.set(actor,request);
 }
 const previous=cache.get(actor);return previous?.signature===signature?previous.canvas:null;
}
function drawAnchored(ctx,image,c,z,side){
 const cx=Math.round(((c.rx??c.x)+.5)*z),ground=Math.round(((c.ry??c.y)+1)*z);
 ctx.save();ctx.imageSmoothingEnabled=false;ctx.translate(cx,ground);
 if((c.facing||1)<0)ctx.scale(-1,1);
 ctx.drawImage(image,-Math.round(side/2),-Math.round(130*side/144),side,side);ctx.restore();
 return {cx,ground};
}
function drawHuman(ctx,c,z,game){
 if(!enabled)return legacyHuman(ctx,c,z,game);
 if(c.hp<=0||c.inDungeon||c.embarked)return;
 const p=game.person(c);if(!p)return;
 if(z<5){counters.lodDraws++;ctx.fillStyle=colorOf(p,c,game);ctx.fillRect(Math.round(((c.rx??c.x)+.25)*z),Math.round(((c.ry??c.y)+.2)*z),Math.max(1,Math.round(z*.5)),Math.max(1,Math.round(z*.8)));return;}
 const plan=citizenPlan(p,c,frame(c,game),colorOf(p,c,game)),image=resultFor(plan,c,lastCitizen);
 if(!image)return legacyHuman(ctx,c,z,game);
 counters.citizenDraws++;
 const b=humanBounds(c,z,game),side=Math.max(12,Math.round(b.h*144/(age(p,c)==='child'?77:110)));
 const {cx,ground}=drawAnchored(ctx,image,c,z,side);
 const kingdom=game.state.kings?.[c.k];
 if(kingdom?.ruler===c.id&&z>6){ctx.fillStyle='#ffe19b';ctx.fillRect(cx-3,ground-b.h-4,6,2);ctx.fillRect(cx-3,ground-b.h-7,1,3);ctx.fillRect(cx,ground-b.h-8,1,4);ctx.fillRect(cx+2,ground-b.h-7,1,3);}
 if(game.state.sel===c.id){ctx.strokeStyle='#ffe4a5';ctx.lineWidth=1;ctx.strokeRect(cx-b.w/2-2,ground-b.h-2,b.w+4,b.h+4);}
 // The existing vegetation occlusion remains part of the world presentation.
 if(z>=6&&typeof foregroundVegetation==='function')foregroundVegetation(ctx,{left:cx-side/2,top:ground-b.h,right:cx+side/2,bottom:ground+z*.12},(c.ry??c.y)+1,z,c);
}
function drawBeast(type,legacy){return function(ctx,c,z,game){
 if(!enabled||z<5||c.hp<=0)return legacy?.(ctx,c,z,game);
 const image=resultFor(beastPlan(c,frame(c,game)),c,lastBeast);
 if(!image)return legacy?.(ctx,c,z,game);
 counters.beastDraws++;
 const scale=typeof WorldArtIntegration!=='undefined'?WorldArtIntegration.animalScale[type]:null;
 const side=Math.max(10,Math.round(z*(scale||1.3)*(beastAge(c)==='baby'?.65:1)*1.25));
 drawAnchored(ctx,image,c,z,side);
};}
function portraitSprite(p,stage,fr,color){
 if(!enabled)return legacyPerson.call(g,p,stage,fr,color);
 const plan=citizenPlan(p,null,fr,color,['child','adult','elder'][stage]||'adult'),image=resultFor(plan,p,lastCitizen);
 if(!image)return legacyPerson.call(g,p,stage,fr,color);
 const can=document.createElement('canvas');can.width=84;can.height=112;const x=can.getContext('2d');x.imageSmoothingEnabled=false;
 const scale=.72,side=144*scale;x.drawImage(image,42-72*scale,105-130*scale,side,side);return can;
}
function install(){
 lock(g,'sprite',portraitSprite);humanSprite=drawHuman;
 if(g.creatures.human)lock(g.creatures.human,'sprite',drawHuman);
 for(const type of Object.keys(manifest.beasts)){
  const definition=g.creatures[type];if(!definition)continue;
  if(!legacyBeasts.has(type))legacyBeasts.set(type,definition.sprite);
  lock(definition,'sprite',drawBeast(type,legacyBeasts.get(type)));
 }
}
const previousInfo=renderInfo;renderInfo=function(game){
 previousInfo(game);if(!enabled)return;
 const portrait=document.getElementById('pt'),p=game.state.people?.[game.state.sel];if(!portrait||!p)return;
 const c=game.find(p.id),result=art.compose(citizenPlan(p,c,0,colorOf(p,c,game)));if(!result.ready)return;
 const x=portrait.getContext('2d'),side=Math.min(portrait.width,portrait.height);x.imageSmoothingEnabled=false;x.clearRect(0,0,portrait.width,portrait.height);
 x.drawImage(result.canvas,Math.round((portrait.width-side)/2),Math.round((portrait.height-side)/2),side,side);
};
const api=global.TinyWorldVisuals={installed:true,version:'v79-modular-1',status:'provisional',manifest,
 personIdentity,beastIdentity,citizenPlan,beastPlan,frame,age,install,
 get enabled(){return enabled;},setEnabled(value){enabled=!!value;try{localStorage.setItem('tinyworld-layered-art-v1',enabled?'cursor':'legacy')}catch{}updateButton();return enabled;},
 diagnostics(){return {version:this.version,enabled,artStatus:'provisional Cursor PNGs; original artwork fallback',
 races:Object.keys(manifest.races).length,beasts:Object.keys(manifest.beasts).length,
 registeredBeasts:Object.keys(manifest.beasts).filter(t=>!!g.creatures[t]),
 artOnlyBeasts:Object.keys(manifest.beasts).filter(t=>!g.creatures[t]),
 counters:{...counters},compositor:art.diagnostics()};}};
install();
let button;
function updateButton(){if(button){button.textContent=enabled?'Art: provisional PNG':'Art: original v79';button.setAttribute('aria-pressed',String(enabled));}}
function addControl(){if(document.getElementById('tw-modular-art'))return;
 button=document.createElement('button');button.id='tw-modular-art';button.type='button';
 button.title='Toggle provisional Cursor character and beast PNGs / original v79 artwork. Gameplay and saves stay the same.';
 button.onclick=()=>api.setEnabled(!enabled);updateButton();
 (document.getElementById('qol-tools')||document.querySelector('header')||document.body).appendChild(button);
}
addControl();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',addControl,{once:true});
})(globalThis);
