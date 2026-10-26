"""Export Stage 1 review PNGs and validate the actual native sprite.
No animation, body-part export, recolour system or sprite viewer is implemented.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from collections import Counter
import argparse,json,hashlib,shutil

def rgba(hexcode):return tuple(bytes.fromhex(hexcode.lstrip('#')))+(255,)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def font(size,bold=False):
 p='/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf'
 try:return ImageFont.truetype(p,size)
 except OSError:return ImageFont.load_default()
def connected_components(im):
 ps={(x,y) for y in range(im.height) for x in range(im.width) if im.getpixel((x,y))[3]};sizes=[]
 while ps:
  stack=[ps.pop()];n=0
  while stack:
   x,y=stack.pop();n+=1
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
    q=(x+dx,y+dy)
    if q in ps:ps.remove(q);stack.append(q)
  sizes.append(n)
 return sorted(sizes,reverse=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--build',type=Path,required=True);parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--repeat-build',type=Path);parser.add_argument('--reference-is-crop',action='store_true')
 a=parser.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True);src=Path(__file__).parent
 meta=json.loads((a.build/'render-metadata.json').read_text());raw=Image.frombytes('RGBA',(144,144),(a.build/'warrior-144.rgba').read_bytes());raw.save(out/'warrior-raw-144.png')
 im=raw.copy();cleanup=json.loads((src/'pixel-cleanup.json').read_text())
 allowed={rgba(h) for ramp in meta['palettes'].values() for h in ramp}|{rgba('#1f1b25'),rgba('#2f252b')}
 changed=0
 for x,y,h in cleanup['edits']:
  colour=rgba(h);assert colour in allowed and im.getpixel((x,y))[3]==255
  changed+=im.getpixel((x,y))!=colour;im.putpixel((x,y),colour)
 im.save(out/'warrior-144.png');large=im.resize((864,864),Image.Resampling.NEAREST);large.save(out/'warrior-nearest-6x.png')
 for name in ['blender-model-render.png','warrior-stage1.blend','render-metadata.json','blend-inspection.json']:
  shutil.copy2(a.build/name,out/name)
 stepped=Image.frombytes('RGBA',(720,720),(a.build/'model-stepped-render.rgba').read_bytes());stepped.save(out/'model-stepped-render.png')
 # Approved concept is cropped only for comparison; it never enters the production raster pipeline.
 reference=Image.open(a.reference).convert('RGBA')
 if not a.reference_is_crop:reference=reference.crop((16,126,235,505))
 reference.save(out/'approved-warrior-reference-crop.png')
 board=Image.new('RGBA',(1500,1140),'#171c24');d=ImageDraw.Draw(board)
 d.text((30,22),'TINY WORLD / WARRIOR / STAGE 1',font=font(30,True),fill='#e5c897')
 d.text((30,66),'STATIC VISUAL REVIEW — no rig, animation, modular reconstruction or game integration',font=font(15),fill='#c3c7c8')
 labels=[(30,'APPROVED PHASE 1 REFERENCE'),(405,'BLENDER MODEL RENDER'),(890,'ACTUAL SPRITE / EXACT 6x')]
 for x,label in labels:d.text((x,112),label,font=font(16,True),fill='#e5c897')
 # Reference illustration, standard Blender render and exact sprite enlargement are explicitly distinct.
 ref=reference.resize((347,600),Image.Resampling.NEAREST);board.alpha_composite(ref,(40,190))
 model=Image.open(out/'blender-model-render.png').convert('RGBA');model=model.crop(model.getbbox());model.thumbnail((440,600),Image.Resampling.LANCZOS);board.alpha_composite(model,(415+(440-model.width)//2,190))
 board.alpha_composite(large,(790,70))
 d.text((1030,850),'144 x 144 native PNG',font=font(16),fill='#e5c897');board.alpha_composite(im,(1100,875))
 d.text((30,1030),'Native sprite: direct 144 x 144 orthographic ray sampling + authored facial pixel cleanup.',font=font(17),fill='#c3c7c8')
 d.text((30,1061),'Ground anchor (72,130) | Binary alpha | Discrete palette | No baked background or ground shadow',font=font(17),fill='#c3c7c8')
 d.text((30,1100),'Artistic approval remains pending. Technical validation does not establish visual quality.',font=font(16),fill='#e5c897');board.save(out/'comparison.png')
 # Enlarged light/dark/checker views expose outlines and transparency. They are review backgrounds only.
 panel=Image.new('RGBA',(1440,640),'#171c24');pd=ImageDraw.Draw(panel)
 for i,bg in enumerate(['#24262d','#e9e2d0','checker']):
  x=i*480;pd.text((x+20,18),['DARK BACKGROUND','LIGHT BACKGROUND','TRANSPARENCY CHECK'][i],font=font(18,True),fill='#e5c897')
  back=Image.new('RGBA',(432,432),bg if bg!='checker' else '#a8adb2')
  if bg=='checker':
   dd=ImageDraw.Draw(back)
   for y in range(0,432,24):
    for xx in range(0,432,24):
     if (xx//24+y//24)%2:dd.rectangle((xx,y,xx+23,y+23),fill='#d8dce0')
  back.alpha_composite(im.resize((432,432),Image.Resampling.NEAREST));panel.alpha_composite(back,(x+24,65));pd.text((x+24,520),'Exact 3x nearest-neighbour preview',font=font(16),fill='#c3c7c8')
 pd.text((24,579),'Only warrior-144.png is the native transparent sprite; preview backgrounds are separate.',font=font(18),fill='#c3c7c8');panel.save(out/'transparency-review.png')
 inspection=json.loads((a.build/'blend-inspection.json').read_text())
 colours=Counter(im.getdata());alphas=Counter(im.getchannel('A').getdata());box=im.getbbox();comps=connected_components(im)
 # Validate enlarged image against every source channel, rather than trusting the resize call.
 enlarge_exact=True
 for y in range(864):
  for x in range(864):
   if large.getpixel((x,y))!=im.getpixel((x//6,y//6)):enlarge_exact=False;break
 repeat=None
 if a.repeat_build:repeat=(a.build/'warrior-144.rgba').read_bytes()==(a.repeat_build/'warrior-144.rgba').read_bytes()
 checks={
  'exact_144x144_rgba':im.size==(144,144) and im.mode=='RGBA',
  'binary_alpha_no_partial_pixels':set(alphas)=={0,255},
  'background_transparent':alphas[0]>0,
  'empty_pixels_have_zero_rgb':all(c[:3]==(0,0,0) for c in colours if c[3]==0),
  'declared_discrete_palette_only':all(c in allowed for c in colours if c[3]),
  'fully_inside_cell':box[0]>0 and box[1]>0 and box[2]<144 and box[3]<144,
  'visible_bottom_pixel_at_y130':box[3]-1==130,
  'figure_height_100_pixels':box[3]-box[1]==100,
  'body_root_projection_x72':abs(inspection['body_root_projected_x']-72)<0.001,
  'orthographic_camera':inspection['orthographic_camera'],
  'no_armature':inspection['armatures']==0,
  'no_animation_actions':inspection['animation_actions']==0,
  'no_ground_plane':inspection['no_ground_plane'],
  'single_connected_silhouette':len(comps)==1,
  'nearest_neighbour_all_pixels_exact':enlarge_exact,
  'repeat_native_render_identical':repeat,
 }
 if repeat is None:checks.pop('repeat_native_render_identical')
 report={'stage':1,'technical_checks_pass':all(checks.values()),'visual_quality':'awaiting user review; not certified by automated tests','production_approved':False,'checks':checks,'image':{'size':[144,144],'mode':im.mode,'visible_bounds_exclusive':list(box),'figure_height':box[3]-box[1],'visible_colour_count':len([c for c in colours if c[3]]),'transparent_pixels':alphas[0],'opaque_pixels':alphas[255],'partial_alpha_pixels':sum(n for k,n in alphas.items() if k not in (0,255)),'alpha_components':comps},'authored_native_pixel_changes':changed,'render_method':'Single pixel-centre orthographic ray per native pixel against original Blender meshes, discrete shading ramps, hard contact shading, silhouette outline and explicit authored facial corrections. No supersampling or downsized illustration.','model_render_note':'The separate 768px standard Blender Cycles model render has normal render filtering. Binary-alpha and no-antialiasing checks apply to the native sprite.','not_implemented':['rigging','animation','anatomical reconstruction','part variants','independent colour-mask assets','compositor','viewer','game integration'],'artistic_limitations':['3D-derived armour and hair styling differ from the hand-designed Phase 1 illustration.','Face and engraving detail are simplified at the 100px figure height.','A single static pose and direction establish no animation or modular-production readiness.'],'files':{name:sha(out/name) for name in ['warrior-144.png','warrior-nearest-6x.png','blender-model-render.png','warrior-stage1.blend']}}
 (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':checks,'technical_checks_pass':report['technical_checks_pass'],'visible_colours':report['image']['visible_colour_count'],'native_pixel_edits':changed},indent=2))
 assert report['technical_checks_pass'], 'Stage 1 technical validation failed'

if __name__=='__main__':main()
