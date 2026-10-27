/* Native-pixel PNG compositor. Never draws character geometry at runtime. */
(function(global){
'use strict';
const M=global.KINGDOM_MANIFEST,A=global.KINGDOM_PNGS||{};
const images=new Map(),rawRows=new Map(),cells=new Map(),composites=new Map();let revision=0,activeLoads=0;const queue=[];
const mod=(n,m)=>((Math.floor(Number(n)||0)%m)+m)%m;
function hash(value){let h=2166136261;for(const c of String(value))h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0}
function canvas(){const c=document.createElement('canvas');c.width=c.height=144;return c}
function requestRow(path,row){
 const key=path+'|'+row;if(rawRows.has(key))return Promise.resolve();
 return new Promise(resolve=>{let e=images.get(path);if(!e){e={path,rows:new Map()};images.set(path,e);queue.push(e)}if(!e.rows.has(row))e.rows.set(row,[]);e.rows.get(row).push(resolve);pump()});
}
function pump(){while(activeLoads<2&&queue.length){const e=queue.shift();activeLoads++;const im=new Image();e.image=im;
 im.onload=()=>{for(const [row,resolvers]of e.rows){const strip=document.createElement('canvas');strip.width=2016;strip.height=144;const ctx=strip.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(im,0,row*144,2016,144,0,0,2016,144);rawRows.set(e.path+'|'+row,strip);while(rawRows.size>200)rawRows.delete(rawRows.keys().next().value);resolvers.forEach(r=>r())}e.image=null;images.delete(e.path);im.onload=im.onerror=null;im.removeAttribute('src');activeLoads--;revision++;composites.clear();pump()};
 im.onerror=()=>{console.error('Missing sprite sheet',e.path);for(const rs of e.rows.values())rs.forEach(r=>r());images.delete(e.path);activeLoads--;pump()};im.src=A[e.path]||e.path;
}}
function colorRGB(color){let s=String(color||'#b0b0b0');if(/^#[0-9a-f]{3}$/i.test(s))s='#'+s.slice(1).split('').map(x=>x+x).join('');if(!/^#[0-9a-f]{6}$/i.test(s))return [176,176,176];return [1,3,5].map(i=>parseInt(s.slice(i,i+2),16))}
function tintPixel(c,shade){return Math.min(255,Math.round(c*shade/176))}
function cell(path,row,frame,color){
 const key=[path,row,frame,color||'raw'].join('|');if(cells.has(key))return cells.get(key);
 const strip=rawRows.get(path+'|'+row);if(!strip){requestRow(path,row);return null;}
 const out=canvas(),ctx=out.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;ctx.drawImage(strip,mod(frame,14)*144,0,144,144,0,0,144,144);
 if(color){const rgb=colorRGB(color),data=ctx.getImageData(0,0,144,144);for(let i=0;i<data.data.length;i+=4){const r=data.data[i],g=data.data[i+1],b=data.data[i+2];if(data.data[i+3]&&r===g&&g===b&&r>=70){for(let k=0;k<3;k++)data.data[i+k]=tintPixel(rgb[k],r)}}ctx.putImageData(data,0,0)}
 if(cells.size>=2000)cells.delete(cells.keys().next().value);cells.set(key,out);return out
}
function paged(d,v,b){const index=Math.floor(v/d.variantsPerPage);return [d.pages[index],(v%d.variantsPerPage)*d.bodyRows+b]}
const classPal={civilian:'cloth',warrior:'steel',tank:'steel',archer:'leather',mage:'magic',healer:'cloth',rogue:'leather',bard:'cloth',monk:'cloth',engineer:'leather',alchemist:'nature',psychic:'magic',mime:'cloth',gunslinger:'leather',hero:'gold',spellblade:'dragon'};
const defaultWeapon={warrior:'sword',tank:'hammer',archer:'bow',mage:'staff',healer:'staff',rogue:'dagger',bard:'lute',monk:'fists',engineer:'wrench',alchemist:'flask',psychic:'orb',mime:'fists',gunslinger:'gun',hero:'sword',spellblade:'sword',civilian:'fists'};
const aliases={'magic knight':'spellblade',magicKnight:'spellblade','vancian wizard':'wizard',vancianWizard:'wizard',elemental:'elementalist','nature mage':'natureMage','flying sword':'flyingSword','ember fox':'emberfox','moon hart':'moonhart'};
function keyOf(x){return aliases[x]||x}
function identity(p,actor){const q={...p,...(p?.spriteIdentity||{}),...(p?.visualIdentity||{})};const seed=p.id??actor?.uid??actor?.id??0;const pick=(k,n,alt)=>q[k]!==undefined?mod(q[k],n):alt!==undefined?mod(alt,n):hash(seed+':'+k)%n;
 let race=keyOf(q.race||'human');if(q.speciesForm&&M.races[keyOf(q.speciesForm)+'folk'])race=keyOf(q.speciesForm)+'folk';if(!M.races[race])race='human';
 return {...q,race,skin:pick('skin',8),hair:pick('hair',8),style:pick('style',10),eyes:pick('eyes',4),face:pick('face',4),build:pick('build',4),sex:typeof q.sex==='string'?(q.sex==='female'?1:0):mod(q.sex,2),ornament:pick('ornament',6,q.acc),material:pick('material',4),seed};
}
function materialTint(base,index){const rgb=colorRGB(base),material=colorRGB(M.palettes.material[index]);return '#'+rgb.map((v,i)=>Math.round(v*.80+material[i]*.20).toString(16).padStart(2,'0')).join('')}
function citizenLayers(p,age='adult',frame=0,color='#6d91ad',actor=null){
 const q=identity(p,actor);if(!M.races[q.race][age])age='adult';const race=M.races[q.race][age],fit=M.fits[race.fit],b=q.sex*4+q.build,cls=keyOf(q.cls||q.class||'civilian'),classIndex=Math.max(0,M.classes.indexOf(cls));
 const palette=keyOf(q.palette||q.outfitPalette||classPal[cls]||'cloth');const outfit=materialTint(M.palettes.class[palette]||M.palettes.class.cloth,q.material);
 const fur=q.race.endsWith('folk')?(M.beasts[q.race.slice(0,-4)]?.tint||'#a99b83'):null;
 const skin=q.race==='orc'?M.palettes.orc[q.skin%4]:fur||M.palettes.skin[q.skin];const hair=M.palettes.hair[q.hair],eye=M.palettes.eye[q.eyes];
 const layers=[];const add=(kind,path,row,tint)=>layers.push({kind,path,row,tint});const pg=(kind,d,v,tint)=>{const [path,row]=paged(d,v,b);add(kind,path,row,tint)};
 const root=keyOf(q.elementRoot||q.root||q.cultivation?.root);const branch=q.branch||q.cultivation?.branch;const branchIndex=M.branches.indexOf(branch);
 if(branchIndex>=0){add('tier',M.tiers,Math.max(0,Math.min(5,Number(q.cultivationTier??q.cultivation?.tier??q.tier??1)-1)),null);if(M.auras[root])add('aura',M.auras[root],0,null)}
 let back=q.back;let backIndex=back==='quiver'?1:back==='banner'?2:back==='cape'?0:cls==='archer'?1:['mage','hero','spellblade'].includes(cls)?0:-1;if(q.cape)backIndex=0;
 if(backIndex>=0)pg('back',fit.back,backIndex,color);
 add('body',race.body,b,skin);add('outfit',...paged(fit.outfit,classIndex,b),outfit);
 if(cls==='civilian')add('tunic',fit.tunic,b,color);
 if(branchIndex>=0)pg('robe',fit.robe,branchIndex,color);
 const specIndex=M.specialisations.indexOf(keyOf(q.spec||q.specialisation));if(specIndex>=0)pg('special',fit.special,specIndex,outfit);
 add('face',race.face,q.face*8+b,skin);pg('eyes',fit.eyes,q.eyes,eye);pg('hair',race.hair,q.style,hair);
 const beard=q.beard!==undefined?mod(q.beard,5):(q.race==='dwarf'?1+q.style%4:q.race==='human'&&!q.sex&&age!=='child'&&q.style%3===0?1+q.style%4:0);
 if(beard)add('beard',fit.beard,beard*8+b,hair);
 pg('ornament',fit.ornament,q.ornament,null);
 const weapon=keyOf(typeof q.weapon==='string'?q.weapon:q.gear?.weapon?.type||defaultWeapon[cls]);const wi=M.weapons.indexOf(weapon);if(wi>=0&&(cls!=='civilian'||typeof q.weapon==='string'))pg('weapon',fit.weapon,wi,null);
 return {q,layers,frame:mod(frame,14),age};
}
function beastLayers(p,age='adult',frame=0){let kind=keyOf(p.type||p.species||'sheep');if(!M.beasts[kind])kind='sheep';if(!['baby','adult'].includes(age))age='adult';const d=M.beasts[kind].ages[age],seed=p.uid??p.id??0;const pick=(k,n,alt)=>p[k]!==undefined?mod(p[k],n):alt!==undefined?mod(alt,n):hash(seed+':'+k)%n;
 const pattern=pick('pattern',5,p.variant),crest=pick('crest',4),tail=pick('tail',4),eye=pick('eye',4),accent=pick('accent',4);const tint=M.beasts[kind].tint;
 const layers=[['tail',d.tail,tail,tint],['body',d.body,0,tint],['pattern',d.pattern,pattern,tint],['crest',d.crest,crest,tint],['accent',d.accent,accent,M.palettes.eye[accent]],['eyes',d.eyes,eye,M.palettes.eye[eye]]].map(([kind,path,row,tint])=>({kind,path,row,tint}));
 if(p.ancient||p.bloodline==='ancient')layers.push({kind:'ancient',path:d.ancient,row:0,tint:null});
 return {layers,frame:mod(frame,14),kind,age};
}
function compose(plan,hidden=[]){
 const key=JSON.stringify([plan.layers,plan.frame,hidden,revision]);if(composites.has(key))return composites.get(key);
 const out=canvas(),ctx=out.getContext('2d');ctx.imageSmoothingEnabled=false;let ready=true;
 for(const l of plan.layers){if(hidden.includes(l.kind))continue;const part=cell(l.path,l.row,plan.frame,l.tint);if(part)ctx.drawImage(part,0,0);else ready=false}
 const result={canvas:out,ready,plan};if(ready){if(composites.size>=600)composites.delete(composites.keys().next().value);composites.set(key,result)}return result
}
async function preload(plan){await Promise.all(plan.layers.map(l=>requestRow(l.path,l.row)));return compose(plan)}
global.KingdomSprites={manifest:M,identity,citizenLayers,beastLayers,compose,preload,cell,hash,get revision(){return revision},stats:()=>({images:images.size,rawRows:rawRows.size,cells:cells.size,composites:composites.size})};
})(globalThis);
