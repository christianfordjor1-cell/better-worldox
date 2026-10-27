/* Tiny World visual anatomy contract, version 1.
 * This describes compatibility; it does not create artwork or gameplay species.
 * Current Cursor PNGs are preposed overlays, not articulated anatomical parts.
 */
(function (global) {
'use strict';
const CELL = [144,144], ANCHOR = [72,130];
const FRAMES = ['idle','walk_contact_l','walk_down_l','walk_pass_l','walk_contact_r','walk_down_r','walk_pass_r','attack','idle_alt','hurt','death','work_1','cast_2','work_cast_3'];
const raceNames = ['human','elf','dwarf','orc','sheepfolk','wolffolk','foxfolk','deerfolk','rabbitfolk','boarfolk','chickenfolk','tortoisefolk','bearfolk','tigerfolk','snakefolk','eaglefolk','dragonfolk','spiderfolk','crowfolk'];
const beastNames = ['sheep','wolf','deer','rabbit','boar','fox','chicken','tortoise','moonhart','emberfox','bear','tiger','snake','eagle','dragon','spider','crow'];
const plans = {
  biped: ['torso','pelvis','head','armLeft','armRight','handLeft','handRight','legLeft','legRight','footLeft','footRight'],
  quadruped: ['torso','pelvis','head','legFrontLeft','legFrontRight','legRearLeft','legRearRight'],
  avian: ['torso','head','wingLeft','wingRight','legLeft','legRight','footLeft','footRight','tail'],
  serpentine: ['head','neck','bodySegment','tail'],
  arachnid: ['cephalothorax','abdomen',...Array.from({length:8},(_,i) => 'leg' + (i+1))],
  dragon: ['torso','pelvis','head','neck','wingLeft','wingRight','legFrontLeft','legFrontRight','legRearLeft','legRearRight','tail']
};
const attachments = {
  human:['hair','ears'], elf:['hair','pointedEars'], dwarf:['hair','beard','ears'], orc:['hair','ears','tusks'],
  sheep:['muzzle','ears','horns','tail','fur'], wolf:['muzzle','ears','tail','fur'], fox:['muzzle','ears','tail','fur'],
  deer:['muzzle','ears','antlers','tail','fur'], rabbit:['muzzle','ears','tail','fur'], boar:['muzzle','ears','tusks','tail','fur'],
  chicken:['beak','crest','wingLeft','wingRight','tail','feathers'], tortoise:['shell','tail','scales'],
  bear:['muzzle','ears','tail','fur'], tiger:['muzzle','ears','tail','fur','pattern'],
  snake:['forkedTongue','tail','scales','pattern'], eagle:['beak','wingLeft','wingRight','tail','feathers','talons'],
  dragon:['horns','crest','wingLeft','wingRight','tail','scales','pattern'],
  spider:['mandibles','eyes','spinnerets','extraLimbs'], crow:['beak','wingLeft','wingRight','tail','feathers','talons'],
  moonhart:['muzzle','ears','antlers','tail','fur','luminousMarkings'], emberfox:['muzzle','ears','tail','fur','emberMarkings']
};
const channels = {
  race: {skin:8,hair:8,style:10,eyes:4,face:4,build:4,ornament:6,material:4},
  beast: {pattern:5,crest:4,eye:4,accent:4,tail:4}
};
const renderOrder = ['tier','aura','wingBack','tailBack','extraLimbsBack','back','legRearLeft','legRearRight','legLeft','legRight','footLeft','footRight','pelvis','torso','bodySegment','shell','outfit','armLeft','armRight','handLeft','handRight','neck','head','muzzle','beak','face','eyes','ears','horns','crest','hair','beard','pattern','ornament','weapon','wingFront','extraLimbsFront','tailFront','effects'];
const own = (object,key) => !!object && Object.prototype.hasOwnProperty.call(object,key);
const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
function freeze(value) { if(value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; }
function hash(value) { let n=2166136261; for(const c of String(value)) n=Math.imul(n ^ c.charCodeAt(0),16777619); return n>>>0; }
function bodyPlans(kind,species) {
  const base = species.replace(/folk$/,'');
  if(kind === 'race') {
    // These are supported future contracts, not claims about the existing design.
    if(base === 'snake') return ['biped','serpentine'];
    if(base === 'spider') return ['biped','arachnid'];
    return ['biped'];
  }
  if(base === 'snake') return ['serpentine'];
  if(base === 'spider') return ['arachnid'];
  if(['chicken','eagle','crow'].includes(base)) return ['avian'];
  if(base === 'dragon') return ['dragon'];
  return ['quadruped'];
}
function catalogEntry(kind,species) {
  const base = species.replace(/folk$/,'');
  return {
    species, kind, ages:kind === 'race' ? ['child','adult','elder'] : ['baby','adult'],
    bodyPlans:bodyPlans(kind,species), attachments:attachments[base] || [],
    motion:kind === 'race' ? ['bipedWalk','speciesExtensions'] : base === 'snake' ? ['slither'] : base === 'spider' ? ['eightLegWalk'] : ['chicken','eagle','crow'].includes(base) ? ['birdWalk','flight'] : base === 'dragon' ? ['quadrupedWalk','flight'] : ['quadrupedWalk'],
    artworkStatus:'provisional working artwork',
    splitAnatomyStatus:'missing artwork',
    note:kind === 'race' && species.endsWith('folk') ? 'Supplied outfits share human fits. Species-specific independently split anatomy is unfinished.' : 'Supplied body sheet contains preposed anatomy; individual limbs are not separately supplied.'
  };
}
const catalog = {
  races:Object.fromEntries(raceNames.map(name => [name,catalogEntry('race',name)])),
  beasts:Object.fromEntries(beastNames.map(name => [name,catalogEntry('beast',name)]))
};
function entry(kind,species) { return (kind === 'race' ? catalog.races : kind === 'beast' ? catalog.beasts : {})[species]; }
function deriveAppearance(kind,seed,saved = {}) {
  const ranges = channels[kind];
  if(!ranges) throw new TypeError('Appearance kind must be race or beast');
  const result = {}, missing = [];
  for(const [name,count] of Object.entries(ranges)) {
    const value = saved && saved[name];
    if(Number.isInteger(value) && value >= 0 && value < count) result[name] = value;
    else { result[name] = hash(String(seed) + ':' + kind + ':' + name) % count; missing.push(name); }
  }
  // A snapshot only: the caller's save object is never filled or rewritten.
  return {seed,values:result,derived:missing};
}
function capability(kind,species,manifest = global.KINGDOM_MANIFEST) {
  const spec = entry(kind,species);
  if(!spec) return {supported:false,kind,species,reason:'Unknown species contract'};
  const supplied = kind === 'race' ? manifest?.races?.[species] : manifest?.beasts?.[species]?.ages;
  const independentLayers = kind === 'race' ? ['body','face','eyes','hair','beard','outfit','tunic','robe','special','back','ornament','weapon'] : ['body','tail','pattern','crest','accent','eyes','ancient'];
  return {
    supported:true,kind,species,contract:spec,assetPresent:!!supplied,
    artworkStatus:spec.artworkStatus,bodyIsPreposed:true,anatomicalModularity:false,
    independentlySuppliedLayers:supplied ? independentLayers : [],
    missingAnatomicalParts:[...new Set(spec.bodyPlans.flatMap(plan => plans[plan]).concat(spec.attachments).filter(name => !(kind === 'race' ? ['hair','beard','eyes'] : ['eyes','tail','crest','pattern']).includes(name)))],
    sharedHumanFit:kind === 'race' && species.endsWith('folk'),
    directions:['threeQuarterSouth','mirrorHorizontal'],
    frameNames:supplied ? [...FRAMES] : [],
    animationQuality:'Slots exist; species-specific gait quality requires visual review.',
    colourChannels:kind === 'race' ? ['skin','hair','eyes','outfit','kingdomCloth','material'] : ['body','pattern','crest','tail','accent','eyes']
  };
}
function validatePart(part,context = {}) {
  const errors = [], warnings = [], fail = (code,message) => errors.push({code,message});
  if(!part || typeof part !== 'object' || Array.isArray(part)) return {ok:false,errors:[{code:'part',message:'Part metadata must be an object'}],warnings};
  const kind = context.kind || part.kind, species = context.species || part.species, spec = entry(kind,species);
  if(!spec) fail('species','Choose a registered race or beast anatomy contract');
  if(part.kind !== kind || part.species !== species) fail('species-fit','Part is for a different species contract');
  if(!same(part.cell,CELL)) fail('cell','Part must use a 144 × 144 cell');
  if(!same(part.anchor,ANCHOR)) fail('anchor','Part must use body centre 72 and ground anchor 130');
  if(!same(part.frames,FRAMES)) fail('frames','Part must declare the same fourteen pose names in order');
  if(!spec?.ages.includes(part.age) || (context.age && part.age !== context.age)) fail('age','Part age does not match the assembly');
  if(!spec?.bodyPlans.includes(part.bodyPlan) || (context.bodyPlan && part.bodyPlan !== context.bodyPlan)) fail('body-plan','Part body plan does not match the species and assembly');
  if(typeof part.fit !== 'string' || !part.fit || (context.fit && context.fit !== part.fit)) fail('fit','Part fit must match the assembly fit');
  if(typeof part.slot !== 'string' || !part.slot) fail('slot','Part must name its anatomical or overlay slot');
  const allowedSlots = new Set([...(plans[part.bodyPlan] || []),...(spec?.attachments || []),'tier','aura','back','outfit','face','eyes','hair','beard','ornament','weapon','effects','pattern','completeBody','faceOverlay','hairOverlay','ancient','accent','citizen','tunic','robe','special']);
  if(spec?.attachments.includes('tail')) { allowedSlots.add('tailBack'); allowedSlots.add('tailFront'); }
  if(spec?.attachments.includes('wingLeft')) { allowedSlots.add('wingBack'); allowedSlots.add('wingFront'); }
  if(spec?.attachments.includes('extraLimbs')) { allowedSlots.add('extraLimbsBack'); allowedSlots.add('extraLimbsFront'); }
  if(!allowedSlots.has(part.slot)) fail('slot','Slot is not supported by this anatomy contract');
  if(part.sex !== undefined && context.sex !== undefined && part.sex !== context.sex) fail('sex-fit','Part sex/body-row does not match');
  if(part.build !== undefined && context.build !== undefined && part.build !== context.build) fail('build-fit','Part build does not match');
  if(part.status && !['approved production artwork','provisional working artwork','legacy artwork','missing artwork'].includes(part.status)) fail('status','Unknown artwork status');
  if(part.status === 'missing artwork') fail('missing-art','Missing artwork cannot be assembled');
  if(part.slot === 'completeBody') warnings.push({code:'preposed-body',message:'This is a complete preposed body, not independent anatomical limbs'});
  if(part.bodyPlan && part.slot !== 'completeBody' && part.slot !== 'bodySegment' && part.instances !== undefined && part.instances !== 1) fail('instances','Use explicit named slots for independently attached limbs');
  for(const [name,coordinates] of Object.entries(part.sockets || {})) {
    if(!Array.isArray(coordinates) || coordinates.length !== FRAMES.length || coordinates.some(p => !Array.isArray(p) || p.length !== 2 || p.some(n => !Number.isInteger(n) || n < 0 || n >= 144))) fail('socket','Socket ' + name + ' must have fourteen native-pixel coordinate pairs');
  }
  if(part.mount && (typeof part.mount.parent !== 'string' || typeof part.mount.socket !== 'string' || typeof part.mount.socketOnPart !== 'string')) fail('mount','Mount needs parent part id, parent socket and socketOnPart');
  return {ok:errors.length === 0,errors,warnings};
}
function validateAssembly(parts,context = {}) {
  const errors = [], warnings = [], fail = (code,message) => errors.push({code,message});
  if(!Array.isArray(parts) || !parts.length) return {ok:false,errors:[{code:'parts',message:'Assembly needs an array of usable parts'}],warnings};
  const inferred = {...parts[0],...context}, byId = new Map(), slots = new Map();
  parts.forEach((part,index) => {
    const result = validatePart(part,inferred);
    result.errors.forEach(error => errors.push({...error,part:part?.id ?? index}));
    result.warnings.forEach(error => warnings.push({...error,part:part?.id ?? index}));
    if(!part || typeof part !== 'object') return;
    if(typeof part.id !== 'string' || !part.id || byId.has(part.id)) fail('part-id','Each part must have a unique id');
    else byId.set(part.id,part);
    if(slots.has(part.slot)) fail('duplicate-slot','Multiple parts occupy slot ' + part.slot);
    else slots.set(part.slot,part);
  });
  if(slots.has('completeBody')) {
    const anatomical = plans[inferred.bodyPlan] || [];
    if(anatomical.some(slot => slots.has(slot))) fail('body-overlap','Do not layer split body anatomy over a complete body');
    if(context.requireSplitAnatomy) fail('split-anatomy','A complete preposed body cannot satisfy independent anatomy');
  } else {
    for(const slot of plans[inferred.bodyPlan] || []) if(!slots.has(slot)) fail('missing-slot','Missing anatomical slot ' + slot);
  }
  for(const part of parts.filter(p => p && p.mount)) {
    const parent = byId.get(part.mount.parent), parentSocket = parent?.sockets?.[part.mount.socket], childSocket = part.sockets?.[part.mount.socketOnPart];
    if(!parent || !parentSocket || !childSocket) fail('mount-socket','Attachment ' + part.id + ' references an absent socket or parent');
    else if(!same(parentSocket,childSocket)) fail('socket-alignment','Attachment ' + part.id + ' does not align to its parent in all fourteen poses');
    const seen = new Set([part.id]); let cursor = parent;
    while(cursor?.mount) { if(seen.has(cursor.id)) { fail('mount-cycle','Attachment ancestry contains a cycle'); break; } seen.add(cursor.id); cursor = byId.get(cursor.mount.parent); }
  }
  return {ok:errors.length === 0,errors,warnings,anatomicalModularity:!slots.has('completeBody'),bodyPlan:inferred.bodyPlan};
}
global.TinyWorldAnatomy = freeze({version:'tiny-world-anatomy-v1',cell:CELL,anchor:ANCHOR,frameOrder:FRAMES,catalog,bodyPlans:plans,appearanceChannels:channels,renderOrder,deriveAppearance,capability,validatePart,validateAssembly});
})(globalThis);
