"""Live REST checks for widget animations, consolidation, Game Features, Smart Objects and Editor Utilities."""
import argparse
import json
import uuid
import httpx

ROOT='/Game/UE5MCP_Test'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='http://127.0.0.1:8080')
    base=parser.parse_args().base
    tag=uuid.uuid4().hex[:8]
    owned=[]
    results={}

    def call(route,body,ok=True):
        r=httpx.post(base+route,json=body,timeout=180)
        if ok:
            assert r.is_success,(route,r.status_code,r.text)
            return r.json()
        assert r.status_code>=400,(route,r.status_code,r.text)
        return r.text

    def undo():
        call('/editor/transactions/undo',{})

    def redo():
        call('/editor/transactions/redo',{})

    assert not httpx.get(base+'/editor/status',timeout=60).json()['is_playing']
    try:
        # Smart Object definition: create, add/set/remove slot, guards, undo/redo.
        so=f'{ROOT}/SO_{tag}.SO_{tag}'
        so2=f'{ROOT}/SO2_{tag}.SO2_{tag}'
        call('/smart-objects/definition',{'Operation':'Create','AssetPath':so},ok=False)
        dry=call('/smart-objects/definition',{'Operation':'Create','AssetPath':so,'bConfirm':True})
        assert dry['would_change'] and not dry['written']
        for p in (so,so2):
            r=call('/smart-objects/definition',{'Operation':'Create','AssetPath':p,'bConfirm':True,'bDryRun':False})
            assert r['written'],r
            owned.append(p)
        call('/smart-objects/definition',{'Operation':'Create','AssetPath':so,'bConfirm':True,'bDryRun':False},ok=False)
        snap=call('/smart-objects/definition',{'AssetPath':so})['snapshot']
        base_slots=len(json.loads(snap)['slots'])
        call('/smart-objects/definition',{'Operation':'AddSlot','AssetPath':so,'bConfirm':True,'ExpectedSnapshot':'stale','bDryRun':False},ok=False)
        r=call('/smart-objects/definition',{'Operation':'AddSlot','AssetPath':so,'bConfirm':True,'ExpectedSnapshot':snap,'Name':'Seat','TextValue':'(X=10,Y=20,Z=0)','bDryRun':False})
        assert r['written'] and len(json.loads(r['snapshot'])['slots'])==base_slots+1,r
        slot=json.loads(r['snapshot'])['slots'][-1]
        assert 'Seat' in slot and 'X=10' in slot,slot
        undo()
        assert len(json.loads(call('/smart-objects/definition',{'AssetPath':so})['snapshot'])['slots'])==base_slots
        redo()
        snap=call('/smart-objects/definition',{'AssetPath':so})['snapshot']
        assert len(json.loads(snap)['slots'])==base_slots+1
        idx=base_slots
        call('/smart-objects/definition',{'Operation':'SetSlot','AssetPath':so,'bConfirm':True,'ExpectedSnapshot':snap,'Index':idx,'FieldName':'Bogus','TextValue':'1','bDryRun':False},ok=False)
        r=call('/smart-objects/definition',{'Operation':'SetSlot','AssetPath':so,'bConfirm':True,'ExpectedSnapshot':snap,'Index':idx,'FieldName':'Name','TextValue':'Bench','bDryRun':False})
        assert r['written'] and 'Name="Bench"' in json.loads(r['snapshot'])['slots'][idx],r
        snap=r['snapshot']
        call('/smart-objects/definition',{'Operation':'RemoveSlot','AssetPath':so,'bConfirm':True,'ExpectedSnapshot':snap,'Index':idx,'bDryRun':False},ok=False)
        r=call('/smart-objects/definition',{'Operation':'RemoveSlot','AssetPath':so,'bConfirm':True,'bAllow':True,'ExpectedSnapshot':snap,'Index':idx,'bDryRun':False})
        assert len(json.loads(r['snapshot'])['slots'])==base_slots
        results['smart_objects']='create/add/set/remove/guards/undo/redo ok'

        # Consolidation: merge SO2 into SO.
        call('/assets/save',{'AssetPath':so})
        call('/assets/save',{'AssetPath':so2})
        ins=call('/assets/consolidate',{'Operation':'Inspect','TargetPath':so,'Paths':[so2]})
        call('/assets/consolidate',{'Operation':'Consolidate','TargetPath':so,'Paths':[so2],'bConfirm':True,'ExpectedSnapshot':ins['snapshot'],'bDryRun':False},ok=False)
        call('/assets/consolidate',{'Operation':'Inspect','TargetPath':so,'Paths':[so]},ok=False)
        r=call('/assets/consolidate',{'Operation':'Consolidate','TargetPath':so,'Paths':[so2],'bConfirm':True,'bAllow':True,'ExpectedSnapshot':ins['snapshot'],'bDryRun':False})
        assert r['written'] and not r['failed_objects'] and not r['invalid_objects'],r
        owned.remove(so2)
        results['consolidation']='guards + consolidate ok'

        # Widget animations.
        wbp_pkg=f'{ROOT}/WBP_{tag}'
        call('/widget-blueprints/create',{'BpPath':wbp_pkg})
        wbp=f'{wbp_pkg}.WBP_{tag}'
        owned.append(wbp)
        snap=call('/widgets/animations',{'AssetPath':wbp})['snapshot']
        assert json.loads(snap)['animations']==[]
        call('/widgets/animations',{'Operation':'Create','AssetPath':wbp,'bConfirm':True,'ExpectedSnapshot':snap,'Name':'Fade','Numbers':[1,0],'bDryRun':False},ok=False)
        r=call('/widgets/animations',{'Operation':'Create','AssetPath':wbp,'bConfirm':True,'ExpectedSnapshot':snap,'Name':'Fade','Numbers':[0,1.5],'bDryRun':False})
        anims=json.loads(r['snapshot'])['animations']
        assert len(anims)==1 and anims[0]['name']=='Fade',anims
        path=anims[0]['path']
        snap=r['snapshot']
        call('/widgets/animations',{'Operation':'Create','AssetPath':wbp,'bConfirm':True,'ExpectedSnapshot':snap,'Name':'Fade','Numbers':[0,1],'bDryRun':False},ok=False)
        r=call('/widgets/animations',{'Operation':'SetRange','AssetPath':wbp,'TargetPath':path,'bConfirm':True,'ExpectedSnapshot':snap,'Numbers':[0.5,2],'bDryRun':False})
        assert r['written'],r
        snap=r['snapshot']
        r=call('/widgets/animations',{'Operation':'Rename','AssetPath':wbp,'TargetPath':path,'bConfirm':True,'ExpectedSnapshot':snap,'Name':'FadeIn','bDryRun':False})
        anims=json.loads(r['snapshot'])['animations']
        assert anims[0]['name']=='FadeIn' and anims[0]['display_label']=='FadeIn',anims
        snap=r['snapshot']
        call('/blueprints/compile',{'BpPath':wbp_pkg})
        r=call('/widgets/animations',{'Operation':'Delete','AssetPath':wbp,'TargetPath':anims[0]['path'],'bConfirm':True,'ExpectedSnapshot':snap,'bDryRun':False})
        assert json.loads(r['snapshot'])['animations']==[]
        results['widget_animations']='create/range/rename/compile/delete/guards ok'

        # Game Features: discovery + guards only (no fixture plugin in this project).
        gf=call('/game-features',{})
        assert isinstance(gf['game_features'],list)
        call('/game-features',{'Operation':'Activate','Name':'NoSuchPlugin_'+tag,'bConfirm':True},ok=False)
        results['game_features']=f"discovery ok ({len(gf['game_features'])} plugins)"

        # Editor Utilities: discovery + guards only.
        eu=call('/editor-utilities',{'PathFilter':'/Game'})
        assert eu['total']>=0 and isinstance(eu['utilities'],list)
        call('/editor-utilities',{'Operation':'Run','AssetPath':'/Game/Nope.Nope'},ok=False)
        call('/editor-utilities',{'PathFilter':'relative'},ok=False)
        results['editor_utilities']=f"discovery ok ({eu['total']} utilities)"
    finally:
        for p in reversed(owned):
            httpx.post(base+'/assets/delete',json={'AssetPath':p},timeout=180)
    print(json.dumps(results,indent=1))


if __name__=='__main__':
    main()
