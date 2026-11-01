/* Tiny World v79 — Provisional Sect Art Update 01.
   Only the approved PixelLab PNGs can draw sect-style replacements. The
   captured v79 core building renderer supplies every unrepresented slot. */
(function(){
  'use strict';
  const SOURCE=window.TW_SECT_PIXEL_PNGS||{},BOX=window.TW_SECT_PIXEL_BOXES||{};
  const originalDeveloped=window.TW79_CORE_DEVELOPED_ARCHITECTURE;
  const originalArchitecture=window.TW79_CORE_ARCHITECTURE_SPRITE;
  if(typeof originalDeveloped!=='function'||typeof originalArchitecture!=='function')throw Error('v79 default architecture was not captured');
  const pixelAssets=Object.create(null),states=Object.create(null),assetDrawn=Object.create(null),drawn=[0,0,0],terrainDrawn=[0,0,0],fallback=[0,0,0],defaultDrawn=Array(30).fill(0),legacy={sprite:0,terrain:0};
  const allowed={0:{sectHall:'citadel-hall-a',sectGate:'citadel-gatehouse'},
                 1:{sectHall:'sky-monastery-hall-a'},
                 2:{sectHall:'iron-foundry-hall-a',tower:'iron-foundry-furnace-tower',blacksmith:'iron-foundry-workshop'}};
  const required=['citadel-hall-a','citadel-gatehouse','citadel-mountain',
                  'sky-monastery-hall-a','sky-monastery-peak','sky-monastery-bridge',
                  'iron-foundry-hall-a','iron-foundry-furnace-tower','iron-foundry-workshop'];
  if(Object.keys(SOURCE).length!==required.length||required.some(key=>!SOURCE[key]||!BOX[key]))throw Error('The approved nine-PNG PixelLab bundle is incomplete');
  for(const key of required){
    const im=new Image();states[key]='loading';assetDrawn[key]=0;pixelAssets[key]=im;
    im.onload=()=>{states[key]='ready';G._ix=null;};
    im.onerror=()=>{states[key]='error';console.error('PixelLab sect PNG could not load:',key)};
    im.src=SOURCE[key];
  }
  const defaultCache=new Map();
  function coreSprite(type,level=0,variant=0){
    const key=type+'|'+(level|0)+'|'+(variant|0);
    if(defaultCache.has(key))return defaultCache.get(key);
    const previous=architectureSprite;
    let image;
    try{
      architectureSprite=originalArchitecture;
      image=originalDeveloped(type,'tw79-release-default',level|0,variant|0);
    }finally{architectureSprite=previous}
    defaultCache.set(key,image);return image;
  }
  function drawDefault(pen,type,i,z){
    const x=i%G.W,y=i/G.W|0,[w,,h]=PLOTS[type]||PLOTS.house;
    const level=G.state?.structures?.[i]?.level||0;
    const image=coreSprite(type,level,i%2);
    pen.save();pen.imageSmoothingEnabled=false;
    pen.drawImage(image,(x+.5-w/2)*z,(y+1-h)*z,w*z,h*z);
    pen.restore();
  }
  let indexState=null,indexTime=-1,indexSize=-1,sectBuildings=new Map();
  function rebuildIndex(){
    const state=G.state?.sects,buildingSize=G.bld.size;
    if(state===indexState&&indexTime===G.time&&indexSize===buildingSize)return;
    indexState=state;indexTime=G.time;indexSize=buildingSize;sectBuildings=new Map();
    for(const sect of Object.values(state||{})){
      const mt=sect?.mt,id=mt?.sectStyle;
      if(!Number.isInteger(id)||id<0||id>29)continue;
      for(const room of mt.rooms||[])if(Number.isInteger(room.i)&&G.bld.get(room.i)===room.type)
        sectBuildings.set(room.i,id);
    }
  }
  function sectId(i){rebuildIndex();return sectBuildings.get(i)}
  function isSectMarker(race){return typeof race==='string'&&/^(?:sect(?:style|snow)?|v73:)/.test(race)}
  function drawPixel(pen,key,i,z){
    if(states[key]!=='ready')return false;
    const image=pixelAssets[key],b=BOX[key];
    if(image.naturalWidth!==b.canvas[0]||image.naturalHeight!==b.canvas[1]){states[key]='error';return false}
    const [sx,sy,right,bottom]=b.visible,sw=right-sx,sh=bottom-sy;
    const type=G.bld.get(i),[plotW,,plotH]=PLOTS[type]||PLOTS.house;
    // Crop transparent padding only. Every remaining source pixel retains its
    // native aspect and material colours; zoom uses nearest-neighbour sampling.
    const uniform=Math.min(1,plotW*32/sw,plotH*32/sh),w=sw*uniform*z/32,h=sh*uniform*z/32;
    const x=(i%G.W+.5)*z,y=(i/G.W|0)+1;
    pen.save();pen.imageSmoothingEnabled=false;
    pen.drawImage(image,sx,sy,sw,sh,Math.round(x-w/2),Math.round(y*z-h),Math.round(w),Math.round(h));
    pen.restore();assetDrawn[key]++;return true;
  }
  function drawRidge(pen,key,m,z){
    if(states[key]!=='ready')return false;
    const image=pixelAssets[key],b=BOX[key];
    if(image.naturalWidth!==b.canvas[0]||image.naturalHeight!==b.canvas[1]){states[key]='error';return false}
    const [sx,sy,right,bottom]=b.visible,sw=right-sx,sh=bottom-sy;
    // Seat the approved peak behind the real summit. Its ground contact stays
    // above the walkable summit row, so it cannot visually replace a path.
    const w=sw*z/32,h=sh*z/32,x=(m.cx+.5)*z,y=(m.top+.5)*z;
    pen.save();pen.imageSmoothingEnabled=false;
    pen.drawImage(image,sx,sy,sw,sh,Math.round(x-w/2),Math.round(y-h),Math.round(w),Math.round(h));
    pen.restore();assetDrawn[key]++;return true;
  }
  const priorBuilding=raceBuilding;
  raceBuilding=function(pen,type,i,z){
    const id=sectId(i);
    if(id===undefined){
      if(isSectMarker(G.state?.buildingStyles?.[i]))return drawDefault(pen,type,i,z);
      return priorBuilding(pen,type,i,z);
    }
    const key=allowed[id]?.[type];
    if(key&&drawPixel(pen,key,i,z)){drawn[id]++;return}
    if(id<3)fallback[id]++;
    defaultDrawn[id]++;
    return drawDefault(pen,type,i,z);
  };
  // The older 30-style generator and sect-specific tint route are blocked even
  // when a settings toggle, legacy save marker, or direct renderer calls reach
  // them. Town, creature and gameplay renderers retain their existing routes.
  const priorDeveloped=developedArchitecture,priorArchitecture=architectureSprite;
  developedArchitecture=function(type,race,level,variant=0){
    if(isSectMarker(race)){legacy.sprite++;return coreSprite(type,level,variant)}
    return priorDeveloped(type,race,level,variant);
  };
  architectureSprite=function(type,race,variant=0){
    if(isSectMarker(race)){legacy.sprite++;return coreSprite(type,0,variant)}
    return priorArchitecture(type,race,variant);
  };
  tw7423SectSprite=function(type,snow,variant,style){legacy.sprite++;return coreSprite(type,0,variant)};
  tw65Sprite=function(type,snow,variant){legacy.sprite++;return coreSprite(type,0,variant)};
  // Real mountain tiles, saved room layouts and pathfinding remain untouched.
  // Reject the procedural overlay. Two approved ridge sprites fit behind their
  // real summit; the bridge is reserved until a matching walkable span exists.
  tw64Draw=function(pen,sect,z,view){
    legacy.terrain++;
    const m=sect.mt,id=m?.sectStyle;
    if(!m||id!==0&&id!==1||m.b[2]<view.x0||m.b[0]>view.x1||m.b[3]<view.y0||m.b[1]>view.y1)return;
    const key=id===0?'citadel-mountain':'sky-monastery-peak';
    if(drawRidge(pen,key,m,z))terrainDrawn[id]++;
  };
  window.TinyWorldSectArt=Object.freeze({
    release:'Tiny World v79 — Provisional Sect Art Update 01',approvedSectIds:Object.freeze([0,1,2]),
    assetNames:Object.freeze(required.slice()),
    get ready(){return required.every(key=>states[key]==='ready')},
    sectIdForBuilding:(i)=>sectId(i),
    snapshot:()=>({loaded:Object.fromEntries(required.map(key=>[key,states[key]])),assetDrawn:{...assetDrawn},
                   drawn:drawn.slice(),terrainDrawn:terrainDrawn.slice(),fallback:fallback.slice(),defaultDrawn:defaultDrawn.slice(),
                   blockedLegacySpriteCalls:legacy.sprite,blockedLegacyTerrainCalls:legacy.terrain,
                   defaultForUnrepresented:true,source:'approved PixelLab PNG masters'})
  });
})();
