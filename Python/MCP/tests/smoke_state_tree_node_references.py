"""Native/Blueprint typed node-reference authoring and persistence."""
import argparse,json,uuid
from state_tree_verification import StateTreeVerification

MATERIAL='/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial'
REFS={'Material':MATERIAL,'SoftMaterial':MATERIAL,'ActorClass':'/Script/Engine.Pawn','SoftActorClass':'/Script/Engine.Pawn'}

def run(base,phase):
    t=StateTreeVerification('state_tree_node_references',base);blueprints=[]
    def cleanup():
        t.cleanup()
        for p in blueprints:t.call('POST','/assets/delete',{'AssetPath':p})
    if phase!='prepare':
        s=json.loads(t.manifest.read_text());blueprints.extend(s['blueprints'])
        if phase=='verify':t.verify();print('Cold native/Blueprint typed reference paths and bindings: OK')
        cleanup();return
    assert not t.manifest.exists();keep=False
    try:
        path,root=t.create('NodeReferences')
        name='BP_Ref_'+uuid.uuid4().hex[:8]
        created=t.call('POST','/blueprint',{'BpPath':'/Game/UE5MCP_Test/'+name,'ParentClass':'/Script/UE5_MCP.MCPVerificationBlueprintTask'})
        bp=created['bpPath'];bp=bp if '.' in bp else bp+'.'+bp.rsplit('/',1)[-1];blueprints.append(bp)
        t.call('POST','/blueprints/compile',{'BpPath':bp})
        state=t.edit(path,'POST','states',ParentId=root,Name='Work')['selected_id']
        for cls in ['/Script/UE5_MCP.MCPVerificationBlueprintTask',bp+'_C']:
            before=t.snapshots();t.edit(path,'POST','nodes',StateId=state,NodeClassPath=cls,InstanceReferences=REFS,bDryRun=True);assert t.snapshots()==before
            task=t.transaction_check(lambda:t.edit(path,'POST','nodes',StateId=state,NodeClassPath=cls,InstanceReferences=REFS))['selected_id']
            def node():return next(n for n in t.state(path,state)['tasks']if n['id']==task)
            assert node()['instance_references']==REFS
            assert not t.edit(path,'PATCH','nodes',StateId=state,ItemId=task,InstanceReferences=REFS)['would_change']
            for refs in [{'ActorClass':'/Script/Engine.Material'},{'Material':'/Script/Engine.Actor'},{'SoftMaterial':'/Game/Missing.Asset'},{'Samples':MATERIAL},{'Missing':MATERIAL}]:
                t.reject(path,'PATCH','nodes',StateId=state,ItemId=task,InstanceReferences=refs)
            t.transaction_check(lambda:t.edit(path,'PATCH','nodes',StateId=state,ItemId=task,InstanceReferences={k:'None'for k in REFS}))
            assert all(not v for v in node()['instance_references'].values())
            t.transaction_check(lambda:t.edit(path,'PATCH','nodes',StateId=state,ItemId=task,InstanceReferences=REFS))
            if cls.endswith('_C'):
                t.call('POST','/blueprints/variables',{'BpPath':bp,'VarSignature':'float Recompiled','DefaultValue':'1'})
                assert node()['instance_references']==REFS
        target=t.state(path,state)['tasks'][0]['id']
        function=t.edit(path,'POST','functions',StructPath='/Script/UE5_MCP.MCPVerificationReferenceFunction',Binding={'TargetId':target,'TargetPath':'Amount'},InstanceReferences=REFS)['selected_id']
        t.transaction_check(lambda:t.edit(path,'PATCH','functions',ItemId=function,InstanceReferences={'Material':'None'}))
        t.transaction_check(lambda:t.edit(path,'PATCH','functions',ItemId=function,InstanceReferences=REFS))
        for field in ['TransientMaterial','ReadOnlyMaterial','InstancedObject']:
            t.reject(path,'PATCH','functions',ItemId=function,InstanceReferences={field:MATERIAL})
        t.edit(path,'POST','nodes',StateId=state,NodeClassPath='/Script/UE5_MCP.MCPVerificationBlueprintTask',Functions=[{'StructPath':'/Script/UE5_MCP.MCPVerificationReferenceFunction','TargetId':'$new','TargetPath':'Amount','InstanceReferences':REFS}])
        t.call('POST','/assets/save',{'AssetPath':bp});t.save();s=json.loads(t.manifest.read_text());s['blueprints']=blueprints;t.manifest.write_text(json.dumps(s,indent=2));keep=True
        print('Native/Blueprint hard-soft references, constraints, clearing, reinstancing and transactions: OK')
    finally:
        if not keep:cleanup()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','verify','cleanup']);p.add_argument('--base',default='http://127.0.0.1:8080');a=p.parse_args();run(a.base,a.phase)
