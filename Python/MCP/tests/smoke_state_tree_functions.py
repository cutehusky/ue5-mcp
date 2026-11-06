"""Property function authoring, nested ownership and persistence."""
import argparse
from state_tree_verification import StateTreeVerification

FUNCTION='/Script/StateTreeModule.StateTreeAddFloatPropertyFunction'

def run(base,phase):
    t=StateTreeVerification('state_tree_functions',base)
    if phase!='prepare':
        if phase=='verify':
            t.verify()
            print('Cold property function identities/settings/nested bindings: OK')
        t.cleanup();return
    assert not t.manifest.exists()
    keep=False
    try:
        path,root=t.create('Functions')
        state=t.edit(path,'POST','states',ParentId=root,Name='Work')['selected_id']
        task=t.edit(path,'POST','nodes',StateId=state,StructPath='/Script/StateTreeModule.StateTreeDelayTask',InstanceProperties={'RandomDeviation':'0'})['selected_id']
        t.edit(path,'POST','transitions',StateId=state)
        t.edit(path,'POST','parameters',Name='Input',ParameterType='Float',bSetValue=True,Value='0.02')
        discovered=t.call('GET','/state-trees/node-types',asset_path=path,kind='property_function',search='StateTreeAddFloatPropertyFunction')
        assert discovered['nodes'][0]['struct']==FUNCTION
        args={'StructPath':FUNCTION,'Binding':{'TargetId':task,'TargetPath':'Duration'},'InstanceProperties':{'Left':'0.02','Right':'0.03'}}
        before=t.snapshots();t.edit(path,'POST','functions',**args,bDryRun=True);assert t.snapshots()==before
        function=t.transaction_check(lambda:t.edit(path,'POST','functions',**args))['selected_id']
        t.transaction_check(lambda:t.edit(path,'PATCH','functions',ItemId=function,InstanceProperties={'Right':'0.04'}))
        assert not t.edit(path,'PATCH','functions',ItemId=function,InstanceProperties={'Right':'0.04'})['would_change']
        nested=t.transaction_check(lambda:t.edit(path,'POST','functions',StructPath=FUNCTION,Binding={'TargetId':function,'TargetPath':'Left'},InstanceProperties={'Right':'0.01'},Bindings=[{'SourceId':'root','SourcePath':'Input','TargetId':'$function','TargetPath':'Left'}]))['selected_id']
        t.reject(path,'POST','bindings',Binding={'SourceId':function,'SourcePath':'Result','TargetId':nested,'TargetPath':'Right'},bConfirm=True)
        t.reject(path,'POST','functions',StructPath=FUNCTION,Binding={'TargetId':task,'TargetPath':'Duration','SourcePath':'Left'},bConfirm=True)
        t.reject(path,'DELETE','functions',ItemId=function)
        before=t.snapshots(stable=True)
        t.edit(path,'DELETE','functions',ItemId=function,bConfirm=True)
        assert t.inspect(path)['binding_count']==0
        t.call('POST','/editor/transactions/undo');assert t.snapshots(stable=True)==before
        t.save();keep=True
        print('Function discovery/create/update/nested inputs/cycle guards/recursive deletion/undo/save: OK')
    finally:
        if not keep:t.cleanup()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','verify','cleanup']);p.add_argument('--base',default='http://127.0.0.1:8080');a=p.parse_args();run(a.base,a.phase)
