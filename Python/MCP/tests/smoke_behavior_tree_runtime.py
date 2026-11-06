"""HTTP PIE-world discovery and target guards; positive mutations use RuntimePIE automation."""
import argparse
import time
import httpx


def run(base):
    def call(method,route,body=None,**params):
        result=httpx.request(method,base+route,json=body,params=params,timeout=120)
        assert result.is_success,(result.status_code,result.text)
        return result.json()
    def rejected(method,route,body=None,**params):
        result=httpx.request(method,base+route,json=body,params=params,timeout=120)
        assert result.status_code>=400,(result.status_code,result.text)
    assert not call('GET','/editor/status')['is_playing'],'Runtime HTTP fixture requires idle editor'
    rejected('GET','/behavior-trees/runtime')
    rejected('GET','/behavior-trees/runtime',pie_instance='invalid')
    rejected('POST','/behavior-trees/runtime/dynamic-subtree',{'ComponentPath':'Missing','InjectionTag':'Missing'})
    owned=False
    try:
        call('POST','/editor/play',{'Operation':'start'});owned=True
        for _ in range(120):
            if call('GET','/editor/status')['is_playing']:break
            time.sleep(.25)
        assert call('GET','/editor/status')['is_playing']
        snapshot=call('GET','/behavior-trees/runtime');assert isinstance(snapshot['components'],list),snapshot
        for component in snapshot['components']:
            assert 'component_path' in component and isinstance(component['dynamic_tasks'],list),component
        rejected('GET','/behavior-trees/runtime',component_path='Missing')
        rejected('GET','/behavior-trees/runtime',pie_instance=999999)
        rejected('POST','/behavior-trees/runtime/dynamic-subtree',{'ComponentPath':'Missing','InjectionTag':'Missing','bDryRun':True})
        rejected('POST','/behavior-trees/runtime/dynamic-subtree',{'ComponentPath':'Missing','PIEInstance':-2})
    finally:
        if owned:
            call('POST','/editor/play',{'Operation':'stop'})
            for _ in range(120):
                if not call('GET','/editor/status')['is_playing']:break
                time.sleep(.25)
            assert not call('GET','/editor/status')['is_playing']
    rejected('GET','/behavior-trees/runtime')
    print('Runtime HTTP discovery, PIE selection, invalid targets and owned play cleanup: OK')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:8080')
    run(parser.parse_args().base)
