#include "AnimationBlueprintUtils.h"
#include "UE5_MCP/API/DTO/AnimationTransitionReq.h"
#include "UE5_MCP/API/DTO/AnimationPoseLinkReq.h"
#include "UE5_MCP/API/DTO/AnimationStateMachineReq.h"

#include "Animation/AnimBlueprint.h"
#include "Animation/Skeleton.h"
#include "AnimationGraph.h"
#include "AnimationStateGraph.h"
#include "AnimationStateMachineGraph.h"
#include "AnimationStateMachineSchema.h"
#include "AnimationTransitionGraph.h"
#include "AnimGraphNode_StateMachineBase.h"
#include "AnimStateEntryNode.h"
#include "AnimStateNode.h"
#include "AnimStateNodeBase.h"
#include "AnimStateTransitionNode.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "Serialization/JsonWriter.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "ScopedTransaction.h"

#include <stdexcept>

namespace
{
	FString NodeId(const UEdGraphNode* Node)
	{
		return Node ? Node->NodeGuid.ToString(EGuidFormats::DigitsWithHyphens) : TEXT("");
	}

	bool IsPosePin(const UEdGraphPin* Pin)
	{
		const UObject* Type = Pin ? Pin->PinType.PinSubCategoryObject.Get() : nullptr;
		return Type && Type->GetName().Contains(TEXT("PoseLink"));
	}

	void WriteGraphDescriptor(const UEdGraph* Graph, TSharedRef<TJsonWriter<>>& Writer)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("path"), Graph->GetPathName());
		Writer->WriteValue(TEXT("name"), Graph->GetName());
		Writer->WriteValue(TEXT("class"), Graph->GetClass()->GetPathName());
		Writer->WriteValue(TEXT("node_count"), Graph->Nodes.Num());
		Writer->WriteValue(TEXT("schema"), Graph->GetSchema() ? Graph->GetSchema()->GetClass()->GetPathName() : TEXT(""));
		Writer->WriteObjectEnd();
	}

	void WriteNode(UEdGraphNode* Node, TSharedRef<TJsonWriter<>>& Writer)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("id"), NodeId(Node));
		Writer->WriteValue(TEXT("name"), Node->GetName());
		Writer->WriteValue(TEXT("title"), Node->GetNodeTitle(ENodeTitleType::ListView).ToString());
		Writer->WriteValue(TEXT("class"), Node->GetClass()->GetPathName());
		Writer->WriteValue(TEXT("x"), Node->NodePosX);
		Writer->WriteValue(TEXT("y"), Node->NodePosY);
		if (const UAnimGraphNode_StateMachineBase* Machine = Cast<UAnimGraphNode_StateMachineBase>(Node))
			Writer->WriteValue(TEXT("state_machine_graph"), Machine->EditorStateMachineGraph ? Machine->EditorStateMachineGraph->GetPathName() : TEXT(""));
		if (const UAnimStateNode* State = Cast<UAnimStateNode>(Node))
		{
			Writer->WriteValue(TEXT("state_name"), State->GetStateName());
			Writer->WriteValue(TEXT("bound_graph"), State->BoundGraph ? State->BoundGraph->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("always_reset_on_entry"), State->bAlwaysResetOnEntry);
			Writer->WriteValue(TEXT("state_type"), StaticEnum<EAnimStateType>()->GetNameStringByValue(State->StateType));
		}
		if (const UAnimStateTransitionNode* Transition = Cast<UAnimStateTransitionNode>(Node))
		{
			Writer->WriteValue(TEXT("from_state_id"), NodeId(Transition->GetPreviousState()));
			Writer->WriteValue(TEXT("to_state_id"), NodeId(Transition->GetNextState()));
			Writer->WriteValue(TEXT("rule_graph"), Transition->BoundGraph ? Transition->BoundGraph->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("custom_blend_graph"), Transition->GetCustomTransitionGraph() ? Transition->GetCustomTransitionGraph()->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("crossfade_duration"), Transition->CrossfadeDuration);
			Writer->WriteValue(TEXT("priority_order"), Transition->PriorityOrder);
			Writer->WriteValue(TEXT("blend_mode"), static_cast<int32>(Transition->BlendMode));
			Writer->WriteValue(TEXT("blend_mode_name"), StaticEnum<EAlphaBlendOption>()->GetNameStringByValue(static_cast<int64>(Transition->BlendMode)));
			Writer->WriteValue(TEXT("disabled"), Transition->bDisabled);
		}
		Writer->WriteArrayStart(TEXT("pins"));
		for (UEdGraphPin* Pin : Node->Pins)
		{
			if (!Pin) continue;
			Writer->WriteObjectStart();
			Writer->WriteValue(TEXT("name"), Pin->PinName.ToString());
			Writer->WriteValue(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
			Writer->WriteValue(TEXT("category"), Pin->PinType.PinCategory.ToString());
			Writer->WriteValue(TEXT("subcategory"), Pin->PinType.PinSubCategory.ToString());
			Writer->WriteValue(TEXT("subtype"), Pin->PinType.PinSubCategoryObject.IsValid() ? Pin->PinType.PinSubCategoryObject->GetPathName() : TEXT(""));
			Writer->WriteValue(TEXT("pose_link"), IsPosePin(Pin));
			Writer->WriteValue(TEXT("default_value"), Pin->DefaultValue);
			Writer->WriteArrayStart(TEXT("links"));
			for (UEdGraphPin* Linked : Pin->LinkedTo)
			{
				if (!Linked || !Linked->GetOwningNode()) continue;
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("node_id"), NodeId(Linked->GetOwningNode()));
				Writer->WriteValue(TEXT("pin_name"), Linked->PinName.ToString());
				Writer->WriteObjectEnd();
			}
			Writer->WriteArrayEnd();
			Writer->WriteObjectEnd();
		}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
	}
}

TArray<UEdGraph*> AnimationBlueprintUtils::AllGraphs(UAnimBlueprint* Blueprint)
{
	TArray<UEdGraph*> Collected;
	if (Blueprint) Blueprint->GetAllGraphs(Collected);
	TArray<UEdGraph*> Unique;
	TSet<UEdGraph*> Seen;
	for (UEdGraph* Graph : Collected)
		if (Graph && !Seen.Contains(Graph)) { Seen.Add(Graph); Unique.Add(Graph); }
	return Unique;
}

UEdGraph* AnimationBlueprintUtils::FindGraph(UAnimBlueprint* Blueprint, const FString& GraphPath)
{
	if (GraphPath.IsEmpty()) throw std::runtime_error("graph_path is required");
	UEdGraph* Match = nullptr;
	for (UEdGraph* Graph : AllGraphs(Blueprint))
	{
		if (Graph->GetPathName() == GraphPath) return Graph;
		if (Graph->GetName() == GraphPath)
		{
			if (Match) throw std::runtime_error("graph name is ambiguous; use the full graph path");
			Match = Graph;
		}
	}
	if (!Match) throw std::runtime_error("Graph was not found in the Animation Blueprint");
	return Match;
}

FString AnimationBlueprintUtils::InspectJson(UAnimBlueprint* Blueprint)
{
	const TArray<UEdGraph*> Graphs = AllGraphs(Blueprint);
	int32 Machines = 0, States = 0, Transitions = 0, PoseLinks = 0;
	for (UEdGraph* Graph : Graphs)
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (!Node) continue;
			Machines += Cast<UAnimGraphNode_StateMachineBase>(Node) != nullptr;
			States += Cast<UAnimStateNode>(Node) != nullptr;
			Transitions += Cast<UAnimStateTransitionNode>(Node) != nullptr;
			for (UEdGraphPin* Pin : Node->Pins) PoseLinks += IsPosePin(Pin);
		}
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Blueprint->GetPathName());
	Writer->WriteValue(TEXT("target_skeleton"), Blueprint->TargetSkeleton ? Blueprint->TargetSkeleton->GetPathName() : TEXT(""));
	Writer->WriteValue(TEXT("parent_class"), Blueprint->ParentClass ? Blueprint->ParentClass->GetPathName() : TEXT(""));
	Writer->WriteValue(TEXT("generated_class"), Blueprint->GeneratedClass ? Blueprint->GeneratedClass->GetPathName() : TEXT(""));
	Writer->WriteValue(TEXT("status"), static_cast<int32>(Blueprint->Status));
	Writer->WriteValue(TEXT("multithreaded_update"), Blueprint->bUseMultiThreadedAnimationUpdate);
	Writer->WriteValue(TEXT("graph_count"), Graphs.Num());
	Writer->WriteValue(TEXT("variable_count"), Blueprint->NewVariables.Num());
	Writer->WriteValue(TEXT("state_machine_count"), Machines);
	Writer->WriteValue(TEXT("state_count"), States);
	Writer->WriteValue(TEXT("transition_count"), Transitions);
	Writer->WriteValue(TEXT("pose_link_pin_count"), PoseLinks);
	Writer->WriteValue(TEXT("dirty"), Blueprint->GetOutermost()->IsDirty());
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString AnimationBlueprintUtils::GraphsJson(UAnimBlueprint* Blueprint)
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Blueprint->GetPathName());
	Writer->WriteArrayStart(TEXT("graphs"));
	for (UEdGraph* Graph : AllGraphs(Blueprint)) WriteGraphDescriptor(Graph, Writer);
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString AnimationBlueprintUtils::GraphJson(UAnimBlueprint* Blueprint, UEdGraph* Graph)
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Blueprint->GetPathName());
	Writer->WriteValue(TEXT("graph_path"), Graph->GetPathName());
	Writer->WriteValue(TEXT("graph_class"), Graph->GetClass()->GetPathName());
	Writer->WriteArrayStart(TEXT("nodes"));
	for (UEdGraphNode* Node : Graph->Nodes) if (Node) WriteNode(Node, Writer);
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString AnimationBlueprintUtils::StateMachinesJson(UAnimBlueprint* Blueprint)
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Blueprint->GetPathName());
	Writer->WriteArrayStart(TEXT("state_machines"));
	for (UEdGraph* Graph : AllGraphs(Blueprint))
	{
		UAnimationStateMachineGraph* Machine = Cast<UAnimationStateMachineGraph>(Graph);
		if (!Machine) continue;
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("graph_path"), Machine->GetPathName());
		Writer->WriteValue(TEXT("owner_node_id"), NodeId(Machine->OwnerAnimGraphNode));
		Writer->WriteValue(TEXT("entry_node_id"), NodeId(Machine->EntryNode));
		Writer->WriteValue(TEXT("entry_target_id"), Machine->EntryNode ? NodeId(Machine->EntryNode->GetOutputNode()) : TEXT(""));
		Writer->WriteArrayStart(TEXT("states"));
		for (UEdGraphNode* Node : Machine->Nodes)
			if (const UAnimStateNode* State = Cast<UAnimStateNode>(Node))
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("id"), NodeId(State));
				Writer->WriteValue(TEXT("name"), State->GetStateName());
				Writer->WriteValue(TEXT("bound_graph"), State->BoundGraph ? State->BoundGraph->GetPathName() : TEXT(""));
				Writer->WriteValue(TEXT("always_reset_on_entry"), State->bAlwaysResetOnEntry);
				Writer->WriteValue(TEXT("state_type"), StaticEnum<EAnimStateType>()->GetNameStringByValue(State->StateType));
				Writer->WriteObjectEnd();
			}
		Writer->WriteArrayEnd();
		Writer->WriteArrayStart(TEXT("transitions"));
		for (UEdGraphNode* Node : Machine->Nodes)
			if (const UAnimStateTransitionNode* Transition = Cast<UAnimStateTransitionNode>(Node))
			{
				Writer->WriteObjectStart();
				Writer->WriteValue(TEXT("id"), NodeId(Transition));
				Writer->WriteValue(TEXT("from_state_id"), NodeId(Transition->GetPreviousState()));
				Writer->WriteValue(TEXT("to_state_id"), NodeId(Transition->GetNextState()));
				Writer->WriteValue(TEXT("rule_graph"), Transition->BoundGraph ? Transition->BoundGraph->GetPathName() : TEXT(""));
				Writer->WriteValue(TEXT("custom_blend_graph"), Transition->GetCustomTransitionGraph() ? Transition->GetCustomTransitionGraph()->GetPathName() : TEXT(""));
				Writer->WriteValue(TEXT("duration"), Transition->CrossfadeDuration);
				Writer->WriteValue(TEXT("priority"), Transition->PriorityOrder);
				Writer->WriteValue(TEXT("blend_mode"), static_cast<int32>(Transition->BlendMode));
				Writer->WriteValue(TEXT("blend_mode_name"), StaticEnum<EAlphaBlendOption>()->GetNameStringByValue(static_cast<int64>(Transition->BlendMode)));
				Writer->WriteValue(TEXT("automatic_rule"), Transition->bAutomaticRuleBasedOnSequencePlayerInState);
				Writer->WriteValue(TEXT("bidirectional"), Transition->Bidirectional);
				Writer->WriteValue(TEXT("disabled"), Transition->bDisabled);
				Writer->WriteObjectEnd();
			}
		Writer->WriteArrayEnd();
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString AnimationBlueprintUtils::VariablesJson(UAnimBlueprint* Blueprint)
{
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Blueprint->GetPathName());
	Writer->WriteArrayStart(TEXT("variables"));
	for (const FBPVariableDescription& Var : Blueprint->NewVariables)
	{
		Writer->WriteObjectStart();
		Writer->WriteValue(TEXT("name"), Var.VarName.ToString());
		Writer->WriteValue(TEXT("category"), Var.Category.ToString());
		Writer->WriteValue(TEXT("type_category"), Var.VarType.PinCategory.ToString());
		Writer->WriteValue(TEXT("type_subcategory"), Var.VarType.PinSubCategory.ToString());
		Writer->WriteValue(TEXT("type_object"), Var.VarType.PinSubCategoryObject.IsValid() ? Var.VarType.PinSubCategoryObject->GetPathName() : TEXT(""));
		Writer->WriteValue(TEXT("default_value"), Var.DefaultValue);
		Writer->WriteValue(TEXT("property_flags"), static_cast<int64>(Var.PropertyFlags));
		Writer->WriteObjectEnd();
	}
	Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

FString AnimationBlueprintUtils::ValidateJson(UAnimBlueprint* Blueprint)
{
	TArray<FString> Errors;
	TArray<FString> Warnings;
	const TArray<UEdGraph*> Graphs = AllGraphs(Blueprint);
	if (!Blueprint->TargetSkeleton) Errors.Add(TEXT("Target Skeleton is missing"));
	if (Graphs.IsEmpty()) Errors.Add(TEXT("Animation Blueprint has no graphs"));
	if (Blueprint->Status == BS_Error) Errors.Add(TEXT("Blueprint compiler status is error"));
	for (UEdGraph* Graph : Graphs)
	{
		TSet<FGuid> Ids;
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (!Node) { Errors.Add(FString::Printf(TEXT("Null node in graph %s"), *Graph->GetPathName())); continue; }
			if (!Node->NodeGuid.IsValid() || Ids.Contains(Node->NodeGuid))
				Errors.Add(FString::Printf(TEXT("Missing or duplicate node GUID in graph %s"), *Graph->GetPathName()));
			Ids.Add(Node->NodeGuid);
			for (UEdGraphPin* Pin : Node->Pins)
				if (Pin) for (UEdGraphPin* Linked : Pin->LinkedTo)
					if (!Linked || !Linked->GetOwningNode() || Linked->GetOwningNode()->GetGraph() != Graph)
						Errors.Add(FString::Printf(TEXT("Dangling or cross-graph pin link on node %s"), *Node->GetName()));
			if (const UAnimGraphNode_StateMachineBase* Owner = Cast<UAnimGraphNode_StateMachineBase>(Node))
				if (!Owner->EditorStateMachineGraph) Errors.Add(FString::Printf(TEXT("State-machine node has no graph: %s"), *Node->GetName()));
		}
		if (UAnimationStateMachineGraph* Machine = Cast<UAnimationStateMachineGraph>(Graph))
		{
			if (!Machine->EntryNode || !Machine->EntryNode->GetOutputNode())
				Errors.Add(FString::Printf(TEXT("State machine has no entry target: %s"), *Graph->GetPathName()));
			for (UEdGraphNode* Node : Machine->Nodes)
			{
				if (const UAnimStateNode* State = Cast<UAnimStateNode>(Node))
					if (!State->BoundGraph) Errors.Add(FString::Printf(TEXT("State has no pose graph: %s"), *State->GetStateName()));
				if (const UAnimStateTransitionNode* Transition = Cast<UAnimStateTransitionNode>(Node))
				{
					if (!Transition->GetPreviousState() || !Transition->GetNextState() || !Transition->BoundGraph)
						Errors.Add(FString::Printf(TEXT("Transition is disconnected or has no rule graph: %s"), *Node->GetName()));
					if (!FMath::IsFinite(Transition->CrossfadeDuration) || Transition->CrossfadeDuration < 0.0f)
						Errors.Add(FString::Printf(TEXT("Transition crossfade duration is invalid: %s"), *Node->GetName()));
				}
			}
		}
	}
	FString Json;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	Writer->WriteObjectStart();
	Writer->WriteValue(TEXT("asset_path"), Blueprint->GetPathName());
	Writer->WriteValue(TEXT("valid"), Errors.IsEmpty());
	Writer->WriteValue(TEXT("graph_count"), Graphs.Num());
	Writer->WriteValue(TEXT("status"), static_cast<int32>(Blueprint->Status));
	Writer->WriteArrayStart(TEXT("errors")); for (const FString& Error : Errors) Writer->WriteValue(Error); Writer->WriteArrayEnd();
	Writer->WriteArrayStart(TEXT("warnings")); for (const FString& Warning : Warnings) Writer->WriteValue(Warning); Writer->WriteArrayEnd();
	Writer->WriteObjectEnd(); Writer->Close();
	return Json;
}

bool AnimationBlueprintUtils::EditTransition(UAnimBlueprint* Blueprint, const FAnimationTransitionReq& Request)
{
	UAnimationStateMachineGraph* Machine = Cast<UAnimationStateMachineGraph>(FindGraph(Blueprint, Request.StateMachineGraphPath));
	if (!Machine) throw std::runtime_error("state_machine_graph_path must identify a state machine graph");
	FGuid Guid;
	if (!FGuid::Parse(Request.TransitionId, Guid) || !Guid.IsValid())
		throw std::runtime_error("transition_id must be a valid node GUID");
	UAnimStateTransitionNode* Transition = nullptr;
	for (UEdGraphNode* Node : Machine->Nodes)
		if (Node && Node->NodeGuid == Guid) { Transition = Cast<UAnimStateTransitionNode>(Node); break; }
	if (!Transition) throw std::runtime_error("transition_id was not found in the specified state machine");
	if (Request.bSetCrossfadeDuration && (!FMath::IsFinite(Request.CrossfadeDuration) || Request.CrossfadeDuration < 0.0f))
		throw std::runtime_error("crossfade_duration must be finite and nonnegative");
	if (Request.bSetPriorityOrder && Request.PriorityOrder < 0)
		throw std::runtime_error("priority_order must be nonnegative");
	EAlphaBlendOption Blend = Transition->BlendMode;
	if (Request.bSetBlendMode)
	{
		const int64 Value = StaticEnum<EAlphaBlendOption>()->GetValueByNameString(Request.BlendMode);
		if (Value < 0 || Value >= StaticEnum<EAlphaBlendOption>()->NumEnums() - 1)
			throw std::runtime_error("blend_mode must be an EAlphaBlendOption name such as Linear or HermiteCubic");
		Blend = static_cast<EAlphaBlendOption>(Value);
	}
	const bool bDurationChanged = Request.bSetCrossfadeDuration && Transition->CrossfadeDuration != Request.CrossfadeDuration;
	const bool bBlendChanged = Request.bSetBlendMode && Transition->BlendMode != Blend;
	const bool bPriorityChanged = Request.bSetPriorityOrder && Transition->PriorityOrder != Request.PriorityOrder;
	const bool bDisabledChanged = Request.bSetDisabled && Transition->bDisabled != Request.bDisabled;
	const bool bAutomaticChanged = Request.bSetAutomaticRule && Transition->bAutomaticRuleBasedOnSequencePlayerInState != Request.bAutomaticRule;
	const bool bChanged = bDurationChanged || bBlendChanged || bPriorityChanged || bDisabledChanged || bAutomaticChanged;
	if (!bChanged || Request.bDryRun) return bChanged;
	const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditAnimationTransition", "Edit Animation State Transition"));
	Blueprint->Modify(); Machine->Modify(); Transition->Modify();
	if (bDurationChanged) Transition->CrossfadeDuration = Request.CrossfadeDuration;
	if (bBlendChanged) Transition->BlendMode = Blend;
	if (bPriorityChanged) Transition->PriorityOrder = Request.PriorityOrder;
	if (bDisabledChanged) Transition->bDisabled = Request.bDisabled;
	if (bAutomaticChanged) Transition->bAutomaticRuleBasedOnSequencePlayerInState = Request.bAutomaticRule;
	auto NotifyChanged = [Transition](FName PropertyName)
	{
		FProperty* Property = FindFProperty<FProperty>(UAnimStateTransitionNode::StaticClass(), PropertyName);
		FPropertyChangedEvent Event(Property);
		Transition->PostEditChangeProperty(Event);
	};
	if (bDurationChanged) NotifyChanged(GET_MEMBER_NAME_CHECKED(UAnimStateTransitionNode, CrossfadeDuration));
	if (bBlendChanged) NotifyChanged(GET_MEMBER_NAME_CHECKED(UAnimStateTransitionNode, BlendMode));
	if (bPriorityChanged) NotifyChanged(GET_MEMBER_NAME_CHECKED(UAnimStateTransitionNode, PriorityOrder));
	if (bDisabledChanged) NotifyChanged(GET_MEMBER_NAME_CHECKED(UAnimStateTransitionNode, bDisabled));
	if (bAutomaticChanged) NotifyChanged(GET_MEMBER_NAME_CHECKED(UAnimStateTransitionNode, bAutomaticRuleBasedOnSequencePlayerInState));
	FBlueprintEditorUtils::MarkBlueprintAsModified(Blueprint);
	return true;
}

bool AnimationBlueprintUtils::EditPoseLink(UAnimBlueprint* Blueprint, const FAnimationPoseLinkReq& Request)
{
	UEdGraph* Graph = FindGraph(Blueprint, Request.GraphPath);
	const bool bConnect = Request.Operation.Equals(TEXT("connect"), ESearchCase::IgnoreCase);
	const bool bDisconnect = Request.Operation.Equals(TEXT("disconnect"), ESearchCase::IgnoreCase);
	if (!bConnect && !bDisconnect) throw std::runtime_error("operation must be connect or disconnect");
	FGuid OutputGuid, InputGuid;
	if (!FGuid::Parse(Request.OutputNodeId, OutputGuid) || !FGuid::Parse(Request.InputNodeId, InputGuid))
		throw std::runtime_error("output_node_id and input_node_id must be valid GUIDs");
	UEdGraphNode* OutputNode = nullptr;
	UEdGraphNode* InputNode = nullptr;
	for (UEdGraphNode* Node : Graph->Nodes)
	{
		if (!Node) continue;
		if (Node->NodeGuid == OutputGuid) OutputNode = Node;
		if (Node->NodeGuid == InputGuid) InputNode = Node;
	}
	if (!OutputNode || !InputNode) throw std::runtime_error("Both nodes must belong to the specified graph");
	UEdGraphPin* Output = OutputNode->FindPin(FName(*Request.OutputPinName));
	UEdGraphPin* Input = InputNode->FindPin(FName(*Request.InputPinName));
	if (!Output || !Input || Output->Direction != EGPD_Output || Input->Direction != EGPD_Input)
		throw std::runtime_error("output_pin_name and input_pin_name must identify opposite-direction pins");
	if (!IsPosePin(Output) || !IsPosePin(Input)) throw std::runtime_error("Both pins must carry a pose link");
	const UEdGraphSchema* Schema = Graph->GetSchema();
	if (!Schema) throw std::runtime_error("Graph has no schema");
	const bool bLinked = Output->LinkedTo.Contains(Input);
	if ((bConnect && bLinked) || (bDisconnect && !bLinked)) return false;
	if (bConnect)
	{
		const FPinConnectionResponse Response = Schema->CanCreateConnection(Output, Input);
		if (Response.Response == CONNECT_RESPONSE_DISALLOW)
			throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Pose link is disallowed: %s"), *Response.Message.ToString())));
		if (!Response.CanSafeConnect() && !Request.bConfirmReplace)
			throw std::runtime_error("Pose link would replace an existing link; confirm_replace=true is required");
	}
	if (Request.bDryRun) return true;
	const FScopedTransaction Transaction(NSLOCTEXT("UE5_MCP", "EditAnimationPoseLink", "Edit Animation Pose Link"));
	Blueprint->Modify(); Graph->Modify(); OutputNode->Modify(); InputNode->Modify();
	if (bConnect)
	{
		if (!Schema->TryCreateConnection(Output, Input)) throw std::runtime_error("Graph schema rejected the pose connection");
	}
	else Schema->BreakSinglePinLink(Output, Input);
	Graph->NotifyGraphChanged();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
	return true;
}

bool AnimationBlueprintUtils::EditStateMachine(UAnimBlueprint* Blueprint, const FAnimationStateMachineReq& Request, FGuid& OutNodeId)
{
	UAnimationStateMachineGraph* Machine = Cast<UAnimationStateMachineGraph>(FindGraph(Blueprint, Request.StateMachineGraphPath));
	if (!Machine) throw std::runtime_error("state_machine_graph_path must identify a state machine graph");
	const bool bAddState = Request.Operation.Equals(TEXT("add_state"), ESearchCase::IgnoreCase);
	const bool bRemoveState = Request.Operation.Equals(TEXT("remove_state"), ESearchCase::IgnoreCase);
	const bool bAddTransition = Request.Operation.Equals(TEXT("add_transition"), ESearchCase::IgnoreCase);
	const bool bRemoveTransition = Request.Operation.Equals(TEXT("remove_transition"), ESearchCase::IgnoreCase);
	const bool bSetEntry = Request.Operation.Equals(TEXT("set_entry"), ESearchCase::IgnoreCase);
	const bool bRenameState = Request.Operation.Equals(TEXT("rename_state"), ESearchCase::IgnoreCase);
	const bool bSetReset = Request.Operation.Equals(TEXT("set_reset"), ESearchCase::IgnoreCase);
	if (!bAddState && !bRemoveState && !bAddTransition && !bRemoveTransition && !bSetEntry && !bRenameState && !bSetReset)
		throw std::runtime_error("operation must be add_state, remove_state, add_transition, remove_transition, set_entry, rename_state, or set_reset");
	auto FindById = [Machine](const FString& Text) -> UEdGraphNode*
	{
		FGuid Id;
		if (!FGuid::Parse(Text, Id) || !Id.IsValid()) throw std::runtime_error("node ID must be a valid GUID");
		for (UEdGraphNode* Node : Machine->Nodes) if (Node && Node->NodeGuid == Id) return Node;
		throw std::runtime_error("node ID was not found in the specified state machine");
	};
	UAnimStateNodeBase* State = nullptr;
	UAnimStateNodeBase* From = nullptr;
	UAnimStateNodeBase* To = nullptr;
	UAnimStateTransitionNode* Transition = nullptr;
	if (bAddState)
	{
		if (Request.StateName.TrimStartAndEnd().IsEmpty()) throw std::runtime_error("state_name is required");
		for (UEdGraphNode* Node : Machine->Nodes)
			if (const UAnimStateNodeBase* Existing = Cast<UAnimStateNodeBase>(Node))
				if (!Cast<UAnimStateTransitionNode>(Existing) && FName(*Existing->GetStateName()) == FName(*Request.StateName))
					throw std::runtime_error("State name already exists in this machine");
	}
	else if (bRemoveState || bSetEntry || bRenameState || bSetReset)
	{
		State = Cast<UAnimStateNodeBase>(FindById(Request.NodeId));
		if (!State || Cast<UAnimStateTransitionNode>(State)) throw std::runtime_error("node_id must identify a state or conduit");
		OutNodeId = State->NodeGuid;
		if (bRemoveState)
		{
			if (!Request.bConfirm) throw std::runtime_error("state removal requires confirm=true");
			if (Machine->EntryNode && Machine->EntryNode->GetOutputNode() == State)
				throw std::runtime_error("Move the state-machine entry before removing its current target");
		}
		else if (bSetEntry && Machine->EntryNode && Machine->EntryNode->GetOutputNode() == State) return false;
		else if (bRenameState)
		{
			if (Request.StateName.TrimStartAndEnd().IsEmpty()) throw std::runtime_error("state_name is required");
			if (State->GetStateName() == Request.StateName) return false;
			for (UEdGraphNode* Node : Machine->Nodes)
				if (const UAnimStateNodeBase* Existing = Cast<UAnimStateNodeBase>(Node))
					if (Existing != State && !Cast<UAnimStateTransitionNode>(Existing)
						&& FName(*Existing->GetStateName()) == FName(*Request.StateName))
						throw std::runtime_error("State name already exists in this machine");
		}
		else if (bSetReset)
		{
			const UAnimStateNode* Typed = Cast<UAnimStateNode>(State);
			if (!Typed) throw std::runtime_error("set_reset requires a regular state node");
			if (Typed->bAlwaysResetOnEntry == Request.bAlwaysResetOnEntry) return false;
		}
	}
	else if (bAddTransition)
	{
		From = Cast<UAnimStateNodeBase>(FindById(Request.FromStateId));
		To = Cast<UAnimStateNodeBase>(FindById(Request.ToStateId));
		if (!From || !To || Cast<UAnimStateTransitionNode>(From) || Cast<UAnimStateTransitionNode>(To)
			|| !From->GetOutputPin() || !To->GetInputPin())
			throw std::runtime_error("from_state_id and to_state_id must identify connectable states in this machine");
	}
	else
	{
		Transition = Cast<UAnimStateTransitionNode>(FindById(Request.NodeId));
		if (!Transition) throw std::runtime_error("node_id must identify a transition");
		if (!Request.bConfirm) throw std::runtime_error("transition removal requires confirm=true");
		OutNodeId = Transition->NodeGuid;
	}
	if (Request.bDryRun) return true;
	const FScopedTransaction TransactionScope(NSLOCTEXT("UE5_MCP", "EditAnimationStateMachine", "Edit Animation State Machine"));
	Blueprint->Modify(); Machine->Modify();
	if (bAddState)
	{
		UAnimStateNode* Added = FEdGraphSchemaAction_NewStateNode::SpawnNodeFromTemplate<UAnimStateNode>(
			Machine, NewObject<UAnimStateNode>(), FVector2f(Request.X, Request.Y), false);
		if (!Added || !Added->BoundGraph) throw std::runtime_error("Unreal did not create the state and its pose graph");
		Added->OnRenameNode(Request.StateName);
		OutNodeId = Added->NodeGuid;
	}
	else if (bAddTransition)
	{
		UAnimStateTransitionNode* Added = FEdGraphSchemaAction_NewStateNode::SpawnNodeFromTemplate<UAnimStateTransitionNode>(
			Machine, NewObject<UAnimStateTransitionNode>(), FVector2f(Request.X, Request.Y), false);
		if (!Added || !Added->BoundGraph) throw std::runtime_error("Unreal did not create the transition rule graph");
		Added->CreateConnections(From, To);
		OutNodeId = Added->NodeGuid;
	}
	else if (bSetEntry)
	{
		if (!Machine->EntryNode || !Machine->EntryNode->GetOutputPin() || !State->GetInputPin())
			throw std::runtime_error("Entry or target state has no connection pin");
		if (!Machine->GetSchema()->TryCreateConnection(Machine->EntryNode->GetOutputPin(), State->GetInputPin()))
			throw std::runtime_error("State-machine schema rejected entry reassignment");
	}
	else if (bRenameState)
	{
		State->Modify();
		State->OnRenameNode(Request.StateName);
	}
	else if (bSetReset)
	{
		UAnimStateNode* Typed = CastChecked<UAnimStateNode>(State);
		Typed->Modify();
		Typed->bAlwaysResetOnEntry = Request.bAlwaysResetOnEntry;
		FProperty* Property = FindFProperty<FProperty>(UAnimStateNode::StaticClass(), GET_MEMBER_NAME_CHECKED(UAnimStateNode, bAlwaysResetOnEntry));
		FPropertyChangedEvent Event(Property);
		Typed->PostEditChangeProperty(Event);
	}
	else FBlueprintEditorUtils::RemoveNode(Blueprint, bRemoveState ? static_cast<UEdGraphNode*>(State) : static_cast<UEdGraphNode*>(Transition));
	Machine->NotifyGraphChanged();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
	return true;
}
