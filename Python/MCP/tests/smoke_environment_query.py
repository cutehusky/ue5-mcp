"""Native EQS graph/settings authoring, transactions and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'environment_query.json'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=120)
        assert r.is_success,(r.status_code,r.text)
        return r.json()
    def inspect(path):return call('GET','/environment-queries/inspect',asset_path=path)
    def edit(path,method,route,**values):return call(method,'/environment-queries/'+route,{'AssetPath':path}|values)
    def stable(snapshot):return {k:v for k,v in snapshot.items() if k not in ['would_change','dry_run','saved','node_guid']}
    def reject(path,method,route,**values):
        before=inspect(path);r=httpx.request(method,base+'/environment-queries/'+route,json={'AssetPath':path}|values,timeout=120)
        assert r.status_code>=400,(r.status_code,r.text)
        assert inspect(path)==before,'Rejected EQS request changed source'
    def cleanup(path):
        call('POST','/assets/delete',{'AssetPath':path});STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text());path=state['path']
        if phase=='verify':
            snapshot=inspect(path);assert stable(snapshot)==state['snapshot'],(snapshot,state['snapshot'])
            assert snapshot['valid'] and not snapshot['dirty'],snapshot
            print('Cold EQS graph GUIDs, fallback/test order, provider defaults/bindings and clean package: OK')
        cleanup(path);return
    assert not STATE.exists(),'Verify or clean prior EQS fixture'
    package='/Game/UE5MCP_Test/EQS_'+uuid.uuid4().hex[:8];path=None;keep=False
    try:
        created=call('POST','/environment-queries/create',{'AssetPath':package});path=created['asset_path']
        edit(path,'POST','graph')
        def option(x):return edit(path,'POST','options',ClassPath='/Script/AIModule.EnvQueryGenerator_CurrentLocation',X=x)['node_guid']
        first=option(0);second=option(300)
        before=inspect(path)
        edit(path,'POST','tests',ParentGuid=first,ClassPath='/Script/AIModule.EnvQueryTest_Distance',bDryRun=True)
        assert inspect(path)==before
        distance=edit(path,'POST','tests',ParentGuid=first,ClassPath='/Script/AIModule.EnvQueryTest_Distance',Properties={'TestPurpose':'Filter','FilterType':'Minimum'},ProviderValues={'FloatValueMin':'0'},NamedParameters={'FloatValueMin':'MinimumDistance'})['node_guid']
        random=edit(path,'POST','tests',ParentGuid=first,ClassPath='/Script/AIModule.EnvQueryTest_Distance',Properties={'TestPurpose':'Score'},ProviderValues={'ScoringFactor':'2'})['node_guid']
        edit(path,'PATCH','tests',NodeGuid=distance,ProviderValues={'BoolValue':'True'},NamedParameters={'BoolValue':'UseGate'})
        circle=edit(path,'POST','options',ClassPath='/Script/AIModule.EnvQueryGenerator_OnCircle',X=900,ProviderValues={'NumberOfPoints':'8'},NamedParameters={'NumberOfPoints':'PointCount'})['node_guid']
        reject(path,'PATCH','tests',NodeGuid=distance,NamedParameters={'BoolValue':'MinimumDistance'})
        reject(path,'PATCH','options',NodeGuid=circle,NamedParameters={'NumberOfPoints':'MinimumDistance'})
        snapshot=inspect(path);assert snapshot['valid'],snapshot
        assert {p['name']:p['type'] for p in snapshot['named_parameters']}=={'MinimumDistance':'FloatValue','UseGate':'BoolValue','PointCount':'IntValue'}
        assert snapshot['options'][0]['tests'][0]['providers']['FloatValueMin']['parameter']=='MinimumDistance'
        assert not edit(path,'PATCH','tests',NodeGuid=distance,ProviderValues={'FloatValueMin':'0'},NamedParameters={'FloatValueMin':'MinimumDistance'})['would_change']
        reject(path,'PATCH','tests',NodeGuid=distance,ProviderValues={'FloatValueMin':'nan'})
        reject(path,'PATCH','tests',NodeGuid=distance,ProviderValues={'ScoringFactor':'0'})
        reject(path,'PATCH','tests',NodeGuid=distance,Properties={'TestPurpose':'999'})
        reject(path,'PATCH','tests',NodeGuid=distance,Properties={'FilterType':'Match'})
        reject(path,'PATCH','tests',NodeGuid=distance,Properties={'FloatValueMin':'(DefaultValue=10)'})
        reject(path,'PATCH','options',NodeGuid=distance,Properties={'TestComment':'wrong route'})
        reject(path,'POST','options',ClassPath='/Script/AIModule.EnvQueryGenerator_CurrentLocation',X=300)
        reject(path,'POST','tests',ParentGuid=first,ClassPath='/Script/AIModule.EnvQueryGenerator_CurrentLocation')
        reject(path,'PATCH','tests',NodeGuid=distance,Classes={'DistanceTo':'/Script/Engine.Actor'})
        reject(path,'DELETE','options',NodeGuid=first)
        edit(path,'PATCH','tests',NodeGuid=distance,bSetEnabled=True,bEnabled=False)
        assert len(inspect(path)['compiled_options'][0]['tests'])==1
        call('POST','/editor/transactions/undo');assert len(inspect(path)['compiled_options'][0]['tests'])==2
        call('POST','/editor/transactions/redo');assert len(inspect(path)['compiled_options'][0]['tests'])==1
        call('POST','/editor/transactions/undo')
        edit(path,'PATCH','tests',NodeGuid=random,Index=0)
        assert inspect(path)['options'][0]['tests'][0]['guid']==random
        call('POST','/editor/transactions/undo');assert inspect(path)['options'][0]['tests'][0]['guid']==distance
        edit(path,'PATCH','tests',NodeGuid=distance,Classes={'DistanceTo':'/Script/AIModule.EnvQueryContext_Querier'})
        edit(path,'POST','layout',Positions=[{'NodeGuid':first,'X':500,'Y':200},{'NodeGuid':second,'X':-100,'Y':200}])
        assert inspect(path)['options'][0]['guid']==second
        call('POST','/editor/transactions/undo');assert inspect(path)['options'][0]['guid']==first
        edit(path,'DELETE','tests',NodeGuid=random,bConfirm=True)
        call('POST','/editor/transactions/undo');assert len(inspect(path)['options'][0]['tests'])==2
        edit(path,'POST','compile',bSave=True)
        snapshot=inspect(path);assert snapshot['valid'] and not snapshot['dirty'],snapshot
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'path':path,'snapshot':stable(snapshot)},indent=2));keep=True
        print('EQS typed graph/settings/providers, no-op/dry-run, invalid input, enabled/order/delete transactions and save: OK')
    finally:
        if path and not keep:cleanup(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
