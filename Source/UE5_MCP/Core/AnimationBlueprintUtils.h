#pragma once

#include "CoreMinimal.h"

class UAnimBlueprint;
class UEdGraph;
struct FAnimationTransitionReq;
struct FAnimationPoseLinkReq;
struct FAnimationStateMachineReq;

namespace AnimationBlueprintUtils
{
	TArray<UEdGraph*> AllGraphs(UAnimBlueprint* Blueprint);
	UEdGraph* FindGraph(UAnimBlueprint* Blueprint, const FString& GraphPath);
	FString InspectJson(UAnimBlueprint* Blueprint);
	FString GraphsJson(UAnimBlueprint* Blueprint);
	FString GraphJson(UAnimBlueprint* Blueprint, UEdGraph* Graph);
	FString StateMachinesJson(UAnimBlueprint* Blueprint);
	FString VariablesJson(UAnimBlueprint* Blueprint);
	FString ValidateJson(UAnimBlueprint* Blueprint);
	bool EditTransition(UAnimBlueprint* Blueprint, const FAnimationTransitionReq& Request);
	bool EditPoseLink(UAnimBlueprint* Blueprint, const FAnimationPoseLinkReq& Request);
	bool EditStateMachine(UAnimBlueprint* Blueprint, const FAnimationStateMachineReq& Request, FGuid& OutNodeId);
}
