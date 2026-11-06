#include "StateTreeUtils.h"
#include "UE5_MCP/API/DTO/StateTreeReq.h"
#include "StateTree.h"
#include "StateTreeInstanceData.h"
#include "StateTreeEvents.h"
#include "NavigationWorldUtils.h"
#include "Components/StateTreeComponent.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "StateTreeSchema.h"
#include "StateTreeState.h"
#include "StateTreeEditorData.h"
#include "StateTreeEditorModule.h"
#include "StateTreeEditorSchema.h"
#include "StateTreeEditingSubsystem.h"
#include "StateTreeCompiler.h"
#include "StateTreeCompilerLog.h"
#include "StateTreeTaskBase.h"
#include "StateTreeConditionBase.h"
#include "StateTreeConsiderationBase.h"
#include "Considerations/StateTreeCommonConsiderations.h"
#include "StateTreeEditorPropertyBindings.h"
#include "StateTreePropertyFunctionBase.h"
#include "Blueprint/StateTreeTaskBlueprintBase.h"
#include "Blueprint/StateTreeConditionBlueprintBase.h"
#include "Blueprint/StateTreeEvaluatorBlueprintBase.h"
#include "Blueprint/StateTreeConsiderationBlueprintBase.h"
#include "Engine/Blueprint.h"
#include "StateTreeEvaluatorBase.h"
#include "StateTreeDelegates.h"
#include "PropertyBindingPath.h"
#include "StructUtils/PropertyBag.h"
#include "GameplayTagsManager.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Editor.h"
#include "ScopedTransaction.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "Misc/PackageName.h"
#include "Misc/StringOutputDevice.h"
#include "Misc/ScopeExit.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/Package.h"
#include "UObject/UObjectIterator.h"
#include "UObject/UObjectHash.h"
#include "UObject/UnrealType.h"
#include <stdexcept>
#include <charconv>
namespace
{
 UStateTree* Load(const FString& Path)
 {
  const FString P=FPackageName::ObjectPathToPackageName(Path); if(!FPackageName::IsValidLongPackageName(P)) throw std::runtime_error("A valid StateTree asset path is required"); const FString O=Path.Contains(TEXT(".")) ? Path : P+TEXT(".")+FPackageName::GetLongPackageAssetName(P);
  auto* T=FindObject<UStateTree>(nullptr,*O); if(!T && FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(O)).IsValid()) T=LoadObject<UStateTree>(nullptr,*O); if(!IsValid(T)) throw std::runtime_error("Asset is not an existing StateTree"); return T;
 }
 FGuid Guid(const FString& S) { FGuid G; if(!FGuid::Parse(S,G) || !G.IsValid()) throw std::runtime_error("A valid StateTree GUID is required"); return G; }
 FString Id(const FGuid& G) { return G.ToString(EGuidFormats::DigitsWithHyphens); }
 template<typename E> E Enum(const FString& S) { auto* EType=StaticEnum<E>(); const int64 V=EType->GetValueByNameString(S); if(V==INDEX_NONE || EType->HasMetaData(TEXT("Hidden"),EType->GetIndexByValue(V)) || (EType->ContainsExistingMax() && EType->GetIndexByValue(V)==EType->NumEnums()-1)) throw std::runtime_error("A visible native enum member is required"); return E(V); }
 EStateTreeExpressionOperand ExpressionOperand(const FStateTreeReq& R)
 {
  const auto Operand=Enum<EStateTreeExpressionOperand>(R.Operand); if(Operand==EStateTreeExpressionOperand::Multiply && R.Kind!=TEXT("consideration")) throw std::runtime_error("Multiply is supported only for consideration expressions"); return Operand;
 }
 bool Plain(FProperty* P,int32 Depth=0) { if(Depth>8 || P->ArrayDim!=1) return false; if(CastField<FNumericProperty>(P) || CastField<FBoolProperty>(P) || CastField<FEnumProperty>(P) || CastField<FStrProperty>(P) || CastField<FNameProperty>(P) || CastField<FTextProperty>(P)) return true; if(auto* S=CastField<FStructProperty>(P)) { if(S->Struct==FGameplayTag::StaticStruct()) return false; for(TFieldIterator<FProperty> It(S->Struct);It;++It) if(!Plain(*It,Depth+1)) return false; return true; } return false; }
 void ValidateIntegerText(FProperty* Property,const FString& Text)
 {
  const auto* Numeric=CastField<FNumericProperty>(Property);
  if(!Numeric || !Numeric->IsInteger() || Numeric->GetIntPropertyEnum()) return;
  FString Token=Text.TrimStartAndEnd(); bool Negative=false;
  if(Token.StartsWith(TEXT("-")) || Token.StartsWith(TEXT("+"))) { Negative=Token[0]==TEXT('-'); Token.RightChopInline(1); }
  int32 Base=10; if(Token.StartsWith(TEXT("0x"),ESearchCase::IgnoreCase)) { Base=16; Token.RightChopInline(2); }
  const FTCHARToUTF8 Bytes(*Token); uint64 Magnitude=0;
  const auto Parsed=std::from_chars(Bytes.Get(),Bytes.Get()+Bytes.Length(),Magnitude,Base);
  if(Token.IsEmpty() || Parsed.ec!=std::errc() || Parsed.ptr!=Bytes.Get()+Bytes.Length()) throw std::runtime_error("Integer setting requires an exact bounded integer token");
  const bool Unsigned=CastField<FByteProperty>(Property) || CastField<FUInt16Property>(Property) || CastField<FUInt32Property>(Property) || CastField<FUInt64Property>(Property);
  if(Unsigned) { if((Negative && Magnitude!=0) || !Numeric->CanHoldValue(Magnitude)) throw std::runtime_error("Integer setting exceeds native unsigned width"); }
  else
  {
   if(Magnitude>uint64(MAX_int64)+(Negative ? 1u : 0u)) throw std::runtime_error("Integer setting exceeds int64 width");
   const int64 Value=Negative ? (Magnitude==uint64(MAX_int64)+1u ? MIN_int64 : -int64(Magnitude)) : int64(Magnitude);
   if(!Numeric->CanHoldValue(Value)) throw std::runtime_error("Integer setting exceeds native signed width");
  }
 }
 void Number(FProperty* P,const void* Data)
 {
  if(auto* N=CastField<FNumericProperty>(P)) if(N->IsInteger() || N->IsFloatingPoint()) { const double V=N->IsFloatingPoint() ? N->GetFloatingPointPropertyValue(Data) : double(N->GetSignedIntPropertyValue(Data)); if(!FMath::IsFinite(V) || FMath::Abs(V)>1.e12 || (P->HasMetaData(TEXT("ClampMin")) && V<FCString::Atod(*P->GetMetaData(TEXT("ClampMin")))) || (P->HasMetaData(TEXT("ClampMax")) && V>FCString::Atod(*P->GetMetaData(TEXT("ClampMax"))))) throw std::runtime_error("StateTree numeric settings violate finite/native clamp bounds"); }
  UEnum* E=nullptr; int64 V=0; if(auto* B=CastField<FByteProperty>(P)) { E=B->Enum; V=B->GetPropertyValue(Data); } else if(auto* F=CastField<FEnumProperty>(P)) { E=F->GetEnum(); V=F->GetUnderlyingProperty()->GetSignedIntPropertyValue(Data); }
  if(E && (!E->IsValidEnumValueOrBitfield(V) || (E->ContainsExistingMax() && E->GetIndexByValue(V)==E->NumEnums()-1))) throw std::runtime_error("StateTree enum setting requires a native member excluding MAX");
  if(auto* S=CastField<FStructProperty>(P)) for(TFieldIterator<FProperty> It(S->Struct);It;++It) Number(*It,It->ContainerPtrToValuePtr<void>(Data));
 }
 void Settings(UStruct* Type,void* Data,const TMap<FString,FString>& Values,UObject* Owner,const TSet<FName>* Allowed=nullptr)
 {
  if(Values.Num()>64) throw std::runtime_error("At most 64 StateTree settings per map");
  for(const auto& Pair:Values) { auto* P=FindFProperty<FProperty>(Type,*Pair.Key); if(!P || !P->HasAnyPropertyFlags(CPF_Edit) || P->HasAnyPropertyFlags(CPF_Transient) || !Plain(P) || Pair.Value.Len()>4096 || (Allowed && !Allowed->Contains(P->GetFName()))) throw std::runtime_error("Settings require supported editable scalar/plain-struct fields and text <=4096 characters"); FStringOutputDevice Errors; auto* Address=P->ContainerPtrToValuePtr<void>(Data); ValidateIntegerText(P,Pair.Value); const auto* End=P->ImportText_Direct(*Pair.Value,Address,Owner,PPF_None,&Errors); if(!End || !Errors.IsEmpty() || !FString(End).TrimStartAndEnd().IsEmpty()) throw std::runtime_error("StateTree setting failed native text import"); Number(P,Address); }
 }
 struct FModel { UStateTreeEditorData* Data=nullptr; TArray<UStateTreeState*> States; TMap<FGuid,UStateTreeState*> ById; TSet<FGuid> IDs; int32 Nodes=0,Transitions=0; };
 FModel Model(UStateTree* T)
 {
  FModel M; M.Data=Cast<UStateTreeEditorData>(T->EditorData); if(!M.Data || !M.Data->IsIn(T) || !M.Data->Schema || !M.Data->Schema->IsIn(M.Data) || !M.Data->EditorSchema || !M.Data->EditorSchema->IsIn(M.Data)) throw std::runtime_error("StateTree requires owned native editor data/schema");
  auto Add=[&](const FGuid& G) { if(!G.IsValid() || M.IDs.Contains(G)) throw std::runtime_error("StateTree has invalid/repeated native IDs"); M.IDs.Add(G); };
  auto CheckBag=[](const FInstancedPropertyBag& B) { TSet<FGuid> Fields; if(const auto* Type=B.GetPropertyBagStruct()) { if(Type->GetPropertyDescs().Num()>64) throw std::runtime_error("At most 64 parameters per bag"); for(const auto& D:Type->GetPropertyDescs()) { if(!D.ID.IsValid() || Fields.Contains(D.ID) || !D.CachedProperty) throw std::runtime_error("Invalid parameter field identity/layout"); Fields.Add(D.ID); } } };
  CheckBag(M.Data->GetRootParametersPropertyBag()); if(M.Data->EditorBindings.GetNumBindings()>1024) throw std::runtime_error("At most 1024 StateTree bindings");
  Add(M.Data->GetRootParametersGuid());
  auto Node=[&](const FStateTreeEditorNode& N) { if(!N.Node.IsValid()) return; if(++M.Nodes>1024 || !N.Node.GetScriptStruct()->IsChildOf(FStateTreeNodeBase::StaticStruct())) throw std::runtime_error("Invalid node type or more than 1024 nodes"); Add(N.ID); if((N.InstanceObject && !N.InstanceObject->IsIn(T)) || (N.ExecutionRuntimeDataObject && !N.ExecutionRuntimeDataObject->IsIn(T))) throw std::runtime_error("Foreign StateTree node instance"); };
  if(M.Data->GlobalTasks.Num()>64 || M.Data->Evaluators.Num()>64) throw std::runtime_error("StateTree global node capacity exceeded"); for(const auto& N:M.Data->GlobalTasks) Node(N); for(const auto& N:M.Data->Evaluators) Node(N);
  TFunction<void(UStateTreeState*,UStateTreeState*,int32)> Visit=[&](UStateTreeState* S,UStateTreeState* Parent,int32 Depth)
  {
   if(!S || !S->IsIn(M.Data) || S->Parent!=Parent || M.States.Contains(S) || M.States.Num()>=512 || Depth>32) throw std::runtime_error("StateTree hierarchy has invalid ownership, parent, cycle or capacity/depth"); Add(S->ID); Add(S->Parameters.ID); CheckBag(S->Parameters.Parameters); M.States.Add(S); M.ById.Add(S->ID,S);
   if(S->Type==EStateTreeStateType::LinkedAsset) { auto* D=IsValid(S->LinkedAsset) ? Cast<UStateTreeEditorData>(S->LinkedAsset->EditorData) : nullptr; if(!D || !D->Schema || D->Schema->GetClass()!=M.Data->Schema->GetClass()) throw std::runtime_error("Linked asset requires owned editor data and the same native schema class"); for(const auto& Required:D->Schema->GetContextDataDescs()) { const auto Available=M.Data->Schema->GetContextDataDescs(); const auto* Match=Available.FindByPredicate([&](const FStateTreeExternalDataDesc& Context) { return Context.ID==Required.ID && Context.Name==Required.Name; }); if(!Match || !Match->Struct || !Required.Struct || !Match->Struct->IsChildOf(Required.Struct)) throw std::runtime_error("Linked asset context requirements are incompatible with caller schema"); } }
   if((S->Type==EStateTreeStateType::Linked || S->Type==EStateTreeStateType::LinkedAsset) && (!S->Children.IsEmpty() || !S->Tasks.IsEmpty() || S->SingleTask.Node.IsValid())) throw std::runtime_error("Linked states cannot own child states or tasks");
   if(S->Tasks.Num()>64 || S->EnterConditions.Num()>64 || S->Considerations.Num()>64 || S->Transitions.Num()>64) throw std::runtime_error("At most 64 items per StateTree state collection");
   auto Condition=[&](const FStateTreeEditorNode& N) { if(N.Node.IsValid() && N.ExpressionOperand==EStateTreeExpressionOperand::Multiply) throw std::runtime_error("Condition expressions cannot use Multiply"); Node(N); }; for(const auto& N:S->Tasks) Node(N); for(const auto& N:S->EnterConditions) Condition(N); for(const auto& N:S->Considerations) Node(N); Node(S->SingleTask);
   for(const auto& Tr:S->Transitions) { if(++M.Transitions>1024 || Tr.Conditions.Num()>64) throw std::runtime_error("StateTree transition capacity exceeded"); Add(Tr.ID); for(const auto& N:Tr.Conditions) Condition(N); }
   for(UStateTreeState* C:S->Children) Visit(C,S,Depth+1);
  }; for(UStateTreeState* S:M.Data->SubTrees) Visit(S,nullptr,1);
  for(auto* S:M.States) for(const auto& Tr:S->Transitions) if(Tr.State.LinkType==EStateTreeTransitionType::GotoState && !M.ById.Contains(Tr.State.ID)) throw std::runtime_error("Dangling StateTree transition target");
  TSet<FGuid> FunctionIDs; for(const auto& B:M.Data->EditorBindings.GetBindings()) if(const auto* Function=B.GetPropertyFunctionNode().GetPtr<const FStateTreeEditorNode>()) { Node(*Function); if(!Function->Node.IsValid() || !Function->Node.GetScriptStruct()->IsChildOf(FStateTreePropertyFunctionBase::StaticStruct()) || B.GetSourcePath().GetStructID()!=Function->ID) throw std::runtime_error("Invalid native property function binding identity/type"); FunctionIDs.Add(Function->ID); }
  TMap<FGuid,TArray<FGuid>> FunctionDependencies; for(const auto& B:M.Data->EditorBindings.GetBindings()) if(FunctionIDs.Contains(B.GetTargetPath().GetStructID()) && FunctionIDs.Contains(B.GetSourcePath().GetStructID())) FunctionDependencies.FindOrAdd(B.GetTargetPath().GetStructID()).Add(B.GetSourcePath().GetStructID());
  TSet<FGuid> VisitingFunctions; TMap<FGuid,int32> FunctionDepths; TFunction<int32(FGuid,int32)> CheckFunction=[&](FGuid ID,int32 Stack) -> int32 { if(Stack>32 || VisitingFunctions.Contains(ID)) throw std::runtime_error("Property function cycle or depth exceeds 32"); if(const auto* Known=FunctionDepths.Find(ID)) { if(Stack+*Known-1>32) throw std::runtime_error("Property function depth exceeds 32"); return *Known; } VisitingFunctions.Add(ID); int32 Depth=1; if(const auto* Inputs=FunctionDependencies.Find(ID)) for(const auto& Input:*Inputs) Depth=FMath::Max(Depth,1+CheckFunction(Input,Stack+1)); VisitingFunctions.Remove(ID); if(Stack+Depth-1>32) throw std::runtime_error("Property function depth exceeds 32"); FunctionDepths.Add(ID,Depth); return Depth; }; for(const auto& ID:FunctionIDs) CheckFunction(ID,1);
  TSet<UStateTreeState*> Active; TMap<UStateTreeState*,int32> SelectionDepth;
  TFunction<int32(UStateTreeState*,int32)> CheckLinks=[&](UStateTreeState* S,int32 StackDepth) -> int32
  {
   if(Active.Contains(S) || StackDepth>64) throw std::runtime_error("Linked subtree selection cycle or depth exceeds 64");
   if(const auto* Cached=SelectionDepth.Find(S)) return *Cached;
   Active.Add(S); int32 Depth=1;
   if(S->Type==EStateTreeStateType::Linked) { auto* Target=M.ById.Find(S->LinkedSubtree.ID); if(!Target || (*Target)->Type!=EStateTreeStateType::Subtree || S->LinkedSubtree.LinkType!=EStateTreeTransitionType::GotoState) throw std::runtime_error("Linked state requires an owned Subtree target"); Depth=1+CheckLinks(*Target,StackDepth+1); }
   else for(UStateTreeState* C:S->Children) Depth=FMath::Max(Depth,1+CheckLinks(C,StackDepth+1));
   if(Depth>64) throw std::runtime_error("Linked subtree selection depth exceeds 64");
   Active.Remove(S); SelectionDepth.Add(S,Depth); return Depth;
  }; for(auto* S:M.States) CheckLinks(S,1);
  return M;
 }
 void DiscardPreview(UStateTree* T)
 {
  // UE's pre-PIE iterator can still see garbage objects until collection.
  // Remove the retired editor graph so CompileIfChanged observes an empty hash.
  T->EditorData=nullptr;
  T->LastCompiledEditorDataHash=0;
  T->MarkAsGarbage();
 }
 TStrongObjectPtr<UStateTree> PreviewCopy(UStateTree* T)
 {
  // Seed each serialization root to bypass its normal PostDuplicate callback.
  // Native editor-data duplication regenerates IDs and asserts on derived global
  // node IDs in UE 5.7. Validation needs the original IDs throughout duplication.
  auto Source=Model(T); TMap<UObject*,UObject*> Copies;
  TStrongObjectPtr<UStateTree> Copy(NewObject<UStateTree>(GetTransientPackage(),T->GetClass(),NAME_None,RF_Transient));
  auto* Data=NewObject<UStateTreeEditorData>(Copy.Get(),Source.Data->GetClass(),NAME_None,RF_Transient);
  bool ValidCopy=false;
  ON_SCOPE_EXIT { if(!ValidCopy) DiscardPreview(Copy.Get()); };
  auto RootParams=InitStaticDuplicateObjectParams(T,GetTransientPackage()); RootParams.CreatedObjects=&Copies;
  RootParams.DuplicationSeed.Add(T,Copy.Get()); RootParams.DuplicationSeed.Add(Source.Data,Data);
  StaticDuplicateObjectEx(RootParams);
  auto DataParams=InitStaticDuplicateObjectParams(Source.Data,Copy.Get()); DataParams.DuplicationSeed=Copies;
  DataParams.DuplicationSeed.Add(T,Copy.Get()); DataParams.DuplicationSeed.Add(Source.Data,Data);
  TMap<UObject*,UObject*> EditorCopies; DataParams.CreatedObjects=&EditorCopies;
  StaticDuplicateObjectEx(DataParams); Copies.Append(EditorCopies); Copies.Add(Source.Data,Data);
  Copy->ClearFlags(RF_Public|RF_Standalone|RF_NeedPostLoad|RF_NeedPostLoadSubobjects); Copy->SetFlags(RF_Transient);
  Data->ClearFlags(RF_NeedPostLoad|RF_NeedPostLoadSubobjects); Data->EditorBindings.SetBindingsOwner(Data);
  Copy->ResetCompiled();
  for(const auto& Pair:Copies) if(Pair.Key==Source.Data || Pair.Key->IsIn(Source.Data))
  {
   TArray<FGuid> Values; for(TPropertyValueIterator<FStructProperty> It(Pair.Key->GetClass(),Pair.Key,EPropertyValueIteratorFlags::FullRecursion,EFieldIteratorFlags::ExcludeDeprecated);It;++It) if(It.Key()->Struct==TBaseStructure<FGuid>::Get()) { Values.Add(*static_cast<const FGuid*>(It.Value())); It.SkipRecursiveProperty(); }
   int32 Index=0; for(TPropertyValueIterator<FStructProperty> It(Pair.Value->GetClass(),Pair.Value,EPropertyValueIteratorFlags::FullRecursion,EFieldIteratorFlags::ExcludeDeprecated);It;++It) if(It.Key()->Struct==TBaseStructure<FGuid>::Get()) { if(!Values.IsValidIndex(Index)) throw std::runtime_error("StateTree preview identity layout changed during duplication"); *const_cast<FGuid*>(static_cast<const FGuid*>(It.Value()))=Values[Index++]; It.SkipRecursiveProperty(); }
   if(Index!=Values.Num()) throw std::runtime_error("StateTree preview identity field count mismatch");
  }
  if(Copy->EditorData!=Data || !Data->IsIn(Copy.Get())) throw std::runtime_error("StateTree preview failed editor ownership"); Data->Colors=Source.Data->Colors; Model(Copy.Get()); ValidCopy=true; return Copy;
 }
 UStateTreeState* State(FModel& M,const FString& S) { auto* P=M.ById.Find(Guid(S)); if(!P) throw std::runtime_error("State GUID does not belong to this tree"); return *P; }
 TArray<TObjectPtr<UStateTreeState>>& Siblings(FModel& M,UStateTreeState* Parent) { return Parent ? Parent->Children : M.Data->SubTrees; }
 FStateTreeTransition& Transition(UStateTreeState* S,const FString& G) { auto ID=Guid(G); for(auto& Tr:S->Transitions) if(Tr.ID==ID) return Tr; throw std::runtime_error("Transition GUID does not belong to the state"); }
 TArray<FStateTreeEditorNode>& Nodes(FModel& M,const FStateTreeReq& R)
 {
  if(R.Kind==TEXT("evaluator")) { if(!M.Data->Schema->AllowEvaluators()) throw std::runtime_error("Schema does not allow evaluators"); return M.Data->Evaluators; } if(R.Kind==TEXT("global_task")) return M.Data->GlobalTasks;
  auto* S=State(M,R.StateId); if(R.Kind==TEXT("task")) { if(S->Type==EStateTreeStateType::Linked || S->Type==EStateTreeStateType::LinkedAsset || S->Type==EStateTreeStateType::Group) throw std::runtime_error("Linked/group states cannot own tasks"); if(!M.Data->Schema->AllowMultipleTasks()) throw std::runtime_error("Single-task schemas require their dedicated adapter"); return S->Tasks; } if(R.Kind==TEXT("enter_condition")) { if(!M.Data->Schema->AllowEnterConditions()) throw std::runtime_error("Schema does not allow enter conditions"); return S->EnterConditions; } if(R.Kind==TEXT("consideration")) { if(!M.Data->Schema->AllowUtilityConsiderations()) throw std::runtime_error("Schema does not allow utility considerations"); return S->Considerations; } if(R.Kind==TEXT("transition_condition")) return Transition(S,R.TransitionId).Conditions; throw std::runtime_error("Kind requires task, global_task, evaluator, enter_condition or transition_condition");
 }
 FStateTreeEditorNode& Node(FModel& M,const FStateTreeReq& R) { auto G=Guid(R.ItemId); for(auto& N:Nodes(M,R)) if(N.ID==G) return N; throw std::runtime_error("Node ID does not belong to the selected collection"); }
 bool ReferenceSettings(UStruct* Type,void* Data,const TMap<FString,FString>& Values);
 bool ContainerSettings(UStruct* Type,void* Data,const TMap<FString,FString>& Values,UObject* Owner);
 void ConsiderationSettings(FStateTreeEditorNode& N,const FStateTreeReq& R);
 bool NodeSettings(FStateTreeEditorNode& N,const FStateTreeReq& R,UObject* Owner)
 {
  if(R.bSetName) { if(R.Name.Len()>128 || R.Name.Contains(TEXT("\n")) || R.Name.Contains(TEXT("\r"))) throw std::runtime_error("Node names require <=128 characters without newlines"); N.Node.GetMutable<FStateTreeNodeBase>().Name=FName(*R.Name); }
  if(R.bSetTaskEnabled) { auto* Task=N.Node.GetMutablePtr<FStateTreeTaskBase>(); if(!Task) throw std::runtime_error("Task enablement requires a native task or Blueprint task wrapper"); Task->bTaskEnabled=R.bEnabled; }
  if(R.bSetTaskCompletion) { auto* Task=N.Node.GetMutablePtr<FStateTreeTaskBase>(); if(!Task || !Task->bCanEditConsideredForCompletion) throw std::runtime_error("Task does not allow editing completion participation"); const auto* Tree=Cast<UStateTree>(Owner); const auto* Data=Tree ? Cast<UStateTreeEditorData>(Tree->EditorData) : nullptr; if(!Data || !Data->Schema->AllowTasksCompletion()) throw std::runtime_error("Schema does not allow task completion settings"); Task->bConsideredForCompletion=R.bConsideredForCompletion; }
  if(R.bSetConditionEvaluation) { auto* Condition=N.Node.GetMutablePtr<FStateTreeConditionBase>(); if(!Condition) throw std::runtime_error("Evaluation mode requires a condition node"); Condition->EvaluationMode=Enum<EStateTreeConditionEvaluationMode>(R.ConditionEvaluation); }
  ConsiderationSettings(N,R);
  Settings(const_cast<UScriptStruct*>(N.Node.GetScriptStruct()),N.Node.GetMutableMemory(),R.Properties,Owner); const auto& Definition=N.Node.Get<FStateTreeNodeBase>();
  if(Definition.GetInstanceDataType() && Definition.GetInstanceDataType()!=N.GetInstance().GetStruct()) throw std::runtime_error("Node configuration changes instance layout; recreate this node");
  bool ObjectChanged=false;
  if(!R.InstanceProperties.IsEmpty()) { if(N.InstanceObject) { if(R.InstanceProperties.Num()>64) throw std::runtime_error("At most 64 node instance settings"); for(const auto& Pair:R.InstanceProperties) { auto* P=FindFProperty<FProperty>(N.InstanceObject->GetClass(),*Pair.Key); FString Before,After; if(P) P->ExportText_InContainer(0,Before,N.InstanceObject,N.InstanceObject,N.InstanceObject,PPF_None); Settings(N.InstanceObject->GetClass(),N.InstanceObject,{{Pair.Key,Pair.Value}},N.InstanceObject); if(P) P->ExportText_InContainer(0,After,N.InstanceObject,N.InstanceObject,N.InstanceObject,PPF_None); ObjectChanged|=Before!=After; } } else { if(!N.Instance.IsValid()) throw std::runtime_error("Node has no editable instance data"); Settings(const_cast<UScriptStruct*>(N.Instance.GetScriptStruct()),N.Instance.GetMutableMemory(),R.InstanceProperties,Owner); } }
  if(!R.InstanceReferences.IsEmpty()) { if(N.InstanceObject) ObjectChanged|=ReferenceSettings(N.InstanceObject->GetClass(),N.InstanceObject,R.InstanceReferences); else { if(!N.Instance.IsValid()) throw std::runtime_error("Node has no instance data for references"); ReferenceSettings(const_cast<UScriptStruct*>(N.Instance.GetScriptStruct()),N.Instance.GetMutableMemory(),R.InstanceReferences); } }
  if(!R.InstanceContainers.IsEmpty()) { if(N.InstanceObject) ObjectChanged|=ContainerSettings(N.InstanceObject->GetClass(),N.InstanceObject,R.InstanceContainers,N.InstanceObject); else { if(!N.Instance.IsValid()) throw std::runtime_error("Node has no instance data for containers"); ContainerSettings(const_cast<UScriptStruct*>(N.Instance.GetScriptStruct()),N.Instance.GetMutableMemory(),R.InstanceContainers,Owner); } }
  return ObjectChanged;
 }
 FInstancedPropertyBag& Bag(FModel& M,const FString& StateId)
 {
  return StateId.IsEmpty() ? const_cast<FInstancedPropertyBag&>(M.Data->GetRootParametersPropertyBag()) : State(M,StateId)->Parameters.Parameters;
 }
 FGuid BagId(FModel& M,const FString& StateId) { return StateId.IsEmpty() ? M.Data->GetRootParametersGuid() : State(M,StateId)->Parameters.ID; }
 FPropertyBindingPath BindingPath(UStateTreeEditorData* D,const FString& ID,const FString& Text,const FGuid& NewId=FGuid())
 {
  FPropertyBindingPath P(ID==TEXT("root") ? D->GetRootParametersGuid() : ID==TEXT("$new") && NewId.IsValid() ? NewId : Guid(ID));
  if(Text.Len()>256 || !P.FromString(Text) || P.NumSegments()>8) throw std::runtime_error("Binding paths require native property syntax, <=256 characters and <=8 segments");
  FPropertyBindingDataView View; TArray<FPropertyBindingPathIndirection> Steps; FString Error;
  if(!D->GetBindingDataViewByID(P.GetStructID(),View) || !P.UpdateSegmentsFromValue(View,&Error) || !P.ResolveIndirectionsWithValue(View,Steps,&Error)) throw std::runtime_error("Binding path does not resolve against an owned native bindable value");
  return P;
 }
 void RemoveBindingTree(UStateTreeEditorData* D,const FPropertyBindingPath& Target)
 {
  TSet<FGuid> Functions; const auto* Binding=D->EditorBindings.FindBinding(Target); if(!Binding) return; if(const auto* Function=Binding->GetPropertyFunctionNode().GetPtr<const FStateTreeEditorNode>()) Functions.Add(Function->ID);
  bool Added=true; while(Added) { Added=false; for(const auto& B:D->EditorBindings.GetBindings()) if(Functions.Contains(B.GetTargetPath().GetStructID())) if(const auto* F=B.GetPropertyFunctionNode().GetPtr<const FStateTreeEditorNode>()) if(!Functions.Contains(F->ID)) { Functions.Add(F->ID); Added=true; } }
  for(const auto& B:D->EditorBindings.GetBindings()) if(Functions.Contains(B.GetSourcePath().GetStructID()) && !Functions.Contains(B.GetTargetPath().GetStructID()) && !(B.GetTargetPath()==Target)) throw std::runtime_error("Other bindings use this property function; remove them first");
  D->EditorBindings.RemoveBindings([&](FPropertyBindingBinding& B) { return B.GetTargetPath()==Target || Functions.Contains(B.GetTargetPath().GetStructID()); });
 }
 // Editor node (and its outer) whose ID is a binding target struct ID.
 FStateTreeEditorNode* BindingTargetNode(UStateTreeEditorData* D,const FGuid& ID,UObject*& Outer)
 {
  auto InList=[&](TArray<FStateTreeEditorNode>& Nodes,UObject* Owner) -> FStateTreeEditorNode* { for(auto& N:Nodes) if(N.ID==ID) { Outer=Owner; return &N; } return nullptr; };
  if(auto* N=InList(D->Evaluators,D)) return N; if(auto* N=InList(D->GlobalTasks,D)) return N;
  TFunction<FStateTreeEditorNode*(UStateTreeState*)> Visit=[&](UStateTreeState* State) -> FStateTreeEditorNode* {
   if(!State) return nullptr; if(State->SingleTask.ID==ID) { Outer=State; return &State->SingleTask; }
   for(auto* List:{&State->Tasks,&State->EnterConditions,&State->Considerations}) if(auto* N=InList(*List,State)) return N;
   for(auto& Transition:State->Transitions) if(auto* N=InList(Transition.Conditions,State)) return N;
   for(auto& Child:State->Children) if(auto* N=Visit(Child)) return N; return nullptr; };
  for(auto& Root:D->SubTrees) if(auto* N=Visit(Root)) return N; return nullptr;
 }
 bool Bind(UStateTreeEditorData* D,const FStateTreeBindingReq& R,bool Confirm,const FGuid& NewId=FGuid())
 {
  auto Source=BindingPath(D,R.SourceId,R.SourcePath,NewId), Target=BindingPath(D,R.TargetId,R.TargetPath,NewId);
  if(R.bOutput && !Target.IsPathEmpty()) { FPropertyBindingDataView View; if(!D->GetBindingDataViewByID(Target.GetStructID(),View)) throw std::runtime_error("Output binding target is unavailable"); TArray<FPropertyBindingPathIndirection> Steps; FString Error; if(!Target.ResolveIndirectionsWithValue(View,Steps,&Error) || Steps.IsEmpty() || UE::StateTree::GetUsageFromMetaData(Steps[0].GetProperty())!=EStateTreePropertyUsage::Output) throw std::runtime_error("Output binding requires a native Output target property"); }
  if(Target.IsPathEmpty() || Source.GetStructID()==Target.GetStructID()) throw std::runtime_error("Binding requires a target property and distinct source/target structs");
  TArray<TInstancedStruct<FPropertyBindingBindableStructDescriptor>> Accessible; D->GetBindableStructs(Target.GetStructID(),Accessible);
  if(!Accessible.ContainsByPredicate([&](const auto& Desc) { return Desc.Get().ID==Source.GetStructID(); })) throw std::runtime_error("Binding source is not accessible in the target execution path");
  if(const auto* Old=D->EditorBindings.FindBinding(Target)) { if(Old->GetSourcePath()==Source && !Old->GetPropertyFunctionNode().IsValid() && static_cast<const FStateTreePropertyPathBinding*>(Old)->IsOutputBinding()==R.bOutput) return false; if(!Confirm) throw std::runtime_error("Replacing a binding requires bConfirm=true"); }
  else if(D->EditorBindings.GetNumBindings()>=1024) throw std::runtime_error("At most 1024 StateTree bindings");
  if(auto* Owner=const_cast<UStateTreeState*>(D->GetStateByStructID(Target.GetStructID()))) if((Owner->Type==EStateTreeStateType::Linked || Owner->Type==EStateTreeStateType::LinkedAsset) && Owner->Parameters.ID==Target.GetStructID()) { const auto* Field=Owner->Parameters.Parameters.FindPropertyDescByName(Target.GetSegment(0).GetName()); if(!Field) throw std::runtime_error("Linked parameter binding target is not a field"); Owner->SetParametersPropertyOverridden(Field->ID,true); }
  RemoveBindingTree(D,Target); if(R.bOutput) { if(!D->EditorBindings.AddOutputBinding(Source,Target)) throw std::runtime_error("Native output binding creation failed"); } else D->AddPropertyBinding(Source,Target); D->OnPropertyBindingChanged(Source,Target);
  /* The editor's details panel, not the editor data, runs the target node's OnBindingChanged (e.g. Enum Input adopts the
     bound enum). Headless edits must call it too, or a bound enum input keeps no enum and native compile check()s. */
  UObject* Outer=nullptr; if(auto* EditorNode=BindingTargetNode(D,Target.GetStructID(),Outer)) if(auto* NodeBase=EditorNode->Node.GetMutablePtr<FStateTreeNodeBase>()) { const FStateTreeDataView Instance=EditorNode->GetInstance(); if(Instance.IsValid()) { if(Outer) Outer->Modify(); const FStateTreeBindingLookup Lookup(D); NodeBase->OnBindingChanged(EditorNode->ID,Instance,Source,Target,Lookup); } }
  return true;
 }
 bool BindMany(UStateTreeEditorData* D,const FStateTreeReq& R,const FGuid& NewId)
 {
  if(R.Bindings.Num()>64) throw std::runtime_error("At most 64 atomic node bindings"); bool Changed=false;
  for(const auto& B:R.Bindings) Changed|=Bind(D,B,R.bConfirm,NewId); return Changed;
 }
 void RemoveNodeBindings(UStateTreeEditorData* D,const TSet<FGuid>& Removed)
 {
  for(const auto& B:D->EditorBindings.GetBindings()) if(Removed.Contains(B.GetSourcePath().GetStructID()) && !Removed.Contains(B.GetTargetPath().GetStructID())) throw std::runtime_error("Other nodes bind to the deleted item; remove those bindings first");
  TArray<FPropertyBindingPath> Targets; for(const auto& B:D->EditorBindings.GetBindings()) if(Removed.Contains(B.GetTargetPath().GetStructID())) Targets.Add(B.GetTargetPath()); for(const auto& Target:Targets) RemoveBindingTree(D,Target);
 }
 UClass* ReferenceClass(const FString& Path)
 {
  if(Path.Len()>1024 || Path.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(Path)) throw std::runtime_error("Reference class requires a full object path without subobjects");
  if(!Path.StartsWith(TEXT("/Script/"))) { FString BlueprintPath=Path; if(!BlueprintPath.RemoveFromEnd(TEXT("_C")) || !FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(BlueprintPath)).IsValid()) throw std::runtime_error("Generated class requires an existing Blueprint asset and its _C class path"); }
  auto* Class=LoadClass<UObject>(nullptr,*Path);
  if(!Class || Class->HasAnyClassFlags(CLASS_Deprecated|CLASS_NewerVersionExists) || (Class->HasAnyFlags(RF_Transient) && !(Class->HasAnyClassFlags(CLASS_Native) && Class->GetOutermost()->GetName().StartsWith(TEXT("/Script/")))) || Class->GetName().StartsWith(TEXT("SKEL_")) || Class->GetName().StartsWith(TEXT("REINST_"))) throw std::runtime_error("Reference class is missing, transient, deprecated or stale"); return Class;
 }
 UObject* PersistentReference(const FString& Path)
 {
  if(Path.IsEmpty() || Path.Equals(TEXT("None"),ESearchCase::IgnoreCase)) return nullptr;
  if(Path.Len()>1024 || Path.Contains(TEXT(":")) || !FPackageName::IsValidObjectPath(Path)) throw std::runtime_error("Reference value requires a persistent object path without subobjects");
  if(Path.StartsWith(TEXT("/Script/")) || Path.EndsWith(TEXT("_C"))) return ReferenceClass(Path);
  auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); if(!Registry.GetAssetByObjectPath(FSoftObjectPath(Path)).IsValid()) throw std::runtime_error("Reference value must identify an existing persistent asset");
  auto* Object=LoadObject<UObject>(nullptr,*Path); if(!IsValid(Object) || !Object->IsAsset() || Object->HasAnyFlags(RF_Transient|RF_ClassDefaultObject)) throw std::runtime_error("Reference value must be a persistent asset or supported class"); return Object;
 }
 bool ReferenceElement(FProperty* P,void* Address,const FString& Text)
 {
  auto* Hard=CastField<FObjectPropertyBase>(P); auto* Soft=CastField<FSoftObjectProperty>(P); auto* Class=CastField<FClassProperty>(P); auto* SoftClass=CastField<FSoftClassProperty>(P);
  if(!Hard && !Soft) throw std::runtime_error("Expected an object/class reference field"); UObject* Object=nullptr;
  if(!Text.IsEmpty() && !Text.Equals(TEXT("None"),ESearchCase::IgnoreCase)) Object=(Class || SoftClass) ? ReferenceClass(Text) : PersistentReference(Text);
  UClass* Constraint=Class ? Class->MetaClass.Get() : SoftClass ? SoftClass->MetaClass.Get() : nullptr;
  if(Object && (Constraint ? !CastChecked<UClass>(Object)->IsChildOf(Constraint) : !Object->IsA(Soft ? Soft->PropertyClass.Get() : Hard->PropertyClass.Get()))) throw std::runtime_error("Instance reference violates native class constraint");
  if(Soft) { const FSoftObjectPtr Value(Object ? FSoftObjectPath(Object) : FSoftObjectPath()); const bool Changed=Soft->GetPropertyValue(Address)!=Value; Soft->SetPropertyValue(Address,Value); return Changed; }
  const bool Changed=Hard->GetObjectPropertyValue(Address)!=Object; Hard->SetObjectPropertyValue(Address,Object); return Changed;
 }
 bool ReferenceSettings(UStruct* Type,void* Data,const TMap<FString,FString>& Values)
 {
  if(Values.Num()>64) throw std::runtime_error("At most 64 instance reference settings"); bool Changed=false;
  for(const auto& Pair:Values) { auto* P=FindFProperty<FProperty>(Type,*Pair.Key); if(!P || P->ArrayDim!=1 || !P->HasAnyPropertyFlags(CPF_Edit) || P->HasAnyPropertyFlags(CPF_Transient|CPF_EditConst|CPF_InstancedReference|CPF_ContainsInstancedReference)) throw std::runtime_error("InstanceReferences requires editable scalar non-instanced fields"); Changed|=ReferenceElement(P,P->ContainerPtrToValuePtr<void>(Data),Pair.Value); }
  return Changed;
 }
 bool ContainerSettings(UStruct* Type,void* Data,const TMap<FString,FString>& Values,UObject* Owner)
 {
  if(Values.Num()>64) throw std::runtime_error("At most 64 instance container settings"); bool Changed=false;
  for(const auto& Pair:Values)
  {
   auto* P=FindFProperty<FProperty>(Type,*Pair.Key); if(!P || P->ArrayDim!=1 || !P->HasAnyPropertyFlags(CPF_Edit) || P->HasAnyPropertyFlags(CPF_Transient|CPF_EditConst|CPF_InstancedReference|CPF_ContainsInstancedReference) || Pair.Value.Len()>65536) throw std::runtime_error("InstanceContainers requires editable non-instanced containers and JSON <=64KiB");
   if(auto* Map=CastField<FMapProperty>(P))
   {
    auto Supported=[](FProperty* Field) { return Field->ArrayDim==1 && (Plain(Field) || CastField<FObjectPropertyBase>(Field) || CastField<FSoftObjectProperty>(Field)); };
    if(!Supported(Map->KeyProp) || !Supported(Map->ValueProp) || !Map->KeyProp->HasAnyPropertyFlags(CPF_HasGetValueTypeHash)) throw std::runtime_error("Map requires supported scalar/plain/reference key/value fields and native key hashing");
    TArray<TSharedPtr<FJsonValue>> Entries; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Pair.Value),Entries) || Entries.Num()>256 || int64(Map->KeyProp->ElementSize+Map->ValueProp->ElementSize)*Entries.Num()>1048576) throw std::runtime_error("Map requires <=256 Key/Value rows and <=1MiB storage");
    void* Prepared=FMemory::Malloc(P->GetSize(),P->GetMinAlignment()); P->InitializeValue(Prepared);
    try { FScriptMapHelper Helper(Map,Prepared); for(const auto& Entry:Entries) { const auto Object=Entry->Type==EJson::Object ? Entry->AsObject() : TSharedPtr<FJsonObject>(); FString Key,Value; if(!Object.IsValid() || !Object->HasTypedField<EJson::String>(TEXT("Key")) || !Object->HasTypedField<EJson::String>(TEXT("Value")) || !Object->TryGetStringField(TEXT("Key"),Key) || !Object->TryGetStringField(TEXT("Value"),Value) || Key.Len()>4096 || Value.Len()>4096) throw std::runtime_error("Map rows require Key and Value typed strings <=4096 characters");
      void* KeyData=FMemory::Malloc(Map->KeyProp->GetSize(),Map->KeyProp->GetMinAlignment()); Map->KeyProp->InitializeValue(KeyData); void* ValueData=FMemory::Malloc(Map->ValueProp->GetSize(),Map->ValueProp->GetMinAlignment()); Map->ValueProp->InitializeValue(ValueData);
      try { auto Assign=[&](FProperty* Field,void* Address,const FString& Text) { if(CastField<FObjectPropertyBase>(Field) || CastField<FSoftObjectProperty>(Field)) ReferenceElement(Field,Address,Text); else { FStringOutputDevice Errors; ValidateIntegerText(Field,Text); const auto* End=Field->ImportText_Direct(*Text,Address,Owner,PPF_None,&Errors); if(!End || !Errors.IsEmpty() || !FString(End).TrimStartAndEnd().IsEmpty()) throw std::runtime_error("Map field failed native import"); Number(Field,Address); } }; Assign(Map->KeyProp,KeyData,Key); Assign(Map->ValueProp,ValueData,Value); if(Helper.FindMapIndexWithKey(KeyData)!=INDEX_NONE) throw std::runtime_error("Duplicate native map key"); Helper.AddPair(KeyData,ValueData); }
      catch(...) { Map->KeyProp->DestroyValue(KeyData); FMemory::Free(KeyData); Map->ValueProp->DestroyValue(ValueData); FMemory::Free(ValueData); throw; } Map->KeyProp->DestroyValue(KeyData); FMemory::Free(KeyData); Map->ValueProp->DestroyValue(ValueData); FMemory::Free(ValueData);
     } auto* Address=P->ContainerPtrToValuePtr<void>(Data); Changed|=!P->Identical(Address,Prepared,PPF_None); P->CopyCompleteValue(Address,Prepared);
    } catch(...) { P->DestroyValue(Prepared); FMemory::Free(Prepared); throw; } P->DestroyValue(Prepared); FMemory::Free(Prepared); continue;
   }
   auto* Array=CastField<FArrayProperty>(P); auto* Set=CastField<FSetProperty>(P); auto* Inner=Array ? Array->Inner : Set ? Set->ElementProp : nullptr;
   if(!Inner || Inner->ArrayDim!=1 || (!Plain(Inner) && !CastField<FObjectPropertyBase>(Inner) && !CastField<FSoftObjectProperty>(Inner)) || (Set && !Inner->HasAnyPropertyFlags(CPF_HasGetValueTypeHash))) throw std::runtime_error("Container requires scalar/plain-struct/reference elements and native set hashing");
   TArray<TSharedPtr<FJsonValue>> Items; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Pair.Value),Items) || Items.Num()>256 || int64(Inner->ElementSize)*Items.Num()>1048576) throw std::runtime_error("Container requires <=256 typed string elements and <=1MiB storage");
   auto* Address=P->ContainerPtrToValuePtr<void>(Data); void* Prepared=FMemory::Malloc(P->GetSize(),P->GetMinAlignment()); P->InitializeValue(Prepared);
   try
   {
    auto Assign=[&](void* Element,const TSharedPtr<FJsonValue>& Item) { FString Text; if(Item->Type!=EJson::String || !Item->TryGetString(Text) || Text.Len()>4096) throw std::runtime_error("Container elements require typed strings <=4096 characters"); if(CastField<FObjectPropertyBase>(Inner) || CastField<FSoftObjectProperty>(Inner)) ReferenceElement(Inner,Element,Text); else { FStringOutputDevice Errors; ValidateIntegerText(Inner,Text); const auto* End=Inner->ImportText_Direct(*Text,Element,Owner,PPF_None,&Errors); if(!End || !Errors.IsEmpty() || !FString(End).TrimStartAndEnd().IsEmpty()) throw std::runtime_error("Container element failed native import"); Number(Inner,Element); } };
    if(Array) { FScriptArrayHelper Helper(Array,Prepared); Helper.AddValues(Items.Num()); for(int32 Index=0;Index<Items.Num();++Index) Assign(Helper.GetRawPtr(Index),Items[Index]); }
    else { FScriptSetHelper Helper(Set,Prepared); for(const auto& Item:Items) { void* Element=FMemory::Malloc(Inner->GetSize(),Inner->GetMinAlignment()); Inner->InitializeValue(Element); try { Assign(Element,Item); Helper.AddElement(Element); } catch(...) { Inner->DestroyValue(Element); FMemory::Free(Element); throw; } Inner->DestroyValue(Element); FMemory::Free(Element); } }
    Changed|=!P->Identical(Address,Prepared,PPF_None); P->CopyCompleteValue(Address,Prepared);
   } catch(...) { P->DestroyValue(Prepared); FMemory::Free(Prepared); throw; }
   P->DestroyValue(Prepared); FMemory::Free(Prepared);
  }
  return Changed;
 }
 void ConsiderationSettings(FStateTreeEditorNode& N,const FStateTreeReq& R)
 {
  if(R.bSetResponseCurve)
  {
   auto* Consideration=N.Node.GetMutablePtr<FStateTreeFloatInputConsideration>(); if(!Consideration) throw std::runtime_error("Response curve requires native Float Input consideration");
   if(R.ResponseCurveKeys.Num()>256 || (!R.ResponseCurveAsset.IsEmpty() && !R.ResponseCurveKeys.IsEmpty())) throw std::runtime_error("Choose external curve or <=256 inline keys");
   auto& Curve=Consideration->ResponseCurve.CurveInfo; Curve.ExternalCurve=nullptr; Curve.EditorCurveData.Reset();
   if(!R.ResponseCurveAsset.IsEmpty()) { auto* Asset=Cast<UCurveFloat>(PersistentReference(R.ResponseCurveAsset)); if(!Asset) throw std::runtime_error("ResponseCurveAsset must be a persistent CurveFloat"); Curve.ExternalCurve=Asset; }
   float Previous=-MAX_flt; for(const auto& Key:R.ResponseCurveKeys) { if(!FMath::IsFinite(Key.Time) || !FMath::IsFinite(Key.Value) || !FMath::IsFinite(Key.ArriveTangent) || !FMath::IsFinite(Key.LeaveTangent) || Key.Time<0 || Key.Time>1 || Key.Value<0 || Key.Value>1 || Key.Time<=Previous || FMath::Abs(Key.ArriveTangent)>1.e6 || FMath::Abs(Key.LeaveTangent)>1.e6) throw std::runtime_error("Curve keys require strictly increasing normalized time/value and finite bounded tangents"); Previous=Key.Time; const auto Handle=Curve.EditorCurveData.AddKey(Key.Time,Key.Value); auto& Native=Curve.EditorCurveData.GetKey(Handle); Native.InterpMode=Key.Interpolation==TEXT("Linear") ? RCIM_Linear : Key.Interpolation==TEXT("Constant") ? RCIM_Constant : Key.Interpolation==TEXT("Cubic") ? RCIM_Cubic : RCIM_None; if(Native.InterpMode!=RCIM_Linear && Native.InterpMode!=RCIM_Constant && Native.InterpMode!=RCIM_Cubic) throw std::runtime_error("Curve interpolation requires Linear, Constant or Cubic"); Native.TangentMode=RCTM_User; Native.ArriveTangent=Key.ArriveTangent; Native.LeaveTangent=Key.LeaveTangent; }
  }
  if(R.bSetEnumScores)
  {
   if(!N.Node.GetScriptStruct()->IsChildOf(FStateTreeEnumInputConsideration::StaticStruct())) throw std::runtime_error("Enum scores require native Enum Input consideration");
   if(R.EnumScores.Num()>256 || R.ScoreEnumPath.Len()>1024 || !FPackageName::IsValidObjectPath(R.ScoreEnumPath)) throw std::runtime_error("Enum scores require an enum object path and <=256 entries");
   auto* Type=LoadObject<UEnum>(nullptr,*R.ScoreEnumPath); /* native script enums carry RF_Transient but live in compiled-in packages */ if(!Type || (Type->HasAnyFlags(RF_Transient) && !Type->GetPackage()->HasAnyPackageFlags(PKG_CompiledIn))) throw std::runtime_error("Score enum must be persistent"); { /* Native compile check()s InstanceData.Input.Enum == EnumValueScorePairs.Enum (it crashed the editor on a mismatch); the
    native binding callback keeps them in sync, so follow it: refuse a different enum, adopt the score enum when Input has none. */
    auto* InputField=N.Instance.IsValid() ? FindFProperty<FStructProperty>(N.Instance.GetScriptStruct(),TEXT("Input")) : nullptr; if(!InputField || InputField->Struct!=FStateTreeAnyEnum::StaticStruct()) throw std::runtime_error("Native Enum Input instance layout mismatch");
    auto* Input=InputField->ContainerPtrToValuePtr<FStateTreeAnyEnum>(N.Instance.GetMutableMemory()); if(Input->Enum && Input->Enum!=Type) throw std::runtime_error("Score enum must match the enum of the bound Input"); if(!Input->Enum) Input->Initialize(Type); }
   auto* Field=FindFProperty<FStructProperty>(N.Node.GetScriptStruct(),TEXT("EnumValueScorePairs")); if(!Field || Field->Struct!=FStateTreeEnumValueScorePairs::StaticStruct()) throw std::runtime_error("Native enum score layout mismatch"); auto* Pairs=Field->ContainerPtrToValuePtr<FStateTreeEnumValueScorePairs>(N.Node.GetMutableMemory()); Pairs->Initialize(Type); Pairs->Data.Reset(); TSet<int64> Used;
   for(const auto& Pair:R.EnumScores) { const int64 Value=Type->GetValueByNameString(Pair.Key); const int32 Index=Type->GetIndexByValue(Value); if(Index==INDEX_NONE || Type->HasMetaData(TEXT("Hidden"),Index) || (Type->ContainsExistingMax() && Index==Type->NumEnums()-1) || Used.Contains(Value) || !FMath::IsFinite(Pair.Value) || Pair.Value<0 || Pair.Value>1) throw std::runtime_error("Enum scores require unique visible native members and scores in [0,1]"); Used.Add(Value); auto& Entry=Pairs->Data.AddDefaulted_GetRef(); Entry.EnumValue=Value; Entry.EnumName=Type->GetNameByValue(Value); Entry.Score=Pair.Value; }
   Pairs->Data.Sort([](const auto& A,const auto& B) { return A.EnumValue<B.EnumValue; });
  }
 }
 bool ReferenceType(EPropertyBagPropertyType Type) { return Type==EPropertyBagPropertyType::Object || Type==EPropertyBagPropertyType::SoftObject || Type==EPropertyBagPropertyType::Class || Type==EPropertyBagPropertyType::SoftClass; }
 void ParameterValue(FInstancedPropertyBag& B,FName Name,const FString& Value,UObject* Owner)
 {
  const auto* Desc=B.FindPropertyDescByName(Name); if(!Desc || !Desc->CachedProperty) throw std::runtime_error("Parameter field is missing");
  if(!Desc->ContainerTypes.IsEmpty())
  {
   if(Desc->ContainerTypes.Num()!=1 || Value.Len()>65536) throw std::runtime_error("Container values require one native container level and JSON text <=64KiB"); TArray<TSharedPtr<FJsonValue>> Items; if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Value),Items) || Items.Num()>256) throw std::runtime_error("Container value requires a JSON array of at most 256 element strings");
   auto* Array=CastField<FArrayProperty>(Desc->CachedProperty); auto* Set=CastField<FSetProperty>(Desc->CachedProperty); auto* Inner=Array ? Array->Inner : Set ? Set->ElementProp : nullptr; if(!Inner || int64(Inner->ElementSize)*Items.Num()>1048576) throw std::runtime_error("Unsupported container layout or element storage exceeds 1MiB"); if(Set && !Inner->HasAnyPropertyFlags(CPF_HasGetValueTypeHash)) throw std::runtime_error("Set elements require native hashing");
   FPropertyBagPropertyDesc ElementDesc=*Desc; ElementDesc.Name=TEXT("Value"); ElementDesc.ContainerTypes.Reset(); ElementDesc.CachedProperty=nullptr; FInstancedPropertyBag ElementTemplate; ElementTemplate.AddProperties(MakeArrayView(&ElementDesc,1),false); const auto* ElementProperty=ElementTemplate.FindPropertyDescByName(TEXT("Value"))->CachedProperty;
   auto* Address=Desc->CachedProperty->ContainerPtrToValuePtr<void>(B.GetMutableValue().GetMemory());
   if(Array) { FScriptArrayHelper Values(Array,Address); Values.EmptyValues(); Values.AddValues(Items.Num()); for(int32 Index=0;Index<Items.Num();++Index) { FString Text; if(Items[Index]->Type!=EJson::String || !Items[Index]->TryGetString(Text)) throw std::runtime_error("Every container element must be a string containing typed UE text or a persistent reference path"); FInstancedPropertyBag Element=ElementTemplate; ParameterValue(Element,TEXT("Value"),Text,Owner); Inner->CopyCompleteValue(Values.GetRawPtr(Index),ElementProperty->ContainerPtrToValuePtr<void>(Element.GetMutableValue().GetMemory())); } }
   else { FScriptSetHelper Values(Set,Address); Values.EmptyElements(); for(const auto& Item:Items) { FString Text; if(Item->Type!=EJson::String || !Item->TryGetString(Text)) throw std::runtime_error("Every set element must be a typed string"); FInstancedPropertyBag Element=ElementTemplate; ParameterValue(Element,TEXT("Value"),Text,Owner); Values.AddElement(ElementProperty->ContainerPtrToValuePtr<void>(Element.GetMutableValue().GetMemory())); } }
   return;
  }
  if(!ReferenceType(Desc->ValueType)) { Settings(const_cast<UPropertyBag*>(B.GetPropertyBagStruct()),B.GetMutableValue().GetMemory(),{{Name.ToString(),Value}},Owner); return; }
  if(!Desc->ContainerTypes.IsEmpty()) throw std::runtime_error("Reference containers require a dedicated container adapter");
  auto* Base=Cast<UClass>(const_cast<UObject*>(Desc->ValueTypeObject.Get())); if(!Base) throw std::runtime_error("Reference parameter requires a class constraint"); UObject* Object=nullptr; const bool IsClass=Desc->ValueType==EPropertyBagPropertyType::Class || Desc->ValueType==EPropertyBagPropertyType::SoftClass;
  if(!Value.IsEmpty() && !Value.Equals(TEXT("None"),ESearchCase::IgnoreCase)) Object=IsClass ? ReferenceClass(Value) : PersistentReference(Value);
  if(Object && (IsClass ? !CastChecked<UClass>(Object)->IsChildOf(Base) : !Object->IsA(Base))) throw std::runtime_error("Reference value is incompatible with the parameter class constraint");
  EPropertyBagResult Result;
  if(Desc->ValueType==EPropertyBagPropertyType::SoftObject || Desc->ValueType==EPropertyBagPropertyType::SoftClass) Result=B.SetValueSoftPath(*Desc,Object ? FSoftObjectPath(Object) : FSoftObjectPath());
  else if(IsClass) Result=B.SetValueClass(*Desc,Cast<UClass>(Object)); else Result=B.SetValueObject(*Desc,Object);
  if(Result!=EPropertyBagResult::Success) throw std::runtime_error("Native property bag rejected the reference value");
 }
 FPropertyBagPropertyDesc ParameterType(const FStateTreeReq& R,FName Name,const FGuid& ID)
 {
   const int64 V=StaticEnum<EPropertyBagPropertyType>()->GetValueByNameString(R.ParameterType); if(V<=0 || V>=int64(EPropertyBagPropertyType::Count)) throw std::runtime_error("A native property bag type is required"); const auto Type=EPropertyBagPropertyType(V); UObject* TypeObject=nullptr;
   if(Type==EPropertyBagPropertyType::Struct) { auto* S=LoadObject<UScriptStruct>(nullptr,*R.TypePath); if(!S || !S->GetOutermost()->GetName().StartsWith(TEXT("/Script/"))) throw std::runtime_error("Struct parameters require a native script struct"); for(TFieldIterator<FProperty> It(S);It;++It) if(!Plain(*It)) throw std::runtime_error("Struct parameters require plain fields"); TypeObject=S; }
   else if(Type==EPropertyBagPropertyType::Enum) { TypeObject=LoadObject<UEnum>(nullptr,*R.TypePath); if(!TypeObject) throw std::runtime_error("Enum parameter requires an enum type path"); }
   else if(ReferenceType(Type)) TypeObject=ReferenceClass(R.TypePath);
   else if(!R.TypePath.IsEmpty()) throw std::runtime_error("TypePath applies only to enum, struct or reference parameters");
  FPropertyBagPropertyDesc Desc(Name,Type,TypeObject); Desc.ID=ID;
  if(!R.ContainerType.IsEmpty() && R.ContainerType!=TEXT("None")) { if(R.ContainerType!=TEXT("Array") && R.ContainerType!=TEXT("Set")) throw std::runtime_error("ContainerType requires Array, Set or None"); if(R.ContainerType==TEXT("Set")) { if(Type==EPropertyBagPropertyType::Text) throw std::runtime_error("Localized text does not support set hashing"); if(auto* Struct=Cast<UScriptStruct>(TypeObject)) if(!Struct->GetCppStructOps() || !Struct->GetCppStructOps()->HasGetTypeHash()) throw std::runtime_error("Set structs need native GetTypeHash support"); } Desc.ContainerTypes.Add(R.ContainerType==TEXT("Array") ? EPropertyBagContainerType::Array : EPropertyBagContainerType::Set); }
  return Desc;
 }
 bool Parameter(UStateTree* T,FModel& M,const FStateTreeReq& R,const FString& Op,const FGuid& NewId)
 {
  if(R.StateId.IsEmpty() && !M.Data->Schema->AllowGlobalParameters()) throw std::runtime_error("Schema does not allow global parameters"); auto& B=Bag(M,R.StateId); const FGuid Scope=BagId(M,R.StateId); auto* OwnerState=R.StateId.IsEmpty() ? nullptr : State(M,R.StateId); const bool Fixed=OwnerState && (OwnerState->Type==EStateTreeStateType::Linked || OwnerState->Type==EStateTreeStateType::LinkedAsset);
  if(Fixed && (Op==TEXT("create_parameter") || Op==TEXT("delete_parameter") || Op==TEXT("replace_parameter") || Op==TEXT("move_parameter") || R.bSetName)) throw std::runtime_error("Linked parameters inherit their layout; edit the target subtree instead");
  auto Notify=[&]() { if(R.StateId.IsEmpty()) M.Data->OnParametersChanged(*T); else M.Data->OnStateParametersChanged(*T,State(M,R.StateId)->ID); };
  if(Op==TEXT("create_parameter"))
  {
   if(R.Name.IsEmpty() || R.Name.Len()>128 || FName(*R.Name).IsNone() || R.Name.TrimStartAndEnd()!=R.Name) throw std::runtime_error("Parameter name requires 1-128 characters without outer whitespace or None");
   for(TCHAR C:R.Name) if(!FChar::IsAlnum(C) && C!=TEXT('_')) throw std::runtime_error("Parameter names require letters, numbers or underscore");
   if(B.FindPropertyDescByName(FName(*R.Name)) || (B.GetPropertyBagStruct() && B.GetPropertyBagStruct()->GetPropertyDescs().Num()>=64)) throw std::runtime_error("Duplicate parameter name or more than 64 parameters per bag");
   auto Desc=ParameterType(R,FName(*R.Name),NewId); B.AddProperties(MakeArrayView(&Desc,1),false);
   if(R.bSetValue) ParameterValue(B,FName(*R.Name),R.Value,T);
   Notify(); return true;
  }
  const auto* Found=B.FindPropertyDescByID(Guid(R.ItemId)); if(!Found) throw std::runtime_error("Parameter ID does not belong to the selected bag"); const FName OldName=Found->Name;
  if(Op==TEXT("move_parameter"))
  {
   const auto Fields=B.GetPropertyBagStruct()->GetPropertyDescs(); const int32 From=Fields.IndexOfByPredicate([&](const FPropertyBagPropertyDesc& Field) { return Field.ID==Found->ID; }); const int32 To=R.Index==-1 ? Fields.Num()-1 : R.Index; if(R.Index < -1 || To<0 || To>=Fields.Num()) throw std::runtime_error("Parameter move index outside the selected bag"); if(From==To) return false; B.ReorderProperty(From,To,From>To); Notify(); return true;
  }
  if(Op==TEXT("replace_parameter"))
  {
   if(!R.bConfirm || R.bSetName) throw std::runtime_error("Type replacement requires bConfirm=true; rename separately"); const auto Type=ParameterType(R,OldName,Found->ID); const bool TypeChanged=Found->ValueType!=Type.ValueType || Found->ValueTypeObject!=Type.ValueTypeObject || Found->ContainerTypes!=Type.ContainerTypes;
   FString Before,After; Found->CachedProperty->ExportTextItem_Direct(Before,Found->CachedProperty->ContainerPtrToValuePtr<void>(B.GetMutableValue().GetMemory()),nullptr,T,PPF_None);
   if(TypeChanged) { auto Replacement=*Found; Replacement.ValueType=Type.ValueType; Replacement.ValueTypeObject=Type.ValueTypeObject; Replacement.ContainerTypes=Type.ContainerTypes; Replacement.CachedProperty=nullptr; B.AddProperties(MakeArrayView(&Replacement,1),true); }
   if(R.bSetValue) ParameterValue(B,OldName,R.Value,T); auto* Property=B.FindPropertyDescByName(OldName)->CachedProperty; Property->ExportTextItem_Direct(After,Property->ContainerPtrToValuePtr<void>(B.GetMutableValue().GetMemory()),nullptr,T,PPF_None); Notify(); return TypeChanged || Before!=After;
  }
  if(Op==TEXT("reset_parameter")) { if(!Fixed || !R.bConfirm) throw std::runtime_error("Reset requires a linked parameter and bConfirm=true"); if(!OwnerState->IsParametersPropertyOverridden(Found->ID)) return false; OwnerState->SetParametersPropertyOverridden(Found->ID,false); Notify(); return true; }
  if(Op==TEXT("delete_parameter"))
  {
   if(!R.bConfirm) throw std::runtime_error("Parameter deletion requires bConfirm=true");
   for(const auto& Binding:M.Data->EditorBindings.GetBindings()) for(const auto* P:{&Binding.GetSourcePath(),&Binding.GetTargetPath()}) if(P->GetStructID()==Scope && (P->IsPathEmpty() || P->GetSegment(0).GetName()==OldName)) throw std::runtime_error("Parameter is used by a binding; remove or replace the binding first");
   B.RemovePropertyByName(OldName); Notify(); return true;
  }
  if(Op!=TEXT("update_parameter")) throw std::runtime_error("Unknown parameter operation");
  bool Changed=false; FName Name=OldName;
  if(R.bSetName && Name!=FName(*R.Name))
  {
   if(R.Name.IsEmpty() || R.Name.Len()>128 || FName(*R.Name).IsNone() || B.FindPropertyDescByName(FName(*R.Name))) throw std::runtime_error("Invalid or duplicate parameter name");
   for(TCHAR C:R.Name) if(!FChar::IsAlnum(C) && C!=TEXT('_')) throw std::runtime_error("Parameter names require letters, numbers or underscore");
   B.RenameProperty(OldName,FName(*R.Name)); Name=FName(*R.Name); Changed=true;
  }
  if(R.bSetValue) { if(Fixed && !OwnerState->IsParametersPropertyOverridden(Found->ID)) { OwnerState->SetParametersPropertyOverridden(Found->ID,true); Changed=true; } auto* P=B.FindPropertyDescByName(Name)->CachedProperty; FInstancedPropertyBag Before=B; ParameterValue(B,Name,R.Value,T); Changed|=!P->Identical(P->ContainerPtrToValuePtr<void>(Before.GetValue().GetMemory()),P->ContainerPtrToValuePtr<void>(B.GetValue().GetMemory()),PPF_None); }
  Notify(); return Changed;
 }
 FStateTreeEventDesc EventDescription(const FStateTreeReq& R)
 {
  FStateTreeEventDesc Desc; if(R.EventTag.Len()>256 || R.PayloadStructPath.Len()>1024) throw std::runtime_error("Event descriptor tag/path exceeds bounds"); if(!R.EventTag.IsEmpty()) { Desc.Tag=UGameplayTagsManager::Get().RequestGameplayTag(FName(*R.EventTag),false); if(!Desc.Tag.IsValid()) throw std::runtime_error("Event requires a registered Gameplay Tag"); }
  if(!R.PayloadStructPath.IsEmpty()) { auto* Type=LoadObject<UScriptStruct>(nullptr,*R.PayloadStructPath); if(!Type || !Type->GetOutermost()->GetName().StartsWith(TEXT("/Script/")) || Type->GetStructureSize()>65536) throw std::runtime_error("Required event payload must be a native struct <=64KiB"); Desc.PayloadStruct=Type; }
  if(!Desc.IsValid()) throw std::runtime_error("Required event needs a registered tag or native payload type"); Desc.bConsumeEventOnSelect=R.bConsumeEvent; return Desc;
 }
 bool RequiredEvent(UStateTreeState* S,const FStateTreeReq& R)
 {
  FStateTreeEventDesc Desc; if(R.bEnabled) Desc=EventDescription(R); const bool Changed=S->bHasRequiredEventToEnter!=R.bEnabled || S->RequiredEventToEnter.Tag!=Desc.Tag || S->RequiredEventToEnter.PayloadStruct!=Desc.PayloadStruct || S->RequiredEventToEnter.bConsumeEventOnSelect!=Desc.bConsumeEventOnSelect; S->bHasRequiredEventToEnter=R.bEnabled; S->RequiredEventToEnter=MoveTemp(Desc); return Changed;
 }
 FStateTreeEditorNode MakeNativeNode(UStateTree* T,FModel& M,const FStateTreeReq& R,const FGuid& NewId)
 {
  if(!R.NodeClassPath.IsEmpty())
  {
   if(!R.StructPath.IsEmpty()) throw std::runtime_error("Choose StructPath or NodeClassPath, not both"); auto* Class=ReferenceClass(R.NodeClassPath); if(Class->HasAnyClassFlags(CLASS_Abstract) || !M.Data->Schema->IsClassAllowed(Class)) throw std::runtime_error("Node class must be concrete and allowed by the schema"); if(auto* Blueprint=Cast<UBlueprint>(Class->ClassGeneratedBy)) if(Blueprint->GeneratedClass!=Class || (Blueprint->Status!=BS_UpToDate && Blueprint->Status!=BS_UpToDateWithWarnings)) throw std::runtime_error("Blueprint node class must be current and compiled");
   FStateTreeEditorNode N; N.ID=NewId;
   if(R.Kind==TEXT("task") || R.Kind==TEXT("single_task") || R.Kind==TEXT("global_task")) { if(!Class->IsChildOf(UStateTreeTaskBlueprintBase::StaticClass())) throw std::runtime_error("Task requires a StateTree task Blueprint class"); N.Node.InitializeAs(FStateTreeBlueprintTaskWrapper::StaticStruct()); N.Node.GetMutable<FStateTreeBlueprintTaskWrapper>().TaskClass=Class; }
   else if(R.Kind==TEXT("evaluator")) { if(!Class->IsChildOf(UStateTreeEvaluatorBlueprintBase::StaticClass())) throw std::runtime_error("Evaluator requires its StateTree Blueprint base"); N.Node.InitializeAs(FStateTreeBlueprintEvaluatorWrapper::StaticStruct()); N.Node.GetMutable<FStateTreeBlueprintEvaluatorWrapper>().EvaluatorClass=Class; }
   else if(R.Kind==TEXT("consideration")) { if(!Class->IsChildOf(UStateTreeConsiderationBlueprintBase::StaticClass())) throw std::runtime_error("Consideration requires its StateTree Blueprint base"); N.Node.InitializeAs(FStateTreeBlueprintConsiderationWrapper::StaticStruct()); N.Node.GetMutable<FStateTreeBlueprintConsiderationWrapper>().ConsiderationClass=Class; }
   else { if(!Class->IsChildOf(UStateTreeConditionBlueprintBase::StaticClass())) throw std::runtime_error("Condition requires its StateTree Blueprint base"); N.Node.InitializeAs(FStateTreeBlueprintConditionWrapper::StaticStruct()); N.Node.GetMutable<FStateTreeBlueprintConditionWrapper>().ConditionClass=Class; }
   N.InstanceObject=NewObject<UObject>(M.Data,Class,NAME_None,RF_Transactional); const auto* Runtime=N.Node.Get<FStateTreeNodeBase>().GetExecutionRuntimeDataType(); if(const auto* Struct=Cast<UScriptStruct>(Runtime)) N.ExecutionRuntimeData.InitializeAs(Struct); else if(auto* RuntimeClass=Cast<UClass>(const_cast<UStruct*>(Runtime))) N.ExecutionRuntimeDataObject=NewObject<UObject>(M.Data,RuntimeClass,NAME_None,RF_Transactional); NodeSettings(N,R,T);
   if(R.ExpressionIndent<0 || R.ExpressionIndent>UE::StateTree::MaxExpressionIndent) throw std::runtime_error("Expression indent requires 0-4"); N.ExpressionIndent=uint8(R.ExpressionIndent); N.ExpressionOperand=ExpressionOperand(R); return N;
  }
  auto* Type=LoadObject<UScriptStruct>(nullptr,*R.StructPath); UScriptStruct* Base=R.Kind==TEXT("task") || R.Kind==TEXT("single_task") || R.Kind==TEXT("global_task") ? FStateTreeTaskBase::StaticStruct() : R.Kind==TEXT("evaluator") ? FStateTreeEvaluatorBase::StaticStruct() : R.Kind==TEXT("consideration") ? FStateTreeConsiderationBase::StaticStruct() : R.Kind==TEXT("property_function") ? FStateTreePropertyFunctionBase::StaticStruct() : FStateTreeConditionBase::StaticStruct();
   if(!Type || !Type->GetOutermost()->GetName().StartsWith(TEXT("/Script/")) || !Type->IsChildOf(Base) || Type->HasMetaData(TEXT("Hidden")) || !M.Data->Schema->IsStructAllowed(Type)) throw std::runtime_error("A visible schema-approved native task/condition/evaluator struct is required");
   FStateTreeEditorNode N; N.ID=NewId; N.Node.InitializeAs(Type); const auto& Definition=N.Node.Get<FStateTreeNodeBase>(); auto* Instance=Definition.GetInstanceDataType(); if(auto* S=Cast<UScriptStruct>(Instance)) N.Instance.InitializeAs(S); else if(Instance) throw std::runtime_error("UObject node instances require a dedicated adapter"); auto* Runtime=Definition.GetExecutionRuntimeDataType(); if(auto* S=Cast<UScriptStruct>(Runtime)) N.ExecutionRuntimeData.InitializeAs(S); else if(Runtime) throw std::runtime_error("UObject execution data requires a dedicated adapter"); NodeSettings(N,R,T);
   if(R.ExpressionIndent<0 || R.ExpressionIndent>UE::StateTree::MaxExpressionIndent) throw std::runtime_error("Condition expression indent requires 0-4"); N.ExpressionIndent=uint8(R.ExpressionIndent); N.ExpressionOperand=ExpressionOperand(R); return N;
 }
 FStateTreeEditorNode* FunctionNode(UStateTreeEditorData* D,const FGuid& ID)
 {
  for(auto& Binding:D->EditorBindings.GetMutableBindings()) if(auto* Function=Binding.GetMutablePropertyFunctionNode().GetPtr<FStateTreeEditorNode>()) if(Function->ID==ID) return Function; return nullptr;
 }
 bool CreateFunction(UStateTree* T,FModel& M,const FStateTreeReq& R,const FGuid& ID,const FGuid& OwnerID=FGuid())
 {
  if(!R.NodeClassPath.IsEmpty()) throw std::runtime_error("Property functions require native struct types"); auto Target=BindingPath(M.Data,R.Binding.TargetId,R.Binding.TargetPath,OwnerID); if(Target.IsPathEmpty()) throw std::runtime_error("Property function requires a target property");
  if(M.Data->EditorBindings.HasBinding(Target) && !R.bConfirm) throw std::runtime_error("Replacing a binding with a function requires bConfirm=true"); if(!M.Data->EditorBindings.HasBinding(Target) && M.Data->EditorBindings.GetNumBindings()>=1024) throw std::runtime_error("At most 1024 bindings"); auto Request=R; Request.Kind=TEXT("property_function"); auto Prepared=MakeNativeNode(T,M,Request,ID); if(!Prepared.Node.GetScriptStruct()->IsChildOf(FStateTreePropertyFunctionBase::StaticStruct()) || !Prepared.Instance.IsValid() || Prepared.InstanceObject) throw std::runtime_error("Function requires native struct instance data");
  FPropertyBindingPath Output(ID); FString OutputText=R.Binding.SourcePath; if(OutputText.IsEmpty()) { for(TFieldIterator<FProperty> It(Prepared.Instance.GetScriptStruct());It;++It) if(It->GetMetaData(TEXT("Category")).Equals(TEXT("Output"),ESearchCase::IgnoreCase)) { if(!OutputText.IsEmpty()) throw std::runtime_error("Function has multiple outputs; select OutputPath"); OutputText=It->GetName(); } }
  if(OutputText.Len()>256 || !Output.FromString(OutputText) || Output.IsPathEmpty() || Output.NumSegments()>8) throw std::runtime_error("Function requires a valid output path"); auto* OutputProperty=FindFProperty<FProperty>(Prepared.Instance.GetScriptStruct(),Output.GetSegment(0).GetName()); if(!OutputProperty || !OutputProperty->GetMetaData(TEXT("Category")).Equals(TEXT("Output"),ESearchCase::IgnoreCase)) throw std::runtime_error("Selected function field is not a native Output property");
  RemoveBindingTree(M.Data,Target); M.Data->EditorBindings.AddFunctionBinding(Prepared.Node.GetScriptStruct(),Output.GetSegments(),Target); bool Found=false;
  for(auto& Binding:M.Data->EditorBindings.GetMutableBindings()) if(Binding.GetTargetPath()==Target) if(auto* Function=Binding.GetMutablePropertyFunctionNode().GetPtr<FStateTreeEditorNode>()) { *Function=MoveTemp(Prepared); Binding.GetMutableSourcePath().SetStructID(ID); Found=true; break; }
  if(!Found) throw std::runtime_error("Native property function binding was not created"); BindingPath(M.Data,Id(ID),OutputText); auto Inputs=R; for(auto& Input:Inputs.Bindings) if(Input.TargetId.IsEmpty() || Input.TargetId==TEXT("$function")) Input.TargetId=Id(ID); BindMany(M.Data,Inputs,ID); M.Data->OnPropertyBindingChanged(FPropertyBindingPath(ID,Output.GetSegments()),Target); return true;
 }
 bool AtomicBindings(UStateTree* T,FModel& M,const FStateTreeReq& R,const FGuid& OwnerID)
 {
  bool Changed=BindMany(M.Data,R,OwnerID); if(R.Functions.Num()>32) throw std::runtime_error("At most 32 atomic property functions"); for(int32 Index=0;Index<R.Functions.Num();++Index) { const auto& F=R.Functions[Index]; FStateTreeReq Request; Request.StructPath=F.StructPath; Request.Binding.TargetId=F.TargetId; Request.Binding.TargetPath=F.TargetPath; Request.Binding.SourcePath=F.OutputPath; Request.Properties=F.Properties; Request.InstanceProperties=F.InstanceProperties; Request.InstanceReferences=F.InstanceReferences; Request.InstanceContainers=F.InstanceContainers; Request.bSetResponseCurve=F.bSetResponseCurve; Request.ResponseCurveAsset=F.ResponseCurveAsset; Request.ResponseCurveKeys=F.ResponseCurveKeys; Request.bSetEnumScores=F.bSetEnumScores; Request.ScoreEnumPath=F.ScoreEnumPath; Request.EnumScores=F.EnumScores; Request.Bindings=F.Inputs; Request.bConfirm=R.bConfirm; const auto ID=FGuid::Combine(OwnerID,FGuid::NewDeterministicGuid(TEXT("MCP Function ")+FString::FromInt(Index))); Changed|=CreateFunction(T,M,Request,ID,OwnerID); } return Changed;
 }
 bool Edit(UStateTree* T,const FStateTreeReq& R,const FString& Op,const FGuid& NewId)
 {
  auto M=Model(T);
  if(Op==TEXT("create_function")) return CreateFunction(T,M,R,NewId);
  if(Op==TEXT("update_function")) { auto* Function=FunctionNode(M.Data,Guid(R.ItemId)); if(!Function) throw std::runtime_error("Function ID does not belong to this asset"); auto Before=*Function; const bool InstanceChanged=NodeSettings(*Function,R,T); const auto FunctionID=Function->ID; const bool SettingsChanged=InstanceChanged || !FStateTreeEditorNode::StaticStruct()->CompareScriptStruct(&Before,Function,0); auto Request=R; for(auto& Input:Request.Bindings) if(Input.TargetId.IsEmpty() || Input.TargetId==TEXT("$function")) Input.TargetId=Id(FunctionID); const bool BindingsChanged=AtomicBindings(T,M,Request,FunctionID); return SettingsChanged || BindingsChanged; }
  if(Op==TEXT("delete_function")) { if(!R.bConfirm) throw std::runtime_error("Function deletion requires bConfirm=true"); FPropertyBindingPath Target; bool Found=false; for(const auto& B:M.Data->EditorBindings.GetBindings()) if(const auto* F=B.GetPropertyFunctionNode().GetPtr<const FStateTreeEditorNode>()) if(F->ID==Guid(R.ItemId)) { Target=B.GetTargetPath(); Found=true; break; } if(!Found) throw std::runtime_error("Function ID does not belong to this asset"); RemoveBindingTree(M.Data,Target); return true; }
  if(Op==TEXT("schema_settings"))
  {
   if(R.Properties.Num()>64 || R.ContextClasses.Num()>64 || R.SchemaReferences.Num()>64 || R.SchemaContainers.Num()>64) throw std::runtime_error("At most 64 schema settings per map"); bool Changed=false;
   auto Notify=[&](FProperty* P) { FEditPropertyChain Chain; Chain.AddHead(P); FPropertyChangedEvent Event(P,EPropertyChangeType::ValueSet); FPropertyChangedChainEvent ChainEvent(Chain,Event); M.Data->Schema->PostEditChangeChainProperty(ChainEvent); };
   for(const auto& Pair:R.Properties) { auto* P=FindFProperty<FProperty>(M.Data->Schema->GetClass(),*Pair.Key); if(!P || P->HasAnyPropertyFlags(CPF_EditConst)) throw std::runtime_error("Unknown/read-only schema setting"); FString Before,After; P->ExportText_InContainer(0,Before,M.Data->Schema,M.Data->Schema,M.Data->Schema,PPF_None); Settings(M.Data->Schema->GetClass(),M.Data->Schema,{{Pair.Key,Pair.Value}},M.Data->Schema); P->ExportText_InContainer(0,After,M.Data->Schema,M.Data->Schema,M.Data->Schema,PPF_None); if(Before!=After) { Changed=true; Notify(P); } }
   for(const auto& Pair:R.ContextClasses) { auto* P=FindFProperty<FClassProperty>(M.Data->Schema->GetClass(),*Pair.Key); if(!P || !P->HasAnyPropertyFlags(CPF_Edit) || P->HasAnyPropertyFlags(CPF_Transient|CPF_EditConst)) throw std::runtime_error("ContextClasses requires editable class fields on this schema"); auto* Class=ReferenceClass(Pair.Value); if(!Class->IsChildOf(P->MetaClass)) throw std::runtime_error("Context class violates native field constraints"); if(P->GetObjectPropertyValue_InContainer(M.Data->Schema)!=Class) { P->SetObjectPropertyValue_InContainer(M.Data->Schema,Class); Changed=true; Notify(P); } }
   for(const auto& Pair:R.SchemaReferences) { if(R.ContextClasses.Contains(Pair.Key) || R.Properties.Contains(Pair.Key)) throw std::runtime_error("Schema field supplied in multiple setting maps"); if(ReferenceSettings(M.Data->Schema->GetClass(),M.Data->Schema,{{Pair.Key,Pair.Value}})) { Changed=true; Notify(FindFProperty<FProperty>(M.Data->Schema->GetClass(),*Pair.Key)); } }
   for(const auto& Pair:R.SchemaContainers) { if(R.ContextClasses.Contains(Pair.Key) || R.Properties.Contains(Pair.Key) || R.SchemaReferences.Contains(Pair.Key)) throw std::runtime_error("Schema field supplied in multiple setting maps"); if(ContainerSettings(M.Data->Schema->GetClass(),M.Data->Schema,{{Pair.Key,Pair.Value}},M.Data->Schema)) { Changed=true; Notify(FindFProperty<FProperty>(M.Data->Schema->GetClass(),*Pair.Key)); } }
   return Changed;
  }
  if(Op.EndsWith(TEXT("_parameter"))) return Parameter(T,M,R,Op,NewId);
  if(Op==TEXT("set_binding")) return Bind(M.Data,R.Binding,R.bConfirm);
  if(Op==TEXT("delete_binding")) { if(!R.bConfirm) throw std::runtime_error("Binding deletion requires bConfirm=true"); auto P=BindingPath(M.Data,R.Binding.TargetId,R.Binding.TargetPath); if(!M.Data->EditorBindings.HasBinding(P)) return false; RemoveBindingTree(M.Data,P); return true; }
  if(R.Index < -1) throw std::runtime_error("Index requires -1 or a nonnegative array position");
  if(Op==TEXT("create_state")) { if(R.Name.IsEmpty() || R.Name.Len()>128 || FName(*R.Name).IsNone()) throw std::runtime_error("State name requires 1-128 characters"); auto* P=R.ParentId.IsEmpty() ? nullptr : State(M,R.ParentId); auto& Array=Siblings(M,P); if(R.Index>Array.Num()) throw std::runtime_error("State insertion index out of range"); const auto Type=Enum<EStateTreeStateType>(R.StateType); if(!M.Data->Schema->IsStateTypeAllowed(Type)) throw std::runtime_error("State type is disallowed by this schema"); auto* LinkedAsset=Type==EStateTreeStateType::LinkedAsset ? Load(R.LinkedAssetPath) : nullptr; if(P && (P->Type==EStateTreeStateType::Linked || P->Type==EStateTreeStateType::LinkedAsset)) throw std::runtime_error("Linked states cannot own children"); auto* Target=Type==EStateTreeStateType::Linked ? State(M,R.TargetStateId) : nullptr; if(Target && Target->Type!=EStateTreeStateType::Subtree) throw std::runtime_error("Linked state target must be a Subtree"); auto* S=P ? &P->AddChildState(FName(*R.Name),Type) : &M.Data->AddSubTree(FName(*R.Name)); S->Type=Type; S->ID=NewId; if(Target) S->SetLinkedState(Target->GetLinkToState()); if(LinkedAsset) S->SetLinkedStateAsset(LinkedAsset); if(R.bSetRequiredEvent) RequiredEvent(S,R); if(R.Index!=-1) { Array.Remove(S); Array.Insert(S,R.Index); } return true; }
  if(Op==TEXT("set_link")) { auto* S=State(M,R.StateId); if(S->Type==EStateTreeStateType::LinkedAsset) { auto* TargetAsset=Load(R.LinkedAssetPath); if(S->LinkedAsset==TargetAsset) return false; if(!R.bConfirm) throw std::runtime_error("Retargeting a linked asset requires bConfirm=true"); S->SetLinkedStateAsset(TargetAsset); return true; } auto* Target=State(M,R.TargetStateId); if(S->Type!=EStateTreeStateType::Linked || Target->Type!=EStateTreeStateType::Subtree) throw std::runtime_error("Retarget requires a Linked state and an owned Subtree target"); if(S->LinkedSubtree.ID==Target->ID) return false; if(!R.bConfirm) throw std::runtime_error("Retargeting a linked state requires bConfirm=true"); S->SetLinkedState(Target->GetLinkToState()); return true; }
  if(Op==TEXT("update_state")) { auto* S=State(M,R.StateId); bool Changed=false; if(R.bSetRequiredEvent) Changed|=RequiredEvent(S,R); if(R.bSetName) { if(R.Name.IsEmpty() || R.Name.Len()>128 || FName(*R.Name).IsNone()) throw std::runtime_error("Invalid StateTree name"); Changed|=S->Name!=FName(*R.Name); S->Name=FName(*R.Name); for(auto* V:M.States) for(auto& Tr:V->Transitions) if(Tr.State.ID==S->ID) Tr.State.Name=S->Name; for(auto* V:M.States) if(V->LinkedSubtree.ID==S->ID) V->LinkedSubtree.Name=S->Name; }
   static const TSet<FName> Allowed={TEXT("Description"),TEXT("Weight"),TEXT("SelectionBehavior"),TEXT("TasksCompletion"),TEXT("CustomTickRate"),TEXT("bHasCustomTickRate"),TEXT("bEnabled"),TEXT("bCheckPrerequisitesWhenActivatingChildDirectly")}; for(const auto& Pair:R.Properties) { if(Pair.Key==TEXT("TasksCompletion") && !M.Data->Schema->AllowTasksCompletion()) throw std::runtime_error("Schema fixes task completion behavior"); if((Pair.Key==TEXT("CustomTickRate") || Pair.Key==TEXT("bHasCustomTickRate")) && !M.Data->Schema->IsScheduledTickAllowed()) throw std::runtime_error("Schema does not allow scheduled ticking"); if(Pair.Key==TEXT("SelectionBehavior")) { const auto Selection=Enum<EStateTreeStateSelectionBehavior>(Pair.Value); if(!M.Data->Schema->IsStateSelectionAllowed(Selection)) throw std::runtime_error("Selection behavior is disallowed by this schema"); if((S->Type==EStateTreeStateType::Linked || S->Type==EStateTreeStateType::LinkedAsset) && Selection!=EStateTreeStateSelectionBehavior::TryEnterState) throw std::runtime_error("Linked states require native TryEnterState selection"); } auto* P=FindFProperty<FProperty>(S->GetClass(),*Pair.Key); FString Before; if(P) P->ExportText_InContainer(0,Before,S,S,S,PPF_None); Settings(S->GetClass(),S,{{Pair.Key,Pair.Value}},S,&Allowed); FString After; if(P) P->ExportText_InContainer(0,After,S,S,S,PPF_None); Changed|=Before!=After; } return Changed; }
  if(Op==TEXT("move_state")) { auto* S=State(M,R.StateId); auto* P=R.ParentId.IsEmpty() ? nullptr : State(M,R.ParentId); if(P && (P->Type==EStateTreeStateType::Linked || P->Type==EStateTreeStateType::LinkedAsset)) throw std::runtime_error("Linked states cannot own children"); for(auto* A=P;A;A=A->Parent) if(A==S) throw std::runtime_error("State move would create a hierarchy cycle"); auto& Old=Siblings(M,S->Parent); auto& New=Siblings(M,P); const int32 Index=R.Index==-1 ? New.Num()-(S->Parent==P ? 1 : 0) : R.Index; if(Index<0 || Index>New.Num()-(S->Parent==P ? 1 : 0)) throw std::runtime_error("State move index out of range"); if(S->Parent==P && Old.IndexOfByKey(S)==Index) return false; Old.Remove(S); New.Insert(S,Index); S->Parent=P; return true; }
  if(Op==TEXT("delete_state")) { if(!R.bConfirm) throw std::runtime_error("State deletion requires bConfirm=true"); auto* S=State(M,R.StateId); TSet<FGuid> Removed; for(auto* V:M.States) for(auto* A=V;A;A=A->Parent) if(A==S) { Removed.Add(V->ID); break; } for(auto* V:M.States) if(!Removed.Contains(V->ID) && V->Type==EStateTreeStateType::Linked && Removed.Contains(V->LinkedSubtree.ID)) throw std::runtime_error("Surviving linked states target this subtree; retarget or remove them first"); for(auto* V:M.States) if(!Removed.Contains(V->ID)) for(const auto& Tr:V->Transitions) if(Removed.Contains(Tr.State.ID)) throw std::runtime_error("External transitions target deleted states; edit them first"); TSet<FGuid> Deleted=Removed; for(auto* V:M.States) if(Removed.Contains(V->ID)) { Deleted.Add(V->Parameters.ID); auto Add=[&](const auto& Nodes) { for(const auto& N:Nodes) Deleted.Add(N.ID); }; Add(V->Tasks); Add(V->EnterConditions); Add(V->Considerations); Deleted.Add(V->SingleTask.ID); for(const auto& Tr:V->Transitions) Add(Tr.Conditions); } RemoveNodeBindings(M.Data,Deleted); Siblings(M,S->Parent).Remove(S); return true; }
  if(Op==TEXT("create_transition") || Op==TEXT("update_transition"))
  {
   auto* S=State(M,R.StateId); const auto Trigger=Enum<EStateTreeTransitionTrigger>(R.Trigger); if(Trigger==EStateTreeTransitionTrigger::OnDelegate) throw std::runtime_error("Delegate transitions require a dedicated binding adapter"); const auto Type=Enum<EStateTreeTransitionType>(R.TargetType); auto* Target=Type==EStateTreeTransitionType::GotoState ? State(M,R.TargetStateId) : nullptr;
   FStateTreeEventDesc Required; if(Trigger==EStateTreeTransitionTrigger::OnEvent) Required=EventDescription(R); else if(!R.EventTag.IsEmpty() || !R.PayloadStructPath.IsEmpty()) throw std::runtime_error("Event descriptors apply only to OnEvent transitions");
   if(!FMath::IsFinite(R.Delay) || !FMath::IsFinite(R.RandomDelay) || R.Delay<0 || R.Delay>25 || R.RandomDelay<0 || R.RandomDelay>25) throw std::runtime_error("Transition delay/variance require 0-25 seconds");
   auto New=FStateTreeTransition(Trigger,Type,Target); New.ID=NewId; New.RequiredEvent=MoveTemp(Required); New.Priority=Enum<EStateTreeTransitionPriority>(R.Priority); New.bTransitionEnabled=R.bEnabled; New.bDelayTransition=R.bDelay; New.DelayDuration=R.Delay; New.DelayRandomVariance=R.RandomDelay;
   if(Op==TEXT("create_transition")) { if(R.Index>S->Transitions.Num()) throw std::runtime_error("Transition insertion index out of range"); S->Transitions.Insert(New,R.Index==-1 ? S->Transitions.Num() : R.Index); return true; }
   auto& Old=Transition(S,R.ItemId); New.ID=Old.ID; New.Conditions=Old.Conditions; if(FStateTreeTransition::StaticStruct()->CompareScriptStruct(&Old,&New,0)) return false; Old=MoveTemp(New); return true;
  }
  if(Op==TEXT("move_transition")) { auto* S=State(M,R.StateId); auto& Array=S->Transitions; const auto ID=Guid(R.ItemId); Transition(S,R.ItemId); const int32 From=Array.IndexOfByPredicate([&](const FStateTreeTransition& Tr) { return Tr.ID==ID; }); const int32 To=R.Index==-1 ? Array.Num()-1 : R.Index; if(To<0 || To>=Array.Num()) throw std::runtime_error("Transition move index outside the state collection"); if(From==To) return false; auto Moving=MoveTemp(Array[From]); Array.RemoveAt(From); Array.Insert(MoveTemp(Moving),To); return true; }
  if(Op==TEXT("delete_transition")) { if(!R.bConfirm) throw std::runtime_error("Transition deletion requires bConfirm=true"); auto* S=State(M,R.StateId); const auto G=Guid(R.ItemId); auto& RemovedTransition=Transition(S,R.ItemId); TSet<FGuid> Deleted; for(const auto& N:RemovedTransition.Conditions) Deleted.Add(N.ID); RemoveNodeBindings(M.Data,Deleted); S->Transitions.RemoveAll([&](const FStateTreeTransition& Tr) { return Tr.ID==G; }); return true; }
  if(R.Kind==TEXT("single_task") && (Op==TEXT("create_node") || Op==TEXT("update_node") || Op==TEXT("delete_node")))
  {
   auto* S=State(M,R.StateId); if(M.Data->Schema->AllowMultipleTasks() || S->Type==EStateTreeStateType::Group || S->Type==EStateTreeStateType::Linked || S->Type==EStateTreeStateType::LinkedAsset) throw std::runtime_error("single_task requires a single-task schema and an ordinary task-capable state"); if(R.Index!=-1 && R.Index!=0) throw std::runtime_error("Single task index requires -1 or 0"); auto& N=S->SingleTask;
   if(Op==TEXT("create_node")) { if(N.Node.IsValid()) throw std::runtime_error("Single task slot is occupied; update or delete it explicitly"); N=MakeNativeNode(T,M,R,NewId); AtomicBindings(T,M,R,NewId); return true; }
   if(!N.Node.IsValid() || N.ID!=Guid(R.ItemId)) throw std::runtime_error("Single task ID does not belong to the state");
   if(Op==TEXT("delete_node")) { if(!R.bConfirm) throw std::runtime_error("Single task deletion requires bConfirm=true"); RemoveNodeBindings(M.Data,{N.ID}); N.Reset(); return true; }
   if(R.bSetExpression) throw std::runtime_error("Single tasks do not have expressions"); auto Before=N; const bool InstanceChanged=NodeSettings(N,R,T); const bool BindingsChanged=AtomicBindings(T,M,R,N.ID); return InstanceChanged || BindingsChanged || !FStateTreeEditorNode::StaticStruct()->CompareScriptStruct(&Before,&N,0);
  }
  if(Op==TEXT("move_node"))
  {
   if(R.Kind==TEXT("single_task")) throw std::runtime_error("Single task slots cannot be reordered"); auto& Array=Nodes(M,R); Node(M,R); const auto ID=Guid(R.ItemId); const int32 From=Array.IndexOfByPredicate([&](const FStateTreeEditorNode& N) { return N.ID==ID; }); const int32 To=R.Index==-1 ? Array.Num()-1 : R.Index; if(To<0 || To>=Array.Num()) throw std::runtime_error("Node move index is outside the selected collection"); if(From==To) return false; auto Moving=MoveTemp(Array[From]); Array.RemoveAt(From); Array.Insert(MoveTemp(Moving),To); return true;
  }
  if(Op==TEXT("create_node"))
  {
   auto& Array=Nodes(M,R); if(Array.Num()>=64 || R.Index>Array.Num()) throw std::runtime_error("Node insertion index/capacity exceeded"); FStateTreeEditorNode N=MakeNativeNode(T,M,R,NewId); Array.Insert(MoveTemp(N),R.Index==-1 ? Array.Num() : R.Index); AtomicBindings(T,M,R,NewId); return true;
  }
  if(Op==TEXT("update_node")) { auto& N=Node(M,R); auto Old=N; const bool InstanceChanged=NodeSettings(N,R,T); if(R.bSetExpression) { if(R.Kind!=TEXT("enter_condition") && R.Kind!=TEXT("transition_condition") && R.Kind!=TEXT("consideration")) throw std::runtime_error("Expression updates require a condition or consideration"); if(R.ExpressionIndent<0 || R.ExpressionIndent>UE::StateTree::MaxExpressionIndent) throw std::runtime_error("Expression indent requires 0-4"); N.ExpressionIndent=uint8(R.ExpressionIndent); N.ExpressionOperand=ExpressionOperand(R); } const bool BindingsChanged=AtomicBindings(T,M,R,N.ID); return InstanceChanged || !FStateTreeEditorNode::StaticStruct()->CompareScriptStruct(&Old,&N,0) || BindingsChanged; }
  if(Op==TEXT("delete_node")) { if(!R.bConfirm) throw std::runtime_error("Node deletion requires bConfirm=true"); Node(M,R); auto G=Guid(R.ItemId); RemoveNodeBindings(M.Data,{G}); Nodes(M,R).RemoveAll([&](const FStateTreeEditorNode& N) { return N.ID==G; }); return true; }
  if(Op==TEXT("compile")) return true; throw std::runtime_error("Unknown StateTree operation");
 }
 bool Compile(UStateTree* T,FStateTreeCompilerLog& Log,bool Notify=false)
 {
  auto M=Model(T); for(auto* S:M.States) if(S->Type==EStateTreeStateType::Linked || S->Type==EStateTreeStateType::LinkedAsset) { S->UpdateParametersFromLinkedSubtree(); if(!S->Parameters.Parameters.GetPropertyBagStruct()) S->Parameters.PropertyOverrides.Reset(); } M.Data->OnParametersChanged(*T);
  const int32 Count=M.Data->EditorBindings.GetNumBindings(); UStateTreeEditingSubsystem::ValidateStateTree(T);
  FStateTreeCompiler Compiler(Log); const bool OK=Notify ? UStateTreeEditingSubsystem::CompileStateTree(T,Log) : Compiler.Compile(T); if(OK) T->LastCompiledEditorDataHash=UStateTreeEditingSubsystem::CalculateStateTreeHash(T); else { T->ResetCompiled(); T->LastCompiledEditorDataHash=0; }
  if(M.Data->EditorBindings.GetNumBindings()!=Count) throw std::runtime_error("Native validation removed invalid bindings; source edit refused"); return OK;
 }
 TArray<UStateTree*> OrderGraph(const TArray<UStateTree*>& Roots)
 {
  TArray<UStateTree*> Order; TSet<UStateTree*> Active; TMap<UStateTree*,int32> Depths; int32 States=0,Nodes=0;
  TFunction<int32(UStateTree*,int32)> Visit=[&](UStateTree* T,int32 Stack) -> int32
  {
   if(!IsValid(T) || Active.Contains(T) || Stack>16) throw std::runtime_error("Linked asset cycle or dependency depth exceeds 16");
   if(const auto* Found=Depths.Find(T)) return *Found;
   if(Depths.Num()+Active.Num()>=64) throw std::runtime_error("At most 64 StateTree assets per dependency operation");
   auto M=Model(T); States+=M.States.Num(); Nodes+=M.Nodes; if(States>4096 || Nodes>8192) throw std::runtime_error("StateTree dependency graph exceeds 4096 states or 8192 nodes"); Active.Add(T); int32 Depth=1;
   for(auto* S:M.States) if(S->Type==EStateTreeStateType::LinkedAsset) Depth=FMath::Max(Depth,1+Visit(S->LinkedAsset,Stack+1));
   if(Depth>16) throw std::runtime_error("Linked asset dependency depth exceeds 16"); Active.Remove(T); Depths.Add(T,Depth); Order.Add(T); return Depth;
  }; for(auto* T:Roots) Visit(T,1); return Order;
 }
 struct FPreviewGraph
 {
  UStateTree* Source;
  TSet<UStateTree*> Affected;
  TMap<UStateTree*,UStateTree*> CopiesBySource;
  TMap<UStateTree*,UStateTree*> SourceByCopy;
  TArray<TStrongObjectPtr<UStateTree>> Copies;
  TArray<UStateTree*> ActualOrder;
  FPreviewGraph(UStateTree* Root,UStateTree* Extra=nullptr):Source(Root)
  {
   bool Initialized=false;
   ON_SCOPE_EXIT { if(!Initialized) DiscardCopies(); };
   // Scan registered and loaded assets, including unsaved callers. Native compile
   // delegates can update any loaded linked state, so callers must be captured.
   TSet<UStateTree*> Catalog; TArray<FAssetData> Assets; auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); Registry.GetAssetsByClass(UStateTree::StaticClass()->GetClassPathName(),Assets,true);
   if(Assets.Num()>256) throw std::runtime_error("StateTree caller discovery exceeds 256 registered assets");
   for(const auto& A:Assets) if(auto* T=Cast<UStateTree>(A.GetAsset())) Catalog.Add(T);
   for(TObjectIterator<UStateTree> It;It;++It) if(IsValid(*It) && !It->HasAnyFlags(RF_ClassDefaultObject|RF_Transient) && It->GetOutermost()!=GetTransientPackage()) Catalog.Add(*It);
   Catalog.Add(Root); if(Extra) Catalog.Add(Extra); if(Catalog.Num()>256) throw std::runtime_error("StateTree caller discovery exceeds 256 assets");
   TMap<UStateTree*,TSet<UStateTree*>> Dependencies;
   for(auto* T:Catalog) if(T->EditorData) { TArray<UObject*> Objects; GetObjectsWithOuter(T->EditorData,Objects,true); if(Objects.Num()>10000) throw std::runtime_error("StateTree editor object count exceeds 10000"); for(auto* Object:Objects) if(auto* S=Cast<UStateTreeState>(Object)) if(IsValid(S->LinkedAsset)) Dependencies.FindOrAdd(T).Add(S->LinkedAsset); }
   Affected.Add(Root); bool Added=true; while(Added) { Added=false; for(const auto& Pair:Dependencies) if(!Affected.Contains(Pair.Key)) for(auto* Child:Pair.Value) if(Affected.Contains(Child)) { Affected.Add(Pair.Key); Added=true; break; } }
   for(auto* T:Affected) if(!T->GetOutermost()->GetName().StartsWith(TEXT("/Game/"))) throw std::runtime_error("Affected linked callers must be editable /Game assets");
   auto Seeds=Affected.Array(); if(Extra) Seeds.AddUnique(Extra); const auto Relevant=OrderGraph(Seeds);
   for(auto* T:Relevant) if(!Affected.Contains(T) && (!T->IsReadyToRun() || T->LastCompiledEditorDataHash!=UStateTreeEditingSubsystem::CalculateStateTreeHash(T))) throw std::runtime_error("Linked dependencies must have current compiled data; compile the dependency first");
   for(auto* T:Relevant) { auto Copy=PreviewCopy(T); CopiesBySource.Add(T,Copy.Get()); SourceByCopy.Add(Copy.Get(),T); Copies.Add(MoveTemp(Copy)); }
   Remap();
   Initialized=true;
  }
  // Rejected edits can leave deliberately invalid preview graphs. Retire them
  // immediately so editor-wide pre-PIE compilation cannot discover them.
  void DiscardCopies() { for(auto& Copy:Copies) if(Copy.Get()) DiscardPreview(Copy.Get()); }
  ~FPreviewGraph() { DiscardCopies(); }
  void Remap()
  {
   for(auto& Copy:Copies) for(auto* S:Model(Copy.Get()).States) if(S->Type==EStateTreeStateType::LinkedAsset) { if(auto* Target=CopiesBySource.Find(S->LinkedAsset)) S->LinkedAsset=*Target; else if(!SourceByCopy.Contains(S->LinkedAsset)) throw std::runtime_error("Linked preview dependency was not isolated"); }
  }
  UStateTree* RootCopy() const { return CopiesBySource.FindChecked(Source); }
  bool CompileCopies(FStateTreeCompilerLog& Log)
  {
   Remap(); TArray<UStateTree*> Roots; for(auto& Copy:Copies) Roots.Add(Copy.Get()); ActualOrder.Reset();
   for(auto* T:OrderGraph(Roots)) { if(!Compile(T,Log)) return false; auto* Original=SourceByCopy.FindChecked(T); if(Affected.Contains(Original)) ActualOrder.Add(Original); } return true;
  }
 };
 // Native runtime caches are not fully serialized by editor transactions.
 FString Signature(UStateTree* T)
 {
  auto M=Model(T); FString S=FString::FromInt(UStateTreeEditingSubsystem::CalculateStateTreeHash(T));
  auto Add=[&](const FInstancedPropertyBag& B) { if(const auto* Type=B.GetPropertyBagStruct()) for(const auto& Desc:Type->GetPropertyDescs()) { FString Value; if(Desc.CachedProperty) Desc.CachedProperty->ExportTextItem_Direct(Value,Desc.CachedProperty->ContainerPtrToValuePtr<void>(B.GetValue().GetMemory()),nullptr,nullptr,PPF_None); S+=TEXT("|")+Id(Desc.ID)+TEXT(":")+Desc.Name.ToString()+TEXT("=")+Value; } };
  Add(M.Data->GetRootParametersPropertyBag()); for(auto* State:M.States) Add(State->Parameters.Parameters); return S;
 }
 TMap<TWeakObjectPtr<UStateTree>,FString> Tracked;
 FDelegateHandle UndoHandle;
 void AfterUndo()
 {
  TGuardValue<ITransaction*> Guard(GUndo,nullptr); TArray<UStateTree*> Roots;
  for(auto It=Tracked.CreateIterator();It;++It) if(auto* T=It.Key().Get()) Roots.Add(T); else It.RemoveCurrent();
  TSet<UStateTree*> Refreshed;
  for(auto* Root:Roots) try
  {
   for(auto* T:OrderGraph({Root})) if(!Refreshed.Contains(T)) if(auto* Previous=Tracked.Find(T))
   {
    Refreshed.Add(T); const FString Current=Signature(T);
    if(Current!=*Previous) { FStateTreeCompilerLog Log; Compile(T,Log); *Previous=Signature(T); }
    else if(!const_cast<FStateTreePropertyBindings&>(T->GetPropertyBindings()).ResolvePaths()) { FStateTreeCompilerLog Log; Compile(T,Log); *Previous=Signature(T); }
   }
  } catch(const std::exception& Error) { UE_LOG(LogTemp,Warning,TEXT("StateTree undo dependency refresh skipped: %s"),UTF8_TO_TCHAR(Error.what())); }
 }
 void Track(UStateTree* T)
 {
  Tracked.Add(T,Signature(T));
  if(!UndoHandle.IsValid()) UndoHandle=FEditorDelegates::PostUndoRedo.AddStatic(&AfterUndo);
 }
 void Modify(UStateTree* T) { auto M=Model(T); T->SetFlags(RF_Transactional); T->Modify(); M.Data->SetFlags(RF_Transactional); M.Data->Modify(); TArray<UObject*> Owned; GetObjectsWithOuter(M.Data,Owned,true); for(auto* Object:Owned) if(IsValid(Object)) { Object->SetFlags(RF_Transactional); Object->Modify(); } M.Data->Schema->SetFlags(RF_Transactional); M.Data->Schema->Modify(); M.Data->EditorSchema->SetFlags(RF_Transactional); M.Data->EditorSchema->Modify(); for(auto* S:M.States) { S->SetFlags(RF_Transactional); S->Modify(); } }
 FString Messages(FStateTreeCompilerLog& Log) { FString S; for(const auto& M:Log.ToTokenizedMessages()) { if(S.Len()>8192) break; S+=M->ToText().ToString()+TEXT("\n"); } return S; }
 void Values(TSharedRef<TJsonWriter<>> J,const TCHAR* Label,const UStruct* Type,const void* Data)
 {
  J->WriteObjectStart(Label); if(Type && Data) for(TFieldIterator<FProperty> It(Type);It;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient) && Plain(*It)) { FString Text; It->ExportTextItem_Direct(Text,It->ContainerPtrToValuePtr<void>(Data),nullptr,nullptr,PPF_None); J->WriteValue(It->GetName(),Text.Left(4096)); } J->WriteObjectEnd();
 }
 void SettingMetadata(TSharedRef<TJsonWriter<>> J,FProperty* P,int32 Depth=0)
 {
  const bool Editable=P->HasAnyPropertyFlags(CPF_Edit) && !P->HasAnyPropertyFlags(CPF_Transient|CPF_EditConst); const bool NonInstanced=!P->HasAnyPropertyFlags(CPF_InstancedReference|CPF_ContainsInstancedReference); const bool Reference=CastField<FObjectPropertyBase>(P) || CastField<FSoftObjectProperty>(P);
  J->WriteValue(TEXT("editable"),Editable); J->WriteValue(TEXT("reference_setting_supported"),Editable && NonInstanced && P->ArrayDim==1 && Reference);
  auto* Array=CastField<FArrayProperty>(P); auto* Set=CastField<FSetProperty>(P); auto* Map=CastField<FMapProperty>(P); auto Supported=[](FProperty* Field) { return Field && Field->ArrayDim==1 && (Plain(Field) || CastField<FObjectPropertyBase>(Field) || CastField<FSoftObjectProperty>(Field)); }; const bool ContainerSupported=Map ? Supported(Map->KeyProp) && Supported(Map->ValueProp) && Map->KeyProp->HasAnyPropertyFlags(CPF_HasGetValueTypeHash) : Array ? Supported(Array->Inner) : Set ? Supported(Set->ElementProp) && Set->ElementProp->HasAnyPropertyFlags(CPF_HasGetValueTypeHash) : false;
  J->WriteValue(TEXT("container_setting_supported"),Editable && NonInstanced && P->ArrayDim==1 && ContainerSupported); J->WriteValue(TEXT("container_kind"),Array ? TEXT("Array") : Set ? TEXT("Set") : Map ? TEXT("Map") : TEXT("None"));
  UClass* Constraint=nullptr; if(auto* C=CastField<FClassProperty>(P)) Constraint=C->MetaClass; else if(auto* SoftClass=CastField<FSoftClassProperty>(P)) Constraint=SoftClass->MetaClass; else if(auto* O=CastField<FObjectPropertyBase>(P)) Constraint=O->PropertyClass; else if(auto* SoftObject=CastField<FSoftObjectProperty>(P)) Constraint=SoftObject->PropertyClass; if(Constraint) J->WriteValue(TEXT("reference_class"),Constraint->GetPathName());
  UEnum* Type=nullptr; if(auto* E=CastField<FEnumProperty>(P)) Type=E->GetEnum(); else if(auto* Byte=CastField<FByteProperty>(P)) Type=Byte->Enum; if(Type) { J->WriteValue(TEXT("enum_path"),Type->GetPathName()); J->WriteArrayStart(TEXT("enum_members")); int32 Written=0; for(int32 Index=0;Index<Type->NumEnums() && Written<256;++Index) if(!Type->HasMetaData(TEXT("Hidden"),Index) && !(Type->ContainsExistingMax() && Index==Type->NumEnums()-1)) { J->WriteValue(Type->GetNameStringByIndex(Index)); ++Written; } J->WriteArrayEnd(); J->WriteValue(TEXT("enum_members_truncated"),Type->NumEnums()>256); }
  if(Depth<2) { auto Element=[&](const TCHAR* Label,FProperty* Field) { J->WriteObjectStart(Label); J->WriteValue(TEXT("type"),Field->GetCPPType()); SettingMetadata(J,Field,Depth+1); J->WriteObjectEnd(); }; if(Array) Element(TEXT("element"),Array->Inner); else if(Set) Element(TEXT("element"),Set->ElementProp); else if(Map) { Element(TEXT("key"),Map->KeyProp); Element(TEXT("value"),Map->ValueProp); } }
 }
 void ReferenceValues(TSharedRef<TJsonWriter<>> J,const UStruct* Type,const void* Data,const TCHAR* Label=TEXT("instance_references"))
 {
  J->WriteObjectStart(Label); if(Type && Data) for(TFieldIterator<FProperty> It(Type);It;++It) if(It->ArrayDim==1 && It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient|CPF_EditConst|CPF_InstancedReference|CPF_ContainsInstancedReference)) { FString Path; const auto* Address=It->ContainerPtrToValuePtr<void>(Data); if(auto* Soft=CastField<FSoftObjectProperty>(*It)) Path=Soft->GetPropertyValue(Address).ToSoftObjectPath().ToString(); else if(auto* Hard=CastField<FObjectPropertyBase>(*It)) { if(auto* Object=Hard->GetObjectPropertyValue(Address)) Path=Object->GetPathName(); } else continue; J->WriteValue(It->GetName(),Path); } J->WriteObjectEnd();
 }
 void ContainerValues(TSharedRef<TJsonWriter<>> J,const UStruct* Type,const void* Data,const TCHAR* Label=TEXT("instance_containers"))
 {
  J->WriteObjectStart(Label); if(Type && Data) for(TFieldIterator<FProperty> It(Type);It;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient))
  {
   if(auto* Map=CastField<FMapProperty>(*It)) { FScriptMapHelper Helper(Map,It->ContainerPtrToValuePtr<void>(Data)); J->WriteObjectStart(It->GetName()); J->WriteValue(TEXT("kind"),TEXT("Map")); J->WriteValue(TEXT("size"),Helper.Num()); J->WriteValue(TEXT("truncated"),Helper.Num()>256); J->WriteArrayStart(TEXT("values")); auto Text=[](FProperty* Field,const void* Address) { FString Value; if(auto* Soft=CastField<FSoftObjectProperty>(Field)) Value=Soft->GetPropertyValue(Address).ToSoftObjectPath().ToString(); else if(auto* Hard=CastField<FObjectPropertyBase>(Field)) { if(auto* Object=Hard->GetObjectPropertyValue(Address)) Value=Object->GetPathName(); } else Field->ExportTextItem_Direct(Value,Address,nullptr,nullptr,PPF_None); return Value.Left(4096); }; int32 Written=0; for(int32 Index=0;Index<Helper.GetMaxIndex() && Written<256;++Index) if(Helper.IsValidIndex(Index)) { J->WriteObjectStart(); J->WriteValue(TEXT("Key"),Text(Map->KeyProp,Helper.GetKeyPtr(Index))); J->WriteValue(TEXT("Value"),Text(Map->ValueProp,Helper.GetValuePtr(Index))); J->WriteObjectEnd(); ++Written; } J->WriteArrayEnd(); J->WriteObjectEnd(); continue; }
   auto* Array=CastField<FArrayProperty>(*It); auto* Set=CastField<FSetProperty>(*It); auto* Inner=Array ? Array->Inner : Set ? Set->ElementProp : nullptr; if(!Inner) continue; const auto* Address=It->ContainerPtrToValuePtr<void>(Data);
   J->WriteObjectStart(It->GetName()); J->WriteValue(TEXT("kind"),Array ? TEXT("Array") : TEXT("Set")); auto Write=[&](const void* Element) { FString Text; if(auto* Soft=CastField<FSoftObjectProperty>(Inner)) Text=Soft->GetPropertyValue(Element).ToSoftObjectPath().ToString(); else if(auto* Hard=CastField<FObjectPropertyBase>(Inner)) { if(auto* Object=Hard->GetObjectPropertyValue(Element)) Text=Object->GetPathName(); } else Inner->ExportTextItem_Direct(Text,Element,nullptr,nullptr,PPF_None); J->WriteValue(Text.Left(4096)); };
   const int32 Count=Array ? FScriptArrayHelper(Array,Address).Num() : FScriptSetHelper(Set,Address).Num(); J->WriteValue(TEXT("size"),Count); J->WriteValue(TEXT("truncated"),Count>256); J->WriteArrayStart(TEXT("values"));
   if(Array) { FScriptArrayHelper Helper(Array,Address); for(int32 Index=0;Index<FMath::Min(Count,256);++Index) Write(Helper.GetRawPtr(Index)); } else { FScriptSetHelper Helper(Set,Address); int32 Written=0; for(int32 Index=0;Index<Helper.GetMaxIndex() && Written<256;++Index) if(Helper.IsValidIndex(Index)) { Write(Helper.GetElementPtr(Index)); ++Written; } } J->WriteArrayEnd(); J->WriteObjectEnd();
  }
  J->WriteObjectEnd();
 }
 void ConsiderationValues(TSharedRef<TJsonWriter<>> J,const FStateTreeEditorNode& N)
 {
  if(const auto* C=N.Node.GetPtr<FStateTreeFloatInputConsideration>()) { J->WriteObjectStart(TEXT("response_curve")); J->WriteValue(TEXT("asset"),GetPathNameSafe(C->ResponseCurve.CurveInfo.ExternalCurve)); J->WriteArrayStart(TEXT("keys")); int32 Count=0; for(auto It=C->ResponseCurve.CurveInfo.EditorCurveData.GetKeyIterator();It && Count<256;++It,++Count) { J->WriteObjectStart(); J->WriteValue(TEXT("time"),It->Time); J->WriteValue(TEXT("value"),It->Value); J->WriteValue(TEXT("interpolation"),It->InterpMode==RCIM_Linear ? TEXT("Linear") : It->InterpMode==RCIM_Constant ? TEXT("Constant") : TEXT("Cubic")); J->WriteValue(TEXT("arrive_tangent"),It->ArriveTangent); J->WriteValue(TEXT("leave_tangent"),It->LeaveTangent); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("truncated"),C->ResponseCurve.CurveInfo.EditorCurveData.GetNumKeys()>256); J->WriteObjectEnd(); }
  if(N.Node.GetScriptStruct()->IsChildOf(FStateTreeEnumInputConsideration::StaticStruct())) if(auto* Field=FindFProperty<FStructProperty>(N.Node.GetScriptStruct(),TEXT("EnumValueScorePairs"))) { const auto* Pairs=Field->ContainerPtrToValuePtr<FStateTreeEnumValueScorePairs>(N.Node.GetMemory()); J->WriteValue(TEXT("score_enum"),GetPathNameSafe(Pairs->Enum)); J->WriteArrayStart(TEXT("enum_scores")); for(int32 Index=0;Index<FMath::Min(Pairs->Data.Num(),256);++Index) { const auto& Pair=Pairs->Data[Index]; J->WriteObjectStart(); J->WriteValue(TEXT("name"),Pair.EnumName.ToString()); J->WriteValue(TEXT("value"),Pair.EnumValue); J->WriteValue(TEXT("score"),Pair.Score); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("enum_scores_truncated"),Pairs->Data.Num()>256); }
 }
 void NodeJson(TSharedRef<TJsonWriter<>> J,const TCHAR* Label,const TArray<FStateTreeEditorNode>& Nodes)
 {
  J->WriteArrayStart(Label); for(const auto& N:Nodes) if(N.Node.IsValid()) { J->WriteObjectStart(); J->WriteValue(TEXT("id"),Id(N.ID)); J->WriteValue(TEXT("struct"),N.Node.GetScriptStruct()->GetPathName()); J->WriteValue(TEXT("name"),N.GetName().ToString()); J->WriteValue(TEXT("explicit_name"),N.Node.Get<FStateTreeNodeBase>().Name.ToString()); if(const auto* Task=N.Node.GetPtr<FStateTreeTaskBase>()) { J->WriteValue(TEXT("task_enabled"),bool(Task->bTaskEnabled)); J->WriteValue(TEXT("considered_for_completion"),bool(Task->bConsideredForCompletion)); J->WriteValue(TEXT("can_edit_completion"),bool(Task->bCanEditConsideredForCompletion)); } if(const auto* Condition=N.Node.GetPtr<FStateTreeConditionBase>()) J->WriteValue(TEXT("condition_evaluation"),StaticEnum<EStateTreeConditionEvaluationMode>()->GetNameStringByValue(int64(Condition->EvaluationMode))); ConsiderationValues(J,N); J->WriteValue(TEXT("expression_indent"),int32(N.ExpressionIndent)); J->WriteValue(TEXT("operand"),StaticEnum<EStateTreeExpressionOperand>()->GetNameStringByValue(int64(N.ExpressionOperand))); Values(J,TEXT("properties"),N.Node.GetScriptStruct(),N.Node.GetMemory()); J->WriteValue(TEXT("instance_class"),N.InstanceObject ? N.InstanceObject->GetClass()->GetPathName() : FString()); if(N.InstanceObject) Values(J,TEXT("instance_properties"),N.InstanceObject->GetClass(),N.InstanceObject); else Values(J,TEXT("instance_properties"),N.Instance.GetScriptStruct(),N.Instance.GetMemory()); if(N.InstanceObject) ReferenceValues(J,N.InstanceObject->GetClass(),N.InstanceObject); else ReferenceValues(J,N.Instance.GetScriptStruct(),N.Instance.GetMemory()); if(N.InstanceObject) ContainerValues(J,N.InstanceObject->GetClass(),N.InstanceObject); else ContainerValues(J,N.Instance.GetScriptStruct(),N.Instance.GetMemory()); J->WriteObjectEnd(); } J->WriteArrayEnd();
 }
 void BagJson(TSharedRef<TJsonWriter<>> J,const TCHAR* Label,const FInstancedPropertyBag& B,const FGuid& Scope)
 {
  J->WriteObjectStart(Label); J->WriteValue(TEXT("id"),Id(Scope)); J->WriteArrayStart(TEXT("fields"));
  if(const auto* Type=B.GetPropertyBagStruct()) for(const auto& Desc:Type->GetPropertyDescs()) { J->WriteObjectStart(); J->WriteValue(TEXT("id"),Id(Desc.ID)); J->WriteValue(TEXT("name"),Desc.Name.ToString()); J->WriteValue(TEXT("type"),StaticEnum<EPropertyBagPropertyType>()->GetNameStringByValue(int64(Desc.ValueType))); J->WriteValue(TEXT("type_path"),GetPathNameSafe(Desc.ValueTypeObject)); FString Value; if(Desc.CachedProperty) Desc.CachedProperty->ExportTextItem_Direct(Value,Desc.CachedProperty->ContainerPtrToValuePtr<void>(B.GetValue().GetMemory()),nullptr,nullptr,PPF_None); J->WriteValue(TEXT("value"),Value.Left(4096)); J->WriteValue(TEXT("value_truncated"),Value.Len()>4096); FString ReferencePath; if(ReferenceType(Desc.ValueType) && Desc.ContainerTypes.IsEmpty()) { const auto* Address=Desc.CachedProperty->ContainerPtrToValuePtr<void>(B.GetValue().GetMemory()); if(auto* Soft=CastField<FSoftObjectProperty>(Desc.CachedProperty)) ReferencePath=Soft->GetPropertyValue(Address).ToSoftObjectPath().ToString(); else if(auto* Object=CastField<FObjectPropertyBase>(Desc.CachedProperty)) if(auto* O=Object->GetObjectPropertyValue(Address)) ReferencePath=O->GetPathName(); } J->WriteValue(TEXT("reference_path"),ReferencePath); J->WriteValue(TEXT("container_type"),Desc.ContainerTypes.IsEmpty() ? FString(TEXT("None")) : StaticEnum<EPropertyBagContainerType>()->GetNameStringByValue(int64(Desc.ContainerTypes[0]))); int32 ContainerSize=0; if(auto* Array=CastField<FArrayProperty>(Desc.CachedProperty)) ContainerSize=FScriptArrayHelper(Array,Desc.CachedProperty->ContainerPtrToValuePtr<void>(B.GetValue().GetMemory())).Num(); else if(auto* Set=CastField<FSetProperty>(Desc.CachedProperty)) ContainerSize=FScriptSetHelper(Set,Desc.CachedProperty->ContainerPtrToValuePtr<void>(B.GetValue().GetMemory())).Num(); J->WriteValue(TEXT("container_size"),ContainerSize); J->WriteValue(TEXT("container_values_truncated"),ContainerSize>256); J->WriteArrayStart(TEXT("container_values"));
   if(Desc.ContainerTypes.Num()==1) { auto* Array=CastField<FArrayProperty>(Desc.CachedProperty); auto* Set=CastField<FSetProperty>(Desc.CachedProperty); auto* Inner=Array ? Array->Inner : Set ? Set->ElementProp : nullptr; const auto* Address=Desc.CachedProperty->ContainerPtrToValuePtr<void>(B.GetValue().GetMemory()); auto Write=[&](const void* Element) { FString Text; if(auto* Soft=CastField<FSoftObjectProperty>(Inner)) Text=Soft->GetPropertyValue(Element).ToSoftObjectPath().ToString(); else if(auto* Object=CastField<FObjectPropertyBase>(Inner)) { if(auto* O=Object->GetObjectPropertyValue(Element)) Text=O->GetPathName(); } else if(Inner) Inner->ExportTextItem_Direct(Text,Element,nullptr,nullptr,PPF_None); J->WriteValue(Text.Left(4096)); }; if(Array) { FScriptArrayHelper Values(Array,Address); for(int32 Index=0;Index<FMath::Min(Values.Num(),256);++Index) Write(Values.GetRawPtr(Index)); } else if(Set) { FScriptSetHelper Values(Set,Address); int32 Count=0; for(int32 Index=0;Index<Values.GetMaxIndex() && Count<256;++Index) if(Values.IsValidIndex(Index)) { Write(Values.GetElementPtr(Index)); ++Count; } } }
   J->WriteArrayEnd(); J->WriteValue(TEXT("container_count"),int32(Desc.ContainerTypes.Num())); J->WriteObjectEnd(); }
  J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 FString Json(UStateTree* T,bool Change=false,bool Dry=false,bool Saved=false,const FGuid& Selected=FGuid(),const FString& Diagnostics=TEXT(""),bool Validation=false,const TArray<UStateTree*>* Affected=nullptr)
 {
  auto M=Model(T); FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),T->GetPathName()); J->WriteValue(TEXT("schema"),M.Data->Schema->GetClass()->GetPathName()); Values(J,TEXT("schema_properties"),M.Data->Schema->GetClass(),M.Data->Schema); ReferenceValues(J,M.Data->Schema->GetClass(),M.Data->Schema,TEXT("schema_references")); ContainerValues(J,M.Data->Schema->GetClass(),M.Data->Schema,TEXT("schema_containers")); J->WriteObjectStart(TEXT("schema_context_classes")); for(TFieldIterator<FClassProperty> It(M.Data->Schema->GetClass());It;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient)) J->WriteValue(It->GetName(),GetPathNameSafe(It->GetObjectPropertyValue_InContainer(M.Data->Schema))); J->WriteObjectEnd(); J->WriteObjectStart(TEXT("schema_capabilities")); J->WriteValue(TEXT("multiple_tasks"),M.Data->Schema->AllowMultipleTasks()); J->WriteValue(TEXT("enter_conditions"),M.Data->Schema->AllowEnterConditions()); J->WriteValue(TEXT("evaluators"),M.Data->Schema->AllowEvaluators()); J->WriteValue(TEXT("considerations"),M.Data->Schema->AllowUtilityConsiderations()); J->WriteValue(TEXT("global_parameters"),M.Data->Schema->AllowGlobalParameters()); J->WriteValue(TEXT("task_completion"),M.Data->Schema->AllowTasksCompletion()); J->WriteValue(TEXT("scheduled_tick"),M.Data->Schema->IsScheduledTickAllowed()); J->WriteObjectEnd(); J->WriteValue(TEXT("ready_to_run"),T->IsReadyToRun()); J->WriteValue(TEXT("editor_hash"),int64(UStateTreeEditingSubsystem::CalculateStateTreeHash(T))); J->WriteValue(TEXT("compiled_hash"),int64(T->LastCompiledEditorDataHash)); J->WriteValue(TEXT("dirty"),T->GetOutermost()->IsDirty()); J->WriteValue(TEXT("would_change"),Change); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("selected_id"),Selected.IsValid() ? Id(Selected) : FString()); J->WriteValue(TEXT("diagnostics"),Diagnostics); J->WriteValue(TEXT("validation_compiled_copy"),Validation);
  J->WriteArrayStart(TEXT("affected_assets")); if(Affected) for(auto* A:*Affected) J->WriteValue(A->GetPathName()); J->WriteArrayEnd(); BagJson(J,TEXT("parameters"),M.Data->GetRootParametersPropertyBag(),M.Data->GetRootParametersGuid()); J->WriteArrayStart(TEXT("states")); for(auto* V:M.States) { J->WriteObjectStart(); J->WriteValue(TEXT("id"),Id(V->ID)); J->WriteValue(TEXT("parent_id"),V->Parent ? Id(V->Parent->ID) : FString()); J->WriteValue(TEXT("name"),V->Name.ToString()); J->WriteValue(TEXT("type"),StaticEnum<EStateTreeStateType>()->GetNameStringByValue(int64(V->Type))); J->WriteValue(TEXT("requires_event"),V->bHasRequiredEventToEnter); J->WriteValue(TEXT("event_source_id"),Id(V->GetEventID())); J->WriteValue(TEXT("required_event_tag"),V->RequiredEventToEnter.Tag.ToString()); J->WriteValue(TEXT("required_payload_struct"),GetPathNameSafe(V->RequiredEventToEnter.PayloadStruct)); J->WriteValue(TEXT("consume_event"),V->RequiredEventToEnter.bConsumeEventOnSelect); J->WriteValue(TEXT("linked_asset"),V->LinkedAsset ? V->LinkedAsset->GetPathName() : FString()); J->WriteValue(TEXT("linked_subtree_id"),V->Type==EStateTreeStateType::Linked ? Id(V->LinkedSubtree.ID) : FString()); J->WriteValue(TEXT("linked_subtree_name"),V->Type==EStateTreeStateType::Linked ? V->LinkedSubtree.Name.ToString() : FString()); J->WriteArrayStart(TEXT("parameter_overrides")); for(const auto& G:V->Parameters.PropertyOverrides) J->WriteValue(Id(G)); J->WriteArrayEnd(); Values(J,TEXT("properties"),V->GetClass(),V); BagJson(J,TEXT("parameters"),V->Parameters.Parameters,V->Parameters.ID); J->WriteArrayStart(TEXT("children")); for(UStateTreeState* C:V->Children) J->WriteValue(Id(C->ID)); J->WriteArrayEnd(); NodeJson(J,TEXT("tasks"),V->Tasks); TArray<FStateTreeEditorNode> Single; if(V->SingleTask.Node.IsValid()) Single.Add(V->SingleTask); NodeJson(J,TEXT("single_task"),Single); NodeJson(J,TEXT("enter_conditions"),V->EnterConditions); NodeJson(J,TEXT("considerations"),V->Considerations); J->WriteArrayStart(TEXT("transitions")); for(const auto& Tr:V->Transitions) { J->WriteObjectStart(); J->WriteValue(TEXT("id"),Id(Tr.ID)); J->WriteValue(TEXT("trigger"),StaticEnum<EStateTreeTransitionTrigger>()->GetNameStringByValue(int64(Tr.Trigger))); J->WriteValue(TEXT("target_type"),StaticEnum<EStateTreeTransitionType>()->GetNameStringByValue(int64(Tr.State.LinkType))); J->WriteValue(TEXT("target_id"),Tr.State.ID.IsValid() ? Id(Tr.State.ID) : FString()); J->WriteValue(TEXT("event_tag"),Tr.RequiredEvent.Tag.ToString()); J->WriteValue(TEXT("event_source_id"),Id(Tr.GetEventID())); J->WriteValue(TEXT("payload_struct"),GetPathNameSafe(Tr.RequiredEvent.PayloadStruct)); J->WriteValue(TEXT("consume_event"),Tr.RequiredEvent.bConsumeEventOnSelect); J->WriteValue(TEXT("enabled"),Tr.bTransitionEnabled); J->WriteValue(TEXT("priority"),StaticEnum<EStateTreeTransitionPriority>()->GetNameStringByValue(int64(Tr.Priority))); J->WriteValue(TEXT("delay_enabled"),Tr.bDelayTransition); J->WriteValue(TEXT("random_delay"),Tr.DelayRandomVariance); J->WriteValue(TEXT("delay"),Tr.DelayDuration); NodeJson(J,TEXT("conditions"),Tr.Conditions); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); } J->WriteArrayEnd();
  NodeJson(J,TEXT("evaluators"),M.Data->Evaluators); NodeJson(J,TEXT("global_tasks"),M.Data->GlobalTasks); J->WriteValue(TEXT("binding_count"),M.Data->EditorBindings.GetBindings().Num()); J->WriteArrayStart(TEXT("bindings")); for(const auto& B:M.Data->EditorBindings.GetBindings()) { J->WriteObjectStart(); J->WriteValue(TEXT("source_id"),Id(B.GetSourcePath().GetStructID())); J->WriteValue(TEXT("source_path"),B.GetSourcePath().ToString()); J->WriteValue(TEXT("target_id"),Id(B.GetTargetPath().GetStructID())); J->WriteValue(TEXT("target_path"),B.GetTargetPath().ToString()); J->WriteValue(TEXT("output_binding"),B.IsOutputBinding()); J->WriteValue(TEXT("property_function"),B.GetPropertyFunctionNode().IsValid()); if(const auto* Function=B.GetPropertyFunctionNode().GetPtr<const FStateTreeEditorNode>()) { TArray<FStateTreeEditorNode> Functions; Functions.Add(*Function); NodeJson(J,TEXT("function_nodes"),Functions); } J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteArrayStart(TEXT("compiled_states")); for(const auto& C:T->GetStates()) { J->WriteObjectStart(); J->WriteValue(TEXT("name"),C.Name.ToString()); J->WriteValue(TEXT("tasks"),int32(C.TasksNum)); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native state hierarchy, transitions and schema-approved native struct nodes; scalar/plain-struct settings and native compilation. Native parameter bags, Array/Set parameters, direct/output bindings, native property functions and compiled Blueprint node instances. Nested containers, typed node references and custom editor layouts remain limited.")); J->WriteObjectEnd(); J->Close(); return S;
 }
}
FString StateTreeUtils::Inspect(const FString& Path,bool Validate)
{
 auto* T=Load(Path); Model(T); FString Diagnostics; if(Validate) { FPreviewGraph Preview(T); FStateTreeCompilerLog Log; const bool OK=Preview.CompileCopies(Log); Diagnostics=(OK ? TEXT("success\n") : TEXT("failed\n"))+Messages(Log); } return Json(T,false,false,false,FGuid(),Diagnostics,Validate);
}
FString StateTreeUtils::InspectBindables(const FString& Path,const FString& TargetId)
{
 auto* T=Load(Path); auto M=Model(T); const auto Target=Guid(TargetId); TInstancedStruct<FPropertyBindingBindableStructDescriptor> TargetDesc;
 if(!M.Data->GetBindableStructByID(Target,TargetDesc)) throw std::runtime_error("Target ID is not a native bindable struct in this tree");
 TArray<TInstancedStruct<FPropertyBindingBindableStructDescriptor>> Sources; M.Data->GetBindableStructs(Target,Sources);
 if(Sources.Num()>1024) throw std::runtime_error("Bindable source count exceeds 1024");
 FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),T->GetPathName()); J->WriteValue(TEXT("target_id"),Id(Target)); J->WriteArrayStart(TEXT("sources"));
 for(const auto& Source:Sources) { const auto& D=Source.Get(); J->WriteObjectStart(); J->WriteValue(TEXT("id"),Id(D.ID)); J->WriteValue(TEXT("name"),D.Name.ToString()); J->WriteValue(TEXT("struct"),GetPathNameSafe(D.Struct)); J->WriteValue(TEXT("category"),D.Category); J->WriteArrayStart(TEXT("properties")); int32 Count=0; if(D.Struct) for(TFieldIterator<FProperty> It(D.Struct);It && Count<128;++It,++Count) { J->WriteObjectStart(); J->WriteValue(TEXT("name"),It->GetName()); J->WriteValue(TEXT("type"),It->GetCPPType()); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("properties_capped"),Count==128); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return S;
}
FString StateTreeUtils::DiscoverSchemas(const FString& Search,int32 Limit)
{
 if(Limit<1 || Limit>256 || Search.Len()>128) throw std::runtime_error("Schema discovery requires limit 1-256 and search <=128"); TArray<UClass*> Classes;
 for(TObjectIterator<UClass> It;It;++It) if(It->IsChildOf(UStateTreeSchema::StaticClass()) && !It->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists) && It->GetOutermost()->GetName().StartsWith(TEXT("/Script/")) && (Search.IsEmpty() || It->GetPathName().Contains(Search))) Classes.Add(*It);
 Classes.Sort([](const UClass& A,const UClass& B) { return A.GetPathName()<B.GetPathName(); }); FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("total"),Classes.Num()); J->WriteValue(TEXT("truncated"),Classes.Num()>Limit); J->WriteValue(TEXT("scope"),TEXT("Loaded concrete native schemas and default context requirements; optional unloaded modules are not enumerated.")); J->WriteArrayStart(TEXT("schemas"));
 for(int32 Index=0;Index<FMath::Min(Limit,Classes.Num());++Index) { auto* Class=Classes[Index]; const auto* Schema=Class->GetDefaultObject<UStateTreeSchema>(); J->WriteObjectStart(); J->WriteValue(TEXT("class_path"),Class->GetPathName()); J->WriteValue(TEXT("display_name"),Class->GetDisplayNameText().ToString());
 J->WriteValue(TEXT("allow_multiple_tasks"),Schema->AllowMultipleTasks()); J->WriteValue(TEXT("allow_enter_conditions"),Schema->AllowEnterConditions()); J->WriteValue(TEXT("allow_evaluators"),Schema->AllowEvaluators()); J->WriteValue(TEXT("allow_considerations"),Schema->AllowUtilityConsiderations()); J->WriteValue(TEXT("allow_global_parameters"),Schema->AllowGlobalParameters()); J->WriteValue(TEXT("allow_tasks_completion"),Schema->AllowTasksCompletion()); J->WriteValue(TEXT("allow_scheduled_tick"),Schema->IsScheduledTickAllowed());
 auto Choices=[&](const TCHAR* Label,UEnum* Type,auto Allowed) { J->WriteArrayStart(Label); for(int32 Entry=0;Entry<Type->NumEnums();++Entry) if(!Type->HasMetaData(TEXT("Hidden"),Entry) && !(Type->ContainsExistingMax() && Entry==Type->NumEnums()-1) && Allowed(Type->GetValueByIndex(Entry))) J->WriteValue(Type->GetNameStringByIndex(Entry)); J->WriteArrayEnd(); }; Choices(TEXT("state_types"),StaticEnum<EStateTreeStateType>(),[&](int64 V) { return Schema->IsStateTypeAllowed(EStateTreeStateType(V)); }); Choices(TEXT("selection_behaviors"),StaticEnum<EStateTreeStateSelectionBehavior>(),[&](int64 V) { return Schema->IsStateSelectionAllowed(EStateTreeStateSelectionBehavior(V)); });
 J->WriteArrayStart(TEXT("contexts")); for(const auto& Context:Schema->GetContextDataDescs()) { J->WriteObjectStart(); J->WriteValue(TEXT("id"),Id(Context.ID)); J->WriteValue(TEXT("name"),Context.Name.ToString()); J->WriteValue(TEXT("type"),GetPathNameSafe(Context.Struct)); J->WriteObjectEnd(); } J->WriteArrayEnd(); Values(J,TEXT("properties"),Class,Schema); J->WriteArrayStart(TEXT("settings")); int32 Fields=0; for(TFieldIterator<FProperty> It(Class);It && Fields<128;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient)) { ++Fields; J->WriteObjectStart(); J->WriteValue(TEXT("name"),It->GetName()); J->WriteValue(TEXT("type"),It->GetCPPType()); SettingMetadata(J,*It); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return S;
}
FString StateTreeUtils::DiscoverClasses(const FString& Path,const FString& Kind,const FString& Search,int32 Limit)
{
 if(Limit<1 || Limit>256 || Search.Len()>128) throw std::runtime_error("Class discovery requires limit 1-256 and search <=128"); auto* T=Load(Path); auto M=Model(T); UClass* Base=nullptr;
 if(Kind==TEXT("task") || Kind==TEXT("single_task") || Kind==TEXT("global_task")) Base=UStateTreeTaskBlueprintBase::StaticClass(); else if(Kind==TEXT("condition")) Base=UStateTreeConditionBlueprintBase::StaticClass(); else if(Kind==TEXT("evaluator")) Base=UStateTreeEvaluatorBlueprintBase::StaticClass(); else if(Kind==TEXT("consideration")) Base=UStateTreeConsiderationBlueprintBase::StaticClass(); else throw std::runtime_error("Unknown Blueprint node kind");
 const bool Allowed=Kind==TEXT("single_task") ? !M.Data->Schema->AllowMultipleTasks() : Kind==TEXT("evaluator") ? M.Data->Schema->AllowEvaluators() : Kind==TEXT("consideration") ? M.Data->Schema->AllowUtilityConsiderations() : true; TArray<UClass*> Classes;
 if(Allowed) for(TObjectIterator<UClass> It;It;++It) { auto* C=*It; if(!IsValid(C) || !C->IsChildOf(Base) || C->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists) || C->GetName().StartsWith(TEXT("SKEL_")) || C->GetName().StartsWith(TEXT("REINST_")) || !M.Data->Schema->IsClassAllowed(C) || (!Search.IsEmpty() && !C->GetPathName().Contains(Search))) continue; if(auto* Blueprint=Cast<UBlueprint>(C->ClassGeneratedBy)) if(Blueprint->GeneratedClass!=C || (Blueprint->Status!=BS_UpToDate && Blueprint->Status!=BS_UpToDateWithWarnings)) continue; Classes.Add(C); }
 Classes.Sort([](const UClass& A,const UClass& B) { return A.GetPathName()<B.GetPathName(); }); FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),T->GetPathName()); J->WriteValue(TEXT("kind"),Kind); J->WriteValue(TEXT("total"),Classes.Num()); J->WriteValue(TEXT("truncated"),Classes.Num()>Limit); J->WriteValue(TEXT("scope"),TEXT("Loaded classes are schema-approved; registry Blueprint candidates require load-time schema, compilation and concrete-class validation.")); J->WriteArrayStart(TEXT("classes"));
 for(int32 Index=0;Index<FMath::Min(Limit,Classes.Num());++Index) { auto* C=Classes[Index]; J->WriteObjectStart(); J->WriteValue(TEXT("class_path"),C->GetPathName()); J->WriteValue(TEXT("display_name"),C->GetDisplayNameText().ToString()); J->WriteArrayStart(TEXT("instance_properties")); int32 Count=0; for(TFieldIterator<FProperty> It(C);It && Count<128;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient)) { ++Count; J->WriteObjectStart(); J->WriteValue(TEXT("name"),It->GetName()); J->WriteValue(TEXT("type"),It->GetCPPType()); J->WriteValue(TEXT("plain_setting_supported"),Plain(*It) && !It->HasAnyPropertyFlags(CPF_EditConst)); SettingMetadata(J,*It); J->WriteValue(TEXT("category"),It->GetMetaData(TEXT("Category"))); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); }
 J->WriteArrayEnd();
 TArray<FAssetData> Candidates; if(Allowed) { auto& Registry=FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get(); TSet<FTopLevelAssetPath> Derived; TArray<FTopLevelAssetPath> Bases={Base->GetClassPathName()}; TSet<FTopLevelAssetPath> Excluded; Registry.GetDerivedClassNames(Bases,Excluded,Derived); TArray<FAssetData> Blueprints; Registry.GetAssetsByClass(UBlueprint::StaticClass()->GetClassPathName(),Blueprints,true); for(const auto& Asset:Blueprints) { FString Generated; if(!Asset.GetTagValue(FName(TEXT("GeneratedClass")),Generated)) continue; const FString ClassPath=FPackageName::ExportTextPathToObjectPath(Generated); if(!Derived.Contains(FSoftObjectPath(ClassPath).GetAssetPath()) || (!Search.IsEmpty() && !ClassPath.Contains(Search))) continue; if(Classes.ContainsByPredicate([&](const UClass* C) { return C->GetPathName()==ClassPath; })) continue; Candidates.Add(Asset); } }
 Candidates.Sort([](const FAssetData& A,const FAssetData& B) { return A.GetSoftObjectPath().ToString()<B.GetSoftObjectPath().ToString(); }); J->WriteValue(TEXT("blueprint_candidate_total"),Candidates.Num()); J->WriteValue(TEXT("blueprint_candidates_truncated"),Candidates.Num()>Limit); J->WriteArrayStart(TEXT("blueprint_candidates")); for(int32 Index=0;Index<FMath::Min(Limit,Candidates.Num());++Index) { const auto& Asset=Candidates[Index]; FString Generated; Asset.GetTagValue(FName(TEXT("GeneratedClass")),Generated); const FString ClassPath=FPackageName::ExportTextPathToObjectPath(Generated); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),Asset.GetSoftObjectPath().ToString()); J->WriteValue(TEXT("class_path"),ClassPath); J->WriteValue(TEXT("loaded"),FindObject<UClass>(nullptr,*ClassPath)!=nullptr); J->WriteValue(TEXT("requires_authoring_validation"),true); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return S;
}
FString StateTreeUtils::Discover(const FString& Path,const FString& Kind,const FString& Search,int32 Limit)
{
 if(Limit<1 || Limit>256 || Search.Len()>128) throw std::runtime_error("Discovery requires limit 1-256 and search <=128 characters");
 auto* T=Load(Path); auto M=Model(T); UScriptStruct* Base=nullptr;
 if(Kind==TEXT("task") || Kind==TEXT("single_task") || Kind==TEXT("global_task")) Base=FStateTreeTaskBase::StaticStruct();
 else if(Kind==TEXT("condition")) Base=FStateTreeConditionBase::StaticStruct();
 else if(Kind==TEXT("evaluator")) Base=FStateTreeEvaluatorBase::StaticStruct();
 else if(Kind==TEXT("consideration")) Base=FStateTreeConsiderationBase::StaticStruct(); else if(Kind==TEXT("property_function")) Base=FStateTreePropertyFunctionBase::StaticStruct();
 else throw std::runtime_error("Discovery kind requires task, global_task, condition, evaluator or consideration");
 TArray<UScriptStruct*> Types;
 const bool Allowed=Kind==TEXT("single_task") ? !M.Data->Schema->AllowMultipleTasks() : Kind==TEXT("evaluator") ? M.Data->Schema->AllowEvaluators() : Kind==TEXT("consideration") ? M.Data->Schema->AllowUtilityConsiderations() : true;
 if(Allowed) for(TObjectIterator<UScriptStruct> It;It;++It) if(*It!=Base && It->IsChildOf(Base) && It->GetOutermost()->GetName().StartsWith(TEXT("/Script/")) && !It->HasMetaData(TEXT("Hidden")) && M.Data->Schema->IsStructAllowed(*It) && (Search.IsEmpty() || It->GetPathName().Contains(Search))) Types.Add(*It);
 Types.Sort([](const UScriptStruct& A,const UScriptStruct& B) { return A.GetPathName()<B.GetPathName(); });
 FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("asset_path"),T->GetPathName()); J->WriteValue(TEXT("schema"),M.Data->Schema->GetClass()->GetPathName()); J->WriteValue(TEXT("kind"),Kind); J->WriteValue(TEXT("total"),Types.Num()); J->WriteValue(TEXT("truncated"),Types.Num()>Limit); J->WriteValue(TEXT("scope"),TEXT("Loaded native script structs approved by this schema; reflected editable fields only. UObject nodes and unloaded optional modules are not enumerated.")); J->WriteArrayStart(TEXT("nodes"));
 for(int32 Index=0;Index<FMath::Min(Limit,Types.Num());++Index)
 {
  auto* Type=Types[Index]; FInstancedStruct Definition; Definition.InitializeAs(Type); const auto& Node=Definition.Get<FStateTreeNodeBase>(); const auto* Instance=Node.GetInstanceDataType();
  J->WriteObjectStart(); J->WriteValue(TEXT("struct"),Type->GetPathName()); J->WriteValue(TEXT("display_name"),Type->GetDisplayNameText().ToString()); J->WriteValue(TEXT("instance_type"),GetPathNameSafe(Instance)); J->WriteValue(TEXT("struct_instance_supported"),!Instance || Instance->IsA<UScriptStruct>());
  auto Fields=[&](const TCHAR* Label,const UStruct* Struct) { J->WriteArrayStart(Label); int32 Count=0; if(Struct) for(TFieldIterator<FProperty> It(Struct);It && Count<128;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient)) { ++Count; J->WriteObjectStart(); J->WriteValue(TEXT("name"),It->GetName()); J->WriteValue(TEXT("type"),It->GetCPPType()); J->WriteValue(TEXT("plain_setting_supported"),Plain(*It) && !It->HasAnyPropertyFlags(CPF_EditConst)); SettingMetadata(J,*It); J->WriteValue(TEXT("category"),It->GetMetaData(TEXT("Category"))); J->WriteValue(TEXT("clamp_min"),It->GetMetaData(TEXT("ClampMin"))); J->WriteValue(TEXT("clamp_max"),It->GetMetaData(TEXT("ClampMax"))); J->WriteObjectEnd(); } J->WriteArrayEnd(); };
  Fields(TEXT("properties"),Type); Fields(TEXT("instance_properties"),Instance); J->WriteObjectEnd();
 }
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return S;
}
FString StateTreeUtils::InspectRuntime(const FString& ComponentPath,const FString& Search,int32 Limit,int32 PIEInstance)
{
 auto* World=NavigationWorldUtils::Resolve(TEXT("pie"),PIEInstance);
 if(!IsInGameThread() || !IsValid(World) || World->WorldType!=EWorldType::PIE || World->bIsTearingDown) throw std::runtime_error("StateTree runtime inspection requires a live PIE world on the game thread");
 if(Limit<1 || Limit>256 || Search.Len()>128 || ComponentPath.Len()>2048) throw std::runtime_error("Runtime inspection requires limit 1-256, search <=128 and component path <=2048 characters");
 TArray<UStateTreeComponent*> Components;
 for(TObjectIterator<UStateTreeComponent> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==World && IsValid(It->GetOwner()) && !It->GetOwner()->IsActorBeingDestroyed() && (ComponentPath.IsEmpty() || It->GetPathName()==ComponentPath) && (Search.IsEmpty() || It->GetPathName().Contains(Search))) Components.Add(*It);
 if(!ComponentPath.IsEmpty() && Components.IsEmpty()) throw std::runtime_error("Component path does not identify a live StateTree component in the selected PIE world");
 Components.Sort([](const UStateTreeComponent& A,const UStateTreeComponent& B) { return A.GetPathName()<B.GetPathName(); });
 FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("world"),World->GetPathName()); J->WriteValue(TEXT("total"),Components.Num()); J->WriteValue(TEXT("truncated"),Components.Num()>Limit); J->WriteArrayStart(TEXT("components"));
 for(int32 I=0;I<FMath::Min(Limit,Components.Num());++I) { auto* C=Components[I]; J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),C->GetPathName()); J->WriteValue(TEXT("class"),C->GetClass()->GetPathName()); J->WriteValue(TEXT("owner_path"),C->GetOwner()->GetPathName()); J->WriteValue(TEXT("authority"),C->GetOwner()->HasAuthority()); J->WriteValue(TEXT("registered"),C->IsRegistered()); J->WriteValue(TEXT("running"),C->IsRunning()); J->WriteValue(TEXT("paused"),C->IsPaused()); J->WriteValue(TEXT("run_status"),StaticEnum<EStateTreeRunStatus>()->GetNameStringByValue(int64(C->GetStateTreeRunStatus()))); J->WriteValue(TEXT("schema"),GetPathNameSafe(C->GetSchema().Get()));
 const auto* ReferenceProperty=FindFProperty<FStructProperty>(C->GetClass(),TEXT("StateTreeRef")); if(ReferenceProperty && ReferenceProperty->Struct==FStateTreeReference::StaticStruct()) { const auto* Stored=ReferenceProperty->ContainerPtrToValuePtr<FStateTreeReference>(C); FStateTreeReference Reference=*Stored; const auto* Tree=Reference.GetStateTree(); J->WriteValue(TEXT("tree_asset"),GetPathNameSafe(Tree)); J->WriteValue(TEXT("reference_requires_sync"),Reference.RequiresParametersSync()); auto* Data=Tree ? Cast<UStateTreeEditorData>(Tree->EditorData) : nullptr; const auto& Parameters=Reference.GetParameters(); BagJson(J,TEXT("reference_parameters"),Parameters,Data ? Data->GetRootParametersGuid() : FGuid()); J->WriteArrayStart(TEXT("reference_parameter_overrides")); if(const auto* Bag=Parameters.GetPropertyBagStruct()) for(const auto& Field:Bag->GetPropertyDescs()) if(Reference.IsPropertyOverridden(Field.ID)) J->WriteValue(Id(Field.ID)); J->WriteArrayEnd(); }

#if WITH_GAMEPLAY_DEBUGGER
 J->WriteValue(TEXT("active_state_names_available"),true); J->WriteArrayStart(TEXT("active_state_names")); for(const auto Name:C->GetActiveStateNames()) J->WriteValue(Name.ToString()); J->WriteArrayEnd();
#else
 J->WriteValue(TEXT("active_state_names_available"),false);
#endif
 J->WriteObjectEnd(); }
 J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Read-only native PIE component status; state names are debug labels and are not unique identifiers across linked assets.")); J->WriteObjectEnd(); J->Close(); return S;
}
FString StateTreeUtils::ControlRuntime(const FStateTreeReq& R)
{
 auto* W=NavigationWorldUtils::Resolve(TEXT("pie"),R.PIEInstance);
 if(!IsInGameThread() || !IsValid(W) || W->bIsTearingDown || R.ComponentPath.IsEmpty() || R.ComponentPath.Len()>2048 || R.Reason.Len()>256) throw std::runtime_error("Runtime control requires an explicit PIE component path and reason <=256 characters");
 auto* C=FindObject<UStateTreeComponent>(nullptr,*R.ComponentPath);
 if(!IsValid(C) || C->IsTemplate() || C->GetWorld()!=W || !C->IsRegistered() || !IsValid(C->GetOwner()) || C->GetOwner()->IsActorBeingDestroyed() || !C->GetOwner()->HasAuthority()) throw std::runtime_error("Component must be registered, live and authoritative in the selected PIE world");
 const FString Op=R.Operation.ToLower(); bool Change=false; FStateTreeReference PreparedReference; bool ParameterOperation=false; FStateTreeInstanceData* RuntimeData=nullptr; int32 EventsBefore=-1,EventsAfter=-1; bool EventAccepted=false; FString AcceptedPayloadType; FGameplayTag RuntimeTag; FInstancedStruct Payload;
 if(Op==TEXT("start")) Change=!C->IsRunning();
 else if(Op==TEXT("restart")) Change=true;
 else if(Op==TEXT("stop")) Change=C->IsRunning();
 else if(Op==TEXT("pause")) { if(!C->IsRunning()) throw std::runtime_error("Pause requires running logic"); Change=!C->IsPaused(); }
 else if(Op==TEXT("resume")) { if(!C->IsRunning()) throw std::runtime_error("Resume requires running logic"); Change=C->IsPaused(); }
 else if(Op==TEXT("parameters") || Op==TEXT("reset_parameter"))
 {
  ParameterOperation=true; if(C->IsRunning() || C->GetStateTreeRunStatus()==EStateTreeRunStatus::Running) throw std::runtime_error("Runtime parameter edits require stopped logic; stop explicitly before updating");
  const auto* Property=FindFProperty<FStructProperty>(C->GetClass(),TEXT("StateTreeRef")); if(!Property || Property->Struct!=FStateTreeReference::StaticStruct()) throw std::runtime_error("Unsupported native StateTree reference layout"); const auto* Original=Property->ContainerPtrToValuePtr<FStateTreeReference>(C); if(!Original->GetStateTree() || !Original->GetStateTree()->IsReadyToRun()) throw std::runtime_error("Parameter edit requires a ready native tree reference"); PreparedReference=*Original; auto& Parameters=PreparedReference.GetMutableParameters();
  if(R.Properties.Num()>64) throw std::runtime_error("At most 64 runtime parameter settings");
  if(Op==TEXT("parameters")) for(const auto& Pair:R.Properties) { if(Pair.Key.IsEmpty() || Pair.Key.Len()>128) throw std::runtime_error("Parameter names require 1-128 characters"); const auto* Field=Parameters.FindPropertyDescByName(FName(*Pair.Key)); if(!Field) throw std::runtime_error("Unknown runtime reference parameter"); const auto ID=Field->ID; ParameterValue(Parameters,Field->Name,Pair.Value,C); PreparedReference.SetPropertyOverridden(ID,true); }
  else { if(R.Name.IsEmpty() || R.Name.Len()>128 || !R.Properties.IsEmpty()) throw std::runtime_error("Reset requires one parameter Name and no Properties"); const auto* Field=Parameters.FindPropertyDescByName(FName(*R.Name)); if(!Field) throw std::runtime_error("Unknown runtime reference parameter"); PreparedReference.SetPropertyOverridden(Field->ID,false); }
  Change=!FStateTreeReference::StaticStruct()->CompareScriptStruct(Original,&PreparedReference,0);
 }
 else if(Op==TEXT("event")) { if(!C->IsRunning() || C->IsPaused()) throw std::runtime_error("Event delivery requires running unpaused logic"); if(R.EventTag.Len()>256 || R.Name.Len()>128 || R.StructPath.Len()>1024) throw std::runtime_error("Event tag/origin exceeds bounds"); RuntimeTag=UGameplayTagsManager::Get().RequestGameplayTag(FName(*R.EventTag),false); if(!RuntimeTag.IsValid()) throw std::runtime_error("Event requires a registered Gameplay Tag"); if(!R.StructPath.IsEmpty()) { auto* Type=LoadObject<UScriptStruct>(nullptr,*R.StructPath); if(!Type || !Type->GetOutermost()->GetName().StartsWith(TEXT("/Script/")) || Type->GetStructureSize()>65536) throw std::runtime_error("Event payload requires a native struct <=64KiB"); for(TFieldIterator<FProperty> It(Type);It;++It) if(!Plain(*It)) throw std::runtime_error("Event payload requires plain scalar/struct fields"); Payload.InitializeAs(Type); Settings(Type,Payload.GetMutableMemory(),R.Properties,C); } else if(!R.Properties.IsEmpty()) throw std::runtime_error("Event payload settings require StructPath"); const auto* InstanceProperty=FindFProperty<FStructProperty>(C->GetClass(),TEXT("InstanceData")); if(!InstanceProperty || InstanceProperty->Struct!=FStateTreeInstanceData::StaticStruct()) throw std::runtime_error("Unsupported native StateTree instance data layout"); RuntimeData=InstanceProperty->ContainerPtrToValuePtr<FStateTreeInstanceData>(C); EventsBefore=RuntimeData->GetEventQueue().GetEventsView().Num(); if(EventsBefore>=FStateTreeEventQueue::MaxActiveEvents) throw std::runtime_error("Native StateTree event queue is full"); Change=true; }
 else throw std::runtime_error("Operation requires start, restart, pause, resume, stop, event, parameters or reset_parameter");
 if((Op==TEXT("start") && Change) || Op==TEXT("restart") || Op==TEXT("event")) { const auto* Property=FindFProperty<FStructProperty>(C->GetClass(),TEXT("StateTreeRef")); if(!Property || Property->Struct!=FStateTreeReference::StaticStruct()) throw std::runtime_error("Unsupported native StateTree reference layout"); const auto* Reference=Property->ContainerPtrToValuePtr<FStateTreeReference>(C); const auto* Tree=Reference->GetStateTree(); if(!IsValid(Tree) || !Tree->IsReadyToRun()) throw std::runtime_error("Component requires a ready native StateTree reference"); }
 if(Change && !R.bDryRun) { const FString Reason=R.Reason.IsEmpty() ? TEXT("UE5 MCP explicit runtime control") : R.Reason; if(ParameterOperation) C->SetStateTreeReference(PreparedReference); else if(Op==TEXT("start")) C->StartLogic(); else if(Op==TEXT("restart")) C->RestartLogic(); else if(Op==TEXT("stop")) C->StopLogic(Reason); else if(Op==TEXT("pause")) C->PauseLogic(Reason); else if(Op==TEXT("resume")) C->ResumeLogic(Reason); else if(Op==TEXT("event")) C->SendStateTreeEvent(RuntimeTag,FConstStructView(Payload),FName(*R.Name)); }
 if(RuntimeData && !R.bDryRun) { const auto Events=RuntimeData->GetEventQueue().GetEventsView(); EventsAfter=Events.Num(); EventAccepted=EventsAfter==EventsBefore+1 && Events.Last().IsValid() && Events.Last()->Tag==RuntimeTag && Events.Last()->Origin==FName(*R.Name) && Events.Last()->Payload.GetScriptStruct()==Payload.GetScriptStruct() && (!Payload.IsValid() || Payload.GetScriptStruct()->CompareScriptStruct(Events.Last()->Payload.GetMemory(),Payload.GetMemory(),0)); if(EventAccepted && Events.Last()->Payload.IsValid()) AcceptedPayloadType=Events.Last()->Payload.GetScriptStruct()->GetPathName(); }
 FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),C->GetPathName()); J->WriteValue(TEXT("operation"),Op); J->WriteValue(TEXT("parameter_operation"),ParameterOperation); J->WriteValue(TEXT("event_submitted"),Op==TEXT("event") && !R.bDryRun); J->WriteValue(TEXT("event_queue_accepted"),EventAccepted); J->WriteValue(TEXT("event_queue_before"),EventsBefore); J->WriteValue(TEXT("event_queue_after"),EventsAfter); J->WriteValue(TEXT("queued_payload_type"),AcceptedPayloadType); J->WriteValue(TEXT("would_change"),Change); J->WriteValue(TEXT("applied"),Change && !R.bDryRun); J->WriteValue(TEXT("dry_run"),R.bDryRun); J->WriteValue(TEXT("running"),C->IsRunning()); J->WriteValue(TEXT("paused"),C->IsPaused()); J->WriteValue(TEXT("run_status"),StaticEnum<EStateTreeRunStatus>()->GetNameStringByValue(int64(C->GetStateTreeRunStatus()))); J->WriteObjectEnd(); J->Close(); return S;
}
FString StateTreeUtils::Control(const FStateTreeReq& R,const FString& Op)
{
 if(!GEditor || GEditor->PlayWorld) throw std::runtime_error("StateTree asset edits require an idle editor");
 if(Op==TEXT("create"))
 {
  const FString P=FPackageName::ObjectPathToPackageName(R.AssetPath); if(!FPackageName::IsValidLongPackageName(P) || !P.StartsWith(TEXT("/Game/")) || P.Len()>200 || (R.AssetPath!=P && R.AssetPath!=P+TEXT(".")+FPackageName::GetLongPackageAssetName(P)) || FindPackage(nullptr,*P) || FPackageName::DoesPackageExist(P)) throw std::runtime_error("StateTree creation requires a new /Game package <=200 characters");
  auto* Schema=LoadClass<UStateTreeSchema>(nullptr,*R.SchemaPath); if(!Schema || Schema->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("A concrete native StateTree schema is required");
  TStrongObjectPtr<UStateTree> Preview(NewObject<UStateTree>()); auto Build=[&](UStateTree* T) { auto& Module=FStateTreeEditorModule::GetModule(); auto* D=NewObject<UStateTreeEditorData>(T,Module.GetEditorDataClass(Schema)); T->EditorData=D; D->Schema=NewObject<UStateTreeSchema>(D,Schema,NAME_None,RF_Transactional); D->EditorSchema=NewObject<UStateTreeEditorSchema>(D,NAME_None,RF_Transactional); D->AddRootState(); UStateTreeEditingSubsystem::ValidateStateTree(T); };
  Build(Preview.Get()); FStateTreeCompilerLog Log; if(!Compile(Preview.Get(),Log)) throw std::runtime_error(TCHAR_TO_UTF8(*Messages(Log))); if(R.bDryRun) return Json(Preview.Get(),true,true,false,FGuid(),Messages(Log));
  auto* T=NewObject<UStateTree>(CreatePackage(*P),*FPackageName::GetLongPackageAssetName(P),RF_Public|RF_Standalone|RF_Transactional); Build(T); FStateTreeCompilerLog Actual; if(!Compile(T,Actual)) throw std::runtime_error("Native StateTree creation compile failed after preflight"); FAssetRegistryModule::AssetCreated(T); T->MarkPackageDirty(); bool Saved=false; if(R.bSave) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(T,false); if(!Saved) throw std::runtime_error("StateTree created but save failed"); } return Json(T,true,false,Saved,FGuid(),Messages(Actual));
 }
 auto* T=Load(R.AssetPath); if(!T->GetOutermost()->GetName().StartsWith(TEXT("/Game/"))) throw std::runtime_error("StateTree edits require /Game assets"); Model(T);
 const FGuid NewId=FGuid::NewGuid(); FPreviewGraph Preview(T,R.LinkedAssetPath.IsEmpty() ? nullptr : Load(R.LinkedAssetPath));
 bool Changed; { TGuardValue<ITransaction*> Guard(GUndo,nullptr); Changed=Edit(Preview.RootCopy(),R,Op,NewId); }
 FStateTreeCompilerLog Log; if(!Preview.CompileCopies(Log)) throw std::runtime_error(TCHAR_TO_UTF8(*Messages(Log)));
 bool Saved=false;
 if(Changed && !R.bDryRun)
 {
  FScopedTransaction Tx(NSLOCTEXT("UE5MCP","StateTreeEdit","Edit StateTree dependencies"));
  for(auto* A:Preview.ActualOrder) Modify(A);
  Edit(T,R,Op,NewId);
  for(auto* A:Preview.ActualOrder) { FStateTreeCompilerLog Actual; if(!Compile(A,Actual,true)) throw std::runtime_error("Native StateTree dependency compile failed after successful preflight"); A->MarkPackageDirty(); UE::StateTree::Delegates::OnIdentifierChanged.Broadcast(*A); }
  for(auto* A:Preview.ActualOrder) Track(A);
 }
 if(R.bSave && !R.bDryRun) { Saved=true; for(auto* A:Preview.ActualOrder) if(!GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(A,false)) Saved=false; if(!Saved) throw std::runtime_error("StateTree dependencies changed but at least one save failed"); }
 const FGuid Selected=Op.StartsWith(TEXT("create_")) ? NewId : !R.ItemId.IsEmpty() ? Guid(R.ItemId) : !R.StateId.IsEmpty() ? Guid(R.StateId) : FGuid(); return Json(T,Changed,R.bDryRun,Saved,Selected,Messages(Log),false,&Preview.ActualOrder);
}

void StateTreeUtils::Shutdown()
{
 if(UndoHandle.IsValid()) { FEditorDelegates::PostUndoRedo.Remove(UndoHandle); UndoHandle.Reset(); }
 Tracked.Reset();
}
