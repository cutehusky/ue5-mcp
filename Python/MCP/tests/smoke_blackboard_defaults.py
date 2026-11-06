"""Typed native key defaults, constraints, Enum resolution and cold persistence."""
import argparse
import json
import uuid
import httpx
from smoke_navigation_mesh import PROJECT
STATE=PROJECT/'Saved'/'UE5MCP_Test'/'blackboard_defaults.json'
ENUM='/Script/AIModule.EPathFollowingStatus'


def run(base,phase):
    def call(method,route,body=None,**params):
        r=httpx.request(method,base+route,json=body,params=params,timeout=180)
        assert r.is_success,(r.status_code,r.text)
        try:return r.json()
        except ValueError:return r.text
    def inspect(path):return call('GET','/blackboards/inspect',asset_path=path)
    def row(path,key):return next(k for k in inspect(path)['keys'] if k['name']==key)
    def add(path,key,typ,settings=None,**kw):
        return call('POST','/blackboards/keys',{'AssetPath':path,'KeyName':key,'KeyType':'/Script/AIModule.BlackboardKeyType_'+typ,'bSetTypeSettings':settings is not None,'TypeSettings':settings or {}}|kw)
    def edit(path,key,settings,**kw):
        return call('PATCH','/blackboards/keys',{'AssetPath':path,'KeyName':key,'bSetTypeSettings':True,'TypeSettings':settings}|kw)
    def reject(path,key,settings,**kw):
        before=inspect(path)
        r=httpx.patch(base+'/blackboards/keys',json={'AssetPath':path,'KeyName':key,'bSetTypeSettings':True,'TypeSettings':settings}|kw,timeout=180)
        assert r.status_code>=400,r.text
        assert inspect(path)==before,'Rejected settings changed Blackboard metadata, key subobjects or dirty state'
    def cleanup(paths):
        for path in reversed(paths):call('POST','/assets/delete',{'AssetPath':path})
        STATE.unlink(missing_ok=True)
    if phase in ['verify','cleanup']:
        state=json.loads(STATE.read_text())
        if phase=='cleanup':cleanup(state['paths']);return
        for path,want in state['snapshots'].items():
            got=inspect(path)
            for field in ['keys','inherited_keys','validation','parent_path']:
                assert got[field]==want[field],(path,field,got[field],want[field])
            assert not got['dirty'],got
        print('Cold native Blackboard defaults, constraints, Enum name/type and inherited settings: OK')
        cleanup(state['paths']);return
    assert not STATE.exists(),'Verify or clean previous defaults fixture'
    paths=[];keep=False
    try:
        for name in ['Defaults','DefaultsChild']:
            paths.append(call('POST','/blackboards/create',{'AssetPath':'/Game/UE5MCP_Test/BB_'+name+'_'+uuid.uuid4().hex[:8]}))
        root,child=paths
        values={
            'Bool':{'BoolValue':True},'Int':{'IntValue':-42},'Float':{'FloatValue':1.25},
            'Name':{'TextValue':'Goal'},'String':{'TextValue':'route\nstep'},
            'Vector':{'VectorValue':{'X':120,'Y':30,'Z':40},'bSetUseDefault':True,'bUseDefault':True},
            'Rotator':{'RotationValue':{'Pitch':10,'Yaw':90,'Roll':-20},'bSetUseDefault':True,'bUseDefault':True},
            'Object':{'bSetBaseClass':True,'BaseClass':'/Script/Engine.StaticMesh','ReferenceValue':'/Engine/BasicShapes/Cube.Cube'},
            'Class':{'bSetBaseClass':True,'BaseClass':'/Script/Engine.Pawn','ReferenceValue':'/Script/Engine.Character'},
            'Enum':{'bSetEnumType':True,'EnumTypePath':ENUM,'IntValue':3}}
        before=inspect(root)
        add(root,'Float','Float',{'bSetDefault':True,'FloatValue':1.25},bDryRun=True)
        assert inspect(root)==before
        for typ,setting in values.items():
            result=add(root,typ,typ,{'bSetDefault':True}|setting)
            assert result['changed'] and result['validation']['valid'],result
            assert row(root,typ)['type_settings']['errors']==[]
        assert row(root,'Bool')['type_settings']['default_value'] is True
        assert row(root,'Vector')['type_settings']['default_value']=={'X':120,'Y':30,'Z':40}
        assert row(root,'Rotator')['type_settings']['use_default_value']
        assert row(root,'Object')['type_settings']['base_class']=='/Script/Engine.StaticMesh'
        assert row(root,'Class')['type_settings']['default_value']=='/Script/Engine.Character'
        assert row(root,'Enum')['type_settings']['enum_type']==ENUM
        add(root,'FreshBool','Bool');assert row(root,'FreshBool')['type_settings']['default_value'] is False
        old=row(root,'Float')['key_object_path']
        edit(root,'Float',{'bSetDefault':True,'FloatValue':2.5})
        assert row(root,'Float')['key_object_path']==old and row(root,'Float')['type_settings']['default_value']==2.5
        call('POST','/editor/transactions/undo');assert row(root,'Float')['type_settings']['default_value']==1.25
        call('POST','/editor/transactions/redo');assert row(root,'Float')['type_settings']['default_value']==2.5
        before=inspect(root);noop=edit(root,'Float',{'bSetDefault':True,'FloatValue':2.5});assert not noop['would_change'] and inspect(root)==before
        reject(root,'Int',{'bSetDefault':True,'IntValue':2147483648},NewKeyName='MustNotApply')
        reject(root,'Float',{'bSetDefault':True,'FloatValue':1e31},bSetDescription=True,Description='must not apply')
        reject(root,'String',{'bSetDefault':True,'TextValue':'x'*4097})
        reject(root,'Name',{'bSetDefault':True,'TextValue':'x'*129})
        reject(root,'Vector',{'bSetDefault':True,'VectorValue':{'X':1e10,'Y':0,'Z':0}})
        reject(root,'Rotator',{'bSetDefault':True,'RotationValue':{'Yaw':1e10}})
        reject(root,'Int',{'bSetUseDefault':True,'bUseDefault':True})
        reject(root,'Object',{'bSetBaseClass':True,'BaseClass':'/Script/Engine.Pawn'})
        reject(root,'Class',{'bSetDefault':True,'ReferenceValue':'/Script/Engine.StaticMesh'})
        reject(root,'Object',{'bSetDefault':True,'ReferenceValue':'/Game/Missing.Default'})
        reject(root,'Enum',{'bSetDefault':True,'IntValue':256})
        reject(root,'Enum',{'bSetDefault':True,'IntValue':250})
        reject(root,'Enum',{'bSetNativeEnumName':True,'NativeEnumName':'EPathFollowingStatus'})
        edit(root,'Enum',{'bSetNativeEnumName':True,'NativeEnumName':ENUM})
        assert row(root,'Enum')['type_settings']['enum_name_valid']
        reject(root,'Enum',{'bSetEnumType':True,'EnumTypePath':'/Script/AIModule.EPathFollowingResult'})
        edit(root,'Enum',{'bSetNativeEnumName':True,'NativeEnumName':''})
        assert not row(root,'Enum')['type_settings']['enum_name_valid'] and row(root,'Enum')['type_settings']['enum_type']==ENUM
        edit(root,'Enum',{'bSetNativeEnumName':True,'NativeEnumName':ENUM})
        edit(root,'Vector',{'bSetUseDefault':True,'bUseDefault':False})
        assert not row(root,'Vector')['type_settings']['use_default_value'] and row(root,'Vector')['type_settings']['default_value']['X']==120
        edit(root,'Vector',{'bSetUseDefault':True,'bUseDefault':True})
        edit(root,'Object',{'bSetDefault':True,'ReferenceValue':''})
        assert row(root,'Object')['type_settings']['default_value']==''
        edit(root,'Object',{'bSetDefault':True,'ReferenceValue':'/Engine/BasicShapes/Cube.Cube'})
        # Replacement plus typed settings must apply in one transaction.
        add(root,'Replace','Bool')
        edit(root,'Replace',{'bSetDefault':True,'IntValue':77},KeyType='/Script/AIModule.BlackboardKeyType_Int')
        assert row(root,'Replace')['type_settings']['default_value']==77
        call('POST','/editor/transactions/undo');assert row(root,'Replace')['type_settings']['kind']=='Bool'
        call('POST','/editor/transactions/redo');assert row(root,'Replace')['type_settings']['default_value']==77
        call('PATCH','/blackboards/settings',{'AssetPath':child,'bSetParent':True,'ParentPath':root,'bSave':True})
        inherited=inspect(child)['inherited_keys'];assert next(k for k in inherited if k['name']=='Float')['type_settings']['default_value']==2.5
        reject(root,'Object',{'bSetBaseClass':True,'BaseClass':'/Script/CoreUObject.Object'})
        edit(root,'Object',{'bSetBaseClass':True,'BaseClass':'/Script/CoreUObject.Object'},bConfirm=True)
        snapshots={}
        for path in paths:
            call('POST','/assets/save',{'AssetPath':path});s=inspect(path);assert s['validation']['valid'] and not s['dirty'];snapshots[path]=s
        STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps({'paths':paths,'snapshots':snapshots}));keep=True
        print('Typed native Blackboard defaults/constraints/Enum settings, transient preflight, CDO isolation, no-op/dry-run, mixed rejection, subobject undo and inherited settings: OK; restart and verify')
    finally:
        if not keep:cleanup(paths)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base-url',default='http://127.0.0.1:8080');p.add_argument('--phase',choices=['prepare','verify','cleanup'],required=True)
    a=p.parse_args();run(a.base_url,a.phase)
