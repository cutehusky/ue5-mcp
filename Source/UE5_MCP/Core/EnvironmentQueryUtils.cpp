#include "EnvironmentQueryUtils.h"
#include "UE5_MCP/API/DTO/EnvironmentQueryReq.h"
#include "AIGraph.h"
#include "AIGraphNode.h"
#include "EnvironmentQuery/EnvQuery.h"
#include "EnvironmentQuery/EnvQueryOption.h"
#include "EnvironmentQuery/EnvQueryGenerator.h"
#include "EnvironmentQuery/Generators/EnvQueryGenerator_Composite.h"
#include "EnvironmentQuery/EnvQueryTest.h"
#include "DataProviders/AIDataProvider_QueryParams.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Subsystems/EditorAssetSubsystem.h"
#include "Editor.h"
#include "Engine/Blueprint.h"
#include "ScopedTransaction.h"
#include "Misc/PackageName.h"
#include "Misc/StringOutputDevice.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/Package.h"
#include <stdexcept>

namespace
{
 UClass* Native(const TCHAR* Name)
 {
  FModuleManager::LoadModuleChecked<IModuleInterface>(TEXT("EnvironmentQueryEditor"));
  auto* C=LoadObject<UClass>(nullptr,*(FString(TEXT("/Script/EnvironmentQueryEditor."))+Name)); if(!C) throw std::runtime_error("Native EQS editor class unavailable"); return C;
 }
 UEnvQuery* Load(const FString& Path)
 {
  const FString P=FPackageName::ObjectPathToPackageName(Path); if(!FPackageName::IsValidLongPackageName(P)) throw std::runtime_error("A valid EQS asset path is required");
  const FString O=Path.Contains(TEXT(".")) ? Path : P+TEXT(".")+FPackageName::GetLongPackageAssetName(P);
  auto* Q=FindObject<UEnvQuery>(nullptr,*O); if(!Q && FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get().GetAssetByObjectPath(FSoftObjectPath(O)).IsValid()) Q=LoadObject<UEnvQuery>(nullptr,*O);
  if(!IsValid(Q)) throw std::runtime_error("Asset is not an existing environment query"); return Q;
 }
 FString Id(UAIGraphNode* N) { return N ? N->NodeGuid.ToString(EGuidFormats::DigitsWithHyphens) : FString(); }
 bool Kind(UAIGraphNode* N,const TCHAR* Name) { return N && N->GetClass()==Native(Name); }
 bool Enabled(UAIGraphNode* N) { auto* P=FindFProperty<FBoolProperty>(N->GetClass(),TEXT("bTestEnabled")); return P && P->GetPropertyValue_InContainer(N); }
 void Enable(UAIGraphNode* N,bool Value) { auto* P=FindFProperty<FBoolProperty>(N->GetClass(),TEXT("bTestEnabled")); if(!P) throw std::runtime_error("Native EQS enabled property unavailable"); P->SetPropertyValue_InContainer(N,Value); }
 bool Plain(FProperty* P,int32 Depth=0)
 {
  if(Depth>8 || P->ArrayDim!=1) return false;
  if(CastField<FNumericProperty>(P) || CastField<FBoolProperty>(P) || CastField<FEnumProperty>(P) || CastField<FStrProperty>(P) || CastField<FNameProperty>(P) || CastField<FTextProperty>(P)) return true;
  if(auto* S=CastField<FStructProperty>(P)) { for(TFieldIterator<FProperty> It(S->Struct);It;++It) if(!Plain(*It,Depth+1)) return false; return true; } return false;
 }
 bool Editable(FProperty* P) { return P && P->HasAnyPropertyFlags(CPF_Edit) && !P->HasAnyPropertyFlags(CPF_Transient) && Plain(P); }
 FString Export(FProperty* P,UObject* O) { FString S; P->ExportText_InContainer(0,S,O,O,O,PPF_None); return S; }
 void CheckNumber(FProperty* P,const void* V,const FProperty* Range=nullptr)
 {
  if(auto* N=CastField<FNumericProperty>(P))
  {
   if(N->IsFloatingPoint() || N->IsInteger()) { const double X=N->IsFloatingPoint() ? N->GetFloatingPointPropertyValue(V) : double(N->GetSignedIntPropertyValue(V)); const auto* R=Range ? Range : P;
    if(!FMath::IsFinite(X) || FMath::Abs(X)>1.e12 || (R->HasMetaData(TEXT("ClampMin")) && X<FCString::Atod(*R->GetMetaData(TEXT("ClampMin")))) || (R->HasMetaData(TEXT("ClampMax")) && X>FCString::Atod(*R->GetMetaData(TEXT("ClampMax"))))) throw std::runtime_error("EQS setting violates finite numeric/native clamp bounds"); }
  }
  UEnum* E=nullptr; int64 X=0;
  if(auto* B=CastField<FByteProperty>(P)) { E=B->Enum; X=B->GetPropertyValue(V); } else if(auto* F=CastField<FEnumProperty>(P)) { E=F->GetEnum(); X=F->GetUnderlyingProperty()->GetSignedIntPropertyValue(V); }
  if(E && (!E->IsValidEnumValueOrBitfield(X) || (E->ContainsExistingMax() && E->GetIndexByValue(X)==E->NumEnums()-1))) throw std::runtime_error("EQS enum requires a valid native member excluding generated MAX");
  if(auto* S=CastField<FStructProperty>(P)) for(TFieldIterator<FProperty> It(S->Struct);It;++It) CheckNumber(*It,It->ContainerPtrToValuePtr<void>(V));
 }
 void Import(FProperty* P,void* V,UObject* O,const FString& Text,const FProperty* Range=nullptr)
 {
  if(Text.Len()>4096) throw std::runtime_error("EQS property values are limited to 4096 characters"); FStringOutputDevice Errors; const auto* End=P->ImportText_Direct(*Text,V,O,PPF_None,&Errors);
  if(!End || !Errors.IsEmpty() || !FString(End).TrimStartAndEnd().IsEmpty()) throw std::runtime_error("EQS property failed native text import"); CheckNumber(P,V,Range);
 }
 FStructProperty* Provider(UObject* O,const FString& Name)
 {
  auto* P=FindFProperty<FStructProperty>(O->GetClass(),*Name); if(!P || !P->HasAnyPropertyFlags(CPF_Edit) || (P->Struct!=FAIDataProviderFloatValue::StaticStruct() && P->Struct!=FAIDataProviderIntValue::StaticStruct() && P->Struct!=FAIDataProviderBoolValue::StaticStruct())) throw std::runtime_error("Provider control requires a native editable Float/Int/Bool data provider"); return P;
 }
 FAIDataProviderValue* Value(FStructProperty* P,UObject* O) { if(P->Struct==FAIDataProviderFloatValue::StaticStruct()) return P->ContainerPtrToValuePtr<FAIDataProviderFloatValue>(O); if(P->Struct==FAIDataProviderIntValue::StaticStruct()) return P->ContainerPtrToValuePtr<FAIDataProviderIntValue>(O); return P->ContainerPtrToValuePtr<FAIDataProviderBoolValue>(O); }
 UClass* Concrete(const FString& Path,UClass* Base)
 {
  auto* C=LoadClass<UObject>(nullptr,*Path); if(!C || !C->IsChildOf(Base) || C->HasAnyClassFlags(CLASS_Abstract|CLASS_Deprecated|CLASS_NewerVersionExists) || C->HasMetaData(TEXT("DeprecatedNode"))) throw std::runtime_error("A concrete compatible EQS class is required");
  if(auto* BP=Cast<UBlueprint>(C->ClassGeneratedBy)) if(BP->GeneratedClass!=C || BP->Status==BS_Error) throw std::runtime_error("EQS Blueprint class must be successfully compiled"); return C;
 }
 TArray<UEnvQueryGenerator*> GeneratorNodes(UEnvQueryGenerator* Root,UObject* Owner,bool Refresh=false,bool AllowEmpty=false)
 {
  TArray<UEnvQueryGenerator*> Nodes;
  TFunction<void(UEnvQueryGenerator*,UEnvQueryGenerator*,int32)> Walk=[&](UEnvQueryGenerator* G,UEnvQueryGenerator* Parent,int32 Depth)
  {
   if(!G || (G!=Owner && !G->IsIn(Owner)) || (Parent && G->GetOuter()!=Parent) || Nodes.Contains(G) || Nodes.Num()>=127 || Depth>8) throw std::runtime_error("Generator tree requires unique owned nodes, depth <=8 and at most 127 generators"); Nodes.Add(G);
   if(Parent && (G->CanRunAsync() || G->GetClass()->GetDefaultObject<UEnvQueryGenerator>()->CanRunAsync())) throw std::runtime_error("Native composite generators cannot contain asynchronous generators");
   if(auto* C=Cast<UEnvQueryGenerator_Composite>(G))
   {
    if(C->bAllowDifferentItemTypes || C->CanRunAsync() || C->Generators.Num()>16 || (C->Generators.IsEmpty() && !AllowEmpty)) throw std::runtime_error("Composite generators require 1-16 synchronous children and matching native item types; forced memory layouts need a separate adapter");
    UClass* Common=nullptr; for(UEnvQueryGenerator* Child:C->Generators) { Walk(Child,C,Depth+1); if(Common && Common!=Child->ItemType) throw std::runtime_error("Composite children must use exactly the same native item type"); Common=Child->ItemType; }
    if(!C->Generators.IsEmpty()) { if(Refresh) C->VerifyItemTypes(); if(!C->bHasMatchingItemType || C->ItemType!=Common) throw std::runtime_error("Composite native item-type cache requires repair"); }
   }
   if(!(AllowEmpty && Cast<UEnvQueryGenerator_Composite>(G) && CastChecked<UEnvQueryGenerator_Composite>(G)->Generators.IsEmpty()) && (!G->IsValidGenerator() || !G->ItemType)) throw std::runtime_error("Generator requires a valid native item type and configuration");
  }; Walk(Root,nullptr,1); return Nodes;
 }
 void TestSettings(UEnvQueryTest* T)
 {
  if(!T) return;
  if((T->GetWorkOnFloatValues() && T->FilterType==EEnvTestFilterType::Match) || (!T->GetWorkOnFloatValues() && (T->FilterType!=EEnvTestFilterType::Match || T->ScoringEquation!=EEnvTestScoreEquation::Constant))) throw std::runtime_error("Native test scalar kind is incompatible with filter/scoring mode");
  if(T->GetWorkOnFloatValues() && T->FilterType==EEnvTestFilterType::Range && !T->FloatValueMin.IsDynamic() && !T->FloatValueMax.IsDynamic() && T->FloatValueMin.DefaultValue>T->FloatValueMax.DefaultValue) throw std::runtime_error("Static test minimum exceeds maximum");
 }
 TStrongObjectPtr<UObject> Prepare(UObject* Source,const FEnvironmentQueryReq& R,bool AllowEmptyComposite=false)
 {
  if(R.Properties.Num()+R.Classes.Num()+R.ProviderValues.Num()+R.NamedParameters.Num()>64) throw std::runtime_error("At most 64 EQS settings per request");
  TStrongObjectPtr<UObject> P(DuplicateObject<UObject>(Source,GetTransientPackage()));
  for(const auto& Pair:R.Properties) { auto* F=FindFProperty<FProperty>(P->GetClass(),*Pair.Key); if(!Editable(F)) throw std::runtime_error("Properties require native editable scalar/plain-struct fields; providers/classes use typed controls"); Import(F,F->ContainerPtrToValuePtr<void>(P.Get()),P.Get(),Pair.Value); }
  for(const auto& Pair:R.Classes)
  {
   auto* F=FindFProperty<FClassProperty>(P->GetClass(),*Pair.Key); if(!F || !F->HasAnyPropertyFlags(CPF_Edit)) throw std::runtime_error("Classes requires an editable native class property");
   auto* C=LoadClass<UObject>(nullptr,*Pair.Value); if(!C || !C->IsChildOf(F->MetaClass) || C->HasAnyClassFlags(CLASS_Deprecated|CLASS_NewerVersionExists) || (C->HasAnyClassFlags(CLASS_Abstract) && !F->HasMetaData(TEXT("AllowAbstract")))) throw std::runtime_error("Class setting must match native MetaClass"); if(auto* BP=Cast<UBlueprint>(C->ClassGeneratedBy)) if(BP->GeneratedClass!=C || BP->Status==BS_Error) throw std::runtime_error("Class setting requires a compiled Blueprint class"); F->SetObjectPropertyValue_InContainer(P.Get(),C);
  }
  for(const auto& Pair:R.ProviderValues) { auto* F=Provider(P.Get(),Pair.Key); if(Value(F,P.Get())->DataBinding && !Value(F,P.Get())->DataBinding->IsA<UAIDataProvider_QueryParams>()) throw std::runtime_error("Custom provider defaults require a separate adapter; explicitly clear the binding first"); auto* D=FindFProperty<FProperty>(F->Struct,TEXT("DefaultValue")); Import(D,D->ContainerPtrToValuePtr<void>(F->ContainerPtrToValuePtr<void>(P.Get())),P.Get(),Pair.Value,F); }
  for(const auto& Pair:R.NamedParameters)
  {
   auto* F=Provider(P.Get(),Pair.Key); auto* V=Value(F,P.Get()); if(Pair.Value.Len()>128 || (!Pair.Value.IsEmpty() && FName(*Pair.Value).IsNone())) throw std::runtime_error("Named parameters require 1-128 characters or empty to clear");
   if(Pair.Value.IsEmpty()) { V->DataBinding=nullptr; V->DataField=NAME_None; }
   else { auto* B=NewObject<UAIDataProvider_QueryParams>(P.Get()); B->ParamName=FName(*Pair.Value); V->DataBinding=B; V->DataField=F->Struct==FAIDataProviderFloatValue::StaticStruct() ? TEXT("FloatValue") : F->Struct==FAIDataProviderIntValue::StaticStruct() ? TEXT("IntValue") : TEXT("BoolValue"); }
  }
  if(auto* T=Cast<UEnvQueryTest>(P.Get())) { TestSettings(T); T->UpdatePreviewData(); }
  if(auto* G=Cast<UEnvQueryGenerator>(P.Get())) GeneratorNodes(G,G,true,AllowEmptyComposite); return P;
 }
 TStrongObjectPtr<UObject> GeneratorExpression(const FEnvironmentQueryReq& R)
 {
  if(R.GeneratorTree.IsEmpty() || R.GeneratorTree.Num()>127) throw std::runtime_error("GeneratorTree requires 1-127 prefix rows");
  int32 Cursor=0,Settings=0;
  TFunction<TStrongObjectPtr<UObject>(UObject*,int32)> Parse=[&](UObject* Outer,int32 Depth)
  {
   if(Depth>8 || !R.GeneratorTree.IsValidIndex(Cursor)) throw std::runtime_error("Invalid generator prefix/depth"); const auto& Row=R.GeneratorTree[Cursor++];
   Settings+=Row.Properties.Num()+Row.Classes.Num()+Row.ProviderValues.Num()+Row.NamedParameters.Num(); if(Settings>256 || Row.ClassPath.Len()>1024) throw std::runtime_error("Generator tree exceeds 256 settings or class path bounds");
   auto* Class=Concrete(Row.ClassPath,UEnvQueryGenerator::StaticClass()); const bool Composite=Class->IsChildOf(UEnvQueryGenerator_Composite::StaticClass());
   if((Composite && (Row.Children<1 || Row.Children>16)) || (!Composite && Row.Children!=0)) throw std::runtime_error("Composite rows require 1-16 children; leaf rows require zero");
   FEnvironmentQueryReq SettingsRow; SettingsRow.Properties=Row.Properties; SettingsRow.Classes=Row.Classes; SettingsRow.ProviderValues=Row.ProviderValues; SettingsRow.NamedParameters=Row.NamedParameters;
   auto P=Prepare(Class->GetDefaultObject(),SettingsRow,Composite); if(Outer) P->Rename(nullptr,Outer,REN_DontCreateRedirectors|REN_DoNotDirty|REN_NonTransactional);
   if(Composite) { auto* C=CastChecked<UEnvQueryGenerator_Composite>(P.Get()); C->Generators.Reset(); for(int32 I=0;I<Row.Children;++I) { auto Child=Parse(C,Depth+1); C->Generators.Add(CastChecked<UEnvQueryGenerator>(Child.Get())); } }
   GeneratorNodes(CastChecked<UEnvQueryGenerator>(P.Get()),P.Get(),true); return P;
  };
  auto Root=Parse(nullptr,1); if(Cursor!=R.GeneratorTree.Num()) throw std::runtime_error("Generator prefix has trailing rows"); if(!R.ClassPath.IsEmpty() && Root->GetClass()!=Concrete(R.ClassPath,UEnvQueryGenerator::StaticClass())) throw std::runtime_error("ClassPath must match the generator-tree root"); return Root;
 }
 bool Same(UObject* A,UObject* B,const FEnvironmentQueryReq& R)
 {
  for(const auto& P:R.Properties) if(Export(FindFProperty<FProperty>(A->GetClass(),*P.Key),A)!=Export(FindFProperty<FProperty>(B->GetClass(),*P.Key),B)) return false;
  for(const auto& P:R.Classes) { auto* F=FindFProperty<FClassProperty>(A->GetClass(),*P.Key); if(F->GetObjectPropertyValue_InContainer(A)!=F->GetObjectPropertyValue_InContainer(B)) return false; }
  TSet<FString> Names; for(const auto& P:R.ProviderValues) Names.Add(P.Key); for(const auto& P:R.NamedParameters) Names.Add(P.Key);
  for(const auto& Name:Names) { auto* F=Provider(A,Name); auto* D=FindFProperty<FProperty>(F->Struct,TEXT("DefaultValue")); auto* AV=Value(F,A); auto* BV=Value(F,B); auto* AB=Cast<UAIDataProvider_QueryParams>(AV->DataBinding); auto* BB=Cast<UAIDataProvider_QueryParams>(BV->DataBinding);
   if(!D->Identical(D->ContainerPtrToValuePtr<void>(F->ContainerPtrToValuePtr<void>(A)),D->ContainerPtrToValuePtr<void>(F->ContainerPtrToValuePtr<void>(B))) || bool(AV->DataBinding)!=bool(BV->DataBinding) || AV->DataField!=BV->DataField || (AB && (!BB || AB->ParamName!=BB->ParamName)) || (!AB && AV->DataBinding && AV->DataBinding!=BV->DataBinding)) return false;
  } return true;
 }
 bool SameGenerators(UEnvQueryGenerator* A,UEnvQueryGenerator* B)
 {
  if(A->GetClass()!=B->GetClass()) return false; FEnvironmentQueryReq All;
  for(TFieldIterator<FProperty> It(A->GetClass());It;++It) if(It->HasAnyPropertyFlags(CPF_Edit) && !It->HasAnyPropertyFlags(CPF_Transient) && It->GetFName()!=TEXT("Generators"))
  {
   if(auto* P=CastField<FStructProperty>(*It); P && (P->Struct==FAIDataProviderFloatValue::StaticStruct() || P->Struct==FAIDataProviderIntValue::StaticStruct() || P->Struct==FAIDataProviderBoolValue::StaticStruct())) All.ProviderValues.Add(It->GetName(),TEXT(""));
   else if(!It->Identical_InContainer(A,B)) return false;
  }
  if(!Same(A,B,All)) return false;
  if(auto* AC=Cast<UEnvQueryGenerator_Composite>(A)) { auto* BC=CastChecked<UEnvQueryGenerator_Composite>(B); if(AC->Generators.Num()!=BC->Generators.Num()) return false; for(int32 I=0;I<AC->Generators.Num();++I) if(!SameGenerators(AC->Generators[I],BC->Generators[I])) return false; } return true;
 }
 void Apply(UObject* O,UObject* P,const FEnvironmentQueryReq& R)
 {
  for(const auto& V:R.Properties) FindFProperty<FProperty>(O->GetClass(),*V.Key)->CopyCompleteValue_InContainer(O,P);
  for(const auto& V:R.Classes) FindFProperty<FProperty>(O->GetClass(),*V.Key)->CopyCompleteValue_InContainer(O,P);
  TSet<FString> Names; for(const auto& V:R.ProviderValues) Names.Add(V.Key); for(const auto& V:R.NamedParameters) Names.Add(V.Key);
  for(const auto& Name:Names) { auto* F=Provider(O,Name); F->CopyCompleteValue_InContainer(O,P); auto* V=Value(F,O); if(V->DataBinding) V->DataBinding=DuplicateObject<UAIDataProvider>(V->DataBinding,O); }
  if(auto* T=Cast<UEnvQueryTest>(O)) T->UpdatePreviewData();
 }
 UEnvQueryGenerator* PersistGenerator(UEnvQueryGenerator* Prepared,UEnvQuery* Q)
 {
  auto* Root=DuplicateObject<UEnvQueryGenerator>(Prepared,Q);
  for(auto* G:GeneratorNodes(Root,Q))
  {
   G->ClearFlags(RF_Transient); G->SetFlags(RF_Transactional);
   for(TFieldIterator<FStructProperty> It(G->GetClass());It;++It) if(It->Struct==FAIDataProviderFloatValue::StaticStruct() || It->Struct==FAIDataProviderIntValue::StaticStruct() || It->Struct==FAIDataProviderBoolValue::StaticStruct()) if(auto* B=Value(*It,G)->DataBinding.Get()) { if(!B->IsIn(Root)) throw std::runtime_error("Generator duplication failed to preserve owned provider bindings"); B->ClearFlags(RF_Transient); B->SetFlags(RF_Transactional); }
  } return Root;
 }
 void ProviderOwnership(UObject* O,UEnvQuery* Q)
 {
  for(TFieldIterator<FStructProperty> It(O->GetClass());It;++It) if(It->Struct==FAIDataProviderFloatValue::StaticStruct() || It->Struct==FAIDataProviderIntValue::StaticStruct() || It->Struct==FAIDataProviderBoolValue::StaticStruct()) { auto* V=Value(*It,O); if(V->DataBinding && !V->DataBinding->IsIn(Q)) throw std::runtime_error("EQS provider binding must be owned by its query"); }
 }
 struct FModel { UAIGraph* Graph=nullptr; UAIGraphNode* Root=nullptr; TArray<UAIGraphNode*> Options,Tests; TArray<UEnvQueryGenerator*> Generators; TMap<UAIGraphNode*,UAIGraphNode*> Parents; };
 FModel Model(UEnvQuery* Q,bool Require=false)
 {
  FModel M; M.Graph=Cast<UAIGraph>(Q->EdGraph); if(!M.Graph) { if(Q->EdGraph || Require) throw std::runtime_error("Initialize a native EQS graph first"); return M; }
  if(M.Graph->GetClass()!=Native(TEXT("EnvironmentQueryGraph")) || !M.Graph->GetSchema() || M.Graph->GetSchema()->GetClass()!=Native(TEXT("EdGraphSchema_EnvironmentQuery")) || M.Graph->Nodes.Num()>65) throw std::runtime_error("Unsupported EQS graph/schema or more than 64 options");
  TSet<FGuid> IDs; TSet<UObject*> Instances;
  auto Check=[&](UAIGraphNode* N) { if(!N || N->GetGraph()!=M.Graph || !N->NodeGuid.IsValid() || IDs.Contains(N->NodeGuid)) throw std::runtime_error("EQS graph contains invalid ownership or repeated GUIDs"); IDs.Add(N->NodeGuid); if(N->NodeInstance) { if(!N->NodeInstance->IsIn(Q) || Instances.Contains(N->NodeInstance)) throw std::runtime_error("EQS graph contains shared/foreign instances"); Instances.Add(N->NodeInstance); } };
  TSet<int32> Xs;
  for(UEdGraphNode* Raw:M.Graph->Nodes)
  {
   auto* N=Cast<UAIGraphNode>(Raw); Check(N);
   if(Kind(N,TEXT("EnvironmentQueryGraphNode_Root"))) { if(M.Root || N->NodeInstance || !N->SubNodes.IsEmpty()) throw std::runtime_error("EQS requires one native root"); M.Root=N; continue; }
   if(!Kind(N,TEXT("EnvironmentQueryGraphNode_Option")) || !Cast<UEnvQueryOption>(N->NodeInstance) || Xs.Contains(N->NodePosX)) throw std::runtime_error("EQS options require native nodes and unique X positions"); Xs.Add(N->NodePosX); M.Options.Add(N);
   auto* O=CastChecked<UEnvQueryOption>(N->NodeInstance); for(auto* G:GeneratorNodes(O->Generator,Q)) { if(G->HasAnyFlags(RF_Transient) || Instances.Contains(G) || M.Generators.Num()>=512) throw std::runtime_error("Shared generator or query generator capacity exceeded"); Instances.Add(G); M.Generators.Add(G); ProviderOwnership(G,Q); }
   if(N->SubNodes.Num()>64) throw std::runtime_error("At most 64 tests per option");
   for(UAIGraphNode* T:N->SubNodes) { Check(T); auto* Test=Cast<UEnvQueryTest>(T->NodeInstance); if(!Kind(T,TEXT("EnvironmentQueryGraphNode_Test")) || !Test || !T->SubNodes.IsEmpty() || !T->Pins.IsEmpty() || !Test->IsSupportedItem(O->Generator->ItemType) || M.Tests.Num()>=512) throw std::runtime_error("Invalid EQS test ownership/item type/capacity"); TestSettings(Test); ProviderOwnership(Test,Q); M.Tests.Add(T); M.Parents.Add(T,N); }
  }
  if(!M.Root || M.Root->Pins.Num()!=1 || !M.Root->GetOutputPin()) throw std::runtime_error("Invalid EQS root pins");
  auto* Out=M.Root->GetOutputPin(); if(Out->LinkedTo.Num()!=M.Options.Num()) throw std::runtime_error("Every option must connect once to the EQS root");
  for(auto* N:M.Options) { auto* In=N->GetInputPin(); if(N->Pins.Num()!=1 || !In || In->LinkedTo.Num()!=1 || In->LinkedTo[0]!=Out || Out->LinkedTo.FilterByPredicate([&](UEdGraphPin* P) { return P==In; }).Num()!=1) throw std::runtime_error("Invalid EQS root/option links"); } return M;
 }
 UAIGraphNode* Find(const FModel& M,const FString& S) { FGuid G; if(!FGuid::Parse(S,G)) throw std::runtime_error("A valid EQS node GUID is required"); for(auto* N:M.Options) if(N->NodeGuid==G) return N; for(auto* N:M.Tests) if(N->NodeGuid==G) return N; throw std::runtime_error("EQS node GUID does not belong to an option/test"); }
 TMap<FName,FString> Parameters(UEnvQuery* Q,const FModel& M,UObject* Target=nullptr,UObject* Prepared=nullptr,UAIGraphNode* Deleted=nullptr)
 {
  TMap<FName,FString> Names;
  auto Check=[&](UObject* Original)
  {
   UObject* O=Original==Target && Prepared ? Prepared : Original; if(!O) return;
   for(TFieldIterator<FStructProperty> It(O->GetClass());It;++It) if(It->Struct==FAIDataProviderFloatValue::StaticStruct() || It->Struct==FAIDataProviderIntValue::StaticStruct() || It->Struct==FAIDataProviderBoolValue::StaticStruct())
   {
    auto* V=Value(*It,O); if(!V->DataBinding) continue;
    if(!V->DataBinding->IsIn(Prepared && (O==Prepared || O->IsIn(Prepared)) ? Prepared : static_cast<UObject*>(Q))) throw std::runtime_error("EQS providers must be owned by the query/node");
    if(auto* P=Cast<UAIDataProvider_QueryParams>(V->DataBinding))
    {
     const FString Type=It->Struct==FAIDataProviderFloatValue::StaticStruct() ? TEXT("FloatValue") : It->Struct==FAIDataProviderIntValue::StaticStruct() ? TEXT("IntValue") : TEXT("BoolValue");
     if(P->ParamName.IsNone() || V->DataField!=FName(*Type)) throw std::runtime_error("Invalid native EQS query parameter binding");
     if(Names.Contains(P->ParamName) && Names[P->ParamName]!=Type) throw std::runtime_error("Named EQS parameter is used with incompatible scalar types"); Names.Add(P->ParamName,Type);
    }
   }
  };
  auto CheckTree=[&](UEnvQueryGenerator* Root) { auto* Effective=Root==Target && Prepared ? CastChecked<UEnvQueryGenerator>(Prepared) : Root; for(auto* G:GeneratorNodes(Effective,Effective)) Check(G); };
  if(M.Graph) for(auto* N:M.Options) { if(N==Deleted) continue; CheckTree(CastChecked<UEnvQueryOption>(N->NodeInstance)->Generator); for(UAIGraphNode* T:N->SubNodes) if(T!=Deleted) Check(T->NodeInstance); }
  else for(auto* O:Q->GetOptions()) { CheckTree(O->Generator); for(UEnvQueryTest* T:O->Tests) Check(T); }
  if(Prepared && !Target) { if(auto* G=Cast<UEnvQueryGenerator>(Prepared)) CheckTree(G); else Check(Prepared); } return Names;
 }
 void Modify(UEnvQuery* Q,const FModel& M)
 {
  Q->SetFlags(RF_Transactional); Q->Modify(); if(M.Graph) M.Graph->Modify();
  auto Object=[](UObject* O) { O->SetFlags(RF_Transactional); O->Modify(); };
  if(M.Root) M.Root->Modify(); for(auto* N:M.Options) { N->Modify(); auto* O=CastChecked<UEnvQueryOption>(N->NodeInstance); Object(O); for(auto* G:GeneratorNodes(O->Generator,Q)) Object(G); } for(auto* N:M.Tests) { N->Modify(); Object(N->NodeInstance); }
  if(!M.Graph) for(auto* O:Q->GetOptions()) { if(!O || !O->Generator || !O->IsIn(Q) || !O->Generator->IsIn(Q)) throw std::runtime_error("Invalid runtime-only option ownership"); Object(O); Object(O->Generator); for(UEnvQueryTest* T:O->Tests) { if(!T || !T->IsIn(Q)) throw std::runtime_error("Invalid runtime-only test ownership"); Object(T); } }
 }
 void Settings(TSharedRef<TJsonWriter<>> J,UObject* O)
 {
  J->WriteObjectStart(TEXT("properties")); for(TFieldIterator<FProperty> It(O->GetClass());It;++It) if(Editable(*It)) J->WriteValue(It->GetName(),Export(*It,O).Left(4096)); J->WriteObjectEnd();
  J->WriteObjectStart(TEXT("classes")); for(TFieldIterator<FClassProperty> It(O->GetClass());It;++It) if(It->HasAnyPropertyFlags(CPF_Edit)) { auto* C=It->GetObjectPropertyValue_InContainer(O); J->WriteValue(It->GetName(),C ? C->GetPathName() : FString()); } J->WriteObjectEnd();
  J->WriteObjectStart(TEXT("providers")); for(TFieldIterator<FStructProperty> It(O->GetClass());It;++It) if(It->Struct==FAIDataProviderFloatValue::StaticStruct() || It->Struct==FAIDataProviderIntValue::StaticStruct() || It->Struct==FAIDataProviderBoolValue::StaticStruct()) { auto* V=Value(*It,O); auto* D=FindFProperty<FProperty>(It->Struct,TEXT("DefaultValue")); FString Text; D->ExportTextItem_Direct(Text,D->ContainerPtrToValuePtr<void>(It->ContainerPtrToValuePtr<void>(O)),nullptr,O,PPF_None); J->WriteObjectStart(It->GetName()); J->WriteValue(TEXT("default"),Text); J->WriteValue(TEXT("binding_class"),V->DataBinding ? V->DataBinding->GetClass()->GetPathName() : FString()); J->WriteValue(TEXT("parameter"),Cast<UAIDataProvider_QueryParams>(V->DataBinding) ? CastChecked<UAIDataProvider_QueryParams>(V->DataBinding)->ParamName.ToString() : FString()); J->WriteObjectEnd(); } J->WriteObjectEnd();
 }
 void GeneratorJson(TSharedRef<TJsonWriter<>> J,UEnvQueryGenerator* G)
 {
  J->WriteObjectStart(); J->WriteValue(TEXT("class"),G->GetClass()->GetPathName()); J->WriteValue(TEXT("item_type"),G->ItemType->GetPathName()); Settings(J,G); J->WriteArrayStart(TEXT("children")); if(auto* C=Cast<UEnvQueryGenerator_Composite>(G)) for(UEnvQueryGenerator* Child:C->Generators) GeneratorJson(J,Child); J->WriteArrayEnd(); J->WriteObjectEnd();
 }
 FString Json(UEnvQuery* Q,bool Changed=false,bool Dry=false,bool Saved=false,UAIGraphNode* Selected=nullptr)
 {
  auto M=Model(Q); bool Valid=M.Graph && !M.Options.IsEmpty(); if(M.Graph && Q->GetOptions().Num()!=M.Options.Num()) Valid=false;
  M.Options.Sort([](const UAIGraphNode& A,const UAIGraphNode& B) { return A.NodePosX<B.NodePosX; });
  if(M.Graph && Q->GetOptions().Num()==M.Options.Num()) for(int32 I=0;I<M.Options.Num();++I) { auto* O=CastChecked<UEnvQueryOption>(M.Options[I]->NodeInstance); if(Q->GetOptions()[I]!=O) Valid=false; int32 Index=0; for(int32 K=0;K<M.Options[I]->SubNodes.Num();++K) { auto* T=M.Options[I]->SubNodes[K].Get(); if(Enabled(T)) { if(!O->Tests.IsValidIndex(Index) || O->Tests[Index]!=T->NodeInstance || CastChecked<UEnvQueryTest>(T->NodeInstance)->TestOrder!=K) Valid=false; ++Index; } } if(Index!=O->Tests.Num()) Valid=false; }
  TMap<FName,FString> Params; FString ParamError; try { Params=Parameters(Q,M); } catch(const std::exception& X) { Valid=false; ParamError=UTF8_TO_TCHAR(X.what()); }
  FString S; auto J=TJsonWriterFactory<>::Create(&S); J->WriteObjectStart(); J->WriteArrayStart(TEXT("named_parameters")); TArray<FName> Names; Params.GetKeys(Names); Names.Sort(FNameLexicalLess()); for(const auto Name:Names) { J->WriteObjectStart(); J->WriteValue(TEXT("name"),Name.ToString()); J->WriteValue(TEXT("type"),Params[Name]); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteArrayStart(TEXT("validation_errors")); if(!M.Graph) J->WriteValue(TEXT("Initialize the native EQS graph")); else if(M.Options.IsEmpty()) J->WriteValue(TEXT("EQS requires at least one option")); if(!ParamError.IsEmpty()) J->WriteValue(ParamError); if(!Valid && M.Graph && !M.Options.IsEmpty() && ParamError.IsEmpty()) J->WriteValue(TEXT("Compiled EQS option/test arrays differ from the graph; compile required")); J->WriteArrayEnd(); J->WriteValue(TEXT("asset_path"),Q->GetPathName()); J->WriteValue(TEXT("graph_path"),M.Graph ? M.Graph->GetPathName() : FString()); J->WriteValue(TEXT("root_guid"),Id(M.Root)); J->WriteValue(TEXT("node_guid"),Id(Selected)); J->WriteValue(TEXT("valid"),Valid); J->WriteValue(TEXT("dirty"),Q->GetOutermost()->IsDirty()); J->WriteValue(TEXT("would_change"),Changed); J->WriteValue(TEXT("dry_run"),Dry); J->WriteValue(TEXT("saved"),Saved);
  J->WriteArrayStart(TEXT("options")); M.Options.Sort([](const UAIGraphNode& A,const UAIGraphNode& B) { return A.NodePosX<B.NodePosX; });
  for(auto* N:M.Options) { auto* O=CastChecked<UEnvQueryOption>(N->NodeInstance); J->WriteObjectStart(); J->WriteValue(TEXT("guid"),Id(N)); J->WriteValue(TEXT("x"),N->NodePosX); J->WriteValue(TEXT("y"),N->NodePosY); J->WriteValue(TEXT("generator_class"),O->Generator->GetClass()->GetPathName()); J->WriteValue(TEXT("item_type"),O->Generator->ItemType->GetPathName()); Settings(J,O->Generator); J->WriteIdentifierPrefix(TEXT("generator_tree")); GeneratorJson(J,O->Generator); J->WriteArrayStart(TEXT("tests")); for(UAIGraphNode* T:N->SubNodes) { J->WriteObjectStart(); J->WriteValue(TEXT("guid"),Id(T)); J->WriteValue(TEXT("class"),T->NodeInstance->GetClass()->GetPathName()); J->WriteValue(TEXT("enabled"),Enabled(T)); Settings(J,T->NodeInstance); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteObjectEnd(); } J->WriteArrayEnd();
  J->WriteArrayStart(TEXT("compiled_options")); for(auto* O:Q->GetOptions()) { J->WriteObjectStart(); FString Guid; for(auto* N:M.Options) if(N->NodeInstance==O) Guid=Id(N); J->WriteValue(TEXT("option_guid"),Guid); J->WriteArrayStart(TEXT("test_guids")); if(O) for(UEnvQueryTest* T:O->Tests) { FString TestGuid; for(auto* N:M.Tests) if(N->NodeInstance==T) TestGuid=Id(N); J->WriteValue(TestGuid); } J->WriteArrayEnd(); J->WriteValue(TEXT("generator_class"),O && O->Generator ? O->Generator->GetClass()->GetPathName() : FString()); J->WriteArrayStart(TEXT("tests")); if(O) for(UEnvQueryTest* T:O->Tests) J->WriteValue(T ? T->GetClass()->GetPathName() : FString()); J->WriteArrayEnd(); J->WriteObjectEnd(); } J->WriteArrayEnd(); J->WriteValue(TEXT("scope"),TEXT("Native EQS graph, scalar/plain-struct settings, class selectors and Float/Int/Bool provider defaults/query parameters. Unique option X determines fallback order; tests use array order, and native auto-sort may reorder execution. Forced item layouts, asynchronous composite children and custom providers require dedicated adapters. Query execution uses the separate runtime controls.")); J->WriteObjectEnd(); J->Close(); return S;
 }
}
FString EnvironmentQueryUtils::Inspect(const FString& Path) { return Json(Load(Path)); }
FString EnvironmentQueryUtils::Control(const FEnvironmentQueryReq& R,const FString& Operation)
{
 const FString Op=Operation.StartsWith(TEXT("update_")) ? TEXT("update") : Operation.StartsWith(TEXT("delete_")) ? TEXT("delete") : Operation;
 if(!GEditor || GEditor->PlayWorld) throw std::runtime_error("EQS asset editing requires an idle editor");
 if(Op==TEXT("create"))
 {
  const FString P=FPackageName::ObjectPathToPackageName(R.AssetPath); if(!FPackageName::IsValidLongPackageName(P) || !P.StartsWith(TEXT("/Game/")) || P.Len()>200 || (R.AssetPath!=P && R.AssetPath!=P+TEXT(".")+FPackageName::GetLongPackageAssetName(P)) || FindPackage(nullptr,*P) || FPackageName::DoesPackageExist(P)) throw std::runtime_error("EQS creation requires a new /Game package path <=200 characters");
  if(R.bDryRun) return TEXT("{\"would_change\":true,\"dry_run\":true}"); auto* Q=NewObject<UEnvQuery>(CreatePackage(*P),*FPackageName::GetLongPackageAssetName(P),RF_Public|RF_Standalone|RF_Transactional); FAssetRegistryModule::AssetCreated(Q); Q->MarkPackageDirty(); if(R.bSave && !GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Q,false)) throw std::runtime_error("EQS created but save failed"); return Json(Q,true,false,R.bSave);
 }
 auto* Q=Load(R.AssetPath); if(!Q->GetOutermost()->GetName().StartsWith(TEXT("/Game/"))) throw std::runtime_error("EQS edits require a /Game asset"); auto M=Model(Q,Op!=TEXT("initialize")); UAIGraphNode* N=nullptr; UAIGraphNode* Parent=nullptr; TStrongObjectPtr<UObject> Prepared; bool Changed=false;
 if((R.bSetGeneratorTree || Op==TEXT("replace_generators")) && (!R.Properties.IsEmpty() || !R.Classes.IsEmpty() || !R.ProviderValues.IsEmpty() || !R.NamedParameters.IsEmpty())) throw std::runtime_error("Generator-tree settings belong in prefix rows");
 if(!R.GeneratorTree.IsEmpty() && !R.bSetGeneratorTree && Op!=TEXT("replace_generators")) throw std::runtime_error("GeneratorTree requires bSetGeneratorTree for creation");
 if(R.bSetGeneratorTree && Op!=TEXT("create_option") && Op!=TEXT("replace_generators")) throw std::runtime_error("GeneratorTree applies only to option creation/generator replacement");
 if(R.Index < -1 || FMath::Abs(int64(R.X))>1000000 || FMath::Abs(int64(R.Y))>1000000) throw std::runtime_error("EQS index/position outside bounds");
 if(Op==TEXT("initialize")) { Changed=!M.Graph; if(Q->GetOptions().Num()>64) throw std::runtime_error("EQS initialization supports at most 64 options");
  if(Changed) { TSet<UObject*> Seen; int32 Count=0,GeneratorCount=0; auto Own=[&](UObject* O) { if(!O || !O->IsIn(Q) || Seen.Contains(O) || O->HasAnyFlags(RF_Transient)) throw std::runtime_error("Runtime-only EQS contains invalid/shared/foreign instances"); Seen.Add(O); }; for(auto* O:Q->GetOptions()) { Own(O); for(auto* G:GeneratorNodes(O->Generator,Q)) { if(++GeneratorCount>512) throw std::runtime_error("Runtime-only query exceeds 512 generators"); Own(G); ProviderOwnership(G,Q); } if(O->Tests.Num()>64) throw std::runtime_error("Invalid runtime-only generator/test capacity"); for(UEnvQueryTest* T:O->Tests) { Own(T); if(++Count>512 || !T->IsSupportedItem(O->Generator->ItemType)) throw std::runtime_error("Runtime-only test/item type/capacity mismatch"); } } } }
 else if(Op==TEXT("create_option")) { if(R.bSetEnabled || R.Index!=-1) throw std::runtime_error("Enabled and test index apply only to tests"); if(M.Options.Num()>=64) throw std::runtime_error("EQS option capacity exceeded"); for(auto* O:M.Options) if(O->NodePosX==R.X) throw std::runtime_error("Options require unique X positions"); Prepared=R.bSetGeneratorTree ? GeneratorExpression(R) : Prepare(Concrete(R.ClassPath,UEnvQueryGenerator::StaticClass())->GetDefaultObject(),R); Changed=true; }
 else if(Op==TEXT("replace_generators"))
 {
  N=Find(M,R.NodeGuid); if(!M.Options.Contains(N) || N->bIsReadOnly) throw std::runtime_error("Generator replacement requires a writable option"); Prepared=GeneratorExpression(R); auto* O=CastChecked<UEnvQueryOption>(N->NodeInstance); auto* G=CastChecked<UEnvQueryGenerator>(Prepared.Get());
  for(UAIGraphNode* T:N->SubNodes) if(!CastChecked<UEnvQueryTest>(T->NodeInstance)->IsSupportedItem(G->ItemType)) throw std::runtime_error("Replacement generator item type is incompatible with attached tests"); Changed=!SameGenerators(O->Generator,G);
 }
 else if(Op==TEXT("create_test")) { Parent=Find(M,R.ParentGuid); if(!M.Options.Contains(Parent) || Parent->SubNodes.Num()>=64 || M.Tests.Num()>=512 || R.Index>Parent->SubNodes.Num()) throw std::runtime_error("Test requires an option, valid insertion index and available capacity"); Prepared=Prepare(Concrete(R.ClassPath,UEnvQueryTest::StaticClass())->GetDefaultObject(),R); if(!CastChecked<UEnvQueryTest>(Prepared.Get())->IsSupportedItem(CastChecked<UEnvQueryOption>(Parent->NodeInstance)->Generator->ItemType)) throw std::runtime_error("Test does not support the generator item type"); Changed=true; }
 else if(Op==TEXT("update") || Op==TEXT("delete"))
 {
  N=Find(M,R.NodeGuid); if((Operation.EndsWith(TEXT("_option")) && !M.Options.Contains(N)) || (Operation.EndsWith(TEXT("_test")) && !M.Tests.Contains(N))) throw std::runtime_error("Node kind does not match the EQS route"); if(N->bIsReadOnly) throw std::runtime_error("Read-only EQS node"); Parent=M.Parents.FindRef(N);
  if(Op==TEXT("delete")) { if(!R.bConfirm) throw std::runtime_error("EQS node deletion requires bConfirm=true"); Changed=true; }
  else
  {
   if(!R.ClassPath.IsEmpty()) throw std::runtime_error("Class replacement requires deleting/recreating the option/test");
   auto* Target=Parent ? N->NodeInstance.Get() : static_cast<UObject*>(CastChecked<UEnvQueryOption>(N->NodeInstance)->Generator.Get()); Prepared=Prepare(Target,R); Changed=!Same(Target,Prepared.Get(),R);
   if(R.bSetEnabled) { if(!Parent) throw std::runtime_error("Enabled applies only to tests"); Changed|=Enabled(N)!=R.bEnabled; }
   if(R.Index!=-1) { if(!Parent || R.Index>=Parent->SubNodes.Num()) throw std::runtime_error("Test reorder requires an existing array index"); Changed|=Parent->SubNodes.IndexOfByKey(N)!=R.Index; }
  }
 }
 else if(Op==TEXT("layout")) { if(R.Positions.Num()>65) throw std::runtime_error("EQS layout capacity exceeded"); TSet<UAIGraphNode*> Seen; TMap<UAIGraphNode*,int32> X; for(auto* O:M.Options) X.Add(O,O->NodePosX); for(const auto& P:R.Positions) { auto* V=Find(M,P.NodeGuid); if(!M.Options.Contains(V) || Seen.Contains(V) || FMath::Abs(int64(P.X))>1000000 || FMath::Abs(int64(P.Y))>1000000) throw std::runtime_error("Layout requires unique option nodes and bounded positions"); Seen.Add(V); X[V]=P.X; Changed|=V->NodePosX!=P.X || V->NodePosY!=P.Y; } TSet<int32> Xs; for(const auto& Pair:X) { if(Xs.Contains(Pair.Value)) throw std::runtime_error("Option X positions must remain unique"); Xs.Add(Pair.Value); } }
 else if(Op==TEXT("compile")) Changed=true; else throw std::runtime_error("Unknown EQS operation");
 UObject* Target=(Op==TEXT("update") || Op==TEXT("replace_generators")) ? (Parent ? N->NodeInstance.Get() : static_cast<UObject*>(CastChecked<UEnvQueryOption>(N->NodeInstance)->Generator.Get())) : nullptr;
 if(Prepared && Prepared->IsA<UEnvQueryGenerator>()) { const int32 Old=Target ? GeneratorNodes(CastChecked<UEnvQueryGenerator>(Target),Q).Num() : 0; if(M.Generators.Num()-Old+GeneratorNodes(CastChecked<UEnvQueryGenerator>(Prepared.Get()),Prepared.Get()).Num()>512) throw std::runtime_error("Query exceeds 512 total generators"); }
 Parameters(Q,M,Target,Prepared.Get(),Op==TEXT("delete") ? N : nullptr);
 if(Changed && !R.bDryRun)
 {
  FScopedTransaction Transaction(NSLOCTEXT("UE5MCP","EQSEdit","Edit Environment Query")); Modify(Q,M);
  if(Op==TEXT("initialize")) { TGuardValue<ITransaction*> Guard(GUndo,nullptr); auto* G=CastChecked<UAIGraph>(FBlueprintEditorUtils::CreateNewGraph(Q,NAME_None,Native(TEXT("EnvironmentQueryGraph")),Native(TEXT("EdGraphSchema_EnvironmentQuery")))); Q->EdGraph=G; G->LockUpdates(); G->GetSchema()->CreateDefaultNodesForGraph(*G); G->OnCreated(); G->Initialize(); G->UnlockUpdates(); }
  else
  {
   M.Graph->LockUpdates();
   if(Op==TEXT("create_option")) { N=NewObject<UAIGraphNode>(M.Graph,Native(TEXT("EnvironmentQueryGraphNode_Option")),NAME_None,RF_Transactional); UAIGraphNode::UpdateNodeClassDataFrom(Prepared->GetClass(),N->ClassData); M.Graph->AddNode(N,false,false); N->CreateNewGuid(); N->NodePosX=R.X; N->NodePosY=R.Y; N->PostPlacedNewNode(); N->AllocateDefaultPins(); if(R.bSetGeneratorTree) CastChecked<UEnvQueryOption>(N->NodeInstance)->Generator=PersistGenerator(CastChecked<UEnvQueryGenerator>(Prepared.Get()),Q); else Apply(CastChecked<UEnvQueryOption>(N->NodeInstance)->Generator,Prepared.Get(),R); if(!M.Graph->GetSchema()->TryCreateConnection(M.Root->GetOutputPin(),N->GetInputPin())) throw std::runtime_error("Native EQS schema failed root connection"); }
   else if(Op==TEXT("replace_generators")) { CastChecked<UEnvQueryOption>(N->NodeInstance)->Generator=PersistGenerator(CastChecked<UEnvQueryGenerator>(Prepared.Get()),Q); UAIGraphNode::UpdateNodeClassDataFrom(Prepared->GetClass(),N->ClassData); }
   else if(Op==TEXT("create_test")) { N=NewObject<UAIGraphNode>(M.Graph,Native(TEXT("EnvironmentQueryGraphNode_Test")),NAME_None,RF_Transactional); UAIGraphNode::UpdateNodeClassDataFrom(Prepared->GetClass(),N->ClassData); Parent->AddSubNode(N,M.Graph); Apply(N->NodeInstance,Prepared.Get(),R); N->InitializeInstance(); if(R.bSetEnabled) Enable(N,R.bEnabled); if(R.Index!=-1) { Parent->SubNodes.Remove(N); Parent->SubNodes.Insert(N,R.Index); } }
   else if(Op==TEXT("update")) { Apply(Parent ? N->NodeInstance.Get() : static_cast<UObject*>(CastChecked<UEnvQueryOption>(N->NodeInstance)->Generator.Get()),Prepared.Get(),R); if(Parent) N->InitializeInstance(); if(R.bSetEnabled) Enable(N,R.bEnabled); if(R.Index!=-1) { Parent->SubNodes.Remove(N); Parent->SubNodes.Insert(N,R.Index); } }
   else if(Op==TEXT("delete")) { if(Parent) N->ParentNode=Parent; N->DestroyNode(); }
   else if(Op==TEXT("layout")) for(const auto& P:R.Positions) { auto* V=Find(M,P.NodeGuid); V->NodePosX=P.X; V->NodePosY=P.Y; }
   M.Graph->UnlockUpdates(); M.Graph->NotifyGraphChanged();
  }
  Q->MarkPackageDirty();
 }
 bool Saved=false; if(R.bSave && !R.bDryRun) { Saved=GEditor->GetEditorSubsystem<UEditorAssetSubsystem>()->SaveLoadedAsset(Q,false); if(!Saved) throw std::runtime_error("EQS changed but save failed"); } return Json(Q,Changed,R.bDryRun,Saved,Op==TEXT("delete") ? nullptr : N);
}

UEnvQuery* EnvironmentQueryUtils::ValidateForRuntime(const FString& Path)
{
 auto* Q=Load(Path); TSharedPtr<FJsonObject> J; const FString Snapshot=Json(Q);
 if(!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Snapshot),J) || !J->GetBoolField(TEXT("valid"))) throw std::runtime_error("Runtime EQS requires a valid compiled native graph; inspect/compile the asset before PIE"); return Q;
}
