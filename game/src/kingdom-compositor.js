/* Corrected native-pixel compositor for the supplied legacy/provisional pack.
 * PNGs provide complete, preposed bodies; this does not articulate anatomy.
 * Load KINGDOM_MANIFEST and optional path -> URL KINGDOM_PNGS before this file.
 */
(function (global) {
'use strict';

const M = global.KINGDOM_MANIFEST || {};
const own = (object, key) => !!object && Object.prototype.hasOwnProperty.call(object, key);
const CELL = 144, COLUMNS = 14, ROW_BYTES = 2016 * CELL * 4, CELL_BYTES = CELL * CELL * 4;
const limits = Object.freeze({rawRows:48, cells:384, composites:256, activeLoads:1,
  pendingSheets:64, pendingRows:256, planLayers:64, diagnosticEvents:40, loadTimeoutMs:15000});
const expected = Object.freeze({
  races:['human','elf','dwarf','orc', ...['sheep','wolf','fox','deer','rabbit','boar','chicken','tortoise','bear','tiger','snake','eagle','dragon','spider','crow'].map(x => x + 'folk')],
  beasts:['sheep','wolf','deer','rabbit','boar','fox','chicken','tortoise','moonhart','emberfox','bear','tiger','snake','eagle','dragon','spider','crow'],
  classes:['civilian','warrior','tank','archer','mage','healer','rogue','bard','monk','engineer','alchemist','psychic','mime','gunslinger','hero','spellblade'],
  specialisations:['barbarian','darkKnight','dragonKnight','knight','paladin','samurai','swashbuckler','warlord','guardian','juggernaut','sniper','bowblade','beastmaster','dualRanger','trapper','magicRanger','druid','elementalist','illusionist','natureMage','necromancer','redMage','shaman','sorcerer','summoner','wizard','warlock','assassin','gambler','ninja','pirate','scout','shadow','thief','battlePriest','priest','templar','witchDoctor','dancer','champion','runeKnight','minstrel','kiMonk','artificer','chemist','psion','mimic','marksman'],
  weapons:['sword','axe','spear','lance','hammer','bow','dagger','staff','mace','lute','fists','wrench','flask','gun','orb','saber','glaive','fan','whip','flyingSword','talisman'],
  roots:['fire','water','wood','earth','metal','ice','lightning','wind','magma','mist','shadow','light','poison','blood','gravity','space','time','sound','solar','lunar','star','void','soul','dream','illusion','spirit','bone','crystal','life','death'],
  branches:['assault','control','defense','movement','cultivation','support']
});

function validateManifest(manifest = M) {
  const errors = [], add = message => { if (errors.length < 128) errors.push(message); };
  const object = value => value && typeof value === 'object' && !Array.isArray(value);
  const m = object(manifest) ? manifest : {};
  const sheets = object(m.sheets) ? m.sheets : {};
  const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const keys = (value, wanted, label) => {
    const actual = Array.isArray(value) ? value : object(value) ? Object.keys(value) : [];
    if (actual.length !== wanted.length || new Set(actual).size !== wanted.length || wanted.some(k => !actual.includes(k))) add(label + ' keys differ from the supplied pack contract');
  };
  if (m.format !== 'kingdom-modular-pixel-v1') add('Unsupported manifest format');
  if (!equal(m.cell, [CELL,CELL]) || m.columns !== COLUMNS || !equal(m.anchor, [72,130])) add('Expected 144px cells, 14 columns and anchor (72,130)');
  if (!Array.isArray(m.frameOrder) || m.frameOrder.length !== COLUMNS) add('Expected fourteen frame names');
  for (const name of Object.keys(expected)) keys(m[name], expected[name], name);
  if (m.tierCount !== 6) add('Expected six art-pack tier rows');
  for (const [path, sheet] of Object.entries(sheets)) {
    if (!/^(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_-]+\.png$/.test(path)) add('Unsafe sheet path: ' + path);
    if (!object(sheet) || !Number.isInteger(sheet.rows) || sheet.rows < 1 || sheet.rows > 64 || !equal(sheet.size, [2016,sheet.rows * CELL])) add('Invalid sheet grid: ' + path);
    if (!Array.isArray(sheet.rowKeys) || sheet.rowKeys.length !== sheet.rows) add('Invalid row keys: ' + path);
    if (typeof sheet.tintable !== 'boolean' || !Number.isInteger(sheet.colors) || sheet.colors < 1 || sheet.colors > 32 || !/^[0-9a-f]{64}$/i.test(sheet.sha256 || '')) add('Invalid sheet metadata: ' + path);
  }
  const referenced = new Set();
  function sheet(path, rows, label, tintable) {
    if (typeof path !== 'string' || !own(sheets, path)) { add('Missing sheet: ' + label); return; }
    referenced.add(path);
    const d = sheets[path];
    if (d.rows !== rows) add('Wrong row count: ' + label);
    if (tintable !== undefined && d.tintable !== tintable) add('Wrong tint mask flag: ' + label);
  }
  function paged(d, variants, label, tintable) {
    if (!object(d) || d.variantsPerPage !== 8 || d.bodyRows !== 8 || !Array.isArray(d.pages) || d.pages.length !== Math.ceil(variants / 8)) { add('Invalid page descriptor: ' + label); return; }
    d.pages.forEach((path, page) => sheet(path, Math.min(8,variants - page * 8) * 8, label + '/' + page, tintable));
  }
  const fitKeys = ['human','elf','dwarf','orc'].flatMap(fit => ['child','adult','elder'].map(age => fit + '/' + age));
  keys(m.fits, fitKeys, 'fits');
  for (const fit of fitKeys) {
    const d = m.fits?.[fit] || {};
    for (const [kind, variants, tintable] of [['eyes',4,true],['outfit',16,true],['special',48,true],['weapon',21,false],['ornament',6,false],['back',3,true],['robe',6,true]]) paged(d[kind],variants,fit + '/' + kind,tintable);
    sheet(d.citizen,8,fit + '/citizen',true); sheet(d.tunic,8,fit + '/tunic',true); sheet(d.beard,40,fit + '/beard',true);
  }
  for (const race of expected.races) {
    keys(m.races?.[race],['child','adult','elder'],race + ' ages');
    for (const age of ['child','adult','elder']) {
      const d = m.races?.[race]?.[age] || {}, fit = (race.endsWith('folk') ? 'human' : race) + '/' + age;
      if (d.fit !== fit || !own(m.fits,d.fit)) add('Invalid shared fit: ' + race + '/' + age);
      sheet(d.body,8,race + '/' + age + '/body',true); sheet(d.face,32,race + '/' + age + '/face',true);
      paged(d.hair,10,race + '/' + age + '/hair',true);
    }
  }
  for (const beast of expected.beasts) {
    const b = m.beasts?.[beast] || {};
    if (!/^#[0-9a-f]{6}$/i.test(b.tint || '')) add('Invalid beast tint: ' + beast);
    keys(b.ages,['baby','adult'],beast + ' ages');
    for (const age of ['baby','adult']) for (const [kind, rows] of [['body',1],['pattern',5],['crest',4],['tail',4],['eyes',4],['accent',4],['ancient',1]]) sheet(b.ages?.[age]?.[kind],rows,beast + '/' + age + '/' + kind,kind !== 'ancient');
  }
  keys(m.auras,expected.roots,'auras');
  for (const root of expected.roots) sheet(m.auras?.[root],1,'aura/' + root,false);
  sheet(m.tiers,6,'tiers',false);
  for (const [name,count] of [['skin',8],['orc',4],['hair',8],['eye',4],['material',4]]) {
    const p = m.palettes?.[name];
    if (!Array.isArray(p) || p.length !== count || p.some(x => !/^#[0-9a-f]{6}$/i.test(x))) add('Invalid palette: ' + name);
  }
  for (const name of ['steel','gold','leather','cloth','dragon','nature','magic']) if (!/^#[0-9a-f]{6}$/i.test(m.palettes?.class?.[name] || '')) add('Invalid class palette: ' + name);
  if (Object.keys(sheets).some(path => !referenced.has(path))) add('Manifest has unreferenced sheets');
  return {ok:errors.length === 0, errors, warnings:[
    'Legacy/provisional art: preposed whole bodies; no independent anatomical articulation.',
    'One south-facing set with horizontal mirroring; no cardinal-direction animations.',
    'Beast eye rows reuse one mask and select colour; six tiers are an art-pack limit.'
  ], counts:{races:Object.keys(m.races || {}).length, beasts:Object.keys(m.beasts || {}).length,
    gameplayClasses:(m.classes || []).filter(x => x !== 'civilian').length, sheets:Object.keys(sheets).length,
    fits:Object.keys(m.fits || {}).length, specialisations:m.specialisations?.length || 0,
    weapons:m.weapons?.length || 0, roots:m.roots?.length || 0, tiers:m.tierCount || 0}};
}
const validation = validateManifest();
const rawRows = new Map(), cells = new Map(), composites = new Map();
const images = new Map(), pendingRows = new Map(), failures = new Map(), queue = [];
const events = [], counters = Object.create(null);
let revision = 0, activeLoads = 0;
const YES = Promise.resolve(true), NO = Promise.resolve(false);
const finite = value => { const number = Number(value); return Number.isFinite(number) ? number : 0; };
const mod = (n,m) => ((Math.floor(finite(n)) % m) + m) % m;
function hash(value) { let h = 2166136261; for (const c of String(value)) h = Math.imul(h ^ c.charCodeAt(0),16777619); return h >>> 0; }
function note(code, path = '', detail = '') {
  counters[code] = (counters[code] || 0) + 1;
  const event = {code,path:String(path).slice(0,160),detail:String(detail).slice(0,160)};
  if (events.some(e => e.code === event.code && e.path === event.path && e.detail === event.detail)) return;
  events.push(event); if (events.length > limits.diagnosticEvents) events.shift();
}
function touch(cache, key) { const value = cache.get(key); if (value !== undefined) { cache.delete(key); cache.set(key,value); } return value; }
function put(cache, key, value, limit) {
  cache.delete(key); cache.set(key,value);
  while (cache.size > limit) {
    const first = cache.keys().next().value, old = cache.get(first); cache.delete(first);
    if (cache === rawRows) { old.width = 0; old.height = 0; }
  }
}
function canvas(width = CELL, height = CELL) {
  const out = global.document.createElement('canvas'); out.width = width; out.height = height; return out;
}
function rowInfo(path, row, record = true) {
  if (!validation.ok) { if (record) note('manifest-incompatible'); return null; }
  if (typeof path !== 'string' || !own(M.sheets,path)) { if (record) note('unknown-path',path); return null; }
  const value = Number(row), sheet = M.sheets[path];
  if (!Number.isInteger(value) || value < 0 || value >= sheet.rows) { if (record) note('invalid-row',path,row); return null; }
  return {path,row:value,key:path + '|' + value,sheet};
}
function markFailure(path, code, detail) {
  if (!failures.has(path)) { failures.set(path,{path,code,detail:String(detail).slice(0,160)}); note(code,path,detail); revision++; }
}
function requestRow(path, row) {
  const info = rowInfo(path,row); if (!info) return NO;
  if (rawRows.has(info.key)) { touch(rawRows,info.key); return YES; }
  if (failures.has(path)) return NO;
  if (pendingRows.has(info.key)) return pendingRows.get(info.key).promise;
  if (pendingRows.size >= limits.pendingRows || (!images.has(path) && images.size >= limits.pendingSheets)) { note('queue-capacity',path); return NO; }
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  const pending = {promise,resolve,...info}; pendingRows.set(info.key,pending);
  let entry = images.get(path);
  if (!entry) { entry = {path,rows:new Map(),image:null}; images.set(path,entry); queue.push(entry); }
  entry.rows.set(info.row,pending); pump(); return promise;
}
function pump() {
  while (activeLoads < limits.activeLoads && queue.length) {
    const entry = queue.shift(), image = new global.Image(); entry.image = image; activeLoads++;
    let settled = false, timeout;
    const finish = (code, detail) => {
      if (settled) return; settled = true; global.clearTimeout(timeout);
      if (code) markFailure(entry.path,code,detail);
      image.onload = image.onerror = null;
      for (const pending of entry.rows.values()) {
        pendingRows.delete(pending.key); pending.resolve(!code && rawRows.has(pending.key));
      }
      entry.rows.clear(); entry.image = null; images.delete(entry.path);
      image.removeAttribute('src'); activeLoads--; revision++; pump();
    };
    image.onload = () => {
      const sheet = M.sheets[entry.path];
      if (image.naturalWidth !== sheet.size[0] || image.naturalHeight !== sheet.size[1]) { finish('sheet-dimensions','Decoded dimensions differ from manifest'); return; }
      try {
        for (const pending of entry.rows.values()) {
          const strip = canvas(2016,CELL), ctx = strip.getContext('2d');
          ctx.imageSmoothingEnabled = false;
          ctx.drawImage(image,0,pending.row * CELL,2016,CELL,0,0,2016,CELL);
          put(rawRows,pending.key,strip,limits.rawRows);
        }
      } catch (error) { finish('sheet-decode',error.message); return; }
      finish();
    };
    image.onerror = () => finish('sheet-load','Image failed to load; explicit resetFailures() is required to retry');
    timeout = global.setTimeout(() => finish('sheet-timeout','Image load exceeded ' + limits.loadTimeoutMs + 'ms'),limits.loadTimeoutMs);
    counters.loadsStarted = (counters.loadsStarted || 0) + 1;
    const assets = global.KINGDOM_PNGS;
    try { image.src = assets && own(assets,entry.path) ? assets[entry.path] : entry.path; }
    catch (error) { finish('sheet-load',error.message); }
  }
}
function colorRGB(color) {
  let s = typeof color === 'string' ? color : '#b0b0b0';
  if (/^#[0-9a-f]{3}$/i.test(s)) s = '#' + s.slice(1).split('').map(x => x + x).join('');
  if (!/^#[0-9a-f]{6}$/i.test(s)) s = '#b0b0b0';
  return [1,3,5].map(i => parseInt(s.slice(i,i + 2),16));
}
function hex(rgb) { return '#' + rgb.map(v => v.toString(16).padStart(2,'0')).join(''); }
function cell(path, row, frame, color) {
  const info = rowInfo(path,row); if (!info || failures.has(path)) return null;
  const rgb = color && info.sheet.tintable ? colorRGB(color) : null;
  const key = [path,info.row,mod(frame,COLUMNS),rgb ? hex(rgb) : 'raw'].join('|');
  const cached = touch(cells,key); if (cached) return cached;
  const strip = touch(rawRows,info.key);
  if (!strip) { requestRow(path,info.row); return null; }
  const out = canvas(), ctx = out.getContext('2d',{willReadFrequently:true}); ctx.imageSmoothingEnabled = false;
  try {
    ctx.drawImage(strip,mod(frame,COLUMNS) * CELL,0,CELL,CELL,0,0,CELL,CELL);
    if (rgb) {
      const data = ctx.getImageData(0,0,CELL,CELL), pixels = data.data;
      for (let i = 0; i < pixels.length; i += 4) {
        // Capture the source shade once: replacing R must not change G/B shading.
        const shade = pixels[i];
        if (pixels[i + 3] && shade === pixels[i + 1] && shade === pixels[i + 2] && shade >= 70) {
          for (let channel = 0; channel < 3; channel++) pixels[i + channel] = Math.min(255,Math.round(rgb[channel] * shade / 176));
        }
      }
      ctx.putImageData(data,0,0);
    }
  } catch (error) { markFailure(path,'cell-read',error.message); return null; }
  put(cells,key,out,limits.cells); return out;
}

const classPal = {civilian:'cloth',warrior:'steel',tank:'steel',archer:'leather',mage:'magic',healer:'cloth',rogue:'leather',bard:'cloth',monk:'cloth',engineer:'leather',alchemist:'nature',psychic:'magic',mime:'cloth',gunslinger:'leather',hero:'gold',spellblade:'dragon'};
const defaultWeapon = {warrior:'sword',tank:'hammer',archer:'bow',mage:'staff',healer:'staff',rogue:'dagger',bard:'lute',monk:'fists',engineer:'wrench',alchemist:'flask',psychic:'orb',mime:'fists',gunslinger:'gun',hero:'sword',spellblade:'sword',civilian:'fists'};
const aliases = {'magic knight':'spellblade',magicKnight:'spellblade','vancian wizard':'wizard',vancianWizard:'wizard',elemental:'elementalist','nature mage':'natureMage','flying sword':'flyingSword','ember fox':'emberfox','moon hart':'moonhart'};
const canonical = new Map(Object.values(expected).flat().concat(Object.keys(classPal),Object.values(classPal)).map(key => [key.toLowerCase(),key]));
function keyOf(value) { if (typeof value !== 'string') return value; return own(aliases,value) ? aliases[value] : canonical.get(value.toLowerCase()) || value; }
function identity(person = {}, actor) {
  const p = person && typeof person === 'object' ? person : {};
  const q = {...p,...(p.spriteIdentity && typeof p.spriteIdentity === 'object' ? p.spriteIdentity : {}),...(p.visualIdentity && typeof p.visualIdentity === 'object' ? p.visualIdentity : {})};
  const seed = q.id ?? actor?.uid ?? actor?.id ?? 0;
  const pick = (key,n,alt) => q[key] !== undefined ? mod(q[key],n) : alt !== undefined ? mod(alt,n) : hash(seed + ':' + key) % n;
  let race = keyOf(q.race || 'human');
  if (q.speciesForm && own(M.races,keyOf(q.speciesForm) + 'folk')) race = keyOf(q.speciesForm) + 'folk';
  if (!own(M.races,race)) race = 'human';
  return {...q,race,skin:pick('skin',8),hair:pick('hair',8),style:pick('style',10),eyes:pick('eyes',4),face:pick('face',4),build:pick('build',4),
    sex:typeof q.sex === 'string' ? (q.sex.toLowerCase() === 'female' ? 1 : 0) : mod(q.sex,2),ornament:pick('ornament',6,q.acc),material:pick('material',4),seed};
}
function materialTint(base,index) {
  const rgb = colorRGB(base), material = colorRGB(M.palettes.material[index]);
  return hex(rgb.map((v,i) => Math.round(v * .80 + material[i] * .20)));
}
function paged(d,variant,body) { return [d.pages[Math.floor(variant / d.variantsPerPage)],(variant % d.variantsPerPage) * d.bodyRows + body]; }
function incompatiblePlan(frame) { return {layers:[],frame:mod(frame,COLUMNS),warnings:['Incompatible sprite manifest'],invalid:true}; }
function citizenLayers(person = {}, age = 'adult', frame = 0, color = '#6d91ad', actor = null) {
  if (!validation.ok) return incompatiblePlan(frame);
  const q = identity(person,actor), warnings = [];
  if (!own(M.races[q.race],age)) age = 'adult';
  const race = M.races[q.race][age], fit = M.fits[race.fit], body = q.sex * 4 + q.build;
  let cls = keyOf(q.cls || q.class || 'civilian');
  if (!M.classes.includes(cls)) { warnings.push('Unknown class uses civilian outfit: ' + String(cls)); cls = 'civilian'; }
  const classIndex = M.classes.indexOf(cls), palette = keyOf(q.palette || q.outfitPalette || classPal[cls] || 'cloth');
  const outfit = materialTint(M.palettes.class[palette] || M.palettes.class.cloth,q.material);
  const fur = q.race.endsWith('folk') ? (M.beasts[q.race.slice(0,-4)]?.tint || '#a99b83') : null;
  const skin = q.race === 'orc' ? M.palettes.orc[q.skin % 4] : fur || M.palettes.skin[q.skin];
  const hair = M.palettes.hair[q.hair], eye = M.palettes.eye[q.eyes], layers = [];
  const add = (kind,path,row,tint) => layers.push({kind,path,row,tint});
  const pg = (kind,d,v,tint) => add(kind,...paged(d,v,body),tint);
  const root = keyOf(q.elementRoot || q.root || q.cultivation?.root), branch = keyOf(q.branch || q.cultivation?.branch), branchIndex = M.branches.indexOf(branch);
  if (branchIndex >= 0) {
    add('tier',M.tiers,Math.max(0,Math.min(5,Math.floor(finite(q.cultivationTier ?? q.cultivation?.tier ?? q.tier ?? 1)) - 1)),null);
    if (own(M.auras,root)) add('aura',M.auras[root],0,null);
  }
  const back = q.back;
  let backIndex = back === 'quiver' ? 1 : back === 'banner' ? 2 : back === 'cape' ? 0 : cls === 'archer' ? 1 : ['mage','hero','spellblade'].includes(cls) ? 0 : -1;
  if (q.cape) backIndex = 0;
  if (backIndex >= 0) pg('back',fit.back,backIndex,color);
  add('body',race.body,body,skin); pg('outfit',fit.outfit,classIndex,outfit);
  if (cls === 'civilian') add('tunic',fit.tunic,body,color);
  if (branchIndex >= 0) pg('robe',fit.robe,branchIndex,color);
  const specIndex = M.specialisations.indexOf(keyOf(q.spec || q.specialisation));
  if (specIndex >= 0) pg('special',fit.special,specIndex,outfit);
  add('face',race.face,q.face * 8 + body,skin); pg('eyes',fit.eyes,q.eyes,eye); pg('hair',race.hair,q.style,hair);
  const beard = q.beard !== undefined ? mod(q.beard,5) : q.race === 'dwarf' ? 1 + q.style % 4 : q.race === 'human' && !q.sex && age !== 'child' && q.style % 3 === 0 ? 1 + q.style % 4 : 0;
  if (beard) add('beard',fit.beard,beard * 8 + body,hair);
  pg('ornament',fit.ornament,q.ornament,null);
  const weapon = keyOf(typeof q.weapon === 'string' ? q.weapon : q.gear?.weapon?.type || defaultWeapon[cls]), wi = M.weapons.indexOf(weapon);
  if (wi >= 0 && (cls !== 'civilian' || typeof q.weapon === 'string')) pg('weapon',fit.weapon,wi,null);
  return {q,layers,frame:mod(frame,COLUMNS),age,cls,warnings};
}
function beastLayers(person = {}, age = 'adult', frame = 0) {
  if (!validation.ok) return incompatiblePlan(frame);
  const p = person && typeof person === 'object' ? person : {}, warnings = [];
  let kind = keyOf(p.type || p.species || 'sheep');
  if (!own(M.beasts,kind)) { warnings.push('Unknown beast uses sheep: ' + String(kind)); kind = 'sheep'; }
  if (!['baby','adult'].includes(age)) age = 'adult';
  const d = M.beasts[kind].ages[age], seed = p.uid ?? p.id ?? 0;
  const pick = (key,n,alt) => p[key] !== undefined ? mod(p[key],n) : alt !== undefined ? mod(alt,n) : hash(seed + ':' + key) % n;
  const pattern = pick('pattern',5,p.variant), crest = pick('crest',4), tail = pick('tail',4), eye = pick('eye',4), accent = pick('accent',4), tint = M.beasts[kind].tint;
  const layers = [['tail',d.tail,tail,tint],['body',d.body,0,tint],['pattern',d.pattern,pattern,tint],['crest',d.crest,crest,tint],['accent',d.accent,accent,M.palettes.eye[accent]],['eyes',d.eyes,eye,M.palettes.eye[eye]]].map(([kind,path,row,tint]) => ({kind,path,row,tint}));
  if (p.ancient || p.bloodline === 'ancient') layers.push({kind:'ancient',path:d.ancient,row:0,tint:null});
  return {layers,frame:mod(frame,COLUMNS),kind,age,warnings};
}
function validPlan(plan) { return !!plan && !plan.invalid && Array.isArray(plan.layers) && plan.layers.length > 0 && plan.layers.length <= limits.planLayers; }
function compose(plan, hidden = []) {
  if (!validPlan(plan)) { note('invalid-plan'); return {canvas:canvas(),ready:false,failed:true,failures:[{code:'invalid-plan'}],pending:0,plan}; }
  const hide = new Set(Array.isArray(hidden) ? hidden : []), visible = plan.layers.filter(layer => layer && !hide.has(layer.kind));
  const key = JSON.stringify([visible.map(l => [l.path,l.row,l.tint || null]),mod(plan.frame,COLUMNS)]);
  const cached = touch(composites,key); if (cached) return {...cached,plan};
  // Allocate only after a cache miss: active worlds reuse completed composites.
  const out = canvas(), ctx = out.getContext('2d'); ctx.imageSmoothingEnabled = false;
  const errors = []; let pending = 0;
  for (const layer of visible) {
    const info = rowInfo(layer.path,layer.row);
    if (!info) { errors.push({kind:layer.kind,path:layer.path,code:'invalid-layer'}); continue; }
    const part = cell(layer.path,layer.row,plan.frame,layer.tint);
    if (part) ctx.drawImage(part,0,0);
    else if (failures.has(layer.path)) errors.push({kind:layer.kind,...failures.get(layer.path)});
    else pending++;
  }
  const result = {canvas:out,ready:errors.length === 0 && pending === 0,failed:errors.length > 0,failures:errors,pending,plan};
  if (result.ready) put(composites,key,{...result,plan:null},limits.composites);
  return result;
}
async function preload(plan) {
  // Extract cells as their strips arrive, before unrelated decoded rows evict them.
  // requestRow coalesces shared strip requests, including different tinted cells.
  if (validPlan(plan)) await Promise.all(plan.layers.filter(Boolean).map(async layer => {
    if (await requestRow(layer.path,layer.row)) cell(layer.path,layer.row,plan.frame,layer.tint);
  }));
  return compose(plan);
}
function resetFailures(paths) {
  const selected = paths === undefined ? [...failures.keys()] : typeof paths === 'string' ? [paths] : Array.isArray(paths) ? paths : [];
  let cleared = 0;
  for (const path of selected) if (failures.delete(path)) { cleared++; for (const key of [...rawRows.keys()]) if (key.startsWith(path + '|')) { const row = rawRows.get(key); rawRows.delete(key); row.width = row.height = 0; } }
  if (cleared) revision++;
  return cleared;
}
function stats() {
  return {images:images.size,rawRows:rawRows.size,cells:cells.size,composites:composites.size,
    activeLoads,queued:queue.length,pendingRows:pendingRows.size,failedSheets:failures.size,
    cacheBytes:rawRows.size * ROW_BYTES + (cells.size + composites.size) * CELL_BYTES,
    maxCacheBytes:limits.rawRows * ROW_BYTES + (limits.cells + limits.composites) * CELL_BYTES};
}
global.KingdomSprites = {manifest:M,identity,citizenLayers,beastLayers,compose,preload,cell,hash,
  get revision() { return revision; },stats,limits,validateManifest,resetFailures,
  diagnostics:() => ({compatible:validation.ok,artStatus:'legacy/provisional',validation:validateManifest(),
    counters:{...counters},failures:[...failures.values()].map(x => ({...x})),events:events.map(x => ({...x})),stats:stats()})};
})(globalThis);
