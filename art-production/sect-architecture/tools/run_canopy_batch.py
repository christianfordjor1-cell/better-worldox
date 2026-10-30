#!/usr/bin/env python3
"""Sequential, explicitly budgeted PixelLab recipes. Uses existing free quota.

Completed local masters are never regenerated. Inspect the request files before
running: creating a missing image consumes one existing PixelLab generation.
"""
import base64,json,re,time
from pathlib import Path
from pixellab_client import call

ROOT=Path(__file__).resolve().parents[1]/'canopy-village'
PRIVATE=Path('/workspace/pixellab-session')

def text(result):return '\n'.join(c.get('text','') for c in result.get('content',[]) if c.get('type')=='text')
def finish(name,job):
    start=time.monotonic()
    while time.monotonic()-start<420:
        result=call('get_image',{'job_id':job})
        (PRIVATE/(name+'-result.json')).write_text(json.dumps(result,indent=2))
        blocks=[c for c in result.get('content',[]) if c.get('type')=='image']
        if blocks:
            if len(blocks)!=1:raise RuntimeError('Unexpected multi-frame result')
            (ROOT/'masters'/f'{name}.png').write_bytes(base64.b64decode(blocks[0]['data']))
            receipt={'tool':'edit_image_pixen','job_id':job,'source':'masters/hall-a.png',
                     'receipt':text(result),'isError':result.get('isError',False)}
            (ROOT/'receipts'/f'{name}.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print(json.dumps({'asset':name,'status':'completed','job_id':job}),flush=True);return
        if result.get('isError') or re.search(r'status:\s*failed',text(result),re.I):
            raise RuntimeError('Generation failed for '+name)
        wait=call('wait_for_jobs',{'timeout_seconds':35,'min_finished':1},timeout=45)
        if wait.get('isError'):raise RuntimeError('Wait request failed')
    raise RuntimeError('Timed out; inspect existing job before retrying: '+job)

def main():
    order=json.loads((ROOT/'generation-order.json').read_text())
    (ROOT/'receipts').mkdir(exist_ok=True)
    for name in order['assets']:
        if (ROOT/'masters'/f'{name}.png').exists():continue
        submit_path=PRIVATE/(name+'-submit.json')
        if submit_path.exists():
            previous=json.loads(submit_path.read_text());match=re.search(r'job_id:\s*([\w-]+)',text(previous))
            if match and not previous.get('isError'):
                finish(name,match.group(1));continue
        recipe=json.loads((ROOT/'requests'/f'{name}.json').read_text())
        arguments=dict(recipe['arguments'])
        arguments['image_base64']=base64.b64encode((ROOT/recipe['sourceFile']).read_bytes()).decode()
        result=call(recipe['tool'],arguments)
        submit_path.write_text(json.dumps(result,indent=2))
        if result.get('isError'):raise RuntimeError('Submit rejected for '+name+': '+text(result)[:160])
        match=re.search(r'job_id:\s*([\w-]+)',text(result))
        if not match:raise RuntimeError('No job id returned for '+name)
        print(json.dumps({'asset':name,'status':'queued','job_id':match.group(1)}),flush=True)
        finish(name,match.group(1))

if __name__=='__main__':main()
