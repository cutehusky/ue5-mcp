"""Output binding direction metadata, guards and persistence."""
import argparse
from state_tree_verification import StateTreeVerification

def run(base,phase):
    t=StateTreeVerification('state_tree_output_bindings',base)
    if phase!='prepare':
        if phase=='verify':t.verify();print('Cold output binding direction and identities: OK')
        t.cleanup();return
    assert not t.manifest.exists();keep=False
    try:
        path,root=t.create('OutputBindings')
        t.edit(path,'POST','parameters',Name='Amount',ParameterType='Float',bSetValue=True,Value='1')
        evaluator=t.edit(path,'POST','nodes',Kind='evaluator',NodeClassPath='/Script/UE5_MCP.MCPVerificationBlueprintEvaluator')['selected_id']
        binding={'SourceId':'root','SourcePath':'Amount','TargetId':evaluator,'TargetPath':'OutputValue','bOutput':True}
        before=t.snapshots();t.edit(path,'POST','bindings',Binding=binding,bDryRun=True);assert t.snapshots()==before
        t.transaction_check(lambda:t.edit(path,'POST','bindings',Binding=binding))
        assert t.inspect(path)['bindings'][0]['output_binding']
        assert not t.edit(path,'POST','bindings',Binding=binding)['would_change']
        t.reject(path,'POST','bindings',Binding=binding|{'TargetPath':'Amount'})
        t.edit(path,'POST','parameters',Name='Text',ParameterType='String',bSetValue=True,Value='value')
        t.reject(path,'POST','bindings',Binding=binding|{'SourcePath':'Text'},bConfirm=True)
        t.save();keep=True;print('Output binding native direction/readback, dry-run/no-op, transactions and invalid direction guards: OK')
    finally:
        if not keep:t.cleanup()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','verify','cleanup']);p.add_argument('--base',default='http://127.0.0.1:8080');a=p.parse_args();run(a.base,a.phase)
