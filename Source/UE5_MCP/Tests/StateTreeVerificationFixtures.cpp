#include "StateTreeVerificationFixtures.h"
#include "StateTreeExecutionContext.h"
#include "UObject/UnrealType.h"

EStateTreeRunStatus FMCPVerificationContainerTask::EnterState(FStateTreeExecutionContext& Context,const FStateTreeTransitionResult&) const
{
 const auto& Data=Context.GetInstanceData(*this);
 ObservedSum=0;
 ++Executions;
 for(float Value:Data.Samples) ObservedSum+=Value;
 for(int32 Value:Data.Codes) ObservedSum+=Value;
 for(const auto& Pair:Data.Scores) ObservedSum+=Pair.Value;
 return FMath::IsNearlyEqual(ObservedSum,Data.Expected) ? EStateTreeRunStatus::Succeeded : EStateTreeRunStatus::Failed;
}

EStateTreeRunStatus UMCPVerificationBlueprintTask::EnterState(FStateTreeExecutionContext& Context,const FStateTreeTransitionResult&)
{
 ++Executions;
 ObservedAmount=Amount;
 ProducedValue=Amount*2;
 ObservedEventCount=Context.GetEventsToProcessView().Num();
 ObservedExtra=0;
 if(const auto* Property=FindFProperty<FFloatProperty>(GetClass(),TEXT("Extra"))) ObservedExtra=Property->GetPropertyValue_InContainer(this);
 return bSucceed ? EStateTreeRunStatus::Succeeded : EStateTreeRunStatus::Failed;
}

void FMCPVerificationReferenceFunction::Execute(FStateTreeExecutionContext& Context) const
{
 auto& Data=Context.GetInstanceData(*this);
 Data.Result=(IsValid(Data.Material.Get()) ? 1.f : 0.f)
  +(!Data.SoftMaterial.IsNull() ? 2.f : 0.f)
  +(Data.ActorClass.Get()!=nullptr ? 4.f : 0.f)
  +(!Data.SoftActorClass.IsNull() ? 8.f : 0.f);
}
