"""Schema-approved loaded native StateTree node discovery is source preserving."""
import httpx
import uuid
BASE='http://127.0.0.1:8080'

def call(method,route,body=None,**params):
    r=httpx.request(method,BASE+route,json=body,params=params,timeout=180)
    assert r.is_success,(r.status_code,r.text)
    return r.json()

path=None
try:
    created=call('POST','/state-trees/create',{'AssetPath':'/Game/UE5MCP_Test/ST_Discovery_'+uuid.uuid4().hex[:8]})
    path=created['asset_path']
    before=call('GET','/state-trees/inspect',asset_path=path)
    for kind,name,field in [('task','StateTreeDelayTask','Duration'),('condition','StateTreeRandomCondition','Threshold'),('consideration','StateTreeConstantConsideration','Constant')]:
        result=call('GET','/state-trees/node-types',asset_path=path,kind=kind,search=name,limit=1)
        assert result['nodes'] and result['nodes'][0]['struct'].endswith('.'+name),result
        node=result['nodes'][0];assert node['struct_instance_supported']
        setting=next(x for x in node['instance_properties'] if x['name']==field)
        assert setting['plain_setting_supported'] and float(setting['clamp_min'])==0,setting
    all_tasks=call('GET','/state-trees/node-types',asset_path=path,kind='task',limit=1)
    assert len(all_tasks['nodes'])<=1 and all_tasks['truncated']==(all_tasks['total']>1)
    empty=call('GET','/state-trees/node-types',asset_path=path,kind='condition',search='DefinitelyMissingFixture')
    assert empty['total']==0 and empty['nodes']==[]
    for params in [{'kind':'wrong'},{'kind':'task','limit':0},{'kind':'task','limit':257}]:
        r=httpx.get(BASE+'/state-trees/node-types',params={'asset_path':path}|params,timeout=180)
        assert r.status_code>=400,(r.status_code,r.text)
    assert call('GET','/state-trees/inspect',asset_path=path)==before
    print('Native schema-filtered node/field discovery, clamps, bounds, filtering and source preservation: OK')
finally:
    if path:call('POST','/assets/delete',{'AssetPath':path})
