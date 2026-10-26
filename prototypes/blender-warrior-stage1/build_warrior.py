"""Stage 1 only: original, static Blender mesh study and deterministic native-pixel render.
Run: blender -b --factory-startup --disable-autoexec --python build_warrior.py -- --out OUTPUT
No armature, animation, game integration, asset swapping or viewer is created.
"""
import bpy, math, random, json, argparse, sys, os, struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
from math import sin,cos,pi

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--skip-studio',action='store_true');opts=p.parse_args(args)
OUT=Path(opts.out).resolve();OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(91)
PALETTES={
 'steel':['#252b3c','#424e62','#718598','#b0c1c7','#e3e6d6'],
 'blade':['#343e52','#687e92','#9eb7c4','#cddbdc','#f0efdc'],
 'steel_dark':['#222837','#374354','#566b7d','#91a6b0'],
 'gold':['#5a382c','#916139','#c59654','#ecd18a'],
 'skin':['#50322d','#7e4b34','#ab7147','#d59b63','#edbb82'],
 'skin_dark':['#472f2b','#694132','#8c593b','#bb8150'],
 'cloth':['#361f2c','#642d32','#983d3e','#c2644c'],
 'cloth_dark':['#241f2b','#3b2933','#603439','#8c4841'],
 'leather':['#211e28','#3e2d2c','#654638','#967049'],
 'hair':['#291d27','#50272b','#81382f','#b65537','#da7d43'],
 'hair_dark':['#231d26','#41252a','#6b302d','#99432f'],
 'eye':['#171b25','#171b25','#2a2429','#4c342a'],
 'ivory':['#54473b','#908368','#c7b992','#e3d7b0'],
 'mouth':['#3f2630','#623634','#865044','#b16e52'],
}
def rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))
def lin(c):c=c/255;return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
LOOK=Vector((.36,-.84,.49)).normalized() # towards camera; ortho, approximately 30 degrees above horizontal
RIGHT=Vector((-LOOK.y,LOOK.x,0)).normalized();UP=LOOK.cross(RIGHT).normalized()
LIGHT=(-RIGHT*.65+LOOK*.35+Vector((0,0,.95))).normalized()
MATS={}
for name,ramps in PALETTES.items():
 mat=bpy.data.materials.new(name);mat.diffuse_color=tuple(v/255 for v in rgb(ramps[2]))+(1,);mat.use_nodes=True;mat['palette_key']=name
 n=mat.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=LIGHT
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='CONSTANT';cr=ramp.color_ramp
 while len(cr.elements)>1:cr.elements.remove(cr.elements[-1])
 for j,h in enumerate(ramps):
  e=cr.elements[0] if j==0 else cr.elements.new(j/len(ramps))
  e.position=j/len(ramps);e.color=tuple(lin(v) for v in rgb(h))+(1,)
 mat.node_tree.links.new(geo.outputs['Normal'],dot.inputs[0]);mat.node_tree.links.new(dot.outputs['Value'],ramp.inputs[0]);mat.node_tree.links.new(ramp.outputs['Color'],em.inputs['Color']);mat.node_tree.links.new(em.outputs[0],out.inputs['Surface']);MATS[name]=mat
OBJECTS=[]
def mesh(name,verts,faces,mat='steel',smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(MATS[mat]);
 for poly in me.polygons:poly.use_smooth=smooth
 ob['stage']='stage1_static';OBJECTS.append(ob);return ob

def rings(name,sections,mat='steel',segments=40):
 # Each authored section is z, centre-x, centre-y, horizontal radius, depth radius.
 vs=[];fs=[]
 for z,cx,cy,rx,ry in sections:
  for i in range(segments):
   a=2*pi*i/segments;vs.append((cx+rx*cos(a),cy+ry*sin(a),z))
 for j in range(len(sections)-1):
  for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
 fs.append(tuple(reversed(range(segments))));fs.append(tuple((len(sections)-1)*segments+i for i in range(segments)))
 return mesh(name,vs,fs,mat)

def tube(name,points,radii,mat='gold',sides=10,depths=None):
 points=[Vector(p) for p in points];vs=[];fs=[]
 for i,pt in enumerate(points):
  t=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized();guide=Vector((0,1,0))
  if abs(t.dot(guide))>.9:guide=Vector((1,0,0))
  u=t.cross(guide).normalized();v=t.cross(u).normalized();r=radii[i] if isinstance(radii,(list,tuple)) else radii;d=depths[i] if depths else r
  for k in range(sides):
   a=2*pi*k/sides;vs.append(pt+u*r*cos(a)+v*d*sin(a))
 for i in range(len(points)-1):
  for k in range(sides):a=i*sides+k;b=i*sides+(k+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+j for j in range(sides))]);return mesh(name,vs,fs,mat)

def path(name,pts,r=.018,mat='gold',sides=8):return tube(name,pts,r,mat,sides)
def ellipse_line(name,z,cx,cy,rx,ry,r=.018,mat='gold'):
 pts=[(cx+rx*cos(2*pi*i/64),cy+ry*sin(2*pi*i/64),z) for i in range(65)];return path(name,pts,r,mat)

def pebble(name,center,scale,mat='gold',seed=0):
 # Curved, explicitly contoured small form: rivets, curls, knuckles, eye and cheek detail.
 cx,cy,cz=center;rx,ry,rz=scale;segments=16;rings_n=10;vs=[];fs=[]
 for j in range(rings_n+1):
  a=pi*j/rings_n
  for i in range(segments):
   b=2*pi*i/segments;w=1+.045*sin(3*b+seed)*sin(a)**2
   vs.append((cx+rx*sin(a)*cos(b)*w,cy+ry*sin(a)*sin(b)*w,cz+rz*cos(a)))
 for j in range(rings_n):
  for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,a+segments,b+segments,b))
 return mesh(name,vs,fs,mat)

def cloth_panel(name,rows,mat='cloth'):
 # Contoured pleated cloth ribbon with side widths defined at every authored height.
 vs=[];fs=[];n=16
 for z,xl,xr,y,pleat in rows:
  for j in range(n+1):
   t=j/n;vs.append((xl+(xr-xl)*t,y+pleat*cos(t*6*pi),z+.012*sin(t*3*pi)))
 for k in range(len(rows)-1):
  for j in range(n):a=k*(n+1)+j;fs.append((a,a+1,a+n+2,a+n+1))
 return mesh(name,vs,fs,mat)

# Silhouette: custom-shaped undergarments, pelvic volume and fitted torso.
rings('padded_torso',[(1.76,0,.04,.32,.23),(1.94,0,.03,.39,.28),(2.18,0,.03,.35,.24),(2.46,0,.02,.44,.27),(2.70,0,.015,.52,.29),(2.87,0,.01,.45,.24),(2.94,0,0,.23,.19)],'cloth_dark')
rings('hip_leather',[(1.61,0,.04,.34,.24),(1.82,0,.02,.40,.29),(2.02,0,.02,.37,.26)],'leather')
# The central breastplate has a sculpted, convex profile instead of a rectangular chest.
rings('steel_cuirass',[(2.10,0,-.012,.345,.265),(2.20,0,-.008,.37,.285),(2.37,0,-.01,.405,.32),(2.57,0,-.008,.46,.35),(2.74,0,.006,.47,.30),(2.85,0,.02,.34,.225)],'steel')
# Breast contours, a subtle sternum ridge and gold-bound upper rim.
path('sternum_ridge',[(0,-.327,2.30),(0,-.372,2.52),(0,-.343,2.70)],.020,'steel')
path('cuirass_gold_neck',[(-.35,-.18,2.81),(-.25,-.255,2.73),(0,-.32,2.67),(.25,-.255,2.73),(.35,-.18,2.81)],.025,'gold')
for side in [-1,1]:
 path('pectoral_etched_seam'+str(side),[(side*.055,-.35,2.54),(side*.18,-.334,2.50),(side*.32,-.27,2.52)],.008,'steel_dark',6)
 path('cuirass_hem_'+str(side),[(side*.36,-.1,2.21),(side*.27,-.24,2.13),(side*.1,-.28,2.15)],.019,'gold')
 for x,z in [(side*.31,2.72),(side*.28,2.27)]:pebble('cuirass_rivet',(x,-.25,z),(.025,.02,.025),'gold')
for i in range(3):
 z=2.05+i*.10
 rings('articulated_abdominal_lame_'+str(i),[(z-.04,0,-.01,.36,.28),(z+.065,0,-.005,.365+i*.009,.29)],'steel_dark')
 ellipse_line('abdominal_edge_'+str(i),z-.025,0,-.01,.36,.285,.010,'steel')
# Oxblood scarf/cowl: curved folds around neck, asymmetric descending cloth.
rings('neck',[(2.88,0,.005,.14,.14),(3.16,0,-.005,.145,.145)],'skin')
rings('scarf_cowl',[(2.80,0,-.01,.22,.22),(2.88,0,-.02,.285,.245),(2.98,0,-.005,.245,.22),(3.06,0,0,.18,.17)],'cloth')
for z in [2.87,2.94]:path('scarf_fold', [(-.23,-.12,z+.03),(-.12,-.25,z-.02),(.07,-.25,z-.04),(.22,-.12,z)],.019,'cloth_dark')
cloth_panel('scarf_end',[(2.94,-.19,-.06,-.23,.014),(2.76,-.31,-.14,-.285,.018),(2.55,-.33,-.18,-.30,.02)],'cloth')
# Cape kept short, shaped to shoulders and off the ground.
cloth_panel('back_mantle',[(2.85,-.42,.43,.21,.018),(2.37,-.45,.49,.31,.025),(1.79,-.36,.42,.35,.038),(1.47,-.29,.34,.32,.04)],'cloth_dark')
# Split tabard with hem binding and visible pleat creases.
for side in [-1,1]:
 xl,xr=(-.32,-.02) if side<0 else (.02,.32)
 cloth_panel('tabard_'+str(side),[(2.08,xl*.9,xr*.9,-.32,.02),(1.83,xl,xr,-.36,.025),(1.43,xl*1.1,xr*1.1,-.32,.03),(1.27 if side<0 else 1.34,xl*.9,xr*.9,-.28,.024)],'cloth')
 xedge=xl if side<0 else xr
 path('tabard_binding_'+str(side),[(xedge*.9,-.335,2.03),(xedge,-.37,1.82),(xedge*1.1,-.33,1.45),(xedge*.9,-.30,1.28 if side<0 else 1.35)],.016,'gold')
# Leather girdle and contoured brass buckle.
rings('waist_belt',[(1.97,0,-.012,.40,.305),(2.10,0,-.012,.40,.305)],'leather')
ellipse_line('belt_upper_stitch',2.08,0,-.012,.405,.31,.008,'gold')
path('belt_buckle',[(-.09,-.335,2.095),(.08,-.335,2.085),(.095,-.338,1.98),(-.09,-.34,1.975),(-.09,-.335,2.095)],.022,'gold')
path('belt_tongue',[(0,-.36,2.075),(0,-.36,1.99)],.014,'gold')
for side in [-1,1]:
 # Hip straps and curved pouch with folded flap, no rectangular box geometry.
 rings('belt_pouch_'+str(side),[(1.65,side*.45,-.08,.12,.11),(1.69,side*.45,-.08,.16,.14),(1.85,side*.45,-.08,.17,.14),(1.91,side*.44,-.08,.13,.12)],'leather',28)
 path('pouch_flap_edge_'+str(side),[(side*.33,-.15,1.88),(side*.44,-.235,1.82),(side*.56,-.16,1.87)],.013,'gold')
 pebble('pouch_clasp',(side*.45,-.23,1.80),(.024,.015,.027),'gold')

# Legs: anatomical centre lines, shaped thighs, broad knees, tapered ankles and boot toes.
FOOT_OBJECTS=[]
for side in [-1,1]:
 sx=side*.255
 thigh=[(sx,.035,1.83),(sx+side*.015,.025,1.57),(sx+side*.035,-.005,1.28),(sx+side*.05,-.02,1.02)]
 tube('trouser_thigh_'+str(side),thigh,[.22,.23,.205,.17],'cloth_dark',24,depths=[.22,.22,.20,.17])
 tube('thigh_armour_'+str(side),[(sx,-.09,1.70),(sx+side*.02,-.105,1.52),(sx+side*.04,-.105,1.27)],[.195,.21,.165],'steel_dark',24,depths=[.15,.15,.13])
 path('thigh_gold_rim_'+str(side),[(sx-.15,-.15,1.69),(sx,-.245,1.72),(sx+.15,-.15,1.69)],.020,'gold')
 pebble('sculpted_knee_plate_'+str(side),(sx+side*.06,-.125,1.035),(.205,.18,.18),'steel')
 path('knee_ridge_'+str(side),[(sx+side*.06,-.31,1.14),(sx+side*.06,-.32,1.00)],.012,'steel_dark')
 legx=sx+side*.055
 tube('boot_shaft_'+str(side),[(legx,0,1.01),(legx+side*.012,.01,.72),(legx+side*.018,0,.40),(legx+side*.02,-.03,.22)],[.16,.16,.12,.14],'leather',24,depths=[.17,.15,.12,.15])
 tube('greave_'+str(side),[(legx,-.11,.92),(legx+side*.01,-.12,.70),(legx+side*.018,-.10,.37)],[.15,.135,.09],'steel',24,depths=[.085,.09,.07])
 path('greave_central_ridge_'+str(side),[(legx,-.205,.89),(legx+side*.01,-.22,.69),(legx+side*.018,-.17,.39)],.012,'steel_dark')
 for z in [.78,.42]:
  rings('boot_strap_'+str(side)+str(z),[(z-.025,legx,-.005,.17 if z>.5 else .14,.16 if z>.5 else .13),(z+.025,legx,-.005,.17 if z>.5 else .14,.16 if z>.5 else .13)],'leather',24)
  pebble('boot_clasp',(legx+side*.11,-.12,z),(.026,.024,.025),'gold')
 # Asymmetric forward-projecting leather feet, individually contoured sole and instep.
 bx=legx+side*.025
 ob=rings('foot_'+str(side),[(.035,bx,-.155,.165,.28),(.075,bx,-.17,.185,.32),(.16,bx,-.16,.18,.30),(.245,bx,-.07,.14,.20),(.30,bx,-.01,.115,.13)],'leather',40);FOOT_OBJECTS.append(ob)
 sole=rings('sole_'+str(side),[(.015,bx,-.16,.17,.29),(.055,bx,-.17,.185,.32)],'steel_dark',40);FOOT_OBJECTS.append(sole)
 path('toe_seam_'+str(side),[(bx-.12,-.34,.16),(bx,-.43,.13),(bx+.12,-.34,.16)],.010,'gold')

# Arms: authored bent centre lines, layered shoulder lames, articulated steel bracers.
HAND_POS={}
for side in [-1,1]:
 shoulder=Vector((side*.58,.015,2.73));elbow=Vector((side*.74,-.015,2.20));wrist=Vector((side*.73,-.16 if side<0 else -.05,1.76))
 tube('upper_sleeve_'+str(side),[shoulder,shoulder.lerp(elbow,.5),elbow],[.205,.20,.15],'cloth_dark',24)
 # Broad domed shoulder shell: convex top and cut, overlapping lames.
 for j,(z,rx,ry) in enumerate([(2.80,.29,.30),(2.58,.255,.265)]):
  sections=([(z-.09,side*.59,.005,rx,ry),(z+.02,side*.59,.005,rx*1.02,ry),(z+.16,side*.56,.015,rx*.73,ry*.75),(z+.20,side*.54,.018,rx*.25,ry*.35)] if j==0 else [(z-.07,side*.61,.005,rx,ry),(z+.02,side*.60,.005,rx*.97,ry*.97),(z+.045,side*.58,.01,rx*.85,ry*.87)])
  rings('pauldron_lame_'+str(side)+'_'+str(j),sections,'steel' if j==0 else 'steel_dark',40)
  ellipse_line('pauldron_bound_edge_'+str(side)+'_'+str(j),z-.065,side*.59,.005,rx,ry,.023 if j==0 else .017,'gold')
 for a in [-2.45,-1.57,-.72]:pebble('pauldron_rivet',(side*.59+.27*cos(a),.005+.28*sin(a),2.74),(.025,.025,.026),'gold')
 pebble('elbow_couter_'+str(side),elbow,(.185,.18,.18),'steel_dark')
 tube('forearm_underlayer_'+str(side),[elbow,elbow.lerp(wrist,.5),wrist],[.155,.145,.115],'cloth',24)
 a=elbow.lerp(wrist,.15);b=elbow.lerp(wrist,.90)
 tube('vambrace_'+str(side),[a,a.lerp(b,.45),b],[.175,.16,.125],'steel',32,depths=[.15,.14,.105])
 for frac,r in [(.17,.177),(.87,.13)]:
  q=elbow.lerp(wrist,frac);d=(wrist-elbow).normalized();u=d.cross(Vector((0,1,0))).normalized();v=d.cross(u)
  pts=[q+(u*cos(2*pi*j/40)+v*sin(2*pi*j/40))*r for j in range(41)];path('bracer_binding',pts,.018,'gold')
 hp=wrist+Vector((0,-.018,-.14));HAND_POS[side]=hp
 pebble('hand_palm_'+str(side),hp,(.115,.085,.15),'skin')
 # Segmented finger curls; geometry is anatomically placed and partially enclosed by gauntlet.
 for k in range(4):
  fx=hp.x-.075+k*.047
  pts=[(fx,hp.y-.035,hp.z+.015),(fx,hp.y-.085,hp.z-.055),(fx,hp.y-.068,hp.z-.12)]
  tube('finger_'+str(side)+'_'+str(k),pts,[.027,.029,.022],'skin',10)
  pebble('knuckle_plate',(fx,hp.y-.047,hp.z+.035),(.028,.025,.025),'steel')
 tube('thumb_'+str(side),[(hp.x-side*.09,hp.y-.005,hp.z+.07),(hp.x-side*.13,hp.y-.07,hp.z+.015),(hp.x-side*.08,hp.y-.10,hp.z-.04)],[.035,.036,.028],'skin',12)

# Head: ring-authored jaw, cheekbones and brow, with sculpted facial features.
rings('head_sculpt',[(3.015,0,-.025,.08,.10),(3.055,0,-.025,.16,.15),(3.14,0,-.005,.218,.193),(3.25,0,.005,.245,.215),(3.35,0,.008,.24,.208),(3.45,0,.012,.222,.19),(3.52,0,.02,.17,.15),(3.55,0,.02,.07,.065)],'skin',64)
# Low cheek planes and shaped chin reinforce an adult face, avoiding a spherical head.
for side in [-1,1]:
 pebble('cheekbone_'+str(side),(side*.145,-.15,3.215),(.075,.035,.049),'skin')
 pebble('ear_'+str(side),(side*.247,.012,3.245),(.052,.055,.10),'skin')
 pebble('ear_concha_'+str(side),(side*.28,-.01,3.25),(.018,.034,.055),'skin_dark')
 # Small almond-shaped eye sockets and raised upper lids; approximately 1-2 sprite pixels.
 pebble('eye_socket_'+str(side),(side*.095,-.199,3.315),(.073,.025,.035),'skin_dark')
 pebble('sclera_'+str(side),(side*.095,-.222,3.315),(.047,.014,.015),'ivory')
 pebble('iris_'+str(side),(side*.083,-.236,3.315),(.014,.009,.016),'eye')
 path('upper_eyelid_'+str(side),[(side*.04,-.22,3.337),(side*.10,-.228,3.343),(side*.15,-.202,3.33)],.012,'skin_dark')
 path('eyebrow_'+str(side),[(side*.04,-.215,3.37),(side*.105,-.225,3.378),(side*.163,-.193,3.365)],.018,'hair_dark')
# Sculpted triangular nose bridge with planes, nostrils and a small tip.
mesh('nose', [(-.037,-.205,3.36),(.037,-.205,3.36),(-.044,-.285,3.22),(.044,-.285,3.22),(0,-.32,3.245),(0,-.252,3.34),(0,-.275,3.20)],[(0,1,5),(0,5,4,2),(1,3,4,5),(2,4,6),(4,3,6),(2,6,3)],'skin',True)
for side in [-1,1]:pebble('nostril',(side*.035,-.281,3.225),(.015,.009,.009),'skin_dark')
path('mouth_line',[(-.075,-.192,3.137),(-.035,-.215,3.13),(.025,-.219,3.132),(.067,-.20,3.14)],.010,'mouth')
pebble('lower_lip',(0,-.211,3.112),(.047,.018,.013),'skin')
# Close-cropped auburn hair: contiguous scalp and deliberately placed curl groups.
rings('hair_cap',[(3.38,0,.02,.21,.19),(3.45,0,.025,.24,.215),(3.55,0,.025,.23,.205),(3.62,0,.02,.18,.17),(3.63,0,.02,.12,.12)],'hair_dark',48)
for row in range(4):
 z=3.43+row*.058;rx=[.23,.24,.22,.16][row];ry=[.205,.21,.19,.15][row];n=[15,15,12,9][row]
 for j in range(n):
  a=2*pi*(j+.4*(row%2))/n
  # Cropped hairline remains above eyes and exposes ears.
  if row==0 and sin(a)<-.35:zj=z+.025
  else:zj=z
  cx=rx*cos(a);cy=.025+ry*sin(a)
  pebble('curl_'+str(row)+'_'+str(j),(cx,cy,zj),(.055,.055,.056),'hair' if (j+row)%4 else 'hair_dark',j)
for i,(x,y) in enumerate([(-.10,-.08),(0,-.12),(.09,-.08),(-.07,.03),(.04,.03),(0,.11)]):pebble('crown_curl_'+str(i),(x*1.35,y,3.63),(.075,.07,.055),'hair',i)
# Short sideburns.
for side in [-1,1]:tube('sideburn_'+str(side),[(side*.22,-.04,3.43),(side*.23,-.04,3.34)],[.038,.026],'hair_dark',12)

# Sword: tapered diamond cross-section, spine, shaped swept guard, bound grip and pommel.
hand=HAND_POS[-1];blade_dir=Vector((.88,-.26,-.92)).normalized();sword_right=Vector((1,0,0));sword_right=(sword_right-blade_dir*sword_right.dot(blade_dir)).normalized();sword_depth=blade_dir.cross(sword_right).normalized()
grip_center=hand+Vector((0,-.075,.02));guard=grip_center+blade_dir*.15
base=guard+blade_dir*.08
vs=[]
for dist,width,thick in [(0,.09,.022),(.25,.085,.021),(1.36,.063,.018),(1.65,0,0)]:
 q=base+blade_dir*dist
 vs.extend([q+sword_right*width,q+sword_depth*thick,q-sword_right*width,q-sword_depth*thick])
faces=[]
for k in range(3):
 for i in range(4):faces.append((k*4+i,k*4+(i+1)%4,(k+1)*4+(i+1)%4,(k+1)*4+i))
mesh('forged_diamond_blade',vs,faces,'blade',False)
path('blade_fuller',[base+blade_dir*.12+sword_depth*.025,base+blade_dir*1.31+sword_depth*.020],.009,'steel_dark',6)
# Each side of the crossguard sweeps towards the blade tip.
for side in [-1,1]:
 pts=[guard,guard+sword_right*side*.14,guard+sword_right*side*.25+blade_dir*.04,guard+sword_right*side*.29+blade_dir*.10]
 tube('swept_guard_'+str(side),pts,[.035,.04,.032,.025],'gold',12)
rear=guard-blade_dir*.36
tube('sword_grip',[rear,guard-blade_dir*.04],[.047,.045],'leather',16)
for i in range(6):
 q=rear+blade_dir*(.04+i*.044);pts=[q+(sword_right*cos(2*pi*j/16)+sword_depth*sin(2*pi*j/16))*.05 for j in range(17)];path('grip_binding',pts,.007,'gold',6)
pebble('sword_pommel',rear-blade_dir*.045,(.072,.065,.072),'gold')

# Additional designed details: curved sabatons, armoured hand backs and embossed cuirass ornament.
for side in [-1,1]:
 legx=side*.255+side*.055;bx=legx+side*.025
 for j,(front,back) in enumerate([(-.45,-.36),(-.36,-.27),(-.27,-.18)]):
  vs=[];faces=[]
  for row,y in enumerate([front,(front+back)/2,back]):
   for k in range(13):
    t=k/12;x=bx+(t-.5)*.29
    z=.16+.055*sin(pi*t)+.020*row/2
    vs.append((x,y,z))
  for row in range(2):
   for k in range(12):a=row*13+k;faces.append((a,a+1,a+14,a+13))
  mesh('sabatons_'+str(side)+'_'+str(j),vs,faces,'steel_dark')
  path('sabaton_edge',[(bx+(k/12-.5)*.29,front-.003,.16+.055*sin(pi*k/12)) for k in range(13)],.009,'steel')
 # A hanging, pointed upper-arm plate replaces a repeated cylindrical band.
 ex=side*.68
 vs=[(ex-side*.13,-.19,2.59),(ex+side*.13,-.19,2.59),(ex+side*.12,-.21,2.34),(ex,-.25,2.28),(ex-side*.12,-.21,2.34)]
 mesh('upper_arm_pointed_plate_'+str(side),vs,[(0,1,2,3,4)],'steel_dark',False)
 path('upper_arm_bound_tip', [vs[2],vs[3],vs[4]],.013,'gold')
 # Small, authored rivet arrangement on the front shoulder face.
 for dx,dz in [(-.11,0),(0,-.05),(.11,0)]:
  pebble('shoulder_front_rivet',(side*.59+dx,-.285,2.79+dz),(.021,.018,.021),'gold')
# A restrained metalwork ornament and vertical engraved seams: visible at larger model scale.
path('cuirass_engraved_left',[(-.20,-.31,2.62),(-.24,-.318,2.48),(-.18,-.32,2.34)],.009,'steel_dark')
path('cuirass_engraved_right',[(.20,-.31,2.62),(.24,-.318,2.48),(.18,-.32,2.34)],.009,'steel_dark')
path('cuirass_small_knot',[(0,-.365,2.57),(-.05,-.36,2.52),(0,-.365,2.47),(.05,-.36,2.52),(0,-.365,2.57)],.013,'gold')
# Widen the head slightly while preserving the mature jaw and close-cropped hair silhouette.
head_prefixes=('head_sculpt','cheekbone','ear_','ear_concha','eye_socket','sclera','iris','upper_eyelid','eyebrow','nose','nostril','mouth_line','lower_lip','hair_cap','curl_','crown_curl','sideburn')
for ob in OBJECTS:
 if ob.name.startswith(head_prefixes):
  for v in ob.data.vertices:
   v.co.x*=1.10;v.co.y*=1.05;v.co.z=3.02+(v.co.z-3.02)*1.045
  ob.data.update()

# Scene, camera and a saveable standard Blender model render.
scene=bpy.context.scene
cam_data=bpy.data.cameras.new('Warrior_orthographic');cam=bpy.data.objects.new('Warrior_orthographic',cam_data);bpy.context.collection.objects.link(cam);scene.camera=cam;cam_data.type='ORTHO'
# Exact sprite framing is derived from authored head and boot geometry, never from a concept image.
headverts=[v.co for ob in OBJECTS if ob.name.startswith(('head_sculpt','hair_cap','curl_','crown_curl')) for v in ob.data.vertices]
footverts=[v.co for ob in FOOT_OBJECTS for v in ob.data.vertices]
top=max(v.dot(UP) for v in headverts);bottom=min(v.dot(UP) for v in footverts)
UPP=(top-bottom)/98.0;VTOP=bottom+130*UPP;U0=0.0
# Camera looks through image centre. The outlined boot contact is placed on pixel row 130.
centre=UP*(VTOP-72*UPP)+RIGHT*U0
cam.location=centre+LOOK*12;cam.rotation_euler=(-LOOK).to_track_quat('-Z','Y').to_euler();cam_data.ortho_scale=144*UPP
scene.render.film_transparent=True;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world.color=(.05,.05,.05)
scene['stage']='Stage 1 only - static artistic quality study';scene['pixel_cell']='144x144';scene['body_anchor']='72,130';scene['no_rig']=True;scene['no_animation']=True
scene['pixel_renderer']='orthographic pixel-centre ray queries; discrete material ramps; no supersampling or image reduction'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'warrior-stage1.blend'),compress=True)
if not opts.skip_studio:
 try:
  import addon_utils;addon_utils.enable('cycles',default_set=False,persistent=False)
  scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=False
  scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.filepath=str(OUT/'blender-model-render.png')
  bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'warrior-stage1.blend'),compress=True)
  bpy.ops.render.render(write_still=True)
 except Exception as e:
  (OUT/'studio-render-error.txt').write_text(str(e));print('STUDIO_RENDER_ERROR',str(e))

# Build a shared triangle BVH from the original Blender geometry.
verts=[];normals=[];tris=[];tri_info=[]
for oid,ob in enumerate(OBJECTS):
 me=ob.data;me.calc_loop_triangles();me.update();off=len(verts);verts.extend(v.co.copy() for v in me.vertices);normals.extend(v.normal.copy() for v in me.vertices)
 for tri in me.loop_triangles:
  ids=tuple(off+i for i in tri.vertices);tris.append(ids);tri_info.append((ob.data.materials[0]['palette_key'],tri.use_smooth,tri.normal.copy(),oid))
bvh=BVHTree.FromPolygons(verts,tris,all_triangles=True)
# Interpolate surface normals for smooth curved modelling; final shades remain discrete.
def normal_at(ti,pt):
 ids=tris[ti];a,b,c=[verts[i] for i in ids];v0=b-a;v1=c-a;v2=pt-a;d00=v0.dot(v0);d01=v0.dot(v1);d11=v1.dot(v1);d20=v2.dot(v0);d21=v2.dot(v1);den=d00*d11-d01*d01
 if abs(den)<1e-16:return tri_info[ti][2]
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den
 n=normals[ids[0]]*(1-v-w)+normals[ids[1]]*v+normals[ids[2]]*w
 return n.normalized() if n.length else tri_info[ti][2]

def render_pixels(size,label,outline):
 scale=144/size;buf=bytearray(size*size*4);depth=[0.0]*(size*size);objids=[-1]*(size*size);nvalues=[None]*(size*size);hit_count=0
 pal={k:[rgb(h) for h in v] for k,v in PALETTES.items()}
 for y in range(size):
  v=VTOP-(y+.5)*UPP*scale
  for x in range(size):
   u=((x+.5)*scale-72)*UPP;origin=RIGHT*u+UP*v+LOOK*12
   loc,no,ti,dist=bvh.ray_cast(origin,-LOOK,25)
   if ti is None:continue
   key,smooth,face,oid=tri_info[ti];n=normal_at(ti,loc) if smooth else face
   if n.dot(LOOK)<0:n=-n
   nd=max(0.0,n.dot(LIGHT));shade=max(.035,min(.999,.12+nd*.86))
   if key.startswith('skin'):shade=.26+nd*.73
   if key.startswith('hair'):shade=.18+nd*.80
   # A hard local cast shadow gives armour/clothing contact without a ground-plane shadow.
   sl,sn,si,sd=bvh.ray_cast(loc+n*.002,LIGHT,1.2)
   if si is not None and sd>.004:shade*=.76 if key.startswith(('skin','hair')) else .57
   ramp=pal[key]
   thresholds=([.0,.24,.48,.74,.94] if len(ramp)==5 else [.0,.25,.53,.82])
   ix=max(j for j,t in enumerate(thresholds) if shade>=t);col=ramp[ix]
   idx=y*size+x;buf[idx*4:idx*4+4]=bytes((*col,255));depth[idx]=loc.dot(LOOK);objids[idx]=oid;nvalues[idx]=n;hit_count+=1
 # One-pixel outer outline at native resolution. No drawn ground shadow.
 if outline:
  original=bytes(buf);ink=(31,27,37,255)
  for y in range(1,size-1):
   for x in range(1,size-1):
    idx=y*size+x
    if original[idx*4+3]==0:
     if any(original[(idx+off)*4+3] for off in [-1,1,-size,size]):buf[idx*4:idx*4+4]=bytes(ink)
    elif nvalues[idx] is not None:
     # Restrained occlusion contours at actual surface discontinuities, not mesh polygon boundaries.
     for off in [1,size]:
      q=idx+off
      if original[q*4+3] and objids[q]!=objids[idx] and depth[idx]-depth[q]>.095:
       col=original[idx*4:idx*4+3]
       if sum(col)>210:buf[idx*4:idx*4+3]=bytes((47,37,43))
       break
 (OUT/(label+'.rgba')).write_bytes(buf)
 return {'name':label,'width':size,'height':size,'ray_surface_hits':hit_count,'ray_samples_per_pixel':1,'supersampling':False,'downscaled_illustration':False,'outline':outline}
results=[render_pixels(144,'warrior-144',True),render_pixels(720,'model-stepped-render',False)]
manifest={'stage':1,'production_approved':False,'cell':[144,144],'body_centre_x':72,'feet_anchor_y':130,'target_figure_height':100,'camera_look':list(LOOK),'world_units_per_pixel':UPP,'palettes':PALETTES,'mesh_objects':len(OBJECTS),'vertices':len(verts),'triangles':len(tris),'renders':results,'excluded':['rigging','animation','modular reconstruction','colour variants','compositor','viewer','game integration']}
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
q=world_to_camera_view(scene,cam,Vector((0,0,0)))
inspection={'blender_version':bpy.app.version_string,'body_root_projected_x':q.x*144,'orthographic_camera':cam.data.type=='ORTHO','armatures':sum(o.type=='ARMATURE' for o in scene.objects),'animation_actions':len(bpy.data.actions),'mesh_count':sum(o.type=='MESH' for o in scene.objects),'render_engine':scene.render.engine,'transparent_film':scene.render.film_transparent,'no_ground_plane':not any(o.name.lower().startswith(('ground','floor','plane')) for o in scene.objects)}
(OUT/'blend-inspection.json').write_text(json.dumps(inspection,indent=2)+'\n')
(OUT/'render-metadata.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('STAGE1_RENDER_DONE',json.dumps({'objects':len(OBJECTS),'triangles':len(tris),'out':str(OUT)}))
