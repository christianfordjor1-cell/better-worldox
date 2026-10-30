#!/usr/bin/env python3
"""PixelLab MCP transport using the securely configured runtime credential.

Never embeds keys in files or command arguments. Call results can contain inline
images; save them locally rather than printing their base64 payloads. This client
does not install a ChatGPT plugin or purchase generation credits.
"""
import argparse,json,os,sys,urllib.error,urllib.request
from pathlib import Path

ENDPOINT='https://api.pixellab.ai/mcp'

def rpc(method,params=None,request_id=1,timeout=55):
    token=os.environ.get('PIXELLAB_API_TOKEN')
    if not token:raise RuntimeError('PIXELLAB_API_TOKEN is not configured')
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json',
             'Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-03-26'}
    data=json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':params or {}}).encode()
    request=urllib.request.Request(ENDPOINT,data=data,headers=headers,method='POST')
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response:
            payload=response.read().decode('utf-8')
            if 'text/event-stream' in response.headers.get('Content-Type',''):
                messages=[]
                for event in payload.replace('\r\n','\n').split('\n\n'):
                    text='\n'.join(line[5:].lstrip() for line in event.splitlines() if line.startswith('data:'))
                    if text:messages.append(json.loads(text))
                result=next((m for m in reversed(messages) if m.get('id')==request_id),{})
            else:result=json.loads(payload)
    except urllib.error.HTTPError as error:
        raise RuntimeError('PixelLab HTTP request rejected: '+str(error.code)) from None
    if result.get('error'):raise RuntimeError('PixelLab RPC failed: '+str(result['error'].get('code','unknown')))
    if 'result' not in result:raise RuntimeError('PixelLab response has no matching result')
    return result['result']

def call(name,arguments=None,timeout=55):
    return rpc('tools/call',{'name':name,'arguments':arguments or {}},timeout=timeout)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool');parser.add_argument('--arguments',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();arguments=json.loads(args.arguments.read_text()) if args.arguments else {}
    result=call(args.tool,arguments);args.output.parent.mkdir(exist_ok=True,parents=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    token=os.environ.get('PIXELLAB_API_TOKEN','')
    text='\n'.join(c.get('text','') for c in result.get('content',[]) if c.get('type')=='text')
    if token:text=text.replace(token,'[REDACTED]')
    print(json.dumps({'tool':args.tool,'isError':result.get('isError',False),'text':text[:10000],
                      'imageBlocks':sum(c.get('type')=='image' for c in result.get('content',[])),'saved':str(args.output)},indent=2))
    if result.get('isError'):sys.exit(2)

if __name__=='__main__':main()
