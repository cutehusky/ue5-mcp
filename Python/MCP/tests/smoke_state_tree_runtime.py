"""Owned actual PIE lifecycle and StateTree component inspection guards."""
import time
import httpx
BASE='http://127.0.0.1:8080'
def call(method,route,body=None,**params):
    r=httpx.request(method,BASE+route,json=body,params=params,timeout=180)
    assert r.is_success,(r.status_code,r.text)
    return r.json()
def reject(**params):
    r=httpx.get(BASE+'/state-trees/runtime',params=params,timeout=180)
    assert r.status_code>=400,(r.status_code,r.text)
def play(op):
    call('POST','/editor/play',{'Operation':op})
    for _ in range(120):
        if call('GET','/editor/status')['is_playing']==(op=='start'):return
        time.sleep(.25)
    raise AssertionError('PIE transition timed out')
assert not call('GET','/editor/status')['is_playing']
reject();owned=False
try:
    play('start');owned=True
    result=call('GET','/state-trees/runtime',limit=256)
    assert result['total']>=len(result['components']) and result['world']
    for c in result['components']:
        assert c['owner_path'] and c['component_path'] and c['run_status'] and c['schema']
        one=call('GET','/state-trees/runtime',component_path=c['component_path'])
        assert len(one['components'])==1
    for values in [{'limit':0},{'limit':257},{'pie_instance':999999},{'component_path':'/Game/Missing.Missing'}]:reject(**values)
    missing=call('GET','/state-trees/runtime',search='DefinitelyMissingFixture')
    assert missing['total']==0 and missing['components']==[]
    for body in [{'Operation':'start'},{'Operation':'pause','ComponentPath':'/Game/Missing.Missing'},{'Operation':'wrong','ComponentPath':'/Game/Missing.Missing'}]:
        r=httpx.post(BASE+'/state-trees/runtime',json=body,timeout=180);assert r.status_code>=400,(r.status_code,r.text)
    count=result['total'];play('stop');owned=False;reject()
    print(f'Actual PIE StateTree inspection/lifecycle and bounds/world/path guards: OK ({count} components)')
finally:
    if owned:play('stop')
