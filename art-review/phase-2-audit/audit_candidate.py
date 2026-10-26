"""Read-only audit of generated anatomy candidates; never converts them to assets."""
import argparse,json
from pathlib import Path
from collections import Counter
from PIL import Image

def audit(path,expected):
    im=Image.open(path).convert('RGBA')
    counts=Counter(im.getdata())
    alpha=Counter()
    for rgba,n in counts.items(): alpha[rgba[3]]+=n
    visible={rgba[:3] for rgba in counts if rgba[3]>0}
    partial=sum(n for a,n in alpha.items() if 0<a<255)
    checks={
        'requested_canvas_size': im.size==(expected,expected),
        'divisible_into_four_by_four_grid': im.width%4==0 and im.height%4==0,
        'transparent_background_present':alpha[0]>0,
        'binary_alpha_only':partial==0,
        'visible_colours_within_16_times_32_upper_bound':len(visible)<=16*32,
    }
    return {'file':Path(path).name,'expected_canvas':[expected,expected],
        'actual_canvas':list(im.size),'unique_rgba':len(counts),
        'visible_rgb_colours':len(visible),'transparent_pixels':alpha[0],
        'opaque_pixels':alpha[255],'partial_alpha_pixels':partial,
        'alpha_levels':len(alpha),'checks':checks,
        'machine_checks_pass':all(checks.values()),
        'production_ready':False,
        'not_verified':['144x144 layer alignment','feet and body anchors','attachment continuity',
            'independent facial and material masks','frame poses and animation',
            'anatomical variations','artistic quality at native scale']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('path');p.add_argument('--expected',type=int,required=True)
    a=p.parse_args();print(json.dumps(audit(a.path,a.expected),indent=2))
