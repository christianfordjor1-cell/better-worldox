/* Sheet-based visual adapter: leaves spawn, biology, combat and saved identities intact. */
const layeredArt=globalThis.KingdomSprites;
const legacyLayeredSprite=G.sprite,legacyLayeredHuman=humanSprite;
function layeredAge(p,c){return c?(c.age<adultAge(c)?'child':c.age>elderAge(c)?'elder':'adult'):'adult'}
function layeredFrame(c,g){
 if(c.hp<=0)return 10;if(c.hurtUntil>g.time)return 9;if(c.attack)return 7;
 const act=String(c.action||'').toLowerCase();if(c.practice||/cast|cultivat|meditat|heal|build|gather|harvest|quarr|repair|craft|work/.test(act))return 11+Math.floor(g.time/2)%3;
 const moving=Math.abs((c.rx??c.x)-c.x)+Math.abs((c.ry??c.y)-c.y)>.06;
 return moving&&!g.paused?1+Math.floor(g.time/2+(c.uid||c.id||0))%6:Math.floor(g.time/12+(c.uid||c.id||0))%6===0?8:0
}
G.sprite=function(p,stage,frame,color){const age=['child','adult','elder'][stage]||'adult',plan=layeredArt.citizenLayers(p,age,frame,color),result=layeredArt.compose(plan);return result.ready?result.canvas:legacyLayeredSprite.call(this,p,stage,frame,color)};
humanSprite=function(ctx,c,z,g){
 if(c.inDungeon||c.embarked)return;const p=g.person(c);if(!p)return;
 const kingdom=g.state.kings?.[c.k],color=kingdom?.color||TUN[p.tun]||'#729aab',age=layeredAge(p,c),frame=layeredFrame(c,g),plan=layeredArt.citizenLayers(p,age,frame,color,c),result=layeredArt.compose(plan);
 if(!result.ready){legacyLayeredHuman(ctx,c,z,g);return}
 const P=g.px||2,unit=Math.max(P,Math.floor(z/4/P)*P),scale=unit/10,side=Math.round(144*scale),cx=Math.round(((c.rx??c.x)+.5)*z),ground=Math.round(((c.ry??c.y)+1)*z);
 const moving=Math.abs((c.rx??c.x)-c.x)>.06;if(moving)c.facing=c.x>(c.rx??c.x)?1:-1;
 ctx.save();ctx.imageSmoothingEnabled=false;ctx.translate(cx,ground);if((c.facing||1)<0)ctx.scale(-1,1);ctx.drawImage(result.canvas,Math.round(-side/2),-Math.round(130*scale),side,side);ctx.restore();
 if(kingdom?.ruler===c.id&&z>6){ctx.fillStyle='#e7c76b';const yy=ground-Math.round((age==='child'?78:113)*scale);ctx.fillRect(cx-4,yy,8,2);ctx.fillRect(cx-4,yy-3,2,3);ctx.fillRect(cx-1,yy-4,2,4);ctx.fillRect(cx+2,yy-3,2,3)}
 if(g.state.sel===c.id){ctx.strokeStyle='#e7c76b';ctx.lineWidth=1;ctx.strokeRect(cx-Math.round(28*scale),ground-Math.round((age==='child'?75:112)*scale),Math.round(56*scale),Math.round((age==='child'?75:112)*scale))}
};
for(const kind of Object.keys(layeredArt.manifest.beasts)){
 const def=G.creatures[kind];if(!def)continue;const legacy=def.sprite;
 def.sprite=function(ctx,c,z,g){const age=c.age<(SPECIES[kind]?.mature??400)?'baby':'adult',plan=layeredArt.beastLayers(c,age,layeredFrame(c,g)),result=layeredArt.compose(plan);if(!result.ready){if(legacy)legacy(ctx,c,z,g);return}
 const side=Math.max(12,Math.round(z*1.9)),scale=side/144,cx=Math.round(((c.rx??c.x)+.5)*z),ground=Math.round(((c.ry??c.y)+1)*z);ctx.save();ctx.imageSmoothingEnabled=false;ctx.translate(cx,ground);if((c.facing||1)<0)ctx.scale(-1,1);ctx.drawImage(result.canvas,-Math.round(side/2),-Math.round(130*scale),side,side);ctx.restore()};
}
// Render inspector portraits at a uniform pixel aspect ratio after legacy UI updates.
const layeredRenderInfo=renderInfo;renderInfo=function(g){layeredRenderInfo(g);const portrait=document.getElementById('pt'),p=g.state.people?.[g.state.sel];if(!portrait||!p)return;const c=g.find(p.id),result=layeredArt.compose(layeredArt.citizenLayers(p,layeredAge(p,c),0,g.state.kings?.[c?.k]?.color||'#729aab',c));if(!result.ready)return;const ctx=portrait.getContext('2d'),side=Math.min(portrait.width,portrait.height);ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,portrait.width,portrait.height);ctx.drawImage(result.canvas,Math.round((portrait.width-side)/2),Math.round((portrait.height-side)/2),side,side)};
// Existing compact-art preference is superseded by this atlas adapter.
globalThis.TinyWorldLayeredArt={frame:layeredFrame,age:layeredAge,compositor:layeredArt};
