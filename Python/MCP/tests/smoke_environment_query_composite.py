"""Nested native EQS generator expressions and persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'environment_query_composite.json'


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
            print('Cold nested native generator ownership, order, item types, settings and query parameters: OK')
        cleanup(path);return
    assert not STATE.exists(),'Verify or clean prior composite EQS fixture'
    path=None;keep=False
    def row(kind,children=0,**kw):return {'ClassPath':'/Script/AIModule.EnvQueryGenerator_'+kind,'Children':children}|kw
    location=row('CurrentLocation')
    expression=[row('Composite',2),location,row('Composite',1),location]
    try:
        path=call('POST','/environment-queries/create',{'AssetPath':'/Game/UE5MCP_Test/EQS_Composite_'+uuid.uuid4().hex[:8]})['asset_path'];edit(path,'POST','graph')
        before=inspect(path);edit(path,'POST','options',bSetGeneratorTree=True,GeneratorTree=expression,bDryRun=True);assert inspect(path)==before
        option=edit(path,'POST','options',bSetGeneratorTree=True,GeneratorTree=expression)['node_guid']
        test=edit(path,'POST','tests',ParentGuid=option,ClassPath='/Script/AIModule.EnvQueryTest_Distance',Properties={'TestPurpose':'Filter','FilterType':'Minimum'},ProviderValues={'FloatValueMin':'0'},NamedParameters={'FloatValueMin':'MinimumDistance'})['node_guid']
        snapshot=inspect(path);assert snapshot['valid']
        assert snapshot['compiled_options'][0]['option_guid']==option and snapshot['compiled_options'][0]['test_guids']==[test]
        tree=snapshot['options'][0]['generator_tree'];assert len(tree['children'])==2 and len(tree['children'][1]['children'])==1,tree
        assert not edit(path,'PATCH','generators',NodeGuid=option,GeneratorTree=expression)['would_change']
        reject(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[row('Composite',2),location,row('ActorsOfClass')])
        reject(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[row('Composite',1),row('CurrentLocation',Properties={'bCanRunAsync':'True'})])
        reject(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[row('Composite',1,Properties={'bAllowDifferentItemTypes':'True'}),location])
        reject(path,'POST','tests',ParentGuid=option,ClassPath='/Script/AIModule.EnvQueryTest_Random')
        reject(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[row('Composite',0)])
        reject(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[location,location])
        reject(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[row('Composite',1)]*8+[location])
        edit(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[location])
        assert inspect(path)['options'][0]['tests'][0]['guid']==test
        call('POST','/editor/transactions/undo');assert inspect(path)['options'][0]['generator_tree']==tree
        call('POST','/editor/transactions/redo');assert not inspect(path)['options'][0]['generator_tree']['children']
        call('POST','/editor/transactions/undo')
        # Persist a nested provider-bearing generator alongside a location generator.
        circle=row('OnCircle',ProviderValues={'NumberOfPoints':'8'},NamedParameters={'NumberOfPoints':'PointCount'})
        persisted=[row('Composite',2),location,row('Composite',1),circle]
        edit(path,'PATCH','generators',NodeGuid=option,GeneratorTree=persisted)
        assert {p['name']:p['type'] for p in inspect(path)['named_parameters']}=={'MinimumDistance':'FloatValue','PointCount':'IntValue'}
        bad_circle=row('OnCircle',NamedParameters={'NumberOfPoints':'MinimumDistance'})
        reject(path,'PATCH','generators',NodeGuid=option,GeneratorTree=[row('Composite',1),bad_circle])
        edit(path,'DELETE','options',NodeGuid=option,bConfirm=True)
        call('POST','/editor/transactions/undo');assert inspect(path)['valid'] and inspect(path)['options'][0]['tests'][0]['guid']==test
        edit(path,'POST','compile',bSave=True);snapshot=inspect(path);assert snapshot['valid'] and not snapshot['dirty'],snapshot
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'path':path,'snapshot':stable(snapshot)},indent=2));keep=True
        print('Composite prefix expressions, item/async/depth/parameter guards, no-op/dry-run, replacement/delete undo and save: OK')
    finally:
        if path and not keep:cleanup(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','verify','cleanup']);parser.add_argument('--base',default='http://127.0.0.1:8080')
    args=parser.parse_args();run(args.base,args.phase)
