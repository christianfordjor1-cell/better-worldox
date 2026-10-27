from PIL import Image,ImageDraw,ImageChops
from pathlib import Path
import math,json,hashlib,zipfile,shutil,time
OUT=Path('/workspace/output/kingdom-sprites');OUT.mkdir(parents=True,exist_ok=True)
CELL=144;FRAMES=14
RACES=['human','elf','dwarf','orc']+[s+'folk' for s in ['sheep','wolf','fox','deer','rabbit','boar','chicken','tortoise','bear','tiger','snake','eagle','dragon','spider','crow']]
BEASTS=['sheep','wolf','deer','rabbit','boar','fox','chicken','tortoise','moonhart','emberfox','bear','tiger','snake','eagle','dragon','spider','crow']
CLASSES=['civilian','warrior','tank','archer','mage','healer','rogue','bard','monk','engineer','alchemist','psychic','mime','gunslinger','hero','spellblade']
SPECIAL=['barbarian','darkKnight','dragonKnight','knight','paladin','samurai','swashbuckler','warlord','guardian','juggernaut','sniper','bowblade','beastmaster','dualRanger','trapper','magicRanger','druid','elementalist','illusionist','natureMage','necromancer','redMage','shaman','sorcerer','summoner','wizard','warlock','assassin','gambler','ninja','pirate','scout','shadow','thief','battlePriest','priest','templar','witchDoctor','dancer','champion','runeKnight','minstrel','kiMonk','artificer','chemist','psion','mimic','marksman']
WEAPONS=['sword','axe','spear','lance','hammer','bow','dagger','staff','mace','lute','fists','wrench','flask','gun','orb','saber','glaive','fan','whip','flyingSword','talisman']
ROOTS=['fire','water','wood','earth','metal','ice','lightning','wind','magma','mist','shadow','light','poison','blood','gravity','space','time','sound','solar','lunar','star','void','soul','dream','illusion','spirit','bone','crystal','life','death']
BRANCHES=['assault','control','defense','movement','cultivation','support']
M={'format':'kingdom-modular-pixel-v1','cell':[144,144],'columns':14,'anchor':[72,130],'frameOrder':['idle','walk_contact_l','walk_down_l','walk_pass_l','walk_contact_r','walk_down_r','walk_pass_r','attack','idle_alt','hurt','death','work_1','cast_2','work_cast_3'],'facing':'three-quarter south; mirror horizontally for west. No north/east/west direction rows requested.','races':{},'fits':{},'beasts':{},'sheets':{},'classes':CLASSES,'specialisations':SPECIAL,'weapons':WEAPONS,'roots':ROOTS,'branches':BRANCHES,'tierCount':6,'sexOrder':['male','female'],'buildOrder':['thin','normal','broad','heavy'],'rowFormula':'body row = sex * 4 + build; variant row = variant * 8 + sex * 4 + build','layerOrder':['tier','aura','back','body','citizen','outfit','tunic','robe','special','face','eyes','hair','beard','ornament','weapon'],'sharedFits':'All beast-folk use human torso/limb fits. Race anatomy is in body/face/hair sheets. Elf/dwarf/orc use separate fits.','palettes':{'skin':['#fddbb4','#f1c27d','#e0ac69','#c68642','#a86b3c','#8d5524','#6b3e1f','#4a2a14'],'orc':['#b1c981','#7a9b55','#536f3f','#354e30'],'hair':['#201b26','#493026','#7a3c2f','#a0794e','#e3d8ab','#b84932','#171a21','#78548f'],'eye':['#6289bc','#6d914e','#a97943','#a466ae'],'material':['#a0aabb','#c0a36f','#8b6551','#a5a38c'],'class':{'steel':'#9bafbf','gold':'#d4ac59','leather':'#9d7451','cloth':'#7283ad','dragon':'#a6534c','nature':'#6a9668','magic':'#9374b5'}}}
# Discrete neutral tones: outlines stay dark during tinting; all alpha is 0 or 255.
O='#242424';S='#777777';B='#b0b0b0';H='#dedede';L='#f2f2f2';D='#505050';GOLD='#cba459';IVORY='#e7dfb9';WOOD='#886044';METAL='#a9bdc8';DARK='#3f5261'
class Pen:
 def __init__(self,im,frame=0,scale=1,shift=(0,0)):
  self.im=im;self.d=ImageDraw.Draw(im);self.frame=frame;self.scale=scale;self.shift=shift
 def pt(self,p):
  x,y=p;x=72+(x-72)*self.scale+self.shift[0];y=max(3,130+(y-130)*self.scale+self.shift[1])
  # Death is a shared geometric transform on every layer, with a stable ground anchor.
  if self.frame==10:x,y=y+2,108+(x-72)*.40
  return (round(x),round(y))
 def poly(self,pts,c=B,outline=O):self.d.polygon([self.pt(p) for p in pts],fill=c,outline=outline,width=1)
 def line(self,pts,c=O,w=1):self.d.line([self.pt(p) for p in pts],fill=c,width=max(1,round(w*self.scale)))
 def rect(self,box,c=B,outline=None):
  a,b,cx,d=box;self.poly([(a,b),(cx,b),(cx,d),(a,d)],c,outline)
 def ell(self,box,c=B,outline=O):
  a,b,cx,d=box
  # Explicit stepped ellipse polygon: integer grid, no antialiasing.
  pts=[((a+cx)/2+(cx-a)/2*math.cos(i*math.pi/12),(b+d)/2+(d-b)/2*math.sin(i*math.pi/12)) for i in range(24)]
  self.poly(pts,c,outline)
 def gem(self,x,y,r=3,c=H):self.poly([(x,y-r),(x+r,y),(x,y+r),(x-r,y)],c)
 def dot(self,x,y,c=H,r=1):self.rect((x,y,x+r-1,y+r-1),c)
def blank():return Image.new('RGBA',(144,144))
def geometry(fit,age,body,frame):
 sex,build=divmod(body,4);base={'human':100,'elf':105,'dwarf':85,'orc':110}[fit]
 sc=.7 if age=='child' else 1
 # elder head and shoulders stoop while soles remain at 130
 top=130-base;head=top+20;shoulder=top+42+(4 if age=='elder' else 0)
 w=[15,18,22,25][build]+({'elf':-2,'dwarf':5,'orc':5}.get(fit,0))-(1 if sex else 0)
 stride=[0,-4,-2,0,4,2,0,0,0,-2,0,-2,0,2][frame]
 bob=[0,0,1,0,0,1,0,-2,1,3,0,0,-2,0][frame]
 hx=72+(3 if age=='elder' else 0)+(-2 if frame==9 else 0);hy=head+bob+(5 if age=='elder' else 0)
 handL=(72-w-4,102+stride);handR=(72+w+4,102-stride)
 if frame==7:handR=(91,shoulder+7);handL=(72-w-5,93)
 if frame in [11,12,13]:handR=(100+(frame-12)*3,shoulder-3);handL=(48,shoulder+5+(frame-12)*2)
 return dict(fit=fit,age=age,sex=sex,build=build,scale=sc,top=top,head=(hx,hy),shoulder=shoulder+bob,w=w,stride=stride,bob=bob,l=handL,r=handR)
def arm(p,g,side,c=B):
 w=g['w'];y=g['shoulder'];a=72+side*(w-2);hx,hy=g['r' if side>0 else 'l']
 p.poly([(a-side*4,y+2),(a+side*5,y+5),(hx+side*4,hy-3),(hx+side*3,hy+3),(hx-side*4,hy+3),(hx-side*5,hy-4)],c)
 p.line([(a,y+7),(hx-2*side,hy-6)],H);p.ell((hx-4,hy-3,hx+4,hy+4),B)
def head(p,g,race):
 x,y=g['head'];rw=15+(2 if g['fit'] in ['dwarf','orc'] else 0);kind=race.removesuffix('folk')
 p.ell((x-rw,y-17,x+rw,y+18),B);p.poly([(x-rw+3,y+5),(x-rw+6,y+15),(x+5,y+18),(x+rw,y+7),(x+rw-2,y+14),(x+6,y+21),(x-7,y+19)],S,None)
 p.line([(x-rw+4,y-9),(x-rw+4,y+3)],H,2);p.ell((x-4,y+1,x+4,y+9),B);p.dot(x-2,y+3,H,2)
 if race=='elf':
  for side in [-1,1]:p.poly([(x+side*12,y-6),(x+side*26,y-12),(x+side*19,y+4),(x+side*13,y+6)],B);p.line([(x+side*15,y),(x+side*21,y-6)],S)
 elif race=='orc':
  p.poly([(x-12,y+8),(x-11,y+19),(x+12,y+19),(x+13,y+8)],S);p.line([(x-10,y+12),(x+10,y+12)],O)
  for side in [-1,1]:p.poly([(x+side*8-3,y+14),(x+side*8,y+5),(x+side*8+3,y+14)],L)
 elif kind in BEASTS:
  if kind in ['wolf','fox','tiger','bear','sheep','deer','rabbit','boar','dragon','crow','chicken','eagle']:
   for side in [-1,1]:
    if kind=='rabbit':p.ell((x+side*9-5,y-44,x+side*9+5,y-10),B);p.line([(x+side*9,y-39),(x+side*9,y-17)],S,2)
    elif kind in ['bear','sheep']:p.ell((x+side*14-6,y-23,x+side*14+6,y-11),B)
    elif kind not in ['crow','chicken','eagle']:p.poly([(x+side*10,y-9),(x+side*18,y-27),(x+side*22,y-5)],B);p.line([(x+side*16,y-12),(x+side*18,y-20)],S,2)
  if kind in ['wolf','fox','boar','bear','tiger','sheep','deer','rabbit']:
   p.ell((x-11,y+4,x+12,y+18),H);p.poly([(x-5,y+5),(x+5,y+5),(x+2,y+10),(x-2,y+10)],O);p.line([(x,y+10),(x,y+14),(x-4,y+16)],D)
  if kind in ['deer','dragon']:
   for side in [-1,1]:p.line([(x+side*11,y-12),(x+side*18,y-29),(x+side*15,y-37)],O,3);p.line([(x+side*17,y-28),(x+side*26,y-31)],H,2)
  if kind=='sheep':
   for dx,dy in [(-12,-12),(-4,-19),(5,-18),(12,-11)]:p.ell((x+dx-6,y+dy-5,x+dx+6,y+dy+6),H)
  if kind=='boar':p.ell((x-10,y+6,x+11,y+17),S);p.dot(x-5,y+10,O,2);p.dot(x+4,y+10,O,2)
  if kind in ['crow','eagle','chicken']:p.poly([(x-7,y+3),(x+7,y+3),(x+3,y+18),(x-3,y+17)],H);p.line([(x,y+5),(x+2,y+13)],D)
  if kind=='chicken':p.poly([(x-8,y-15),(x-8,y-24),(x-3,y-20),(x,y-29),(x+5,y-20),(x+9,y-23),(x+9,y-12)],S)
  if kind=='tortoise':p.line([(x-11,y+6),(x-6,y+11),(x+8,y+11),(x+13,y+5)],D,2);p.poly([(x-10,y-14),(x,y-20),(x+11,y-12),(x+8,y-6),(x-8,y-6)],S)
  if kind=='snake':p.poly([(x-17,y-5),(x-12,y-17),(x+13,y-17),(x+18,y-5),(x+11,y+13),(x-10,y+13)],B);p.line([(x-5,y+9),(x+7,y+9)],D)
  if kind=='dragon':p.poly([(x-8,y+6),(x+9,y+6),(x+12,y+17),(x-9,y+17)],H);p.gem(x,y-8,4,S)
  if kind=='spider':
   for dx,dy in [(-12,-6),(-6,-13),(6,-13),(12,-6)]:p.ell((x+dx-2,y+dy-2,x+dx+2,y+dy+2),D)
  if kind=='tiger':
   for side in [-1,1]:
    for dy in [-8,-1,6]:p.line([(x+side*14,y+dy),(x+side*9,y+dy+3)],D,2)
def body_frame(fit,age,row,f,race='human'):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);w=g['w'];y=g['shoulder'];st=g['stride']
 for side in [-1,1]:
  x=72+side*9;lift=max(0,side*st)
  p.poly([(x-7,103),(x+7,103),(x+8,126-lift),(x+5,130-lift),(x-8,130-lift)],B);p.rect((x+3,108,x+7,125-lift),S);p.line([(x-5,112),(x-5,125-lift)],H)
 p.poly([(72-w+4,y),(72+w-4,y),(72+w,y+15),(72+w-4,108),(72-w+4,108),(72-w,y+15)],B)
 p.poly([(72+w-8,y+4),(72+w,y+15),(72+w-4,108),(75,108),(79,y+22)],S,None);p.line([(72-w+5,y+5),(72-w+5,y+20)],H,2)
 if g['sex']:p.line([(62,y+14),(69,y+17),(73,y+14),(81,y+17)],S)
 arm(p,g,-1);arm(p,g,1);p.rect((66,y-11,78,y+2),B,O);head(p,g,race)
 # Base modesty garment belongs to body, remains greyscale.
 p.poly([(72-w+3,99),(72+w-3,99),(72+w-4,109),(74,112),(71,106),(68,112),(72-w+4,109)],D)
 return im
def face_frame(fit,age,row,f,variant,race):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);x,y=g['head']
 for side in [-1,1]:
  bx=x+side*8
  p.line([(bx-4,y-5-variant%2),(bx+3,y-6+variant%2)],D,2 if race=='dwarf' else 1)
 if variant==0:p.line([(x-5,y+13),(x+4,y+13)],D)
 if variant==1:p.line([(x-5,y+11),(x,y+14),(x+5,y+11)],D)
 if variant==2:p.line([(x-5,y+14),(x,y+11),(x+5,y+14)],D);p.dot(x-11,y+6,S,2)
 if variant==3:p.line([(x-5,y+13),(x+5,y+13)],D);p.line([(x+8,y+1),(x+11,y+5),(x+8,y+10)],S);p.dot(x-12,y+4,S,2)
 if age=='elder':
  p.line([(x-13,y),(x-10,y+3)],S);p.line([(x+10,y+3),(x+14,y)],S);p.line([(x-8,y+8),(x-10,y+12)],S)
 return im
def eyes_frame(fit,age,row,f,v):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);x,y=g['head']
 for side in [-1,1]:
  ex=x+side*8;ey=y+(v==1)
  if f==9:p.line([(ex-3,ey+1),(ex,ey-1),(ex+3,ey+1)],O)
  elif f==10:p.line([(ex-2,ey-1),(ex+2,ey+2)],O);p.line([(ex+2,ey-1),(ex-2,ey+2)],O)
  elif f==8:p.line([(ex-3,ey),(ex+3,ey)],O)
  else:
   p.rect((ex-3,ey-1,ex+3,ey+(2 if v!=2 else 1)),H,O);p.rect((ex+(1 if v==3 else -1),ey-1,ex+(2 if v==3 else 0),ey+2),S);p.dot(ex,ey-1,L)
 return im
def hair_frame(fit,age,row,f,v,beard=False,race='human'):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);x,y=g['head'];w=17+(2 if fit in ['dwarf','orc'] else 0)
 if beard:
  if v==0:return im
  length=[0,9,17,25,14][v];p.poly([(x-13,y+9),(x-7,y+12),(x,y+10),(x+8,y+12),(x+13,y+8),(x+11,y+length),(x+3,y+length+8),(x-4,y+length+6),(x-12,y+length)],B)
  for dx in [-8,-3,3,8]:p.line([(x+dx,y+16),(x+dx-1,y+length+2)],S)
  p.line([(x-9,y+12),(x-3,y+10),(x,y+12),(x+5,y+10),(x+10,y+12)],D,2)
  if v==4:
   for dy in [18,23]:p.rect((x-8,y+dy,x+8,y+dy+2),H,O)
  return im
 if v==9: # shaved, sideburns and small crown tuft
  p.poly([(x-5,y-16),(x-1,y-22),(x+4,y-18),(x+7,y-14)],B);return im
 if v in [2,4,6,8]:
  p.poly([(x-w,y-8),(x-w+1,y+23),(x-w+5,y+32),(x-w+9,y+28),(x-w+8,y-8)],S)
  p.poly([(x+w-8,y-8),(x+w,y-9),(x+w,y+29),(x+w-4,y+35),(x+w-10,y+28)],B)
 p.poly([(x-w,y+1),(x-w,y-13),(x-w+6,y-22),(x+4,y-25),(x+w-3,y-19),(x+w,y-9),(x+w,y+1),(x+w-5,y-4),(x+5,y-11),(x-1,y-5),(x-6,y-10),(x-12,y-2)],B)
 p.poly([(x-w+2,y-12),(x-w+7,y-20),(x+3,y-22),(x+11,y-18),(x-3,y-17)],H,None)
 for dx in [-10,-4,3,10]:p.line([(x+dx,y-18),(x+dx-2,y-10)],S)
 if v==1:
  for dx in range(-13,15,6):p.poly([(x+dx-4,y-15),(x+dx,y-31-abs(dx)//3),(x+dx+5,y-13)],B)
 if v==3:p.ell((x+9,y-30,x+23,y-14),B);p.line([(x+14,y-27),(x+19,y-23)],H,2)
 if v==4:
  for side in [-1,1]:
   for dy in range(8,29,6):p.poly([(x+side*18-4,y+dy),(x+side*18,y+dy-3),(x+side*18+4,y+dy),(x+side*18,y+dy+4)],B)
 if v==5:p.poly([(x-8,y-18),(x-5,y-35),(x,y-39),(x+5,y-34),(x+8,y-18)],B);p.line([(x-3,y-32),(x-2,y-21)],H,2)
 if v==6:
  for side in [-1,1]:p.ell((x+side*18-8,y-19,x+side*18+8,y-5),B)
 if v==7:p.poly([(x-18,y-13),(x-10,y-30),(x+3,y-27),(x+18,y-13)],B);p.line([(x-7,y-24),(x-12,y-13)],H,2)
 if v==8:p.rect((x-16,y-8,x+16,y-5),D,O)
 # Ears/antlers remain visible over hair. Folk styles are crests/mane styles.
 if race.endswith('folk'):
  kind=race[:-4]
  if kind in ['eagle','crow','chicken','dragon','snake','spider','tortoise']:
   im=blank();p=Pen(im,f,g['scale'])
   for i in range(3+v%4):p.poly([(x-13+i*5,y-14),(x-10+i*5,y-25-(v%3)*3),(x-6+i*5,y-13)],B)
 return im

def outfit_frame(fit,age,row,f,kind):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);w=g['w'];y=g['shoulder'];hx,hy=g['head'];robe=kind in ['mage','healer','psychic','alchemist'];armored=kind in ['warrior','tank','hero','spellblade'];short=kind in ['rogue','archer','engineer','gunslinger'];skirt=122 if robe else 109
 # Boots follow the body's planted and lifted feet.
 for side in [-1,1]:
  xx=72+side*9;lift=max(0,side*g['stride']);p.poly([(xx-7,116-lift),(xx+7,116-lift),(xx+8,126-lift),(xx+7,130-lift),(xx-8,130-lift),(xx-8,125-lift)],D);p.line([(xx-5,120-lift),(xx+4,120-lift)],S);p.line([(xx-6,127-lift),(xx+3,127-lift)],B)
 p.poly([(72-w+1,y),(65,y-2),(72,y+5),(79,y-2),(72+w-1,y),(72+w,y+16),(72+w-4,101),(72+w+(3 if robe else -3),skirt),(72-w-(3 if robe else -3),skirt),(72-w+4,101),(72-w,y+16)],B)
 p.poly([(76,y+6),(72+w-3,y+2),(72+w,y+16),(72+w-4,101),(72+w+(3 if robe else -3),skirt),(77,skirt)],S,None)
 p.line([(72-w+5,y+5),(72-w+6,96)],H,2);p.line([(67,y),(72,y+7),(77,y)],D,2)
 for side in [-1,1]:
  a=72+side*(w-2);hx1,hy1=g['r' if side>0 else 'l']
  end=.82 if robe else .48
  ex=a+(hx1-a)*end;ey=y+3+(hy1-y-3)*end
  p.poly([(a-side*6,y),(a+side*6,y+4),(ex+side*5,ey+3),(ex-side*4,ey+3)],B)
  p.line([(a-side*3,y+4),(ex-side*2,ey)],H)
 p.rect((72-w+3,98,72+w-3,103),D,O);p.rect((69,98,75,103),H,O);p.rect((71,99,73,102),S)
 if armored:
  p.poly([(72-w+4,y+3),(66,y+3),(72,y+10),(78,y+3),(72+w-4,y+3),(72+w-5,89),(72,95),(72-w+5,89)],B)
  p.line([(72,y+13),(72,91)],H,2);p.line([(72-w+7,y+6),(72-w+7,86)],H)
  for side in [-1,1]:
   xx=72+side*w;p.poly([(xx-side*8,y-1),(xx+side*4,y),(xx+side*8,y+8),(xx+side*3,y+14),(xx-side*8,y+10)],B);p.line([(xx-side*5,y+2),(xx+side*2,y+3)],H,2)
  for yy in [105,110]:p.line([(72-w+4,yy),(69,yy+2),(72,yy-1),(76,yy+2),(72+w-4,yy)],D)
 if kind=='tank':
  p.poly([(39,86),(50,80),(60,85),(59,111),(50,121),(40,112)],B);p.poly([(50,84),(56,87),(55,109),(50,115)],S,None);p.line([(43,88),(43,108),(50,116)],H,2);p.gem(50,98,5,H)
 if kind in ['mage','psychic']:
  p.poly([(hx-24,hy-13),(hx-14,hy-20),(hx-7,hy-44),(hx+4,hy-48),(hx+13,hy-20),(hx+24,hy-13)],B);p.line([(hx-18,hy-17),(hx+17,hy-17)],H,2);p.gem(hx,hy-24,3,H)
 if kind=='healer':
  p.rect((69,y+9,75,96),H,O);p.rect((62,y+18,82,y+23),H,O);p.line([(67,111),(72,116),(77,111)],H,2)
 if kind in ['archer','rogue']:
  p.poly([(hx-20,hy+3),(hx-19,hy-16),(hx-7,hy-31),(hx+7,hy-31),(hx+20,hy-14),(hx+20,hy+4),(hx+14,hy-8),(hx+5,hy-18),(hx-7,hy-18),(hx-14,hy-8)],B);p.line([(hx-7,hy-26),(hx+4,hy-26)],H,2)
  p.line([(72-w+3,y+4),(72+w-4,95)],D,4);p.line([(72-w+4,y+4),(72+w-3,95)],H)
 if kind=='bard':
  p.poly([(hx-24,hy-16),(hx-14,hy-24),(hx+17,hy-24),(hx+23,hy-16)],B);p.poly([(hx+8,hy-24),(hx+15,hy-37),(hx+22,hy-39),(hx+17,hy-27)],H);p.line([(63,y+6),(80,95)],H,3)
 if kind=='monk':p.poly([(58,y),(66,y),(88,100),(76,102)],H);p.line([(58,y+4),(80,98)],S,2);p.line([(72,102),(83,117)],D,3)
 if kind=='engineer':
  p.rect((72-w+4,85,72+w-4,111),S,O);p.line([(60,y+3),(63,88)],H,3);p.line([(83,y+3),(80,88)],H,3)
  for dx in [-8,0,8]:p.rect((72+dx-3,101,72+dx+3,108),B,O)
  p.rect((hx-17,hy-10,hx+17,hy-4),D,O)
  for dx in [-9,9]:p.ell((hx+dx-6,hy-13,hx+dx+6,hy-1),H)
 if kind=='alchemist':
  for dx in [-10,0,10]:p.ell((72+dx-3,102,72+dx+3,110),H);p.rect((72+dx-1,99,72+dx+1,103),D)
 if kind=='mime':
  for yy in range(int(y+7),96,7):p.rect((72-w+5,yy,72+w-5,yy+2),D)
  p.ell((hx-18,hy-24,hx+18,hy-13),D);p.line([(69,100),(66,116)],H,3)
 if kind=='gunslinger':
  p.poly([(hx-24,hy-13),(hx-12,hy-16),(hx-11,hy-29),(hx+12,hy-29),(hx+15,hy-16),(hx+25,hy-13)],B);p.rect((hx-11,hy-20,hx+13,hy-17),D)
  p.line([(72+w-5,y+5),(72+w-8,98)],H,3);p.rect((72+w-6,104,72+w,115),D,O)
 if kind in ['hero','spellblade']:p.gem(72,y+20,5,H);p.line([(61,90),(66,94),(72,90),(79,94),(84,90)],H)
 return im

def special_frame(fit,age,row,f,v):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);x,y=g['head'];w=g['w'];sy=g['shoulder'];name=SPECIAL[v]
 # Explicit silhouette families plus per-specialisation emblem; overlays stay tintable.
 horn=name in ['barbarian','darkKnight','dragonKnight','warlord','witchDoctor','shaman']
 if horn:
  for side in [-1,1]:p.poly([(x+side*13,y-12),(x+side*24,y-31),(x+side*23,y-14),(x+side*16,y-4)],B)
 if name in ['knight','paladin','guardian','juggernaut','templar','battlePriest','samurai','dragonKnight','darkKnight']:
  p.poly([(x-19,y-1),(x-19,y-16),(x-10,y-24),(x+10,y-24),(x+19,y-16),(x+19,y-1),(x+13,y+7),(x+13,y-7),(x-13,y-7),(x-13,y+7)],B);p.line([(x-13,y-17),(x+10,y-17)],H,2)
  if name=='samurai':
   for yy in [sy+3,sy+10,sy+17]:p.line([(72-w-3,yy),(72-w+8,yy+3)],D,3);p.line([(72+w-8,yy+3),(72+w+3,yy)],H,2)
 if name in ['necromancer','witchDoctor','warlock']:
  p.ell((66,sy+8,78,sy+20),H);p.rect((68,sy+18,76,sy+23),H,O);p.dot(68,sy+12,D,3);p.dot(74,sy+12,D,3)
 elif name in ['natureMage','druid','beastmaster','shaman']:
  for side in [-1,1]:
   for yy in [sy+3,sy+11,sy+19]:p.poly([(72+side*w,yy),(72+side*(w+8),yy-4),(72+side*(w+6),yy+6)],H)
 elif name in ['ninja','shadow','assassin','thief','scout','trapper']:
  p.poly([(x-16,y+6),(x+16,y+6),(x+13,y+18),(x-11,y+18)],S);p.line([(x+15,y+9),(x+28,y+16),(x+34,y+9)],H,3)
 elif name=='pirate':
  p.poly([(x-25,y-12),(x-18,y-26),(x,y-19),(x+18,y-26),(x+25,y-12)],B);p.rect((x+3,y-2,x+13,y+4),D,O);p.line([(x-13,y-8),(x+14,y+7)],O)
 elif name=='swashbuckler':p.poly([(x+12,y-17),(x+21,y-37),(x+31,y-38),(x+23,y-23)],H)
 elif name in ['redMage','wizard','sorcerer','illusionist','summoner','elementalist','magicRanger','psion']:
  p.poly([(x-19,y-17),(x-4,y-39),(x+5,y-35),(x+18,y-17)],B);p.gem(x,y-24,4,H)
 elif name in ['priest','paladin','templar']:p.rect((70,sy+7,74,sy+26),H,O);p.rect((64,sy+12,80,sy+16),H,O)
 elif name=='dancer':
  p.line([(53,sy+5),(58,88),(52,111)],H,3);p.line([(91,sy+5),(86,88),(94,112)],B,3)
 # 48 different heraldic glyphs, discrete pixels, no labels.
 bits=v+1
 p.ell((66,92,78,104),D)
 for i in range(6):
  if bits&(1<<i):p.rect((68+(i%3)*3,94+(i//3)*4,69+(i%3)*3,96+(i//3)*4),H)
 if name in ['bowblade','dualRanger','sniper','trapper','magicRanger','beastmaster']:p.line([(55,sy+1),(86,94)],H,3);p.gem(80,sy+7,4,H)
 if name=='gambler':
  for j in range(3):p.poly([(56+j*7,sy+4),(61+j*7,sy+1),(65+j*7,sy+14),(59+j*7,sy+16)],H);p.gem(60+j*7,sy+8,2,D)
 return im

def weapon_frame(fit,age,row,f,name):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);x,y=g['r'];attack=f==7
 # Every grip is at the exact animated right-hand socket, no independent offsets.
 dx,dy=(.9,-.44) if attack else (.16,-.98)
 def pt(a,b=0):return (x+dx*a-dy*b,y+dy*a+dx*b)
 def poly(ps,c=METAL):p.poly([pt(a,b) for a,b in ps],c)
 def line(ps,c=O,w=1):p.line([pt(a,b) for a,b in ps],c,w)
 long=name in ['spear','lance','staff','glaive','hammer','mace']
 if name in ['sword','saber','dagger','flyingSword','spear','lance','glaive']:
  n={'sword':35,'saber':39,'dagger':20,'flyingSword':35,'spear':48,'lance':54,'glaive':48}[name]
  if name in ['spear','lance','glaive']:
   poly([(-15,-2),(n-13,-2),(n-13,2),(-15,2)],WOOD);poly([(n-16,-5),(n,0),(n-16,5),(n-11,0)],METAL)
  else:
   poly([(-7,-2),(5,-2),(5,2),(-7,2)],WOOD);poly([(7,-4),(n-7,-3),(n,0),(n-7,4),(7,4)],METAL);line([(8,-2),(n-4,0)],IVORY);poly([(4,-8),(7,-8),(8,8),(5,8)],GOLD)
  if name=='flyingSword':p.gem(x-8,y-11,4,'#8bbbd2');p.gem(x+6,y-17,2,IVORY)
 elif name in ['axe','hammer','mace','wrench']:
  poly([(-8,-2),(30,-2),(30,2),(-8,2)],WOOD)
  if name=='axe':poly([(20,-2),(18,-11),(29,-16),(34,-7),(30,1)],METAL);line([(21,-10),(28,-13),(31,-7)],IVORY)
  elif name=='hammer':poly([(23,-11),(33,-11),(33,12),(23,12)],METAL);line([(24,-8),(31,-8)],IVORY,2)
  elif name=='mace':poly([(23,-6),(21,-10),(28,-8),(34,-10),(32,-3),(36,1),(31,5),(32,10),(26,8),(21,10),(23,4)],METAL)
  else:poly([(23,-6),(28,-10),(35,-9),(28,-4),(29,2),(35,4),(28,7),(22,3)],METAL)
 elif name=='bow':
  line([(-24,0),(-20,9),(-9,15),(7,15),(20,9),(25,0)],O,5);line([(-24,0),(-20,9),(-9,15),(7,15),(20,9),(25,0)],WOOD,3);line([(-24,0),(25,0)],IVORY);line([(-3,-19),(-3,21)],METAL);poly([(-6,18),(-3,25),(0,18)],METAL)
 elif name=='staff':
  poly([(-16,-2),(38,-2),(38,2),(-16,2)],WOOD);p.ell((*pt(37,-7),*pt(48,7)),GOLD) if False else None
  p.gem(*pt(43),8,'#91c5c6');p.gem(*pt(43),3,IVORY)
 elif name=='lute':
  p.ell((x-9,y-3,x+10,y+22),WOOD);p.ell((x-4,y+4,x+5,y+13),DARK);poly([(0,-3),(26,-3),(26,2),(0,2)],GOLD)
  for b in [-1,1]:line([(1,b),(24,b)],IVORY)
 elif name=='flask':
  p.poly([(x-3,y-14),(x+4,y-14),(x+4,y-7),(x+10,y+3),(x+7,y+9),(x-7,y+9),(x-10,y+3),(x-3,y-7)],METAL);p.rect((x-6,y+1,x+7,y+6),'#72b5a0');p.rect((x-4,y-16,x+5,y-13),WOOD,O)
 elif name=='gun':poly([(-7,-4),(1,-4),(4,-14),(12,-14),(10,0),(4,3),(-4,3)],WOOD);poly([(7,-16),(29,-16),(29,-10),(7,-10)],METAL);line([(12,-15),(27,-15)],IVORY)
 elif name=='orb':p.ell((x-10,y-21,x+10,y-1),'#7e709e');p.gem(x-2,y-14,5,'#d7c6e7');p.line([(x-7,y-8),(x-2,y-4),(x+5,y-5)],'#514968')
 elif name=='fan':
  for i in range(8):
   a=-2.8+i*.26;px=x+math.cos(a)*27;py=y+math.sin(a)*27;p.poly([(x,y),(px,py),(px+5,py-2)],IVORY);p.line([(x,y),(px,py)],WOOD)
 elif name=='whip':p.line([(x,y),(x+12,y-13),(x+23,y-8),(x+27,y+8),(x+29,y+15),(x+33,y+7)],WOOD,3);p.line([(x+2,y-2),(x+12,y-12)],GOLD)
 elif name=='talisman':p.poly([(x-6,y-23),(x+9,y-20),(x+6,y+2),(x-8,y-1)],IVORY);p.line([(x-2,y-17),(x+3,y-14),(x-2,y-10),(x+3,y-7),(x-2,y-4)],'#ab5647',2)
 elif name=='fists':
  for xx,yy in [g['l'],g['r']]:p.poly([(xx-5,yy-4),(xx+5,yy-4),(xx+6,yy+3),(xx-4,yy+5)],IVORY);p.line([(xx-4,yy),(xx+4,yy)],DARK)
 # Fingers appear over the grip, but tint is kept on body: weapon alpha leaves grip centre open.
 return im

def ornament_frame(fit,age,row,f,v):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);x,y=g['head'];sy=g['shoulder']
 if v==0:p.ell((x+16,y+4,x+22,y+12),GOLD);p.dot(x+18,y+5,IVORY,2)
 elif v==1:p.line([(61,sy),(65,sy+8),(72,sy+11),(80,sy+7),(83,sy)],GOLD,2);p.gem(72,sy+12,3,'#81b8ac')
 elif v==2:p.line([(x+5,y-3),(x+11,y+8)],'#784442',2);p.line([(x+5,y+2),(x+10,y+1)],'#b66b59')
 elif v==3:
  for side in [-1,1]:p.line([(x+side*12,y+3),(x+side*7,y+5),(x+side*12,y+7)],'#566e82',2)
 elif v==4:p.gem(72-g['w']+6,sy+8,5,GOLD);p.gem(72-g['w']+6,sy+8,2,'#81b8ac')
 return im

def back_frame(fit,age,row,f,v):
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);w=g['w'];y=g['shoulder'];sway=[0,1,2,1,-1,-2,-1,4,0,-2,0,3,0,-3][f]
 if v==0:
  p.poly([(72-w+2,y-3),(72+w-2,y-3),(72+w+6+sway,119),(85+sway,123),(76+sway,119),(63+sway,124),(49+sway,120),(72-w-6+sway,113)],B);p.poly([(75,y),(72+w-2,y),(72+w+6+sway,119),(85+sway,123)],S,None)
  for dx in [-12,0,12]:p.line([(72+dx,y+8),(72+dx+sway*2,116)],S)
 elif v==1:
  p.poly([(49,y-10),(61,y-6),(62,105),(50,107)],B);p.line([(51,y-7),(51,102)],H,2)
  for dx in [0,4,8]:p.line([(51+dx,y-5),(49+dx,y-23)],D,2);p.poly([(49+dx,y-22),(45+dx,y-27),(49+dx,y-28),(52+dx,y-23)],H)
 elif v==2:
  p.line([(72+w-2,121),(72+w-2,y-40)],D,3);p.poly([(72+w,y-39),(72+w+25,y-35),(72+w+20+sway,y-22),(72+w+27,y-12),(72+w,y-15)],B);p.gem(72+w+11,y-26,5,H)
 return im

def citizen_frame(fit,age,row,f,tunic=False):
 if not tunic:return outfit_frame(fit,age,row,f,'civilian')
 im=blank();g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);w=g['w'];y=g['shoulder']
 p.poly([(72-w+4,y+2),(65,y),(72,y+7),(79,y),(72+w-4,y+2),(72+w-3,97),(72-w+3,97)],B);p.poly([(78,y+6),(72+w-4,y+3),(72+w-3,97),(79,97)],S,None);p.line([(72-w+7,y+7),(72-w+7,92)],H,2);p.line([(67,y+3),(72,y+9),(77,y+3)],D)
 return im

def robe_frame(fit,age,row,f,v):
 im=outfit_frame(fit,age,row,f,'healer' if v==5 else 'civilian');g=geometry(fit,age,row,f);p=Pen(im,f,g['scale']);w=g['w'];y=g['shoulder']
 p.poly([(72-w+3,y+2),(65,y),(72,y+8),(79,y),(72+w-3,y+2),(72+w-2,100),(72+w+5,124),(73,121),(72-w-5,124),(72-w+2,100)],B);p.poly([(76,y+12),(72+w-4,y+5),(72+w-2,100),(72+w+5,124),(78,122)],S,None)
 p.line([(65,y),(83,96)],H,3);p.line([(79,y),(65,98)],D,2);p.rect((72-w+2,98,72+w-2,103),D,O);p.line([(72,103),(66,121)],H,2)
 if v==0:p.poly([(72-w-4,y+2),(72-w+7,y-2),(72-w+9,y+14),(72-w-3,y+17)],S)
 elif v==1:p.line([(61,105),(59,119)],H,3);p.gem(60,111,4,H)
 elif v==2:p.poly([(72-w-4,y),(72-w+8,y-2),(72-w+8,y+16),(72-w-3,y+17)],S);p.poly([(72+w-8,y-2),(72+w+4,y),(72+w+3,y+17),(72+w-8,y+16)],S)
 elif v==3:p.line([(54,y+12),(45,97),(51,112)],H,3);p.line([(90,y+12),(101,99),(97,114)],H,3)
 elif v==4:p.gem(72,88,7,H);p.gem(72,88,3,S)
 elif v==5:p.line([(69,84),(75,84)],H,3);p.line([(72,81),(72,88)],H,3)
 return im

def write_sheet(path,rows,render,tint=False,descriptors=None):
 path=str(path);im=Image.new('RGBA',(2016,len(rows)*144))
 for r,value in enumerate(rows):
  for f in range(14):im.paste(render(value,f),(f*144,r*144))
 dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True)
 # Exact palette conversion; no quantisation, dithering, or loss of pixels.
 colors=im.getcolors(256)
 if colors is None:raise ValueError('palette overflow '+path)
 im.save(dest,optimize=False,compress_level=3)
 M['sheets'][path]={'rows':len(rows),'size':[2016,len(rows)*144],'tintable':tint,'colors':len(colors),'rowKeys':descriptors if descriptors is not None else rows,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
 return path

def generate_people():
 for fit in ['human','elf','dwarf','orc']:
  for age in ['child','adult','elder']:
   key=fit+'/'+age;prefix='people/fits/'+key;entries={}
   # Layer sheets have bounded dimensions (max 2016 x 9216).
   for kind,variants,renderer,tint in [
    ('eyes',4,lambda b,f,v:eyes_frame(fit,age,b,f,v),True),
    ('outfit',16,lambda b,f,v:outfit_frame(fit,age,b,f,CLASSES[v]),True),
    ('special',len(SPECIAL),lambda b,f,v:special_frame(fit,age,b,f,v),True),
    ('weapon',len(WEAPONS),lambda b,f,v:weapon_frame(fit,age,b,f,WEAPONS[v]),False),
    ('ornament',6,lambda b,f,v:ornament_frame(fit,age,b,f,v),False),
    ('back',3,lambda b,f,v:back_frame(fit,age,b,f,v),True),
    ('robe',6,lambda b,f,v:robe_frame(fit,age,b,f,v),True)]:
    paths=[]
    for start in range(0,variants,8):
     rows=[(v,b) for v in range(start,min(start+8,variants)) for b in range(8)]
     paths.append(write_sheet(f'{prefix}/{kind}-{start//8}.png',rows,lambda vb,f:renderer(vb[1],f,vb[0]),tint))
    entries[kind]={'pages':paths,'variantsPerPage':8,'bodyRows':8}
   for k in ['citizen','tunic']:
    entries[k]=write_sheet(f'{prefix}/{k}.png',list(range(8)),lambda b,f:citizen_frame(fit,age,b,f,k=='tunic'),True)
   entries['beard']=write_sheet(f'{prefix}/beard.png',[(v,b) for v in range(5) for b in range(8)],lambda vb,f:hair_frame(fit,age,vb[1],f,vb[0],True),True)
   M['fits'][key]=entries
   print('fit',key,flush=True)
 for race in RACES:
  fit=race if race in ['human','elf','dwarf','orc'] else 'human';M['races'][race]={}
  for age in ['child','adult','elder']:
   prefix=f'people/races/{race}/{age}';d={'fit':fit+'/'+age}
   d['body']=write_sheet(prefix+'/body.png',list(range(8)),lambda b,f:body_frame(fit,age,b,f,race),True)
   d['face']=write_sheet(prefix+'/face.png',[(v,b) for v in range(4) for b in range(8)],lambda vb,f:face_frame(fit,age,vb[1],f,vb[0],race),True)
   d['hair']={'pages':[],'variantsPerPage':8,'bodyRows':8}
   for start in [0,8]:d['hair']['pages'].append(write_sheet(prefix+f'/hair-{start//8}.png',[(v,b) for v in range(start,min(start+8,10)) for b in range(8)],lambda vb,f:hair_frame(fit,age,vb[1],f,vb[0],False,race),True))
   M['races'][race][age]=d
  print('race',race,flush=True)

BEAST_COLORS={'sheep':'#d5c9ac','wolf':'#8795a0','deer':'#b48455','rabbit':'#c1aa93','boar':'#82654e','fox':'#cb7c46','chicken':'#e1c89c','tortoise':'#7d9561','moonhart':'#a3c6c9','emberfox':'#d78448','bear':'#876047','tiger':'#d39648','snake':'#8ca46a','eagle':'#9b8566','dragon':'#789b8b','spider':'#897594','crow':'#59627d'}
def beast_geom(kind,age,f):
 sc=.6 if age=='baby' else 1
 sc*= {'rabbit':.73,'chicken':.76,'crow':.8,'dragon':1.06,'bear':1.04}.get(kind,1)
 stride=[0,-4,-2,0,4,2,0,1,0,-2,0,-2,1,3][f];bob=[0,0,1,0,0,1,0,-3,1,3,0,0,-2,0][f]
 return sc,stride,bob

def beast_frame(kind,age,f,layer='body',v=0):
 im=blank();sc,st,bob=beast_geom(kind,age,f);p=Pen(im,f,sc);h=68+bob
 bird=kind in ['chicken','eagle','crow'];serpent=kind=='snake';spider=kind=='spider';shell=kind=='tortoise'
 if layer=='tail':
  if serpent:
   paths=[[(35,122),(20,128)],[(35,122),(23,121),(22,114),(29,113)],[(35,122),(24,126),(17,122)],[(35,122),(25,115),(17,117)]]
   p.line(paths[v],O,7);p.line(paths[v],B,5)
   if v==2:
    for xx in [17,20,23]:p.line([(xx,120),(xx,125)],D)
   return im
  if spider:
   if v:p.poly([(66,72),(68,53-v*3),(72,49-v*2),(76,53-v*3),(78,72)],B)
   return im
  start=(49,101+bob)
  if bird:
   for j in range(3+v):p.poly([(54,103),(32-j*3,80-j*3),(37+j*2,110),(57,115)],B)
  elif shell:p.poly([(47,111),(29-v*2,119),(49,121)],B)
  elif kind in ['deer','moonhart','rabbit','sheep','boar','bear'] and v==0:p.ell((38,100,55,116),B)
  else:
   if v==0:pts=[(52,101),(37,93),(25,79),(24,98),(33,116),(51,121)]
   elif v==1:pts=[(51,101),(32,106),(21,95),(19,108),(30,121),(51,121)]
   elif v==2:pts=[(51,103),(35,94),(30,81),(37,75),(39,85),(36,95),(51,112)]
   else:pts=[(50,102),(27,90),(16,67),(19,91),(34,117),(51,122)]
   p.poly(pts,B);p.line([(31,99),(40,111),(49,114)],H,2)
  return im
 if layer=='body':
  if serpent:
   p.line([(35,122),(51,113),(79,118),(91,109),(61,102),(51,91),(63,82),(87,82)],O,16)
   p.line([(35,122),(51,113),(79,118),(91,109),(61,102),(51,91),(63,82),(87,82)],B,14)
   p.line([(40,119),(54,116),(79,121),(91,113)],S,3);p.poly([(78,h+8),(86,h-1),(105,h+2),(115,h+13),(104,h+22),(83,h+21)],B);p.line([(94,h+18),(111,h+17)],D);return im
  if spider:
   for side in [-1,1]:
    for j in range(4):
     xx=72+side*13;yy=84+j*8;p.line([(xx,yy),(72+side*(35+j%2*7),yy-9+st*side),(72+side*(47-j*2),112+j*5)],O,5);p.line([(xx,yy),(72+side*(35+j%2*7),yy-9+st*side),(72+side*(47-j*2),112+j*5)],S,3)
   p.ell((47,63+bob,96,108+bob),B);p.ell((54,93+bob,90,124+bob),B);p.ell((54,70+bob,82,89+bob),H,None);p.line([(62,116),(66,126),(70,118)],D,2);p.line([(77,118),(82,126),(85,116)],D,2);return im
  for xx,phase in [(51,1),(66,-1),(85,-1),(99,1)]:
   lift=max(0,st*phase)
   if bird and xx in [51,99]:continue
   p.poly([(xx-5,103),(xx+5,103),(xx+5,126-lift),(xx+9,130-lift),(xx-5,130-lift)],S);p.line([(xx-2,109),(xx-2,124-lift)],B,2)
  if bird:
   p.ell((49,78+bob,91,119+bob),B);p.poly([(57,87+bob),(78,90+bob),(87,109+bob),(70,116+bob),(56,105+bob)],S);p.line([(59,94+bob),(72,106+bob),(81,107+bob)],H,2)
   if kind in ['eagle','crow'] and f in [7,11,12,13]:
    for side in [-1,1]:p.poly([(72+side*13,86),(72+side*39,66),(72+side*55,76),(72+side*37,89),(72+side*24,99)],B)
  else:
   p.ell((38,77+bob,106,118+bob),B);p.poly([(45,102+bob),(59,113+bob),(94,112+bob),(104,100+bob),(101,113+bob),(86,120+bob),(52,117+bob)],S,None);p.line([(48,84+bob),(65,80+bob),(79,82+bob)],H,2)
  if shell:
   p.ell((36,68+bob,108,118+bob),S);p.poly([(58,72+bob),(80,72+bob),(94,89+bob),(83,106+bob),(58,106+bob),(46,89+bob)],B)
   p.poly([(60,77+bob),(77,77+bob),(87,89+bob),(78,101+bob),(61,101+bob),(52,89+bob)],H);p.line([(61,101+bob),(56,112+bob)],D);p.line([(78,101+bob),(86,111+bob)],D);p.line([(52,89+bob),(39,91+bob)],D);p.line([(87,89+bob),(104,92+bob)],D)
  # Head projects toward the foreground/right: readable from overhead.
  xx=96 if not bird else 86;yy=h+11 if not bird else h
  if kind in ['deer','moonhart']:p.poly([(82,99+bob),(82,74+bob),(90,65+bob),(103,76+bob),(106,104+bob)],B)
  p.ell((xx-17,yy-16,xx+17,yy+17),B);p.poly([(xx-13,yy+5),(xx-6,yy+18),(xx+13,yy+15),(xx+20,yy+5),(xx+13,yy+1)],H if kind in ['wolf','fox','emberfox','tiger','bear','rabbit'] else B)
  if kind in ['wolf','fox','emberfox','tiger','rabbit','deer','moonhart','bear','sheep','boar','dragon']:
   for side in [-1,1]:
    ex=xx+side*11
    if kind=='rabbit':p.ell((ex-5,yy-49,ex+5,yy-8),B);p.line([(ex,yy-43),(ex,yy-16)],S,2)
    elif kind in ['bear','sheep']:p.ell((ex-6,yy-23,ex+6,yy-11),B)
    else:p.poly([(ex-5,yy-10),(ex+side*7,yy-29),(ex+7,yy-8)],B);p.line([(ex,yy-15),(ex+side*3,yy-23)],S)
  if kind in ['deer','moonhart']:
   for side in [-1,1]:
    p.line([(xx+side*8,yy-12),(xx+side*15,yy-33),(xx+side*11,yy-45)],O,4);p.line([(xx+side*8,yy-12),(xx+side*15,yy-33),(xx+side*11,yy-45)],H,2);p.line([(xx+side*14,yy-32),(xx+side*24,yy-38)],H,2)
  if kind=='sheep':
   for a,b in [(45,83),(50,74),(62,73),(76,74),(84,81),(43,94),(54,101),(67,103),(79,101)]:p.ell((a-6,b+bob-5,a+6,b+bob+6),H)
  if kind=='boar':p.ell((xx-8,yy+5,xx+15,yy+18),S);p.dot(xx-2,yy+9,D,3);p.dot(xx+8,yy+9,D,3);p.poly([(xx-10,yy+12),(xx-14,yy+3),(xx-16,yy+16)],H)
  elif bird:
   p.poly([(xx+8,yy+2),(xx+25,yy+9),(xx+11,yy+14)],H)
   if kind=='chicken':p.poly([(xx-9,yy-15),(xx-9,yy-26),(xx-3,yy-21),(xx,yy-30),(xx+5,yy-23),(xx+10,yy-25),(xx+10,yy-12)],S);p.ell((xx+7,yy+14,xx+13,yy+25),S)
  elif not shell:p.poly([(xx+5,yy+6),(xx+15,yy+6),(xx+10,yy+11)],O)
  if kind=='dragon':
   for side in [-1,1]:p.poly([(67,82),(67+side*20,46),(67+side*45,58),(67+side*31,71),(67+side*32,83),(67+side*19,79),(67+side*12,91)],S);p.line([(67,82),(67+side*20,46),(67+side*19,79)],H,2)
   for dx in range(45,84,9):p.poly([(dx,81),(dx+5,70),(dx+9,82)],H)
  return im
 # Separate phenotype layers use exactly the same animal pose and baby scale.
 x=96 if not bird else 86;y=h+11 if not bird else h
 if spider:x,y=72,108+bob
 if layer=='eyes':
  if spider:
   for dx,dy in [(-10,2),(-4,-2),(4,-2),(10,2)]:p.ell((72+dx-2,105+bob+dy-2,72+dx+2,105+bob+dy+2),H)
  elif serpent:p.ell((96,h+4,101,h+10),H);p.line([(98,h+4),(98,h+10)],D)
  else:
   for dx in [-8,8]:
    if f==10:p.line([(x+dx-2,y-1),(x+dx+2,y+2)],O)
    elif f in [8,9]:p.line([(x+dx-3,y),(x+dx+2,y)],O)
    else:p.ell((x+dx-3,y-3,x+dx+3,y+2),H);p.rect((x+dx,y-2,x+dx+1,y+1),S);p.dot(x+dx,y-2,L)
  return im
 if layer=='pattern':
  if v==0:return im
  if serpent:
   for j in range(6):p.gem(51+j*6,101+int(math.sin(j)*9),3+(v==4),D if v%2 else H)
  elif spider:
   for j in range(3+v):p.gem(60+j%3*10,77+j//3*10,3,H if v%2 else D)
  else:
   if v==1:
    for dx,dy in [(48,87),(62,93),(75,85),(87,100)]:p.ell((dx-3,dy+bob-3,dx+3,dy+bob+3),H)
   elif v==2:
    for dx in [48,60,72,84]:p.poly([(dx,80+bob),(dx+5,83+bob),(dx+2,98+bob),(dx-3,101+bob)],D,None)
   elif v==3:p.poly([(43,90+bob),(54,81+bob),(79,82+bob),(88,91+bob),(77,100+bob),(55,101+bob)],H)
   elif v==4:
    for dx,dy in [(49,88),(62,96),(78,87),(88,99),(69,81)]:p.ell((dx-5,dy+bob-4,dx+5,dy+bob+4),D);p.ell((dx-2,dy+bob-1,dx+2,dy+bob+1),B,None)
  return im
 if layer=='crest':
  if v==0:return im
  if v==1:
   for side in [-1,1]:p.poly([(x+side*11,y-13),(x+side*18,y-35),(x+side*21,y-17)],B)
  elif v==2:
   for dx in [-9,-3,3,9]:p.poly([(x+dx-4,y-13),(x+dx,y-31-abs(dx)//2),(x+dx+5,y-13)],B)
  elif v==3:p.poly([(x-17,y-7),(x-24,y-15),(x-10,y-19),(x,y-32),(x+9,y-19),(x+22,y-14),(x+16,y-6)],B);p.gem(x,y-17,4,H)
  return im
 if layer=='accent':
  if v==0:p.poly([(x-9,y+8),(x+10,y+8),(x+6,y+16),(x-5,y+16)],H)
  elif v==1:p.line([(x-12,y-6),(x-5,y-8),(x-2,y-4)],H,2);p.line([(x+5,y-8),(x+12,y-6)],H,2)
  elif v==2:
   for dx in [-12,12]:p.gem(x+dx,y+4,3,H)
  else:p.gem(x,y-10,5,H);p.line([(x-6,y+13),(x,y+16),(x+6,y+13)],H)
  return im
 if layer=='ancient':
  # Glow is deliberately made of opaque, stepped rings and sparks, never blur.
  c='#89d9cf';bright='#e6f5cc';dark='#467c91';cx,cy=(68,93+bob)
  p.poly([(cx,cy-11),(cx+8,cy),(cx,cy+11),(cx-8,cy)],dark);p.poly([(cx,cy-7),(cx+5,cy),(cx,cy+7),(cx-5,cy)],c);p.line([(cx,cy-3),(cx,cy+3)],bright,2)
  for j in range(4):
   a=(f/14+j/4)*math.tau;xx=cx+math.cos(a)*20;yy=cy+math.sin(a)*15;p.gem(xx,yy,2,bright)
  return im
 return im

def generate_beasts():
 for kind in BEASTS:
  M['beasts'][kind]={'tint':BEAST_COLORS[kind],'ages':{}}
  for age in ['baby','adult']:
   d={};prefix=f'beasts/{kind}/{age}'
   for layer,count in [('body',1),('pattern',5),('crest',4),('tail',4),('eyes',4),('accent',4),('ancient',1)]:
    def render(v,f):
     im=beast_frame(kind,age,f,layer,v)
     if layer=='pattern':
      im.putalpha(ImageChops.multiply(im.getchannel('A'),beast_frame(kind,age,f,'body',0).getchannel('A')))
      clean=blank();clean.paste(im,mask=im.getchannel('A'));im=clean
     return im
    d[layer]=write_sheet(f'{prefix}/{layer}.png',list(range(count)),render,layer!='ancient')
   M['beasts'][kind]['ages'][age]=d
  print('beast',kind,flush=True)

ROOT_COLORS=['#e99a55','#77accb','#85a765','#b89b73','#b8c7ca','#a8d7df','#e3d374','#b7cec2','#cf6b49','#a9b9c4','#77678d','#e8d79e','#a6b876','#bd6975','#9d88b7','#8d9dc7','#d7c797','#b8a3cd','#e9bc70','#b0c7db','#c1bddc','#736e9b','#8bc8c1','#c1a7d4','#b68fca','#a6d3bb','#d4c9a5','#afcbd9','#a9c67e','#a39bb2']
def aura_frame(root,f,tier=None):
 im=blank();p=Pen(im);v=ROOTS.index(root) if root in ROOTS else 0;base=ROOT_COLORS[v];dark=tuple(int(int(base[i:i+2],16)*.58) for i in [1,3,5]);light=tuple(min(255,int(int(base[i:i+2],16)*.65+86)) for i in [1,3,5]);n=6+(tier or 0)*2;rx=45+(tier or 0)*3;ry=10+(tier or 0)
 # Rotating discrete rune segments form a seamless 7-frame loop in slots 0..6.
 phase=(f%7)/7*math.tau
 for j in range(n):
  a=j/n*math.tau+phase;pts=[(72+math.cos(a+k*.065)*rx,125+math.sin(a+k*.065)*ry) for k in range(4)];p.line(pts,dark,3);p.line(pts,base)
 if tier is not None:
  for ring in range(tier+1):
   for j in range(4+ring):
    a=j/(4+ring)*math.tau-phase;x=72+math.cos(a)*(26+ring*5);y=113-ring*14+math.sin(a)*8;p.gem(x,y,1+(tier>2),base)
  if tier>=3:
   for side in [-1,1]:p.line([(72+side*53,119),(72+side*57,95),(72+side*50,74),(72+side*53,54)],base)
  return im
 # Each root has its own symbol vocabulary as well as its own discrete palette.
 for j in range(5):
  a=j/5*math.tau+phase;x=72+math.cos(a)*43;y=92+math.sin(a)*23
  if root in ['fire','magma','solar']:p.poly([(x-5,y+7),(x-7,y),(x-2,y-10),(x+1,y-4),(x+5,y-8),(x+7,y+1),(x+3,y+7)],base);p.poly([(x-2,y+5),(x,y-3),(x+3,y+4)],light,None)
  elif root in ['water','mist','blood']:p.poly([(x,y-8),(x+5,y+1),(x+3,y+6),(x-3,y+6),(x-5,y+1)],base);p.line([(x-2,y+1),(x-2,y+3)],light)
  elif root in ['wood','nature','life']:p.poly([(x-6,y+6),(x-5,y-2),(x+7,y-8),(x+5,y+3)],base);p.line([(x-4,y+4),(x+4,y-4)],light)
  elif root in ['earth','metal','crystal','ice']:p.poly([(x,y-9),(x+6,y-3),(x+4,y+7),(x-4,y+7),(x-6,y-3)],base);p.line([(x,y-6),(x,y+4),(x+3,y+5)],light)
  elif root=='lightning':p.poly([(x+2,y-10),(x-6,y+1),(x,y),(x-2,y+10),(x+7,y-3),(x+1,y-2)],base)
  elif root in ['wind','sound']:p.line([(x-7,y-3),(x+4,y-3),(x+7,y),(x+4,y+3),(x-4,y+3)],base,2);p.line([(x-4,y+6),(x+3,y+6)],light)
  elif root in ['shadow','void','death']:p.poly([(x,y-8),(x+6,y),(x,y+8),(x-6,y)],base);p.rect((x-1,y-4,x+2,y+4),dark)
  elif root in ['light','star','spirit']:p.poly([(x,y-8),(x+2,y-2),(x+7,y),(x+2,y+2),(x,y+8),(x-2,y+2),(x-7,y),(x-2,y-2)],light)
  elif root=='poison':
   for xx,yy,r in [(x,y,5),(x+5,y-7,2),(x-4,y-8,3)]:p.ell((xx-r,yy-r,xx+r,yy+r),base)
  elif root in ['gravity','space']:p.ell((x-8,y-5,x+8,y+5),None,base);p.gem(x,y,3,light)
  elif root=='time':p.poly([(x-6,y-8),(x+6,y-8),(x+1,y),(x+6,y+8),(x-6,y+8),(x-1,y)],base);p.line([(x-3,y-6),(x+3,y-6)],light)
  elif root=='lunar':p.ell((x-7,y-8,x+7,y+8),base);p.poly([(x+2,y-8),(x+7,y-6),(x+4,y+3),(x-1,y+4),(x-4,y)],dark,None)
  elif root in ['soul','dream','illusion']:p.line([(x-6,y+7),(x-2,y-5),(x+4,y-7),(x+7,y-2),(x+1,y+1)],base,2);p.gem(x-1,y-3,2,light)
  elif root=='bone':p.line([(x-4,y+5),(x+4,y-5)],base,4);p.ell((x-7,y+2,x-1,y+8),light);p.ell((x+1,y-8,x+7,y-2),light)
 return im

def generate_auras():
 M['auras']={}
 for root in ROOTS:M['auras'][root]=write_sheet(f'auras/roots/{root}.png',[0],lambda v,f:aura_frame(root,f))
 M['tiers']=write_sheet('auras/tiers.png',list(range(6)),lambda v,f:aura_frame('spirit',f,v))
 M['auraLoop']={'columns':[0,1,2,3,4,5,6],'fps':9,'note':'Root aura animation uses 0..6 as a seamless loop; slots 7..13 remain valid stackable action poses.'}
 print('auras complete',flush=True)

if __name__=='__main__':
 t=time.time();generate_people();generate_beasts();generate_auras()
 (OUT/'manifest.json').write_text(json.dumps(M,separators=(',',':')))
 print('DONE',len(M['sheets']),'sheets',round(time.time()-t,1),'seconds',flush=True)
