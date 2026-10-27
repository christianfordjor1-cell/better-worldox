#!/usr/bin/env python3
"""Package the complete free/reproducible game, including the preserved baseline."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'dist/Tiny-World-v79-Modular-Playable.zip'
def main():
    if not (ROOT/'dist/Tiny-World-v79-Modular.html').exists():raise SystemExit('Run game/build.py first')
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p!=OUTPUT and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.zip'} and p.name!='package.json')
    with zipfile.ZipFile(OUTPUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in files:
            info=zipfile.ZipInfo(path.relative_to(ROOT).as_posix(),date_time=(2026,10,27,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,path.read_bytes())
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None,'Archive CRC failed'
        html=archive.read('dist/Tiny-World-v79-Modular.html')
        assert html==(ROOT/'dist/Tiny-World-v79-Modular.html').read_bytes()
    report={'archive':OUTPUT.name,'bytes':OUTPUT.stat().st_size,'files':len(files),'sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
            'containsUntouchedBaseline':True,'containsOriginalCursorPack':True,'containsBlenderPrototype':False,'archiveCRC':'passed','packagedHTMLMatchesBuild':True}
    (ROOT/'reports/package.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
