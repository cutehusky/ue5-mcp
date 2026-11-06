"""Native asynchronous EQS HTTP execution in an owned actual PIE session."""
import argparse
import time
import uuid
import httpx


def run(base):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=120)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def reject(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=120)
        assert r.status_code>=400,(r.status_code,r.text)
    def inspect(path):return call('GET','/environment-queries/inspect',asset_path=path)
    def edit(path,route,**values):return call('POST','/environment-queries/'+route,{'AssetPath':path}|values)
    def play(operation):
        call('POST','/editor/play',{'Operation':operation})
        for _ in range(120):
            if call('GET','/editor/status')['is_playing']==(operation=='start'):return
            time.sleep(.25)
        raise AssertionError('Owned PIE transition timed out')
    def read(key):return call('GET','/environment-queries/runtime',request_id=key)['request']
    def finish(body):
        key=call('POST','/environment-queries/runtime',body)['request']['request_id']
        for _ in range(200):
            result=read(key)
            if result['state']!='running':break
            time.sleep(.025)
        assert result['state']=='succeeded',result
        return key,result
    assert not call('GET','/editor/status')['is_playing'],'EQS HTTP fixture requires idle editor'
    reject('GET','/environment-queries/runtime')
    reject('GET','/environment-queries/runtime/owners')
    path=None;owned=False
    try:
        path=call('POST','/environment-queries/create',{'AssetPath':'/Game/UE5MCP_Test/EQS_HTTP_'+uuid.uuid4().hex[:8]})['asset_path'];edit(path,'graph')
        prefix='/Script/AIModule.EnvQueryGenerator_'
        tree=[{'ClassPath':prefix+'Composite','Children':2},{'ClassPath':prefix+'CurrentLocation'},{'ClassPath':prefix+'CurrentLocation'}]
        first=edit(path,'options',bSetGeneratorTree=True,GeneratorTree=tree)['node_guid']
        edit(path,'options',ClassPath=prefix+'CurrentLocation',X=300)
        edit(path,'tests',ParentGuid=first,ClassPath='/Script/AIModule.EnvQueryTest_Distance',Properties={'TestPurpose':'Filter','FilterType':'Minimum'},ProviderValues={'FloatValueMin':'0','BoolValue':'False'},NamedParameters={'FloatValueMin':'MinimumDistance','BoolValue':'UseGate'})
        edit(path,'compile',bSave=True);before=inspect(path)
        play('start');owned=True
        owners=call('GET','/environment-queries/runtime/owners',search='PlayerStart',limit=10)['owners']
        if not owners:owners=call('GET','/environment-queries/runtime/owners',limit=256)['owners']
        owner=next(a['path'] for a in owners if a['authority'] and 'Controller' not in a['class'])
        request={'AssetPath':path,'OwnerPath':owner,'MaxItems':1}
        preview=call('POST','/environment-queries/runtime',request|{'bDryRun':True})
        assert preview['request']['state']=='preview' and preview['would_change']
        reject('GET','/environment-queries/runtime',request_id=preview['request']['request_id'])
        key,result=finish(request);assert result['total_items']==2 and result['returned_items']==1 and result['truncated'],result
        assert 'location' in result['items'][0] and 'score' in result['items'][0],result
        assert not call('POST','/environment-queries/runtime',{'Operation':'cancel','RequestId':key})['would_change']
        call('POST','/environment-queries/runtime',{'Operation':'forget','RequestId':key});reject('GET','/environment-queries/runtime',request_id=key)
        key,result=finish(request|{'Parameters':[{'Name':'MinimumDistance','Type':'float','Value':'1'}]});assert result['option_index']==1 and result['total_items']==1,result
        call('POST','/environment-queries/runtime',{'Operation':'forget','RequestId':key})
        for mode in ['single','random_best_5','random_best_25']:
            key,result=finish(request|{'RunMode':mode});assert result['total_items']==1,result
            call('POST','/environment-queries/runtime',{'Operation':'forget','RequestId':key})
        baseline=call('GET','/environment-queries/runtime')
        for patch in [
            {'OwnerPath':path}, {'PIEInstance':999999}, {'RunMode':'invalid'}, {'MaxItems':513},
            {'TimeoutSeconds':0}, {'Parameters':[{'Name':'MinimumDistance','Type':'int','Value':'1'}]},
            {'Parameters':[{'Name':'MinimumDistance','Type':'float','Value':'nan'}]},
            {'Parameters':[{'Name':'Missing','Type':'float','Value':'1'}]},
            {'Parameters':[{'Name':'MinimumDistance','Type':'float','Value':'1'},{'Name':'minimumdistance','Type':'float','Value':'2'}]},
            {'Parameters':[{'Name':'UseGate','Type':'bool','Value':'not_boolean'}]},
        ]:reject('POST','/environment-queries/runtime',request|patch)
        assert call('GET','/environment-queries/runtime')==baseline
        key,result=finish(request|{'RequestId':'cleanup_'+uuid.uuid4().hex})
        assert inspect(path)==before,'Runtime EQS changed authored source or package state'
        play('stop');owned=False
        reject('GET','/environment-queries/runtime',request_id=key)
        play('start');owned=True
        assert not call('GET','/environment-queries/runtime')['requests'],'World cleanup retained old query records'
        play('stop');owned=False
        assert inspect(path)==before
        print('Actual PIE EQS HTTP execution, fallback/modes/results, typed guards, source isolation and world cleanup: OK')
    finally:
        if owned:play('stop')
        if path:call('POST','/assets/delete',{'AssetPath':path})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:8080');run(parser.parse_args().base)
