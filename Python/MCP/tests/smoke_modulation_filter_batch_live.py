"""Native PIE mix filtering, batch preflight, device-wide controls and asset preservation."""
import argparse
import time
import uuid
import httpx


def run(base):
    def call(method, route, body=None, **params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        return r.json()

    def control(op, asset='', **extra):
        return call('POST','/audio/modulation/runtime',{'Operation':op,'AssetPath':asset}|extra)

    def reject(op, asset='', **extra):
        r=httpx.post(base+'/audio/modulation/runtime',json={'Operation':op,'AssetPath':asset}|extra,timeout=180)
        assert r.status_code>=400,r.text

    def inspect(asset=''):
        return call('GET','/audio/modulation/runtime',asset_path=asset)

    def until(fetch,predicate):
        end=time.monotonic()+20
        while time.monotonic()<end:
            s=fetch()
            if predicate(s):
                return s
            time.sleep(.05)
        raise AssertionError(s)

    def values(expected):
        def matches(s):
            data={d['destination_id']:d['value_normalized'] for d in s['destinations']}
            return all(k in data and abs(data[k]-v)<.005 for k,v in expected.items())
        return until(inspect,matches)

    def active(mix,state=True):
        return until(lambda:inspect(mix),lambda s:s['mix_active']==state)

    created=[]
    started=False
    name='MRF_MCP_'+uuid.uuid4().hex[:8]
    def create(suffix,kind,**extra):
        a=call('POST','/audio/modulation/create',{'AssetPath':'/Game/UE5MCP_Test/'+name+suffix,'AssetType':kind,'bSave':True}|extra)['asset_path']
        created.append(a)
        return a

    assert not call('GET','/editor/status')['is_playing']
    try:
        p1=create('_P1','parameter')
        p2=create('_P2','parameter')
        p3=create('_P3','parameter',ParameterType='volume')
        buses=[create('_'+key,'bus',ParameterPath=p) for key,p in zip('ABCDE',[p1,p2,p3,p1,p1])]
        a,b,c,d,e=buses
        for bus,address in zip(buses,['MCP_Filter_A','MCP_Filter_B','MCP_Filter_C','Other_D','Second_E']):
            call('PATCH','/audio/modulation/settings',{'AssetPath':bus,'bSetAddress':True,'bOverrideAddress':True,'Address':address,'bSave':True})
        m1,m2=create('_M1','mix'),create('_M2','mix')
        lfo=create('_LFO','generator')
        for mix,bus,target in [(m1,a,.8),(m1,b,.6),(m1,c,.4),(m1,d,.9),(m2,e,.7)]:
            call('POST','/audio/modulation/stages',{'AssetPath':mix,'BusPath':bus,'TargetNormalized':target,'AttackSeconds':0,'ReleaseSeconds':0,'bSave':True})
        before={asset:call('GET','/audio/modulation/settings',asset_path=asset) for asset in created}
        call('POST','/editor/play',{'Operation':'start'})
        started=True
        until(inspect,lambda s:s['modulation_available'])
        for key,bus in zip('ABCDE',buses):
            control('create_destination',bus,DestinationId=key)
        control('create_destination',lfo,DestinationId='lfo')
        reject('activate_mixes',AssetPaths=[m1,a])
        time.sleep(.2)
        assert not inspect(m1)['mix_active']
        reject('activate_mixes',AssetPaths=[m1,m1])
        reject('activate_mixes',AssetPaths=[m1]*129)
        reject('activate_mixes',m1,AssetPaths=[m2])
        assert not control('activate_mixes',AssetPaths=[m1,m2],bDryRun=True)['command_submitted']
        assert not inspect(m1)['mix_active'] and not inspect(m2)['mix_active']
        control('activate_mixes',AssetPaths=[m1,m2])
        active(m1); active(m2)
        baseline=dict(zip('ABCDE',[.8,.6,.4,.9,.7]))
        values(baseline)
        assert not control('update_mix_by_filter',m1,AddressFilter='MCP_Filter_[AB]',TargetNormalized=.2,FadeSeconds=0,bDryRun=True)['command_submitted']
        values(baseline)
        for pattern in ['[]','{}','[abc','abc]','{a,{b,c}}','a\nb','x'*257]:
            reject('update_mix_by_filter',m1,AddressFilter=pattern,TargetNormalized=.2)
        reject('update_mix_by_filter',m1,ParameterClassFilter='/Script/Engine.Actor')
        reject('update_mix_by_filter',m1,ParameterFilterPath=a)
        reject('update_mix_by_filter',m1,TargetNormalized=2)
        control('update_mix_by_filter',m1,AddressFilter='MCP_Filter_[AB]',TargetNormalized=.2,FadeSeconds=0)
        values(dict(zip('ABCDE',[.2,.2,.4,.9,.7])))
        control('update_mix_by_filter',m1,AddressFilter='MCP_Filter_*',ParameterClassFilter='/Script/AudioModulation.SoundModulationParameterVolume',TargetNormalized=.35,FadeSeconds=0)
        values(dict(zip('ABCDE',[.2,.2,.35,.9,.7])))
        control('update_mix_by_filter',m1,ParameterFilterPath=p1,TargetNormalized=.45,FadeSeconds=0)
        values(dict(zip('ABCDE',[.45,.2,.35,.45,.7])))
        control('update_mix_by_filter',m1,ParameterFilterPath=p1,ParameterClassFilter='/Script/AudioModulation.SoundModulationParameterVolume',TargetNormalized=.1,FadeSeconds=0)
        time.sleep(.2)
        values(dict(zip('ABCDE',[.45,.2,.35,.45,.7])))
        control('update_mix_by_filter',m1,TargetNormalized=.6,FadeSeconds=0)
        values(dict(zip('ABCDE',[.6,.6,.6,.6,.7])))
        control('update_mix_by_filter',m1,AddressFilter='MCP_Filter_{A,B}',TargetNormalized=.3,FadeSeconds=0)
        # UE 5.7's native BracePatternMatches does not accept a terminal alternative.
        time.sleep(.2)
        values(dict(zip('ABCDE',[.6,.6,.6,.6,.7])))
        control('update_mix_by_filter',m1,AddressFilter='MCP_Filter_[AB]',TargetNormalized=.3,FadeSeconds=0)
        values(dict(zip('ABCDE',[.3,.3,.6,.6,.7])))
        control('update_mix_by_filter',m1,AddressFilter='Other_?',TargetNormalized=.4,FadeSeconds=0)
        filtered=dict(zip('ABCDE',[.3,.3,.6,.4,.7]))
        values(filtered)
        control('deactivate_mix',m2); active(m2,False)
        reject('update_mixes_from_assets',AssetPaths=[m1,m2],FadeSeconds=0)
        time.sleep(.2)
        values({'A':.3,'B':.3,'C':.6,'D':.4,'E':1})
        control('activate_mixes',AssetPaths=[m2]); active(m2)
        assert not control('update_mixes_from_assets',AssetPaths=[m1,m2],FadeSeconds=0,bDryRun=True)['command_submitted']
        values(filtered)
        control('update_mixes_from_assets',AssetPaths=[m1,m2],FadeSeconds=0)
        values(baseline)
        reject('update_modulators',AssetPaths=[a,p1])
        control('update_modulators',AssetPaths=buses+[lfo])
        observed=[next(x['value_normalized'] for x in inspect()['destinations'] if x['destination_id']=='lfo') for _ in range(8)]
        assert max(observed)-min(observed)>.1,observed
        reject('set_globals',AssetPaths=[a,m1],TargetNormalized=.5,FadeSeconds=0)
        time.sleep(.2); values(baseline)
        assert not control('set_globals',AssetPaths=[a,b],TargetNormalized=.5,FadeSeconds=0,bDryRun=True)['command_submitted']
        values(baseline)
        control('set_globals',AssetPaths=[a,b],TargetNormalized=.5,FadeSeconds=0)
        values(dict(zip('ABCDE',[.4,.3,.4,.9,.7])))
        control('clear_globals',AssetPaths=[a,b],FadeSeconds=0)
        values(baseline)
        control('set_globals',AssetPaths=[a,e],TargetNormalized=.5,FadeSeconds=0)
        assert not control('clear_all_globals',FadeSeconds=0,bDryRun=True)['command_submitted']
        values(dict(zip('ABCDE',[.4,.6,.4,.9,.35])))
        control('clear_all_globals',FadeSeconds=0); values(baseline)
        reject('deactivate_mixes',AssetPaths=[m1,a])
        assert inspect(m1)['mix_active'] and inspect(m2)['mix_active']
        control('deactivate_mixes',AssetPaths=[m1,m2]); active(m1,False); active(m2,False)
        values({k:1 for k in 'ABCDE'})
        control('activate_mixes',AssetPaths=[m1,m2]); active(m1); active(m2); values(baseline)
        control('set_globals',AssetPaths=[a,e],TargetNormalized=.5,FadeSeconds=0)
        assert not control('deactivate_all_mixes',bDryRun=True)['command_submitted']
        values(dict(zip('ABCDE',[.4,.6,.4,.9,.35])))
        control('deactivate_all_mixes'); active(m1,False); active(m2,False)
        values({k:1 for k in 'ABCDE'})
        assert all(call('GET','/audio/modulation/settings',asset_path=x)==before[x] for x in created)
        # Leave batch-created ownership and live destinations for native PIE cleanup.
        control('activate_mixes',AssetPaths=[m1,m2]); active(m1); active(m2)
        control('set_globals',AssetPaths=[a,e],TargetNormalized=.5,FadeSeconds=0)
        call('POST','/editor/play',{'Operation':'stop'})
        until(lambda:call('GET','/editor/status'),lambda s:not s['is_playing'])
        call('POST','/editor/play',{'Operation':'start'})
        until(inspect,lambda s:s['modulation_available'])
        assert inspect()['destinations']==[]
        active(m1,False); active(m2,False)
        control('create_destination',a,DestinationId='A'); values({'A':1})
        print('Native modulation filters, exact class/parameter intersection, batch preflight/controls, device-wide reset, asset preservation and PIE cleanup: OK')
    finally:
        if started:
            call('POST','/editor/play',{'Operation':'stop'})
            until(lambda:call('GET','/editor/status'),lambda s:not s['is_playing'])
        for asset in reversed(created):
            call('POST','/assets/delete',{'AssetPath':asset})


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base-url',default='http://127.0.0.1:8080')
    run(p.parse_args().base_url)
