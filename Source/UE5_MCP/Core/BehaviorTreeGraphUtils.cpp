#include "BehaviorTreeGraphUtils.h"
#include "NavigationWorldUtils.h"
#include "UE5_MCP/API/DTO/BehaviorTreeRuntimeReq.h"
#include "BehaviorTree/BehaviorTreeComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "UObject/UObjectIterator.h"
#include "UE5_MCP/API/DTO/BehaviorTreeGraphReq.h"
#include "BehaviorTreeGraph.h"
#include "BehaviorTreeGraphNode.h"
#include "BehaviorTreeGraphNode_Root.h"
#include "BehaviorTreeGraphNode_Composite.h"
#include "BehaviorTreeGraphNode_SimpleParallel.h"
#include "BehaviorTreeGraphNode_Task.h"
#include "BehaviorTreeGraphNode_SubtreeTask.h"
#include "BehaviorTreeGraphNode_CompositeDecorator.h"
#include "BehaviorTreeDecoratorGraph.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "BehaviorTreeGraphNode_Service.h"
#include "BehaviorTreeGraphNode_Decorator.h"
#include "EdGraphSchema_BehaviorTree.h"
#include "BehaviorTree/BehaviorTree.h"
#include "BehaviorTree/BTCompositeNode.h"
#include "BehaviorTree/BTTaskNode.h"
#include "BehaviorTree/BTService.h"
#include "BehaviorTree/BTDecorator.h"
#include "BehaviorTree/Composites/BTComposite_SimpleParallel.h"
#include "BehaviorTree/Tasks/BTTask_RunBehavior.h"
#include "BehaviorTree/Tasks/BTTask_RunBehaviorDynamic.h"
#include "GameplayTagsManager.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/ValueOrBBKey.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Editor.h"
#include "ScopedTransaction.h"
#include "Misc/PackageName.h"
#include "Misc/StringOutputDevice.h"
#include "Engine/Blueprint.h"
#include "Serialization/JsonWriter.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "UObject/Package.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UnrealType.h"
#include <stdexcept>

namespace
{
 UBehaviorTree* Load(const FString& Path)
 {
  const FString P=FPackageName::ObjectPathToPackageName(Path); if(!FPackageName::IsValidLongPackageName(P)) throw std::runtime_error("A valid Behavior Tree asset path is required");
  const FString O=Path.Contains(TEXT(".")) ? Path : P+TEXT(".")+FPackageName::GetLongPackageAssetName(P);
  auto* T=FindObject<UBehaviorTree>(nullptr,*O);
  if(!T && FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(O)).IsValid()) T=LoadObject<UBehaviorTree>(nullptr,*O);
  if(!IsValid(T)) throw std::runtime_error("Asset is not an existing Behavior Tree"); return T;
 }
 FGuid ScopedGuid(const UEdGraphNode* N,const UBehaviorTreeGraphNode* Parent=nullptr)
 {
  if(!N) return FGuid(); const auto* BT=Cast<UBehaviorTreeGraphNode>(N);
  if(BT && BT->bInjectedNode)
  {
   if(!Parent) Parent=Cast<UBehaviorTreeGraphNode>(BT->ParentNode);
   if(!Parent) if(auto* G=BT->GetGraph()) for(UEdGraphNode* Top:G->Nodes) if(auto* P=Cast<UBehaviorTreeGraphNode>(Top)) if(P->SubNodes.Contains(BT)) { Parent=P; break; }
   if(Parent) return FGuid::Combine(Parent->NodeGuid,N->NodeGuid);
  }
  if(auto* G=N->GetGraph()) if(auto* Wrapper=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(G->GetOuter())) if(Wrapper->bInjectedNode) return FGuid::Combine(ScopedGuid(Wrapper),N->NodeGuid);
  return N->NodeGuid;
 }
 FString Id(const UEdGraphNode* N) { return N ? ScopedGuid(N).ToString(EGuidFormats::DigitsWithHyphens) : FString(); }
 struct FModel
 {
  UBehaviorTreeGraph* Graph=nullptr; UBehaviorTreeGraphNode_Root* Root=nullptr;
  TArray<UBehaviorTreeGraphNode*> Nodes; TMap<UBehaviorTreeGraphNode*,UBehaviorTreeGraphNode*> Parents;
 };
 FModel Model(UBehaviorTree* T,bool Require=false)
 {
  FModel M; M.Graph=Cast<UBehaviorTreeGraph>(T->BTGraph);
  if(!M.Graph) { if(Require) throw std::runtime_error("Initialize the native Behavior Tree graph first"); return M; }
  if(M.Graph->GetClass()!=UBehaviorTreeGraph::StaticClass() || !M.Graph->GetSchema() || M.Graph->GetSchema()->GetClass()!=UEdGraphSchema_BehaviorTree::StaticClass()) throw std::runtime_error("Custom Behavior Tree graph/schema adapters are separate");
  if(M.Graph->Nodes.Num()>512) throw std::runtime_error("Graph exceeds 512 top-level nodes");
  TSet<FGuid> Guids;
  TFunction<void(UBehaviorTreeGraphNode*,UBehaviorTreeGraphNode*)> Add=[&](UBehaviorTreeGraphNode* N,UBehaviorTreeGraphNode* Parent)
  {
   if(!N || M.Nodes.Contains(N) || N->GetGraph()!=M.Graph || !N->NodeGuid.IsValid() || Guids.Contains(ScopedGuid(N,Parent)) || M.Nodes.Num()>=512) throw std::runtime_error("Graph has invalid/repeated nodes, GUIDs or exceeds 512 nodes");
   M.Nodes.Add(N); Guids.Add(ScopedGuid(N,Parent)); if(Parent) M.Parents.Add(N,Parent);
   if(auto* R=Cast<UBehaviorTreeGraphNode_Root>(N)) { if(M.Root) throw std::runtime_error("Graph requires one root anchor"); M.Root=R; }
   for(UAIGraphNode* Sub:N->SubNodes) Add(Cast<UBehaviorTreeGraphNode>(Sub),N);
  };
  for(UEdGraphNode* N:M.Graph->Nodes) if(auto* BT=Cast<UBehaviorTreeGraphNode>(N)) Add(BT,nullptr);
  if(!M.Root) throw std::runtime_error("Graph has no root anchor");
  TSet<UBehaviorTreeGraphNode*> Done,Stack;
  TFunction<void(UBehaviorTreeGraphNode*,int32)> Visit=[&](UBehaviorTreeGraphNode* N,int32 Depth)
  {
   if(Stack.Contains(N) || Depth>64) throw std::runtime_error("Graph cycle or depth exceeding 64"); if(Done.Contains(N)) return; Stack.Add(N);
   for(auto* P:N->Pins)
   {
    if(!P || P->LinkedTo.Num()>512 || (P->Direction==EGPD_Input && P->LinkedTo.Num()>1)) throw std::runtime_error("Invalid pin or multiple parents");
    for(auto* L:P->LinkedTo)
    {
     auto* Other=L ? Cast<UBehaviorTreeGraphNode>(L->GetOwningNode()) : nullptr;
     if(!Other || !M.Nodes.Contains(Other) || !L->LinkedTo.Contains(P) || L->Direction==P->Direction) throw std::runtime_error("Graph has invalid/external/asymmetric links");
     if(P->Direction==EGPD_Output) Visit(Other,Depth+1);
    }
   } Stack.Remove(N); Done.Add(N);
  };
  for(auto* N:M.Nodes) Visit(N,0); return M;
 }
 UBehaviorTreeGraphNode* Find(const FModel& M,const FString& Value)
 {
  FGuid Guid; if(!FGuid::Parse(Value,Guid)) throw std::runtime_error("A valid node GUID is required");
  for(auto* N:M.Nodes) if(ScopedGuid(N)==Guid) return N; throw std::runtime_error("Node GUID does not belong to this Behavior Tree graph");
 }
 void EdgeDepth(const FModel& M,UEdGraphPin* A,UEdGraphPin* B,ECanCreateConnectionResponse Response)
 {
  const bool BreakA=Response==CONNECT_RESPONSE_BREAK_OTHERS_A || Response==CONNECT_RESPONSE_BREAK_OTHERS_AB;
  const bool BreakB=Response==CONNECT_RESPONSE_BREAK_OTHERS_B || Response==CONNECT_RESPONSE_BREAK_OTHERS_AB;
  TSet<UBehaviorTreeGraphNode*> Stack;
  TFunction<void(UBehaviorTreeGraphNode*,int32)> Visit=[&](UBehaviorTreeGraphNode* N,int32 Depth)
  {
   if(Depth>64 || Stack.Contains(N)) throw std::runtime_error("Proposed link causes a cycle or graph depth exceeding 64"); Stack.Add(N);
   for(auto* P:N->Pins) if(P->Direction==EGPD_Output)
   {
    for(auto* L:P->LinkedTo) if(!(P==A && BreakA) && !(L==B && BreakB)) Visit(CastChecked<UBehaviorTreeGraphNode>(L->GetOwningNode()),Depth+1);
    if(P==A) Visit(CastChecked<UBehaviorTreeGraphNode>(B->GetOwningNode()),Depth+1);
   } Stack.Remove(N);
  };
  for(auto* N:M.Nodes) if(!M.Parents.Contains(N)) Visit(N,0);
 }
 void Writable(UBehaviorTreeGraphNode* N)
 {
  if(!N || N->bIsReadOnly || N->bInjectedNode || N->IsA<UBehaviorTreeGraphNode_Root>()) throw std::runtime_error("Root/read-only/injected nodes cannot be edited through node operations");
 }
 void Blackboard(UBlackboardData* B)
 {
  TSet<UBlackboardData*> Seen; TSet<FName> Names; int32 Count=0;
  for(;B;B=B->Parent)
  {
   if(Seen.Contains(B) || Seen.Num()>=32) throw std::runtime_error("Blackboard parent cycle or depth exceeds 32"); Seen.Add(B);
   for(const auto& K:B->Keys) { if(!K.KeyType || K.EntryName.IsNone() || Names.Contains(K.EntryName) || ++Count>1024 || Count>=int32(FBlackboard::InvalidKey)) throw std::runtime_error("Blackboard has missing/duplicate keys/types or exceeds key capacity"); Names.Add(K.EntryName); }
  }
 }
 bool Plain(FProperty* P,int32 Depth=0)
 {
  if(Depth>8 || P->ArrayDim!=1) return false;
  if(CastField<FNumericProperty>(P) || CastField<FBoolProperty>(P) || CastField<FEnumProperty>(P) || CastField<FStrProperty>(P) || CastField<FNameProperty>(P) || CastField<FTextProperty>(P)) return true;
  if(auto* S=CastField<FStructProperty>(P)) { if(S->Struct==FBlackboardKeySelector::StaticStruct()) return false; for(TFieldIterator<FProperty> It(S->Struct);It;++It) if(!Plain(*It,Depth+1)) return false; return true; }
  return false;
 }
 bool Editable(FProperty* P) { return P && P->HasAnyPropertyFlags(CPF_Edit) && !P->HasAnyPropertyFlags(CPF_Transient|CPF_DisableEditOnInstance) && Plain(P); }
 FString Export(FProperty* P,UObject* O)
 {
  FString S; P->ExportText_InContainer(0,S,O,O,O,PPF_None); return S;
 }
 void Numeric(FProperty* P,const void* Value,const FProperty* Outer=nullptr)
 {
  if(auto* N=CastField<FNumericProperty>(P)) if(N->IsFloatingPoint() || N->IsInteger())
  {
   const double V=N->IsFloatingPoint() ? N->GetFloatingPointPropertyValue(Value) : double(N->GetSignedIntPropertyValue(Value));
   if(!FMath::IsFinite(V) || FMath::Abs(V)>1.e12) throw std::runtime_error("Numeric node settings must be finite and within +/-1e12");
   const auto* Range=P->HasMetaData(TEXT("ClampMin")) || P->HasMetaData(TEXT("ClampMax")) ? P : Outer;
   if(Range && ((Range->HasMetaData(TEXT("ClampMin")) && V<FCString::Atod(*Range->GetMetaData(TEXT("ClampMin")))) || (Range->HasMetaData(TEXT("ClampMax")) && V>FCString::Atod(*Range->GetMetaData(TEXT("ClampMax")))))) throw std::runtime_error("Node setting violates native ClampMin/ClampMax");
  }
  UEnum* Enum=nullptr; int64 EnumValue=0;
  if(auto* B=CastField<FByteProperty>(P)) { Enum=B->Enum; EnumValue=B->GetPropertyValue(Value); }
  else if(auto* E=CastField<FEnumProperty>(P)) { Enum=E->GetEnum(); EnumValue=E->GetUnderlyingProperty()->GetSignedIntPropertyValue(Value); }
  if(Enum && (!Enum->IsValidEnumValueOrBitfield(EnumValue) || (Enum->ContainsExistingMax() && Enum->GetIndexByValue(EnumValue)==Enum->NumEnums()-1))) throw std::runtime_error("Node enum setting requires a valid native member or flag combination, excluding generated MAX");
  if(auto* S=CastField<FStructProperty>(P)) for(TFieldIterator<FProperty> It(S->Struct);It;++It) Numeric(*It,It->ContainerPtrToValuePtr<void>(Value),It->GetFName()==TEXT("DefaultValue") ? P : nullptr);
 }
 void Select(FStructProperty* P,UObject* O,const FString& Name,UBlackboardData* B)
 {
  const FName Key(*Name);
  if(P->Struct==FBlackboardKeySelector::StaticStruct())
  {
   auto* S=P->ContainerPtrToValuePtr<FBlackboardKeySelector>(O); S->SelectedKeyName=Key; S->InvalidateResolvedKey();
   if(Key.IsNone()) { if(!S->IsNone()) throw std::runtime_error("This selector requires an explicit compatible Blackboard key"); S->SelectedKeyType=nullptr; return; }
   if(!B) throw std::runtime_error("A Blackboard is required for key selection");
   const auto Id=B->GetKeyID(Key); if(Id==FBlackboard::InvalidKey) throw std::runtime_error("Selected Blackboard key does not exist"); const auto* K=B->GetKey(Id);
   bool Allowed=S->AllowedTypes.IsEmpty(); for(UBlackboardKeyType* Filter:S->AllowedTypes) if(Filter && K->KeyType->IsAllowedByFilter(Filter)) Allowed=true;
   if(!Allowed) throw std::runtime_error("Selected Blackboard key is incompatible with native selector filters"); S->ResolveSelectedKey(*B);
  }
  else if(P->Struct->IsChildOf(FValueOrBlackboardKeyBase::StaticStruct()))
  {
   auto* V=P->ContainerPtrToValuePtr<FValueOrBlackboardKeyBase>(O);
   if(!Key.IsNone()) { if(!B) throw std::runtime_error("A Blackboard is required for bound values"); const auto Id=B->GetKeyID(Key); if(Id==FBlackboard::InvalidKey || !V->IsCompatibleType(B->GetKey(Id)->KeyType)) throw std::runtime_error("Bound Blackboard key is missing or incompatible with native value binding"); }
   V->SetKey(Key);
  }
  else throw std::runtime_error("BlackboardSelectors require a native selector or ValueOrBBKey struct property");
 }
 void ValidateSelectors(UObject* O,UBlackboardData* B)
 {
  for(TFieldIterator<FStructProperty> It(O->GetClass());It;++It)
  {
   if(It->Struct==FBlackboardKeySelector::StaticStruct())
   {
    auto* S=It->ContainerPtrToValuePtr<FBlackboardKeySelector>(O);
    Select(*It,O,S->SelectedKeyName.ToString(),B);
   }
   else if(It->Struct->IsChildOf(FValueOrBlackboardKeyBase::StaticStruct())) Select(*It,O,It->ContainerPtrToValuePtr<FValueOrBlackboardKeyBase>(O)->GetKey().ToString(),B);
  }
 }
 UBehaviorTree* Subtree(UBTNode* Node)
 {
  if(auto* Run=Cast<UBTTask_RunBehavior>(Node)) return Run->GetSubtreeAsset();
  if(auto* Run=Cast<UBTTask_RunBehaviorDynamic>(Node)) return Run->GetDefaultBehaviorAsset();
  return nullptr;
 }
 void SubtreeReference(UBTNode* Node,UBehaviorTree* Value)
 {
  const bool Dynamic=Node->IsA<UBTTask_RunBehaviorDynamic>();
  if(!Dynamic && !Node->IsA<UBTTask_RunBehavior>()) throw std::runtime_error("bSetSubtree requires a native RunBehavior or RunBehaviorDynamic task");
  auto* P=FindFProperty<FObjectProperty>(Node->GetClass(),Dynamic ? TEXT("DefaultBehaviorAsset") : TEXT("BehaviorAsset"));
  if(!P) throw std::runtime_error("Native subtree asset property is unavailable"); P->SetObjectPropertyValue_InContainer(Node,Value);
 }
 void InjectionTag(UBTNode* Node,const FString& Name)
 {
  if(!Node->IsA<UBTTask_RunBehaviorDynamic>() || Name.Len()>256) throw std::runtime_error("InjectionTag requires a RunBehaviorDynamic task and <=256 characters");
  const FGameplayTag Tag=Name.IsEmpty() ? FGameplayTag() : UGameplayTagsManager::Get().RequestGameplayTag(FName(*Name),false);
  if(!Name.IsEmpty() && !Tag.IsValid()) throw std::runtime_error("InjectionTag must be a registered Gameplay Tag");
  auto* P=FindFProperty<FStructProperty>(Node->GetClass(),TEXT("InjectionTag"));
  if(!P || P->Struct!=FGameplayTag::StaticStruct()) throw std::runtime_error("Native InjectionTag property is unavailable"); *P->ContainerPtrToValuePtr<FGameplayTag>(Node)=Tag;
 }
 bool Compatible(UBlackboardData* Parent,UBlackboardData* Child)
 {
  if(!Child) return true; if(!Parent) return false; Blackboard(Parent); Blackboard(Child);
  // The native predicate is pure once the diagnostic component has an asset.
  TStrongObjectPtr<UBlackboardComponent> C(NewObject<UBlackboardComponent>());
  auto* P=FindFProperty<FObjectProperty>(UBlackboardComponent::StaticClass(),TEXT("BlackboardAsset"));
  if(!P) throw std::runtime_error("Native Blackboard compatibility property is unavailable"); P->SetObjectPropertyValue_InContainer(C.Get(),Parent);
  if(!C->IsCompatibleWith(Child)) return false;
  // Native local-key equality can accept layouts with different inherited IDs.
  // Require the selected child keys to address the same runtime entries.
  for(int32 I=0;I<Child->GetNumKeys();++I)
  {
   const auto* K=Child->GetKey(FBlackboard::FKey(I)); const auto Id=Parent->GetKeyID(K->EntryName);
   if(Id!=FBlackboard::FKey(I) || !Parent->GetKey(Id)->KeyType || Parent->GetKey(Id)->KeyType->GetClass()!=K->KeyType->GetClass() || !Parent->GetKey(Id)->KeyType->IsAllowedByFilter(K->KeyType)) return false;
  } return true;
 }
 TStrongObjectPtr<UBTNode> Prepare(UBTNode* Source,UBehaviorTree* Tree,const FBehaviorTreeGraphReq& R)
 {
  if(R.Properties.Num()>64 || R.BlackboardSelectors.Num()>32) throw std::runtime_error("At most 64 scalar/struct properties and 32 selectors per request");
  TStrongObjectPtr<UBTNode> P(DuplicateObject<UBTNode>(Source,GetTransientPackage())); P->InitializeFromAsset(*Tree);
  if(R.bSetSubtree) SubtreeReference(P.Get(),R.SubtreePath.IsEmpty() ? nullptr : Load(R.SubtreePath));
  if(R.bSetInjectionTag) InjectionTag(P.Get(),R.InjectionTag);
  for(const auto& Pair:R.Properties)
  {
   if(FName(*Pair.Key)==TEXT("InjectionTag") && P->IsA<UBTTask_RunBehaviorDynamic>()) throw std::runtime_error("Use bSetInjectionTag/InjectionTag for registered tag validation");
   auto* Field=FindFProperty<FProperty>(P->GetClass(),*Pair.Key);
   if(!Editable(Field) || Pair.Value.Len()>4096) throw std::runtime_error("Properties require top-level editable scalar/plain-struct fields and values <=4096; UObject/container/custom providers are separate");
   FStringOutputDevice Errors; auto* Address=Field->ContainerPtrToValuePtr<void>(P.Get()); const TCHAR* End=Field->ImportText_Direct(*Pair.Value,Address,P.Get(),PPF_None,&Errors);
   if(!End || !Errors.IsEmpty() || !FString(End).TrimStartAndEnd().IsEmpty()) throw std::runtime_error("Node property value failed native import"); Numeric(Field,Address);
  }
  for(const auto& Pair:R.BlackboardSelectors)
  {
   auto* Field=FindFProperty<FStructProperty>(P->GetClass(),*Pair.Key); if(!Field || !Field->HasAnyPropertyFlags(CPF_Edit) || Pair.Value.Len()>128) throw std::runtime_error("A native editable Blackboard selector/value-binding field is required"); Select(Field,P.Get(),Pair.Value,Tree->GetBlackboardAsset());
  }
  for(const auto& Pair:R.Properties) { FPropertyChangedEvent Event(FindFProperty<FProperty>(P->GetClass(),*Pair.Key),EPropertyChangeType::ValueSet); P->PostEditChangeProperty(Event); }
  for(const auto& Pair:R.BlackboardSelectors)
  {
   auto* Field=FindFProperty<FStructProperty>(P->GetClass(),*Pair.Key); auto* Member=Field->Struct==FBlackboardKeySelector::StaticStruct() ? FindFProperty<FProperty>(FBlackboardKeySelector::StaticStruct(),TEXT("SelectedKeyName")) : static_cast<FProperty*>(Field);
   FPropertyChangedEvent Event(Member,EPropertyChangeType::ValueSet); Event.MemberProperty=Field; P->PostEditChangeProperty(Event);
  }
  ValidateSelectors(P.Get(),Tree->GetBlackboardAsset()); return P;
 }
 void Apply(UBTNode* Target,UBTNode* Prepared,UBehaviorTree* T,const FBehaviorTreeGraphReq& R)
 {
  if(R.bSetSubtree) SubtreeReference(Target,Subtree(Prepared));
  if(R.bSetInjectionTag) InjectionTag(Target,R.InjectionTag);
  for(const auto& Pair:R.Properties) FindFProperty<FProperty>(Target->GetClass(),*Pair.Key)->CopyCompleteValue_InContainer(Target,Prepared);
  for(const auto& Pair:R.BlackboardSelectors) Select(FindFProperty<FStructProperty>(Target->GetClass(),*Pair.Key),Target,Pair.Value,T->GetBlackboardAsset());
  Target->InitializeFromAsset(*T);
  for(const auto& Pair:R.Properties) { FPropertyChangedEvent Event(FindFProperty<FProperty>(Target->GetClass(),*Pair.Key),EPropertyChangeType::ValueSet); Target->PostEditChangeProperty(Event); }
  for(const auto& Pair:R.BlackboardSelectors)
  {
   auto* Field=FindFProperty<FStructProperty>(Target->GetClass(),*Pair.Key); auto* Member=Field->Struct==FBlackboardKeySelector::StaticStruct() ? FindFProperty<FProperty>(FBlackboardKeySelector::StaticStruct(),TEXT("SelectedKeyName")) : static_cast<FProperty*>(Field);
   FPropertyChangedEvent Event(Member,EPropertyChangeType::ValueSet); Event.MemberProperty=Field; Target->PostEditChangeProperty(Event);
  }
 }
 UClass* GraphClass(UClass* C)
 {
  if(C->IsChildOf(UBTComposite_SimpleParallel::StaticClass())) return UBehaviorTreeGraphNode_SimpleParallel::StaticClass();
  if(C->IsChildOf(UBTTask_RunBehavior::StaticClass())) return UBehaviorTreeGraphNode_SubtreeTask::StaticClass();
  if(C->IsChildOf(UBTCompositeNode::StaticClass())) return UBehaviorTreeGraphNode_Composite::StaticClass();
  if(C->IsChildOf(UBTTaskNode::StaticClass())) return UBehaviorTreeGraphNode_Task::StaticClass();
  if(C->IsChildOf(UBTService::StaticClass())) return UBehaviorTreeGraphNode_Service::StaticClass();
  if(C->IsChildOf(UBTDecorator::StaticClass())) return UBehaviorTreeGraphNode_Decorator::StaticClass();
  throw std::runtime_error("Class requires a concrete Behavior Tree composite, task, service or decorator");
 }
 TArray<UBTNode*> RuntimeNodes(UBehaviorTree* T)
 {
  TArray<UBTNode*> Nodes;
  auto Add=[&](UBTNode* N) { if(!N || !N->IsIn(T) || Nodes.Contains(N) || Nodes.Num()>=511) throw std::runtime_error("Runtime tree contains missing/shared/foreign nodes or exceeds graph initialization capacity"); Nodes.Add(N); };
  TFunction<void(UBTCompositeNode*,int32)> Visit=[&](UBTCompositeNode* C,int32 Depth)
  {
   if(Depth>63) throw std::runtime_error("Runtime tree exceeds graph initialization depth"); Add(C); for(UBTService* Service:C->Services) Add(Service);
   for(const auto& Child:C->Children)
   {
    for(UBTDecorator* D:Child.Decorators) Add(D);
    if(bool(Child.ChildComposite)==bool(Child.ChildTask)) throw std::runtime_error("Runtime children require exactly one composite or task");
    if(Child.ChildComposite) Visit(Child.ChildComposite,Depth+1);
    else { Add(Child.ChildTask); for(UBTService* Service:Child.ChildTask->Services) Add(Service); }
   }
  };
  for(UBTDecorator* D:T->RootDecorators) Add(D); if(T->RootNode) Visit(T->RootNode,0); return Nodes;
 }
 void Inject(UBehaviorTreeGraph* G)
 {
  // Native preview duplication temporarily moves source decorators. Keep those
  // reversible copy operations out of the parent's transaction history.
  TGuardValue<ITransaction*> CopyGuard(GUndo,nullptr);
  // Native cache identity uses only the asset's short name. Force refresh so
  // equal-named assets in different packages cannot reuse stale previews.
  struct FSourceName { UBTDecorator* Instance; UObject* Outer; FName Name; };
  TArray<FSourceName> SourceNames; TSet<UBTDecorator*> Seen;
  for(UEdGraphNode* N:G->Nodes) if(auto* Run=Cast<UBehaviorTreeGraphNode_SubtreeTask>(N))
  {
   if(auto* Task=Cast<UBTTask_RunBehavior>(Run->NodeInstance)) if(auto* Source=Task->GetSubtreeAsset()) for(UBTDecorator* Leaf:Source->RootDecorators) if(Leaf && !Seen.Contains(Leaf)) { Seen.Add(Leaf); SourceNames.Add({Leaf,Leaf->GetOuter(),Leaf->GetFName()}); }
   Run->SubtreePath.Empty(); Run->SubtreeVersion=MIN_int32;
  }
  G->UpdateInjectedNodes();
  // Native compound PostCopyNode restores ownership with generated names. Keep
  // referenced source object identities stable after the temporary copy moves.
  for(const auto& Entry:SourceNames) if(Entry.Instance->GetOuter()!=Entry.Outer || Entry.Instance->GetFName()!=Entry.Name) Entry.Instance->Rename(*Entry.Name.ToString(),Entry.Outer,REN_DontCreateRedirectors|REN_DoNotDirty|REN_NonTransactional);
 }
 struct FCompoundData { TArray<UBTDecorator*> Tests; TArray<FBTDecoratorLogic> Ops; };
 UBTDecorator* InnerInstance(UEdGraphNode* N)
 {
  auto* P=FindFProperty<FObjectProperty>(N->GetClass(),TEXT("NodeInstance")); return P ? Cast<UBTDecorator>(P->GetObjectPropertyValue_InContainer(N)) : nullptr;
 }
 FCompoundData Compound(UBehaviorTreeGraphNode_CompositeDecorator* C,UBehaviorTree* T)
 {
  auto* G=Cast<UBehaviorTreeDecoratorGraph>(C->BoundGraph);
  if(!G || G->GetClass()!=UBehaviorTreeDecoratorGraph::StaticClass() || G->Nodes.Num()<2 || G->Nodes.Num()>128) throw std::runtime_error("Compound graph requires 2-128 native inner nodes");
  UEdGraphNode* Sink=nullptr; TSet<UEdGraphNode*> Seen,Stack; TSet<FGuid> Guids;
  for(UEdGraphNode* N:G->Nodes)
  {
   if(!N || N->GetGraph()!=G || !N->NodeGuid.IsValid() || Guids.Contains(N->NodeGuid)) throw std::runtime_error("Invalid compound node ownership/GUID"); Guids.Add(N->NodeGuid);
   if(auto* P=FindFProperty<FByteProperty>(N->GetClass(),TEXT("LogicMode"))) if(P->GetPropertyValue_InContainer(N)==0) { if(Sink) throw std::runtime_error("Compound graph has multiple result sinks"); Sink=N; }
  }
  if(!Sink) throw std::runtime_error("Compound graph requires one result sink");
  TFunction<void(UEdGraphNode*,int32)> Visit=[&](UEdGraphNode* N,int32 Depth)
  {
   if(Depth>17 || Stack.Contains(N) || Seen.Contains(N)) throw std::runtime_error("Compound logic must be a tree with depth at most 16"); Stack.Add(N); Seen.Add(N);
   int32 Inputs=0,Outputs=0;
   for(auto* P:N->Pins)
   {
    if(!P) throw std::runtime_error("Invalid compound pin");
    if(P->Direction==EGPD_Input) { ++Inputs; if(P->LinkedTo.Num()!=1) throw std::runtime_error("Every compound input requires one condition"); }
    else { ++Outputs; if(N!=Sink && P->LinkedTo.Num()!=1) throw std::runtime_error("Compound conditions require one parent"); }
    for(auto* L:P->LinkedTo) if(!L || !G->Nodes.Contains(L->GetOwningNode()) || !L->LinkedTo.Contains(P) || L->Direction==P->Direction) throw std::runtime_error("Invalid/external compound link");
    if(P->Direction==EGPD_Input) Visit(P->LinkedTo[0]->GetOwningNode(),Depth+1);
   }
   if(auto* I=InnerInstance(N)) { if(Inputs!=0 || Outputs!=1 || !I->IsIn(T)) throw std::runtime_error("Invalid compound test instance/pins"); }
   else
   {
    auto* P=FindFProperty<FByteProperty>(N->GetClass(),TEXT("LogicMode")); const int32 Mode=P ? P->GetPropertyValue_InContainer(N) : -1;
    if(Mode<0 || Mode>3 || (Mode==0 && (N!=Sink || Inputs!=1 || Outputs!=0)) || (Mode==3 && Inputs!=1) || ((Mode==1 || Mode==2) && (Inputs<2 || Inputs>16))) throw std::runtime_error("Invalid native compound logic arity");
   }
   Stack.Remove(N);
  };
  Visit(Sink,0); if(Seen.Num()!=G->Nodes.Num()) throw std::runtime_error("Compound graph contains disconnected inner nodes");
  FCompoundData D; C->CollectDecoratorData(D.Tests,D.Ops);
  if(D.Tests.IsEmpty() || D.Tests.Num()>64 || D.Ops.IsEmpty() || D.Ops.Num()>127) throw std::runtime_error("Compound graph exceeds bounded test/operation capacity");
  return D;
 }
 void Dependencies(UBehaviorTree* Owner,UBTNode* Replace=nullptr,UBTNode* Candidate=nullptr,bool Replacing=false,UBlackboardData* OverrideBoard=nullptr,bool SetBoard=false)
 {
  TSet<UBehaviorTree*> Active,Visited; int32 References=0;
  TFunction<void(UBehaviorTree*,int32)> Visit=[&](UBehaviorTree* T,int32 Depth)
  {
   if(Active.Contains(T) || Depth>32 || Visited.Num()>=256 || ++References>1024) throw std::runtime_error("Subtree cycle or dependency capacity/depth exceeded");
   Active.Add(T); auto M=Model(T); TArray<UBTNode*> Nodes;
   if(M.Graph) { for(auto* N:M.Nodes) if(auto* I=Cast<UBTNode>(N->NodeInstance)) if(!N->bInjectedNode) Nodes.Add(I); }
   else Nodes=RuntimeNodes(T);
   if(T==Owner && Replacing) { Nodes.Remove(Replace); if(Candidate) Nodes.Add(Candidate); }
   auto* ParentBoard=T==Owner && SetBoard ? OverrideBoard : T->GetBlackboardAsset(); Blackboard(ParentBoard);
   for(auto* I:Nodes) if(auto* Child=Subtree(I))
   {
    if(!Child->IsAsset() || Child->HasAnyFlags(RF_Transient)) throw std::runtime_error("Subtree references require persistent Behavior Tree assets");
    if(!Child->RootNode) throw std::runtime_error("Referenced subtree requires a compiled composite root");
    if(I->IsA<UBTTask_RunBehaviorDynamic>() && Child->RootDecorators.Num()) throw std::runtime_error("Dynamic subtrees cannot use root decorators; native execution ignores them");
    if(!Compatible(ParentBoard,Child->GetBlackboardAsset())) throw std::runtime_error("Referenced subtree Blackboard is incompatible or key IDs differ");
    for(auto* N:RuntimeNodes(Child))
    {
     if(auto* RunNode=Cast<UBTTask_RunBehavior>(N)) if(!RunNode->GetSubtreeAsset()) throw std::runtime_error("Referenced subtree contains an unconfigured RunBehavior task");
     if(auto* Dynamic=Cast<UBTTask_RunBehaviorDynamic>(N)) if(!Dynamic->GetInjectionTag().IsValid() || !UGameplayTagsManager::Get().RequestGameplayTag(Dynamic->GetInjectionTag().GetTagName(),false).IsValid()) throw std::runtime_error("Referenced dynamic tasks require registered injection tags");
     if(auto* Parallel=Cast<UBTComposite_SimpleParallel>(N)) if(Parallel->Children.Num()!=2 || !Parallel->Children[0].ChildTask || (Parallel->FinishMode!=EBTParallelMode::AbortBackground && Parallel->FinishMode!=EBTParallelMode::WaitForBackground)) throw std::runtime_error("Referenced subtree has incomplete parallel roles or finish mode");
     TStrongObjectPtr<UBTNode> Probe(DuplicateObject<UBTNode>(N,GetTransientPackage())); ValidateSelectors(Probe.Get(),Child->GetBlackboardAsset());
    }
    auto CM=Model(Child);
    if(Child->RootDecorators.Num()>0)
    {
     if(!CM.Graph) throw std::runtime_error("Initialize the referenced subtree graph before root-decorator injection");
     auto* Pin=CM.Root->GetOutputPin(); auto* Root=Pin && Pin->LinkedTo.Num()==1 ? Cast<UBehaviorTreeGraphNode>(Pin->LinkedTo[0]->GetOwningNode()) : nullptr;
     if(!Root || Root->NodeInstance!=Child->RootNode) throw std::runtime_error("Referenced root decorator graph/runtime data requires compile");
     TArray<UBTDecorator*> Tests; TArray<FBTDecoratorLogic> Ops; int32 Groups=0; bool HasCompound=false;
     for(UBehaviorTreeGraphNode* D:Root->Decorators)
     {
      if(!D || D->bInjectedNode) throw std::runtime_error("Invalid referenced root decorator"); ++Groups;
      if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(D))
      {
       const auto Data=Compound(C,Child); const int32 Offset=Tests.Num(); HasCompound=true; Tests.Append(Data.Tests);
       for(auto Op:Data.Ops) { if(Op.Operation==EBTDecoratorLogic::Test) Op.Number+=Offset; Ops.Add(Op); }
      }
      else { auto* Leaf=Cast<UBTDecorator>(D->NodeInstance); if(!Leaf || !Leaf->IsIn(Child)) throw std::runtime_error("Invalid referenced root decorator instance"); Ops.Add(FBTDecoratorLogic(EBTDecoratorLogic::Test,uint16(Tests.Num()))); Tests.Add(Leaf); }
     }
     if(HasCompound && Groups>1) Ops.Insert(FBTDecoratorLogic(EBTDecoratorLogic::And,uint16(Groups)),0); else if(!HasCompound) Ops.Reset();
     if(Tests.Num()!=Child->RootDecorators.Num() || Ops.Num()!=Child->RootDecoratorOps.Num()) throw std::runtime_error("Referenced root decorator graph/runtime data requires compile");
     for(int32 Index=0;Index<Tests.Num();++Index) if(Tests[Index]!=Child->RootDecorators[Index]) throw std::runtime_error("Referenced root decorator instances require compile");
     for(int32 Index=0;Index<Ops.Num();++Index) if(Ops[Index].Operation!=Child->RootDecoratorOps[Index].Operation || Ops[Index].Number!=Child->RootDecoratorOps[Index].Number) throw std::runtime_error("Referenced root decorator operations require compile");
    }
    Visit(Child,Depth+1);
   }
   Active.Remove(T); Visited.Add(T);
  };
  Visit(Owner,0);
  auto M=Model(Owner); int32 OuterCount=0,EditorCount=0,RuntimeCount=0;
  auto AddSubtree=[&](UBTNode* Instance)
  {
   if(auto* Run=Cast<UBTTask_RunBehavior>(Instance)) if(auto* Child=Run->GetSubtreeAsset())
   {
    RuntimeCount+=Child->RootDecorators.Num(); auto CM=Model(Child);
    if(CM.Graph && Child->RootDecorators.Num())
    {
     auto* Root=CastChecked<UBehaviorTreeGraphNode>(CM.Root->GetOutputPin()->LinkedTo[0]->GetOwningNode());
     OuterCount+=Root->Decorators.Num(); EditorCount+=Root->Decorators.Num();
     for(UBehaviorTreeGraphNode* D:Root->Decorators) if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(D)) EditorCount+=C->BoundGraph->Nodes.Num();
    }
   }
  };
  for(auto* N:M.Nodes) if(!N->bInjectedNode)
  {
   ++OuterCount; ++EditorCount;
   if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(N)) { const auto Data=Compound(C,Owner); EditorCount+=C->BoundGraph->Nodes.Num(); RuntimeCount+=Data.Tests.Num(); }
   else
   {
    UBTNode* Instance=Cast<UBTNode>(N->NodeInstance); if(Replacing && Replace && Instance==Replace) Instance=Candidate;
    if(Instance) { ++RuntimeCount; AddSubtree(Instance); }
   }
  }
  if(Replacing && !Replace && Candidate) { ++OuterCount; ++EditorCount; ++RuntimeCount; AddSubtree(Candidate); }
  if(OuterCount>512 || EditorCount>1024 || RuntimeCount>511) throw std::runtime_error("Subtree injection exceeds parent outer/editor/runtime node capacity");
 }
 struct FDynamicTask
 {
  UBTTask_RunBehaviorDynamic* Template=nullptr; UBTTask_RunBehaviorDynamic* Instance=nullptr;
  UBTCompositeNode* Root=nullptr; int32 Index=0; UBehaviorTree* Current=nullptr;
 };
 TArray<FDynamicTask> DynamicTasks(UBehaviorTreeComponent* C)
 {
  TArray<FDynamicTask> Tasks;
  C->ForEachChildTask([&](UBTTaskNode& Task,const FBehaviorTreeInstance& Info,int32 Index)
  {
   if(auto* D=Cast<UBTTask_RunBehaviorDynamic>(&Task))
   {
    if(Tasks.Num()>=512) throw std::runtime_error("Live dynamic task inspection exceeds 512 instances");
    auto* Memory=const_cast<uint8*>(D->GetNodeMemory<uint8>(Info)); auto* Instance=Cast<UBTTask_RunBehaviorDynamic>(D->GetNodeInstance(*C,Memory));
    if(!Instance) throw std::runtime_error("Dynamic task has no native node instance");
    auto* P=FindFProperty<FObjectProperty>(Instance->GetClass(),TEXT("BehaviorAsset")); if(!P) throw std::runtime_error("Native runtime BehaviorAsset property unavailable");
    Tasks.Add({D,Instance,Info.RootNode,Index,Cast<UBehaviorTree>(P->GetObjectPropertyValue_InContainer(Instance))});
   }
  }); return Tasks;
 }
 void RuntimeDependencies(UBehaviorTreeComponent* C,const TArray<FDynamicTask>& Tasks,FGameplayTag Tag,UBehaviorTree* Candidate)
 {
  auto* BB=C->GetBlackboardComponent(); auto* Board=BB ? const_cast<UBlackboardData*>(BB->GetBlackboardAsset()) : nullptr;
  if(BB && !BB->HasBeenInitialized()) throw std::runtime_error("Existing runtime Blackboard component must be initialized");
  TMap<UBehaviorTree*,UBTCompositeNode*> Roots; TMap<UBTTask_RunBehaviorDynamic*,UBehaviorTree*> Effective;
  for(const auto& T:Tasks)
  {
   auto* Asset=T.Template->GetTreeAsset(); if(!Asset || !T.Root) throw std::runtime_error("Live task has no source tree/root"); Roots.Add(Asset,T.Root);
   auto* Value=T.Template->HasMatchingTag(Tag) ? Candidate : T.Current;
   if(Effective.Contains(T.Template) && Effective[T.Template]!=Value) throw std::runtime_error("Ambiguous current overrides for a shared runtime template"); Effective.Add(T.Template,Value);
  }
  TSet<UBehaviorTree*> Active,Validated; int32 Visits=0;
  TFunction<void(UBehaviorTree*,int32,bool)> Visit=[&](UBehaviorTree* Tree,int32 Depth,bool Dynamic)
  {
   if(!Tree) return;
   if(Depth>32 || ++Visits>1024 || Validated.Num()>=256 || Active.Contains(Tree)) throw std::runtime_error("Effective runtime subtree cycle or dependency capacity/depth exceeded");
   if(!Tree->IsAsset() || !Tree->RootNode || Tree->HasAnyFlags(RF_Transient)) throw std::runtime_error("Runtime replacement requires persistent compiled Behavior Tree assets");
   if(Dynamic && Tree->RootDecorators.Num()) throw std::runtime_error("Dynamic subtrees cannot use ignored root decorators");
   if(!Compatible(Board,Tree->GetBlackboardAsset())) throw std::runtime_error("Replacement Blackboard/key IDs are incompatible with the live component");
   if(!Validated.Contains(Tree))
   {
    Dependencies(Tree);
    for(auto* Node:RuntimeNodes(Tree))
    {
     TStrongObjectPtr<UBTNode> Probe(DuplicateObject<UBTNode>(Node,GetTransientPackage())); ValidateSelectors(Probe.Get(),Board);
     if(auto* Static=Cast<UBTTask_RunBehavior>(Node)) if(!Static->GetSubtreeAsset()) throw std::runtime_error("Runtime candidate contains an unconfigured static subtree task");
     if(auto* DynamicTask=Cast<UBTTask_RunBehaviorDynamic>(Node)) if(!DynamicTask->GetInjectionTag().IsValid() || !UGameplayTagsManager::Get().RequestGameplayTag(DynamicTask->GetInjectionTag().GetTagName(),false).IsValid()) throw std::runtime_error("Runtime candidate contains an unregistered dynamic injection tag");
     if(auto* Parallel=Cast<UBTComposite_SimpleParallel>(Node)) if(Parallel->Children.Num()!=2 || !Parallel->Children[0].ChildTask || (Parallel->FinishMode!=EBTParallelMode::AbortBackground && Parallel->FinishMode!=EBTParallelMode::WaitForBackground) || Parallel->Children[0].ChildTask->IsA<UBTTask_RunBehavior>() || Parallel->Children[0].ChildTask->IsA<UBTTask_RunBehaviorDynamic>()) throw std::runtime_error("Runtime candidate contains invalid SimpleParallel roles or finish mode");
    }
    Validated.Add(Tree);
   }
   Active.Add(Tree); auto* Root=Roots.Contains(Tree) ? Roots[Tree] : Tree->RootNode.Get();
   TSet<UBTNode*> Seen;
   TFunction<void(UBTCompositeNode*,int32)> Walk=[&](UBTCompositeNode* Node,int32 NodeDepth)
   {
    if(!Node || NodeDepth>64 || Seen.Contains(Node) || Seen.Num()>=511) throw std::runtime_error("Invalid live/candidate composite topology"); Seen.Add(Node);
    for(const auto& Child:Node->Children)
    {
     if(bool(Child.ChildComposite)==bool(Child.ChildTask)) throw std::runtime_error("Invalid live/candidate child role");
     if(Child.ChildComposite) Walk(Child.ChildComposite,NodeDepth+1);
     else
     {
      auto* Task=Child.ChildTask.Get(); if(Seen.Contains(Task) || Seen.Num()>=511) throw std::runtime_error("Repeated live task or runtime node capacity exceeded"); Seen.Add(Task);
      if(auto* D=Cast<UBTTask_RunBehaviorDynamic>(Task)) Visit(Effective.Contains(D) ? Effective[D] : D->GetDefaultBehaviorAsset(),Depth+1,true);
      else if(auto* S=Cast<UBTTask_RunBehavior>(Task)) Visit(S->GetSubtreeAsset(),Depth+1,false);
     }
    }
   }; Walk(Root,0); Active.Remove(Tree);
  };
  Visit(C->GetRootTree(),0,false);
  // Tasks on active descendant stacks can be replaced before their caller exits.
  for(const auto& T:Tasks) if(T.Template->HasMatchingTag(Tag)) Visit(T.Template->GetTreeAsset(),0,false);
 }
 void RuntimeJson(TSharedRef<TJsonWriter<>> J,UBehaviorTreeComponent* C)
 {
  const auto Tasks=DynamicTasks(C);
  J->WriteObjectStart(); J->WriteValue(TEXT("component_path"),C->GetPathName()); J->WriteValue(TEXT("owner_path"),C->GetOwner() ? C->GetOwner()->GetPathName() : FString());
  J->WriteValue(TEXT("authority"),C->GetOwner() && C->GetOwner()->HasAuthority()); J->WriteValue(TEXT("running"),C->IsRunning()); J->WriteValue(TEXT("paused"),C->IsPaused());
  J->WriteValue(TEXT("root_asset_path"),C->GetRootTree() ? C->GetRootTree()->GetPathName() : FString()); J->WriteValue(TEXT("current_asset_path"),C->GetCurrentTree() ? C->GetCurrentTree()->GetPathName() : FString());
  J->WriteArrayStart(TEXT("dynamic_tasks")); for(const auto& T:Tasks)
  {
   J->WriteObjectStart(); J->WriteValue(TEXT("template_path"),T.Template->GetPathName()); J->WriteValue(TEXT("instance_path"),T.Instance->GetPathName()); J->WriteValue(TEXT("instance_index"),T.Index); J->WriteValue(TEXT("execution_index"),int32(T.Template->GetExecutionIndex())); J->WriteValue(TEXT("injection_tag"),T.Template->GetInjectionTag().ToString());
   J->WriteValue(TEXT("default_asset_path"),T.Template->GetDefaultBehaviorAsset() ? T.Template->GetDefaultBehaviorAsset()->GetPathName() : FString()); J->WriteValue(TEXT("current_asset_path"),T.Current ? T.Current->GetPathName() : FString()); J->WriteObjectEnd();
  } J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 UBehaviorTreeComponent* LiveComponent(const FString& Path,int32 PIEInstance)
 {
  auto* W=NavigationWorldUtils::Resolve(TEXT("pie"),PIEInstance);
  if(Path.IsEmpty() || Path.Len()>2048) throw std::runtime_error("An explicit live ComponentPath is required");
  auto* C=FindObject<UBehaviorTreeComponent>(nullptr,*Path);
  if(!IsValid(C) || C->IsTemplate() || C->GetWorld()!=W || !C->IsRegistered()) throw std::runtime_error("ComponentPath must identify a registered component in the selected PIE world"); return C;
 }
 struct FExpression
 {
  TArray<TStrongObjectPtr<UBTNode>> Tests; TArray<FBehaviorTreeGraphReq> Settings; TArray<FBTDecoratorLogic> Ops;
 };
 FExpression Expression(UBehaviorTree* T,const FBehaviorTreeGraphReq& R)
 {
  if(R.Logic.IsEmpty() || R.Logic.Num()>127 || R.CompoundName.Len()>128) throw std::runtime_error("Logic requires 1-127 prefix rows and a name <=128 characters");
  FExpression E; int32 Cursor=0;
  TFunction<void(int32)> Parse=[&](int32 Depth)
  {
   if(Depth>16 || !R.Logic.IsValidIndex(Cursor)) throw std::runtime_error("Invalid compound prefix/depth"); const auto& Row=R.Logic[Cursor++]; const FString Op=Row.Operation.ToLower();
   if(Op==TEXT("test"))
   {
    if(Row.Children!=0 || Row.ClassPath.IsEmpty() || E.Tests.Num()>=64) throw std::runtime_error("Test rows require a decorator class, no children, and at most 64 tests");
    auto* Class=LoadClass<UBTDecorator>(nullptr,*Row.ClassPath); if(!Class || Class->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("Test class requires a concrete compatible decorator");
    if(auto* BP=Cast<UBlueprint>(Class->ClassGeneratedBy)) if(BP->GeneratedClass!=Class || BP->Status==BS_Error) throw std::runtime_error("Decorator Blueprint must be compiled");
    FBehaviorTreeGraphReq Settings; Settings.Properties=Row.Properties; Settings.BlackboardSelectors=Row.BlackboardSelectors;
    E.Ops.Add(FBTDecoratorLogic(EBTDecoratorLogic::Test,uint16(E.Tests.Num()))); E.Tests.Add(Prepare(Class->GetDefaultObject<UBTNode>(),T,Settings)); E.Settings.Add(Settings);
   }
   else
   {
    const auto Type=Op==TEXT("and") ? EBTDecoratorLogic::And : Op==TEXT("or") ? EBTDecoratorLogic::Or : Op==TEXT("not") ? EBTDecoratorLogic::Not : EBTDecoratorLogic::Invalid;
    if(Type==EBTDecoratorLogic::Invalid || (Type==EBTDecoratorLogic::Not ? Row.Children!=1 : Row.Children<2 || Row.Children>16) || !Row.ClassPath.IsEmpty() || !Row.Properties.IsEmpty() || !Row.BlackboardSelectors.IsEmpty()) throw std::runtime_error("Logic rows require AND/OR (2-16 children) or NOT (1), without decorator settings");
    E.Ops.Add(FBTDecoratorLogic(Type,uint16(Row.Children))); for(int32 I=0;I<Row.Children;++I) Parse(Depth+1);
   }
  };
  Parse(1); if(Cursor!=R.Logic.Num()) throw std::runtime_error("Compound expression has trailing prefix rows"); return E;
 }
 bool SameExpression(UBehaviorTreeGraphNode_CompositeDecorator* C,UBehaviorTree* T,const FExpression& E,const FBehaviorTreeGraphReq& R)
 {
  const auto D=Compound(C,T); if((R.bSetCompoundName && C->CompositeName!=R.CompoundName) || D.Ops.Num()!=E.Ops.Num() || D.Tests.Num()!=E.Tests.Num()) return false;
  for(int32 I=0;I<D.Ops.Num();++I) if(D.Ops[I].Operation!=E.Ops[I].Operation || D.Ops[I].Number!=E.Ops[I].Number) return false;
  for(int32 I=0;I<D.Tests.Num();++I)
  {
   if(D.Tests[I]->GetClass()!=E.Tests[I]->GetClass()) return false;
   for(TFieldIterator<FProperty> It(D.Tests[I]->GetClass());It;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient))
   {
    if(auto* P=CastField<FStructProperty>(*It); P && P->Struct==FBlackboardKeySelector::StaticStruct()) { if(P->ContainerPtrToValuePtr<FBlackboardKeySelector>(D.Tests[I])->SelectedKeyName!=P->ContainerPtrToValuePtr<FBlackboardKeySelector>(E.Tests[I].Get())->SelectedKeyName) return false; }
    else if(!It->Identical_InContainer(D.Tests[I],E.Tests[I].Get())) return false;
   }
  } return true;
 }
 void CompoundBudget(const FModel& M,UBehaviorTree* T,UBehaviorTreeGraphNode_CompositeDecorator* Replace,const FExpression& E)
 {
  int32 Editor=M.Nodes.Num(),Runtime=0;
  for(auto* N:M.Nodes)
  {
   if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(N)) { if(C!=Replace) { const auto D=Compound(C,T); Editor+=C->BoundGraph->Nodes.Num(); Runtime+=D.Tests.Num(); } }
   else if(N->NodeInstance) ++Runtime;
  }
  Editor+=E.Ops.Num()+1+(Replace ? 0 : 1); Runtime+=E.Tests.Num();
  if(Editor>1024 || Runtime>511) throw std::runtime_error("Compound expression exceeds total editor/runtime node capacity");
 }
 void Populate(UBehaviorTreeGraphNode_CompositeDecorator* C,UBehaviorTree* T,const FExpression& E)
 {
  TArray<UBTDecorator*> Tests;
  for(int32 I=0;I<E.Tests.Num();++I)
  {
   auto* Leaf=NewObject<UBTDecorator>(T,E.Tests[I]->GetClass(),NAME_None,RF_Transactional); Leaf->InitializeFromAsset(*T); Leaf->OnNodeCreated(); Apply(Leaf,E.Tests[I].Get(),T,E.Settings[I]); Tests.Add(Leaf);
  }
  if(C->SpawnMissingNodes(Tests,E.Ops,0)!=E.Ops.Num()) throw std::runtime_error("Native compound graph generation failed");
  for(UEdGraphNode* N:C->BoundGraph->Nodes) if(auto* I=InnerInstance(N)) if(auto* P=FindFProperty<FStructProperty>(N->GetClass(),TEXT("ClassData"))) UAIGraphNode::UpdateNodeClassDataFrom(I->GetClass(),*P->ContainerPtrToValuePtr<FGraphNodeClassData>(N));
  C->OnInnerGraphChanged(); C->OnBlackboardUpdate(); Compound(C,T);
 }
 void Transact(UBehaviorTree* T,const FModel& M)
 {
  T->SetFlags(RF_Transactional); T->Modify(); if(M.Graph) M.Graph->Modify();
  for(auto* N:M.Nodes) { if(N->bInjectedNode) continue; N->Modify(); if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(N)) for(auto* I:Compound(C,T).Tests) { I->SetFlags(RF_Transactional); I->Modify(); } if(N->NodeInstance) { N->NodeInstance->SetFlags(RF_Transactional); N->NodeInstance->Modify(); } }
 }
 TArray<FString> Errors(UBehaviorTree* T,const FModel& M)
 {
  TArray<FString> E; if(!M.Graph) return {TEXT("No editor graph; initialize it explicitly")};
  if(M.Root->BlackboardAsset!=T->GetBlackboardAsset()) E.Add(TEXT("Root anchor and compiled asset Blackboard references differ"));
  auto* Out=M.Root->GetOutputPin(); if(!Out || Out->LinkedTo.Num()!=1 || !Out->LinkedTo[0]->GetOwningNode()->IsA<UBehaviorTreeGraphNode_Composite>()) E.Add(TEXT("Root anchor must connect to one composite"));
  try { Blackboard(T->GetBlackboardAsset()); } catch(const std::exception& X) { E.Add(UTF8_TO_TCHAR(X.what())); return E; }
  TSet<UBehaviorTreeGraphNode*> Reachable;
  TFunction<void(UBehaviorTreeGraphNode*)> Visit=[&](UBehaviorTreeGraphNode* N) { if(Reachable.Contains(N)) return; Reachable.Add(N); for(auto* P:N->Pins) if(P->Direction==EGPD_Output) for(auto* L:P->LinkedTo) Visit(CastChecked<UBehaviorTreeGraphNode>(L->GetOwningNode())); };
  Visit(M.Root);
  if(Out && Out->LinkedTo.Num()==1 && T->RootNode!=Cast<UBehaviorTreeGraphNode>(Out->LinkedTo[0]->GetOwningNode())->NodeInstance) E.Add(TEXT("Compiled root differs from the graph; compile required"));
  for(auto* N:M.Nodes)
  {
   if(N==M.Root) continue;
   if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(N))
   {
    try { for(auto* I:Compound(C,T).Tests) { TStrongObjectPtr<UBTNode> P(DuplicateObject<UBTNode>(I,GetTransientPackage())); ValidateSelectors(P.Get(),T->GetBlackboardAsset()); } } catch(const std::exception& X) { E.Add(Id(N)+TEXT(": ")+UTF8_TO_TCHAR(X.what())); }
    continue;
   }
   auto* Node=Cast<UBTNode>(N->NodeInstance);
   if(!Node) { E.Add(Id(N)+TEXT(": missing native node instance")); continue; }
   if(!Node->IsIn(T)) E.Add(Id(N)+TEXT(": node instance belongs to another owner"));
   if(auto* Parallel=Cast<UBTComposite_SimpleParallel>(Node))
   {
    auto* Main=N->GetOutputPin(0); auto* Background=N->GetOutputPin(1);
    const bool MainValid=N->IsA<UBehaviorTreeGraphNode_SimpleParallel>() && Main && Main->LinkedTo.Num()==1 && Main->LinkedTo[0]->GetOwningNode()->IsA<UBehaviorTreeGraphNode_Task>();
    const bool BackgroundValid=Background && Background->LinkedTo.Num()==1;
    if(!MainValid) E.Add(Id(N)+TEXT(": SimpleParallel requires exactly one task on output 0 (main)"));
    if(!BackgroundValid) E.Add(Id(N)+TEXT(": SimpleParallel requires exactly one task/composite on output 1 (background)"));
    if(Parallel->FinishMode!=EBTParallelMode::AbortBackground && Parallel->FinishMode!=EBTParallelMode::WaitForBackground) E.Add(Id(N)+TEXT(": invalid native parallel finish mode"));
    if(MainValid && BackgroundValid)
    {
     auto* MainNode=CastChecked<UBehaviorTreeGraphNode>(Main->LinkedTo[0]->GetOwningNode());
     if(MainNode->NodeInstance && (MainNode->NodeInstance->IsA<UBTTask_RunBehavior>() || MainNode->NodeInstance->IsA<UBTTask_RunBehaviorDynamic>())) E.Add(Id(N)+TEXT(": SimpleParallel main task cannot push a subtree"));
     auto* BackgroundNode=CastChecked<UBehaviorTreeGraphNode>(Background->LinkedTo[0]->GetOwningNode());
     if(Parallel->Children.Num()!=2 || Parallel->Children[0].ChildTask!=MainNode->NodeInstance || (Parallel->Children[1].ChildTask ? static_cast<UBTNode*>(Parallel->Children[1].ChildTask.Get()) : static_cast<UBTNode*>(Parallel->Children[1].ChildComposite.Get()))!=BackgroundNode->NodeInstance) E.Add(Id(N)+TEXT(": compiled parallel roles differ from main/background pins; compile required"));
    }
   }
   if(auto* Run=Cast<UBTTask_RunBehavior>(Node)) if(!Run->GetSubtreeAsset()) E.Add(Id(N)+TEXT(": missing subtree asset"));
   if(auto* Run=Cast<UBTTask_RunBehaviorDynamic>(Node)) if(!Run->GetInjectionTag().IsValid() || !UGameplayTagsManager::Get().RequestGameplayTag(Run->GetInjectionTag().GetTagName(),false).IsValid()) E.Add(Id(N)+TEXT(": dynamic subtree requires a registered injection tag"));
   if(N->HasErrors()) E.Add(Id(N)+TEXT(": ")+N->ErrorMessage);
   if(!M.Parents.Contains(N) && !Reachable.Contains(N)) E.Add(Id(N)+TEXT(": disconnected node"));
   TStrongObjectPtr<UBTNode> Probe(DuplicateObject<UBTNode>(Node,GetTransientPackage()));
   try { ValidateSelectors(Probe.Get(),T->GetBlackboardAsset()); } catch(const std::exception& X) { E.Add(Id(N)+TEXT(": ")+UTF8_TO_TCHAR(X.what())); }
  }
  try { Dependencies(T); } catch(const std::exception& X) { E.Add(UTF8_TO_TCHAR(X.what())); }
  return E;
 }
 FString Json(UBehaviorTree* T,bool Change=false,bool Dry=false,bool Saved=false,const FString& Selected=TEXT(""),const TArray<FString>& Affected={})
 {
  const auto M=Model(T); const auto E=Errors(T,M); FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart();
  J->WriteValue(TEXT("asset_path"),T->GetPathName()); J->WriteValue(TEXT("blackboard_path"),T->GetBlackboardAsset() ? T->GetBlackboardAsset()->GetPathName() : FString()); J->WriteValue(TEXT("root_class"),T->RootNode ? T->RootNode->GetClass()->GetPathName() : FString()); J->WriteValue(TEXT("root_name"),T->RootNode ? T->RootNode->GetNodeName() : FString());
  J->WriteValue(TEXT("graph_path"),M.Graph ? M.Graph->GetPathName() : FString()); J->WriteValue(TEXT("root_guid"),Id(M.Root)); J->WriteValue(TEXT("node_guid"),Selected);
  J->WriteValue(TEXT("changed"),Change && !Dry); J->WriteValue(TEXT("would_change"),Change); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("saved"),Saved); J->WriteValue(TEXT("dirty"),T->GetOutermost()->IsDirty()); J->WriteValue(TEXT("valid"),E.IsEmpty());
  J->WriteArrayStart(TEXT("affected_nodes")); for(const auto& V:Affected) J->WriteValue(V); J->WriteArrayEnd();
  J->WriteValue(TEXT("execution_indices_are_transient"),true);
  auto InstanceGuid=[&](const UObject* O) { for(auto* N:M.Nodes) { if(N->NodeInstance==O) return Id(N); if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(N)) if(C->BoundGraph) for(UEdGraphNode* Inner:C->BoundGraph->Nodes) if(InnerInstance(Inner)==O) return Id(Inner); } return FString(); };
  J->WriteArrayStart(TEXT("compiled_root_decorators")); for(const auto& D:T->RootDecorators) J->WriteValue(InstanceGuid(D)); J->WriteArrayEnd();
  J->WriteArrayStart(TEXT("nodes"));
  for(auto* N:M.Nodes)
  {
   auto* Instance=Cast<UBTNode>(N->NodeInstance); J->WriteObjectStart(); J->WriteValue(TEXT("guid"),Id(N)); J->WriteValue(TEXT("graph_node_class"),N->GetClass()->GetPathName()); J->WriteValue(TEXT("class"),Instance ? Instance->GetClass()->GetPathName() : FString()); J->WriteValue(TEXT("instance_path"),Instance ? Instance->GetPathName() : FString()); J->WriteValue(TEXT("parent_guid"),M.Parents.Contains(N) ? Id(M.Parents[N]) : FString());
   J->WriteValue(TEXT("x"),N->NodePosX); J->WriteValue(TEXT("y"),N->NodePosY); J->WriteValue(TEXT("read_only"),bool(N->bIsReadOnly || N->bInjectedNode)); J->WriteValue(TEXT("injected"),bool(N->bInjectedNode)); J->WriteValue(TEXT("execution_index"),Instance ? int32(Instance->GetExecutionIndex()) : -1);
   if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(N))
   {
    const auto D=Compound(C,T); J->WriteObjectStart(TEXT("compound")); J->WriteValue(TEXT("name"),C->CompositeName); J->WriteValue(TEXT("graph_path"),C->BoundGraph->GetPathName());
    J->WriteArrayStart(TEXT("operations")); for(const auto& Op:D.Ops) { J->WriteObjectStart(); J->WriteValue(TEXT("operation"),int32(Op.Operation)); J->WriteValue(TEXT("number"),int32(Op.Number)); J->WriteObjectEnd(); } J->WriteArrayEnd();
    J->WriteArrayStart(TEXT("tests")); for(auto* I:D.Tests)
    {
     J->WriteObjectStart(); J->WriteValue(TEXT("class"),I->GetClass()->GetPathName()); J->WriteValue(TEXT("instance_path"),I->GetPathName());
     J->WriteObjectStart(TEXT("properties")); int32 Count=0; for(TFieldIterator<FProperty> It(I->GetClass());It && Count<128;++It) if(Editable(*It)) { ++Count; J->WriteValue(It->GetName(),Export(*It,I).Left(4096)); } J->WriteObjectEnd();
     J->WriteObjectStart(TEXT("blackboard_selectors")); for(TFieldIterator<FStructProperty> It(I->GetClass());It;++It) if(It->Struct==FBlackboardKeySelector::StaticStruct()) J->WriteValue(It->GetName(),It->ContainerPtrToValuePtr<FBlackboardKeySelector>(I)->SelectedKeyName.ToString()); J->WriteObjectEnd(); J->WriteObjectEnd();
    } J->WriteArrayEnd();
    J->WriteArrayStart(TEXT("inner_nodes")); for(UEdGraphNode* Inner:C->BoundGraph->Nodes)
    {
     J->WriteObjectStart(); J->WriteValue(TEXT("guid"),Id(Inner)); J->WriteValue(TEXT("class"),Inner->GetClass()->GetPathName()); J->WriteValue(TEXT("x"),Inner->NodePosX); J->WriteValue(TEXT("y"),Inner->NodePosY);
     J->WriteArrayStart(TEXT("pins")); for(auto* P:Inner->Pins) { J->WriteObjectStart(); J->WriteValue(TEXT("direction"),P->Direction==EGPD_Input ? TEXT("input") : TEXT("output")); J->WriteArrayStart(TEXT("linked_nodes")); for(auto* L:P->LinkedTo) J->WriteValue(Id(L->GetOwningNode())); J->WriteArrayEnd(); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd();
    } J->WriteArrayEnd(); J->WriteObjectEnd();
   }
   if(auto* Run=Cast<UBTTask_RunBehavior>(Instance))
   {
    J->WriteObjectStart(TEXT("subtree")); J->WriteValue(TEXT("asset_path"),Run->GetSubtreeAsset() ? Run->GetSubtreeAsset()->GetPathName() : FString()); J->WriteValue(TEXT("native_injected_count"),Run->GetInjectedNodesCount());
    int32 Count=0; for(const auto& D:N->Decorators) if(D && D->bInjectedNode) ++Count; J->WriteValue(TEXT("preview_count"),Count); J->WriteObjectEnd();
   }
   if(auto* Run=Cast<UBTTask_RunBehaviorDynamic>(Instance))
   {
    J->WriteObjectStart(TEXT("dynamic_subtree")); J->WriteValue(TEXT("default_asset_path"),Run->GetDefaultBehaviorAsset() ? Run->GetDefaultBehaviorAsset()->GetPathName() : FString()); J->WriteValue(TEXT("injection_tag"),Run->GetInjectionTag().ToString()); J->WriteValue(TEXT("tag_registered"),Run->GetInjectionTag().IsValid() && UGameplayTagsManager::Get().RequestGameplayTag(Run->GetInjectionTag().GetTagName(),false).IsValid()); J->WriteObjectEnd();
   }
   if(auto* Parallel=Cast<UBTComposite_SimpleParallel>(Instance))
   {
    J->WriteObjectStart(TEXT("parallel")); J->WriteValue(TEXT("finish_mode"),StaticEnum<EBTParallelMode::Type>()->GetNameStringByValue(Parallel->FinishMode));
    for(int32 Slot=0;Slot<2;++Slot) { auto* Pin=N->GetOutputPin(Slot); J->WriteValue(Slot==0 ? TEXT("main_guid") : TEXT("background_guid"),Pin && Pin->LinkedTo.Num()==1 ? Id(Pin->LinkedTo[0]->GetOwningNode()) : FString()); }
    J->WriteObjectEnd();
   }
   J->WriteArrayStart(TEXT("compiled_children"));
   if(auto* C=Cast<UBTCompositeNode>(Instance)) for(const auto& Child:C->Children)
   {
    J->WriteObjectStart(); J->WriteValue(TEXT("node_guid"),InstanceGuid(Child.ChildComposite ? static_cast<UBTNode*>(Child.ChildComposite.Get()) : static_cast<UBTNode*>(Child.ChildTask.Get())));
    J->WriteArrayStart(TEXT("decorators")); for(const auto& D:Child.Decorators) J->WriteValue(InstanceGuid(D)); J->WriteArrayEnd();
    J->WriteArrayStart(TEXT("decorator_ops")); for(const auto& Op:Child.DecoratorOps) { J->WriteObjectStart(); J->WriteValue(TEXT("operation"),int32(Op.Operation)); J->WriteValue(TEXT("number"),int32(Op.Number)); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd();
   } J->WriteArrayEnd();
   J->WriteArrayStart(TEXT("compiled_services"));
   if(auto* C=Cast<UBTCompositeNode>(Instance)) for(const auto& Service:C->Services) J->WriteValue(InstanceGuid(Service));
   if(auto* Task=Cast<UBTTaskNode>(Instance)) for(const auto& Service:Task->Services) J->WriteValue(InstanceGuid(Service));
   J->WriteArrayEnd();
   J->WriteObjectStart(TEXT("properties")); int32 Count=0; if(Instance) for(TFieldIterator<FProperty> It(Instance->GetClass());It && Count<128;++It) if(Editable(*It)) { ++Count; J->WriteValue(It->GetName(),Export(*It,Instance).Left(4096)); } J->WriteObjectEnd();
   J->WriteArrayStart(TEXT("blackboard_selectors")); if(Instance) for(TFieldIterator<FStructProperty> It(Instance->GetClass());It;++It)
   {
    if(It->Struct==FBlackboardKeySelector::StaticStruct()) { auto* V=It->ContainerPtrToValuePtr<FBlackboardKeySelector>(Instance); J->WriteObjectStart(); J->WriteValue(TEXT("property"),It->GetName()); J->WriteValue(TEXT("key"),V->SelectedKeyName.ToString()); J->WriteValue(TEXT("key_id"),int32(V->GetSelectedKeyID())); J->WriteValue(TEXT("kind"),TEXT("selector")); J->WriteObjectEnd(); }
    else if(It->Struct->IsChildOf(FValueOrBlackboardKeyBase::StaticStruct())) { auto* V=It->ContainerPtrToValuePtr<FValueOrBlackboardKeyBase>(Instance); J->WriteObjectStart(); J->WriteValue(TEXT("property"),It->GetName()); J->WriteValue(TEXT("key"),V->GetKey().ToString()); J->WriteValue(TEXT("kind"),TEXT("value_or_blackboard")); J->WriteObjectEnd(); }
   } J->WriteArrayEnd();
   J->WriteArrayStart(TEXT("pins")); int32 In=0,Out=0; for(auto* P:N->Pins) { J->WriteObjectStart(); J->WriteValue(TEXT("direction"),P->Direction==EGPD_Output ? TEXT("output") : TEXT("input")); J->WriteValue(TEXT("index"),P->Direction==EGPD_Output ? Out++ : In++); J->WriteValue(TEXT("name"),P->PinName.ToString()); J->WriteValue(TEXT("category"),P->PinType.PinCategory.ToString()); J->WriteArrayStart(TEXT("linked_nodes")); for(auto* L:P->LinkedTo) J->WriteValue(Id(L->GetOwningNode())); J->WriteArrayEnd(); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd();
  } J->WriteArrayEnd(); J->WriteObjectStart(TEXT("validation")); J->WriteValue(TEXT("valid"),E.IsEmpty()); J->WriteArrayStart(TEXT("errors")); for(const auto& V:E) J->WriteValue(V); J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native editor graph/compiled execution data, bounded topology and direct native selector/value-binding compatibility. Scalar/plain-struct properties use UE text. X position affects persisted compiled child order. Execution indexes and selector IDs are transient caches that refresh on compilation/runtime load. Custom graphs and UObject/container settings require dedicated adapters; no runtime execution is implied by validation.")); J->WriteObjectEnd(); J->WriteObjectEnd(); J->Close(); return S;
 }
}
FString BehaviorTreeGraphUtils::Inspect(const FString& Path) { return Json(Load(Path)); }
FString BehaviorTreeGraphUtils::Control(const FBehaviorTreeGraphReq& R,const FString& Op)
{
 if(!IsInGameThread() || !GEditor || GEditor->PlayWorld || GEditor->bIsSimulatingInEditor) throw std::runtime_error("Stop PIE/simulation before editing Behavior Tree graphs");
 auto* T=Load(R.AssetPath); if(!T->GetOutermost()->GetName().StartsWith(TEXT("/Game/"))) throw std::runtime_error("Graph editing requires a /Game Behavior Tree");
 auto M=Model(T,Op!=TEXT("initialize")); Blackboard(T->GetBlackboardAsset());
 if(M.Graph)
 {
  for(auto* N:M.Nodes) if(N!=M.Root)
  {
   auto* I=Cast<UBTNode>(N->NodeInstance);
   if(auto* C=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(N)) { Compound(C,T); continue; }
   if(!I || !I->IsIn(T) || (N->IsA<UBehaviorTreeGraphNode_Composite>() && !I->IsA<UBTCompositeNode>()) || (N->IsA<UBehaviorTreeGraphNode_Task>() && !I->IsA<UBTTaskNode>())) throw std::runtime_error("Missing/incompatible node instances or compound-decorator adapters prevent safe native compilation");
  }
  auto* Out=M.Root->GetOutputPin(); if(Out && Out->LinkedTo.Num()>0 && !Out->LinkedTo[0]->GetOwningNode()->IsA<UBehaviorTreeGraphNode_Composite>()) throw std::runtime_error("Malformed root connection requires repair before native compilation");
 }
 if((R.bSetSubtree || R.bSetInjectionTag) && Op!=TEXT("create_node") && Op!=TEXT("update_node")) throw std::runtime_error("Subtree references apply only to node creation/update");
 bool Changed=false; UBehaviorTreeGraphNode* Node=nullptr; UBehaviorTreeGraphNode* Parent=nullptr; UClass* Class=nullptr; UClass* GraphNodeClass=nullptr; UEdGraphPin* A=nullptr; UEdGraphPin* B=nullptr; UBlackboardData* Board=nullptr;
 TStrongObjectPtr<UBTNode> Prepared; TArray<FString> Affected; FExpression Expr; UBehaviorTreeGraphNode_CompositeDecorator* CompoundNode=nullptr;
 TArray<UBTNode*> ExistingRuntime;
 if(Op==TEXT("initialize")) { Changed=!M.Graph; if(Changed) ExistingRuntime=RuntimeNodes(T); }
 else if(Op==TEXT("create_compound") || Op==TEXT("replace_compound"))
 {
  Expr=Expression(T,R);
  if(Op==TEXT("create_compound")) { Parent=Find(M,R.ParentGuid); Writable(Parent); if(M.Parents.Contains(Parent) || M.Nodes.Num()>=512) throw std::runtime_error("Compound groups require a top-level composite/task parent and available capacity"); Changed=true; }
  else { Node=Find(M,R.NodeGuid); Writable(Node); CompoundNode=Cast<UBehaviorTreeGraphNode_CompositeDecorator>(Node); if(!CompoundNode) throw std::runtime_error("Node must be a native compound decorator group"); Changed=!SameExpression(CompoundNode,T,Expr,R); }
  CompoundBudget(M,T,CompoundNode,Expr);
 }
 else if(Op==TEXT("create_node"))
 {
  if(M.Nodes.Num()>=512 || M.Graph->Nodes.Num()>=512 || FMath::Abs(int64(R.X))>1000000 || FMath::Abs(int64(R.Y))>1000000) throw std::runtime_error("Node capacity reached or position outside +/-1e6");
  if(R.ClassPath.IsEmpty()) throw std::runtime_error("A concrete node ClassPath is required"); Class=LoadClass<UBTNode>(nullptr,*R.ClassPath); if(!Class || Class->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists)) throw std::runtime_error("A concrete compatible Behavior Tree node class is required"); if(auto* BP=Cast<UBlueprint>(Class->ClassGeneratedBy)) if(BP->GeneratedClass!=Class || BP->Status==BS_Error) throw std::runtime_error("Select a successfully compiled generated Blueprint class, not a skeleton/stale class"); GraphNodeClass=GraphClass(Class);
  const bool Sub=Class->IsChildOf(UBTService::StaticClass()) || Class->IsChildOf(UBTDecorator::StaticClass());
  if(Sub)
  {
   Parent=Find(M,R.ParentGuid); Writable(Parent); if(M.Parents.Contains(Parent)) throw std::runtime_error("Subnodes require a composite or task parent");
   TStrongObjectPtr<UBehaviorTreeGraphNode> Template(NewObject<UBehaviorTreeGraphNode>(GetTransientPackage(),GraphNodeClass)); const auto Result=M.Graph->GetSchema()->CanMergeNodes(Template.Get(),Parent); if(Result.Response==CONNECT_RESPONSE_DISALLOW) throw std::runtime_error("Native schema rejects this subnode parent");
  }
  else if(!R.ParentGuid.IsEmpty()) throw std::runtime_error("Composite/task creation uses links; ParentGuid is only for services/decorators");
  Prepared=Prepare(Class->GetDefaultObject<UBTNode>(),T,R); Changed=true;
 }
 else if(Op==TEXT("update_node"))
 {
  Node=Find(M,R.NodeGuid); Writable(Node); auto* I=Cast<UBTNode>(Node->NodeInstance); if(!I) throw std::runtime_error("Node instance is unavailable"); Prepared=Prepare(I,T,R);
  if(R.bSetSubtree) Changed|=Subtree(I)!=Subtree(Prepared.Get());
  if(R.bSetInjectionTag) Changed|=CastChecked<UBTTask_RunBehaviorDynamic>(I)->GetInjectionTag()!=CastChecked<UBTTask_RunBehaviorDynamic>(Prepared.Get())->GetInjectionTag();
  for(const auto& P:R.Properties) Changed|=Export(FindFProperty<FProperty>(I->GetClass(),*P.Key),I)!=Export(FindFProperty<FProperty>(I->GetClass(),*P.Key),Prepared.Get());
  for(const auto& P:R.BlackboardSelectors)
  {
   auto* F=FindFProperty<FStructProperty>(I->GetClass(),*P.Key);
   if(F->Struct==FBlackboardKeySelector::StaticStruct()) Changed|=F->ContainerPtrToValuePtr<FBlackboardKeySelector>(I)->SelectedKeyName!=F->ContainerPtrToValuePtr<FBlackboardKeySelector>(Prepared.Get())->SelectedKeyName;
   else Changed|=F->ContainerPtrToValuePtr<FValueOrBlackboardKeyBase>(I)->GetKey()!=F->ContainerPtrToValuePtr<FValueOrBlackboardKeyBase>(Prepared.Get())->GetKey();
  }
 }
 else if(Op==TEXT("delete_node"))
 {
  Node=Find(M,R.NodeGuid); Writable(Node); Affected.Add(Id(Node)); for(UAIGraphNode* Sub:Node->SubNodes) Affected.Add(Id(Sub)); for(auto* P:Node->Pins) for(auto* L:P->LinkedTo) Affected.AddUnique(Id(L->GetOwningNode()));
  if(!R.bConfirm && !R.bDryRun) throw std::runtime_error("Node deletion requires bConfirm=true; dry-run reports affected_nodes"); Changed=true;
 }
 else if(Op==TEXT("connect") || Op==TEXT("disconnect"))
 {
  Node=Find(M,R.NodeGuid); auto* Target=Find(M,R.TargetGuid); if((Node!=M.Root && Node->bIsReadOnly) || (Target!=M.Root && Target->bIsReadOnly) || Node->bInjectedNode || Target->bInjectedNode || M.Parents.Contains(Node) || M.Parents.Contains(Target)) throw std::runtime_error("Links require top-level, noninjected nodes");
  if(R.PinIndex<0 || R.PinIndex>8 || R.TargetPinIndex<0 || R.TargetPinIndex>8) throw std::runtime_error("Pin indexes require [0,8]"); A=Node->GetOutputPin(R.PinIndex); B=Target->GetInputPin(R.TargetPinIndex); if(!A || !B) throw std::runtime_error("Requested output/input pin is unavailable");
  Changed=Op==TEXT("connect") ? !A->LinkedTo.Contains(B) : A->LinkedTo.Contains(B);
  if(Changed && Op==TEXT("connect"))
  {
   if(Node->NodeInstance && Node->NodeInstance->IsA<UBTComposite_SimpleParallel>() && R.PinIndex==0 && Target->NodeInstance && (Target->NodeInstance->IsA<UBTTask_RunBehavior>() || Target->NodeInstance->IsA<UBTTask_RunBehaviorDynamic>())) throw std::runtime_error("SimpleParallel main tasks cannot push a subtree");
   const auto Result=M.Graph->GetSchema()->CanCreateConnection(A,B); if(Result.Response==CONNECT_RESPONSE_DISALLOW) throw std::runtime_error(TCHAR_TO_UTF8(*Result.Message.ToString()));
   EdgeDepth(M,A,B,Result.Response);
   if(Result.Response!=CONNECT_RESPONSE_MAKE) { for(auto* L:A->LinkedTo) Affected.AddUnique(Id(L->GetOwningNode())); for(auto* L:B->LinkedTo) Affected.AddUnique(Id(L->GetOwningNode())); if(!R.bConfirm && !R.bDryRun) throw std::runtime_error("Replacing existing links requires bConfirm=true; preview affected_nodes with dry-run"); }
  }
 }
 else if(Op==TEXT("set_positions"))
 {
  if(R.Positions.IsEmpty() || R.Positions.Num()>512) throw std::runtime_error("Positions requires 1-512 unique top-level nodes"); TSet<FString> Seen;
  for(const auto& P:R.Positions) { auto* N=Find(M,P.NodeGuid); if(M.Parents.Contains(N) || N->bInjectedNode || Seen.Contains(Id(N)) || FMath::Abs(int64(P.X))>1000000 || FMath::Abs(int64(P.Y))>1000000) throw std::runtime_error("Layout requires unique noninjected top-level nodes and positions within +/-1e6"); Seen.Add(Id(N)); Changed|=N->NodePosX!=P.X || N->NodePosY!=P.Y; }
 }
 else if(Op==TEXT("set_blackboard"))
 {
  if(!R.BlackboardPath.IsEmpty())
  {
   const auto Path=FPackageName::ObjectPathToPackageName(R.BlackboardPath); const FString Object=R.BlackboardPath.Contains(TEXT(".")) ? R.BlackboardPath : Path+TEXT(".")+FPackageName::GetLongPackageAssetName(Path);
   if(!FPackageName::IsValidLongPackageName(Path) || !FPackageName::IsValidObjectPath(Object)) throw std::runtime_error("BlackboardPath requires a valid asset path");
   Board=FindObject<UBlackboardData>(nullptr,*Object);
   if(!Board && FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(Object)).IsValid()) Board=LoadObject<UBlackboardData>(nullptr,*Object);
   if(!Board) throw std::runtime_error("BlackboardPath is not an existing Blackboard"); Blackboard(Board);
  }
  Changed=M.Root->BlackboardAsset!=Board || T->GetBlackboardAsset()!=Board;
  if(Changed && !R.bConfirm && !R.bDryRun) throw std::runtime_error("Changing a Behavior Tree Blackboard requires bConfirm=true; selectors may require repair");
 }
 else if(Op==TEXT("compile")) Changed=true;
 else throw std::runtime_error("Unknown Behavior Tree graph operation");
 if(Op!=TEXT("initialize")) Dependencies(T,Node ? Cast<UBTNode>(Node->NodeInstance) : nullptr,Prepared.Get(),Op==TEXT("create_node") || Op==TEXT("update_node") || Op==TEXT("delete_node"),Board,Op==TEXT("set_blackboard"));
 if(Changed && !R.bDryRun)
 {
  FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","BehaviorTreeGraphEdit","Edit Behavior Tree Graph")); Transact(T,M);
  if(Op==TEXT("initialize"))
  {
   for(auto* I:ExistingRuntime) { I->SetFlags(RF_Transactional); I->Modify(); }
   // The completed graph is retained by the asset transaction. Recording its
   // partial construction would let a detached graph's native PostEditUndo
   // clear the restored runtime tree.
   TGuardValue<ITransaction*> ConstructionGuard(GUndo,nullptr);
   auto* Original=T->GetBlackboardAsset(); auto* G=CastChecked<UBehaviorTreeGraph>(FBlueprintEditorUtils::CreateNewGraph(T,NAME_None,UBehaviorTreeGraph::StaticClass(),UEdGraphSchema_BehaviorTree::StaticClass())); T->BTGraph=G; G->LockUpdates();
   G->GetSchema()->CreateDefaultNodesForGraph(*G); for(UEdGraphNode* N:G->Nodes) if(auto* Root=Cast<UBehaviorTreeGraphNode_Root>(N)) { Root->BlackboardAsset=Original; Root->UpdateBlackboard(); }
   G->OnCreated(); G->Initialize(); Inject(G); G->UnlockUpdates(); M=Model(T,true);
  }
  else
  {
   M.Graph->LockUpdates();
   if(Op==TEXT("create_compound") || Op==TEXT("replace_compound"))
   {
    TGuardValue<ITransaction*> ConstructionGuard(GUndo,nullptr);
    if(!CompoundNode) { CompoundNode=NewObject<UBehaviorTreeGraphNode_CompositeDecorator>(M.Graph,NAME_None,RF_Transactional); Parent->AddSubNode(CompoundNode,M.Graph); Node=CompoundNode; }
    else
    {
     auto* Old=CompoundNode->BoundGraph.Get(); M.Graph->SubGraphs.Remove(Old);
     auto* G=CastChecked<UBehaviorTreeDecoratorGraph>(FBlueprintEditorUtils::CreateNewGraph(CompoundNode,NAME_None,UBehaviorTreeDecoratorGraph::StaticClass(),GetDefault<UBehaviorTreeDecoratorGraph>()->Schema));
     CompoundNode->BoundGraph=G; G->GetSchema()->CreateDefaultNodesForGraph(*G); M.Graph->SubGraphs.Add(G);
    }
    if(R.bSetCompoundName) CompoundNode->CompositeName=R.CompoundName; else if(Op==TEXT("create_compound")) CompoundNode->CompositeName=TEXT("Logic");
    Populate(CompoundNode,T,Expr);
   }
   else if(Op==TEXT("create_node"))
   {
    Node=NewObject<UBehaviorTreeGraphNode>(M.Graph,GraphNodeClass,NAME_None,RF_Transactional); UAIGraphNode::UpdateNodeClassDataFrom(Class,Node->ClassData);
    if(Parent) Parent->AddSubNode(Node,M.Graph);
    else { M.Graph->AddNode(Node,false,false); Node->CreateNewGuid(); Node->NodePosX=R.X; Node->NodePosY=R.Y; Node->PostPlacedNewNode(); Node->AllocateDefaultPins(); }
    Apply(CastChecked<UBTNode>(Node->NodeInstance),Prepared.Get(),T,R);
   }
   else if(Op==TEXT("update_node")) Apply(CastChecked<UBTNode>(Node->NodeInstance),Prepared.Get(),T,R);
   else if(Op==TEXT("delete_node")) { if(M.Parents.Contains(Node)) Node->ParentNode=M.Parents[Node]; Node->DestroyNode(); }
   else if(Op==TEXT("connect")) { if(!M.Graph->GetSchema()->TryCreateConnection(A,B)) { M.Graph->UnlockUpdates(); throw std::runtime_error("Native schema connection failed after preflight"); } }
   else if(Op==TEXT("disconnect")) M.Graph->GetSchema()->BreakSinglePinLink(A,B);
   else if(Op==TEXT("set_positions")) for(const auto& P:R.Positions) { auto* N=Find(M,P.NodeGuid); N->NodePosX=P.X; N->NodePosY=P.Y; }
   else if(Op==TEXT("set_blackboard")) { M.Root->BlackboardAsset=Board; M.Root->UpdateBlackboard(); }
   Inject(M.Graph); M.Graph->UnlockUpdates(); M.Graph->NotifyGraphChanged();
  }
  T->MarkPackageDirty();
 }
 bool Saved=false; if(R.bSave && !R.bDryRun) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(T,false); if(!Saved) throw std::runtime_error("Behavior Tree changed but save failed"); }
 return Json(T,Changed,R.bDryRun,Saved,Id(Node),Affected);
}


FString BehaviorTreeGraphUtils::Runtime(const FString& Path,int32 PIEInstance)
{
 auto* W=NavigationWorldUtils::Resolve(TEXT("pie"),PIEInstance); FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteArrayStart(TEXT("components"));
 if(!Path.IsEmpty()) RuntimeJson(J,LiveComponent(Path,PIEInstance));
 else { int32 Count=0; for(TObjectIterator<UBehaviorTreeComponent> It;It;++It) if(IsValid(*It) && !It->IsTemplate() && It->GetWorld()==W && It->IsRegistered()) { if(++Count>256) throw std::runtime_error("Live component listing exceeds 256; select ComponentPath"); RuntimeJson(J,*It); } }
 J->WriteArrayEnd(); J->WriteObjectEnd(); J->Close(); return S;
}
FString BehaviorTreeGraphUtils::ReplaceDynamic(UBehaviorTreeComponent* C,const FString& Name,const FString& Path,bool DryRun)
{
 if(!IsInGameThread() || !IsValid(C) || !C->IsRegistered() || !C->GetWorld() || (C->GetWorld()->WorldType!=EWorldType::PIE && C->GetWorld()->WorldType!=EWorldType::Game) || C->GetWorld()->bIsTearingDown || !IsValid(C->GetOwner()) || C->GetOwner()->IsActorBeingDestroyed() || !C->GetOwner()->HasAuthority() || !C->IsRunning() || C->IsPaused()) throw std::runtime_error("Dynamic replacement requires a running, unpaused authoritative native component");
 if(Name.IsEmpty() || Name.Len()>256) throw std::runtime_error("An explicit registered injection tag is required"); const auto Tag=UGameplayTagsManager::Get().RequestGameplayTag(FName(*Name),false); if(!Tag.IsValid()) throw std::runtime_error("Injection tag is not registered");
 auto* Candidate=Path.IsEmpty() ? nullptr : Load(Path); const auto Tasks=DynamicTasks(C); int32 Matched=0,Changed=0;
 for(const auto& T:Tasks) if(T.Template->HasMatchingTag(Tag)) { ++Matched; if(T.Current!=Candidate) ++Changed; }
 if(!Matched) throw std::runtime_error("No instantiated dynamic task matches the exact injection tag");
 if(Changed) RuntimeDependencies(C,Tasks,Tag,Candidate);
 if(Changed && !DryRun) C->SetDynamicSubtree(Tag,Candidate);
 FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteValue(TEXT("matched_tasks"),Matched); J->WriteValue(TEXT("would_change_tasks"),Changed); J->WriteValue(TEXT("dry_run"),DryRun); J->WriteValue(TEXT("applied"),Changed>0 && !DryRun);
 J->WriteValue(TEXT("scope"),TEXT("Updates currently instantiated matching tasks only. Active task replacement requests native restart asynchronously; clearing disables that subtree and may fail its branch. New task instances start from authored defaults. No asset edits or undo transaction.")); J->WriteIdentifierPrefix(TEXT("component")); RuntimeJson(J,C); J->WriteObjectEnd(); J->Close(); return S;
}
FString BehaviorTreeGraphUtils::RuntimeControl(const FBehaviorTreeRuntimeReq& R)
{
 return ReplaceDynamic(LiveComponent(R.ComponentPath,R.PIEInstance),R.InjectionTag,R.AssetPath,R.bDryRun);
}
