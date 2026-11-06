#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "UE5_MCP/Core/BlackboardUtils.h"
#include "UE5_MCP/Core/BlackboardKeySettingsUtils.h"
#include "UE5_MCP/API/DTO/BlackboardKeyReq.h"
#include "BehaviorTree/BlackboardData.h"
#include "BehaviorTree/BlackboardComponent.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Bool.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Int.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Float.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Name.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_String.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Vector.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Rotator.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Object.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Class.h"
#include "BehaviorTree/Blackboard/BlackboardKeyType_Enum.h"
#include "Navigation/PathFollowingComponent.h"
#include "GameFramework/Character.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Editor.h"
#include "UObject/Package.h"
#include "AITypes.h"
#include "Engine/World.h"
#include <stdexcept>

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBlackboardDefaultsTest,"UE5MCP.Blackboard.NativeDefaults",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FBlackboardDefaultsTest::RunTest(const FString&)
{
 const FString Id=FGuid::NewGuid().ToString(EGuidFormats::Digits);
 auto* Package=CreatePackage(*(TEXT("/Game/UE5MCP_Test/BB_DefaultAutomation_")+Id));
 auto* B=NewObject<UBlackboardData>(Package,*FString(TEXT("BB_DefaultAutomation_")+Id),RF_Public|RF_Standalone|RF_Transactional);
 FAssetRegistryModule::AssetCreated(B);
 ON_SCOPE_EXIT { FAssetRegistryModule::AssetDeleted(B); B->ClearFlags(RF_Public|RF_Standalone); B->MarkAsGarbage(); Package->SetDirtyFlag(false); };
 UWorld::InitializationValues Values; Values.AllowAudioPlayback(false).CreatePhysicsScene(false).CreateNavigation(false).CreateAISystem(true).ShouldSimulatePhysics(false).SetTransactional(false).CreateFXSystem(false);
 auto* World=UWorld::CreateWorld(EWorldType::Game,false,NAME_None,nullptr,true,ERHIFeatureLevel::Num,&Values);
 if(!TestNotNull(TEXT("Owned transient test world"),World)) return false;
 ON_SCOPE_EXIT { World->DestroyWorld(false); };
 World->CreateAISystem(); auto* Actor=World->SpawnActor<AActor>();
 if(!TestNotNull(TEXT("Owned component actor"),Actor)) return false;
 auto Key=[&](const TCHAR* Name) { return B->GetKey(B->GetKeyID(Name))->KeyType.Get(); };
 auto Add=[&](const TCHAR* Name,const TCHAR* Type,FBlackboardTypeSettings Settings)
 {
  FBlackboardKeyReq R; R.AssetPath=B->GetPathName(); R.KeyName=Name; R.KeyType=FString(TEXT("/Script/AIModule.BlackboardKeyType_"))+Type; R.bSetTypeSettings=true; R.TypeSettings=Settings;
  BlackboardUtils::Control(R,TEXT("add"));
 };
 auto Initialized=[&]<typename T>(const TCHAR* Name,const typename T::FDataType& Want)
 {
  TStrongObjectPtr<UBlackboardComponent> Runtime(NewObject<UBlackboardComponent>(Actor));
  Runtime->RegisterComponentWithWorld(World); if(!Runtime->HasBeenInitialized()) Runtime->InitializeComponent();
  ON_SCOPE_EXIT { Runtime->DestroyComponent(); };
  if(TestTrue(FString(Name)+TEXT(" native InitializeBlackboard"),Runtime->InitializeBlackboard(*B)))
   TestEqual(FString(Name)+TEXT(" native component GetValue"),Runtime->GetValue<T>(FName(Name)),Want);
 };
 try
 {
  const FString CDO=BlackboardKeySettingsUtils::Snapshot(GetMutableDefault<UBlackboardKeyType_Bool>());
  FBlackboardTypeSettings S; S.bSetDefault=true; S.BoolValue=true; Add(TEXT("Bool"),TEXT("Bool"),S); Initialized.template operator()<UBlackboardKeyType_Bool>(TEXT("Bool"),true);
  TestEqual(TEXT("Native CDO unchanged"),BlackboardKeySettingsUtils::Snapshot(GetMutableDefault<UBlackboardKeyType_Bool>()),CDO);
  S={}; S.bSetDefault=true; S.IntValue=-42; Add(TEXT("Int"),TEXT("Int"),S); Initialized.template operator()<UBlackboardKeyType_Int>(TEXT("Int"),-42);
  S={}; S.bSetDefault=true; S.FloatValue=1.25; Add(TEXT("Float"),TEXT("Float"),S); Initialized.template operator()<UBlackboardKeyType_Float>(TEXT("Float"),1.25f);
  S={}; S.bSetDefault=true; S.TextValue=TEXT("Goal"); Add(TEXT("Name"),TEXT("Name"),S); Initialized.template operator()<UBlackboardKeyType_Name>(TEXT("Name"),FName(TEXT("Goal")));
  S.TextValue=TEXT("route\nstep"); Add(TEXT("String"),TEXT("String"),S); Initialized.template operator()<UBlackboardKeyType_String>(TEXT("String"),S.TextValue);
  TestTrue(TEXT("Runtime string copy does not alter the asset's StringValue"),CastChecked<UBlackboardKeyType_String>(Key(TEXT("String")))->StringValue.IsEmpty());
  S={}; S.bSetDefault=true; S.VectorValue=FVector(120,30,40); S.bSetUseDefault=true; S.bUseDefault=true; Add(TEXT("Vector"),TEXT("Vector"),S); Initialized.template operator()<UBlackboardKeyType_Vector>(TEXT("Vector"),S.VectorValue);
  S.bUseDefault=false; Add(TEXT("UnsetVector"),TEXT("Vector"),S); Initialized.template operator()<UBlackboardKeyType_Vector>(TEXT("UnsetVector"),FAISystem::InvalidLocation);
  S={}; S.bSetDefault=true; S.RotationValue=FRotator(10,90,-20); S.bSetUseDefault=true; S.bUseDefault=true; Add(TEXT("Rotator"),TEXT("Rotator"),S); Initialized.template operator()<UBlackboardKeyType_Rotator>(TEXT("Rotator"),S.RotationValue);
  S.bUseDefault=false; Add(TEXT("UnsetRotator"),TEXT("Rotator"),S); Initialized.template operator()<UBlackboardKeyType_Rotator>(TEXT("UnsetRotator"),FAISystem::InvalidRotation);
  auto* Cube=LoadObject<UObject>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube"));
  S={}; S.bSetDefault=true; S.ReferenceValue=Cube->GetPathName(); S.bSetBaseClass=true; S.BaseClass=TEXT("/Script/Engine.StaticMesh"); Add(TEXT("Object"),TEXT("Object"),S); Initialized.template operator()<UBlackboardKeyType_Object>(TEXT("Object"),Cube);
  S.ReferenceValue=TEXT("/Script/Engine.Character"); S.BaseClass=TEXT("/Script/Engine.Pawn"); Add(TEXT("Class"),TEXT("Class"),S); Initialized.template operator()<UBlackboardKeyType_Class>(TEXT("Class"),ACharacter::StaticClass());
  S={}; S.bSetDefault=true; S.IntValue=EPathFollowingStatus::Moving; S.bSetEnumType=true; S.EnumTypePath=StaticEnum<EPathFollowingStatus::Type>()->GetPathName(); Add(TEXT("Enum"),TEXT("Enum"),S); Initialized.template operator()<UBlackboardKeyType_Enum>(TEXT("Enum"),uint8(EPathFollowingStatus::Moving));
  FBlackboardKeyReq R; R.AssetPath=B->GetPathName(); R.KeyName=TEXT("Enum"); R.bSetTypeSettings=true; R.TypeSettings.bSetNativeEnumName=true; R.TypeSettings.NativeEnumName=S.EnumTypePath;
  BlackboardUtils::Control(R,TEXT("update")); TestTrue(TEXT("Native EnumName resolved"),CastChecked<UBlackboardKeyType_Enum>(Key(TEXT("Enum")))->bIsEnumNameValid);
  R.TypeSettings.NativeEnumName.Empty(); BlackboardUtils::Control(R,TEXT("update")); TestFalse(TEXT("Native enum override cleared"),CastChecked<UBlackboardKeyType_Enum>(Key(TEXT("Enum")))->bIsEnumNameValid);
  Initialized.template operator()<UBlackboardKeyType_Enum>(TEXT("Enum"),uint8(EPathFollowingStatus::Moving));
  R={}; R.AssetPath=B->GetPathName(); R.KeyName=TEXT("Int"); R.bSetTypeSettings=true; R.TypeSettings.bSetDefault=true; R.TypeSettings.IntValue=50; BlackboardUtils::Control(R,TEXT("update"));
  Initialized.template operator()<UBlackboardKeyType_Int>(TEXT("Int"),50); TestTrue(TEXT("Undo default"),GEditor->UndoTransaction()); Initialized.template operator()<UBlackboardKeyType_Int>(TEXT("Int"),-42); TestTrue(TEXT("Redo default"),GEditor->RedoTransaction()); Initialized.template operator()<UBlackboardKeyType_Int>(TEXT("Int"),50);
  auto* Invalid=NewObject<UEnum>(Package,TEXT("InvalidByteEnum")); TArray<TPair<FName,int64>> Names={{TEXT("Negative"),-1},{TEXT("Positive"),1}}; Invalid->SetEnums(Names,UEnum::ECppForm::Regular,EEnumFlags::None,false);
  const FString Before=BlackboardUtils::Inspect(B->GetPathName()); R={}; R.AssetPath=B->GetPathName(); R.KeyName=TEXT("Enum"); R.NewKeyName=TEXT("MustNotApply"); R.bSetTypeSettings=true; R.TypeSettings.bSetEnumType=true; R.TypeSettings.EnumTypePath=Invalid->GetPathName();
  bool Rejected=false; try { BlackboardUtils::Control(R,TEXT("update")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Reject invalid signed Enum before native modal handler"),Rejected); TestEqual(TEXT("Rejected mixed update preserves Blackboard"),BlackboardUtils::Inspect(B->GetPathName()),Before);
  FBlackboardEntry Missing; Missing.EntryName=TEXT("MissingType"); B->Keys.Add(Missing);
  R={}; R.AssetPath=B->GetPathName(); R.KeyName=TEXT("MissingType"); R.bSetTypeSettings=true;
  Rejected=false; try { BlackboardUtils::Control(R,TEXT("update")); } catch(const std::exception&) { Rejected=true; }
  TestTrue(TEXT("Missing key type rejects settings without dereference"),Rejected);
  return true;
 }
 catch(const std::exception& E) { AddError(UTF8_TO_TCHAR(E.what())); return false; }
}
#endif
