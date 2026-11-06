#include "GraphUtils.h"

#include "ClassUtils.h"
#include "EdGraphNode_Comment.h"
#include "K2Node_BreakStruct.h"
#include "K2Node_CallFunction.h"
#include "K2Node_CastByteToEnum.h"
#include "K2Node_ClassDynamicCast.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_DynamicCast.h"
#include "K2Node_ExecutionSequence.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_MakeStruct.h"
#include "K2Node_SwitchEnum.h"
#include "K2Node_SwitchInteger.h"
#include "K2Node_SwitchName.h"
#include "K2Node_SwitchString.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "PinUtils.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "AnimGraphNode_Base.h"
#include "Materials/MaterialExpression.h"



void GraphUtils::AddFunctionCallToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& FunctionName)
{
    if (!Blueprint || !Graph)
        throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

    auto BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");

    UFunction* TargetFunction = BPClass->FindFunctionByName(*FunctionName);
    if (!TargetFunction)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Function %s not found in Blueprint class"), *FunctionName)));

    FGraphNodeCreator<UK2Node_CallFunction> NodeCreator(*Graph);
    UK2Node_CallFunction* CallFuncNode = NodeCreator.CreateNode();
    CallFuncNode->SetFromFunction(TargetFunction);
    NodeCreator.Finalize();

    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddFunctionCallToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& ClassToCall,
	const FString& FunctionName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	auto TargetClass = ClassUtils::FindClassByName(ClassToCall);
	if (!TargetClass)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Class %s not found"), *ClassToCall)));

	UFunction* TargetFunction = TargetClass->FindFunctionByName(*FunctionName);
	if (!TargetFunction)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Function %s not found in class %s"), *FunctionName, *ClassToCall)));

	FGraphNodeCreator<UK2Node_CallFunction> NodeCreator(*Graph);
	UK2Node_CallFunction* CallFuncNode = NodeCreator.CreateNode();
	CallFuncNode->SetFromFunction(TargetFunction);
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

#include "Kismet/KismetMathLibrary.h"

void GraphUtils::AddMathFunctionCallToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& FunctionName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	UClass* MathClass = UKismetMathLibrary::StaticClass();
	UFunction* TargetFunction = MathClass->FindFunctionByName(*FunctionName);
	if (!TargetFunction)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Function %s not found in KismetMathLibrary"), *FunctionName)));
	
	FGraphNodeCreator<UK2Node_CallFunction> NodeCreator(*Graph);
	UK2Node_CallFunction* CallFuncNode = NodeCreator.CreateNode();
	CallFuncNode->SetFromFunction(TargetFunction);
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}



void GraphUtils::AddEventToGraph(UBlueprint* Blueprint,
                                 UEdGraph* Graph, const FString& EventName)
{
    if (!Blueprint || !Graph)
        throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
    
    UClass* BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");
    
    auto EventFunc = BPClass->FindFunctionByName(*EventName);
    if (!EventFunc)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Event %s not found in Blueprint class"), *EventName)));
    
    FGraphNodeCreator<UK2Node_Event> NodeCreator(*Graph);
    UK2Node_Event* EventNode = NodeCreator.CreateNode();
    EventNode->EventReference.SetFromField<UFunction>(EventFunc, true);
    EventNode->bOverrideFunction = true;
    NodeCreator.Finalize();

    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddCustomEventToGraph(
    UBlueprint* Blueprint,
    UEdGraph* Graph,
    const FString& EventName,
    const FString& EventSignature)
{
    if (!Blueprint || !Graph) return;

    // Create the node
    FGraphNodeCreator<UK2Node_CustomEvent> NodeCreator(*Graph);
    UK2Node_CustomEvent* CustomEventNode = NodeCreator.CreateNode();
    CustomEventNode->CustomFunctionName = *EventName;

    // Always has execution pin
    CustomEventNode->AllocateDefaultPins();

    TArray<FString> Params;
    FEdGraphPinType PinType;
    EventSignature.ParseIntoArray(Params, TEXT(","), true);
    for (FString& Param : Params)
    {
        FString TypeStr, NameStr;
        if (!PinUtils::SplitTypeVar(Param, TypeStr, NameStr))
        {
            UE_LOG(LogTemp, Warning, TEXT("Invalid parameter: %s"), *Param);
            continue;
        }
        
        NameStr = NameStr.TrimStartAndEnd();
        if (NameStr.IsEmpty())
        {
            UE_LOG(LogTemp, Warning, TEXT("Invalid parameter: %s"), *Param);
            continue;
        }
            
        if (PinUtils::ResolvePinTypeByName(TypeStr, PinType))
        {
            CustomEventNode->CreateUserDefinedPin(*NameStr, PinType, EGPD_Output);
        }
        else
        {
            UE_LOG(LogTemp, Warning, TEXT("Unknown type: %s"), *TypeStr);
        }
    }

    NodeCreator.Finalize();

    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

#include "EdGraph/EdGraph.h"
#include "EdGraphSchema_K2.h"


void GraphUtils::AddGetVariableNodeToGraph(
    UBlueprint* Blueprint, UEdGraph* Graph, const FString& VarName)
{
    if (!Blueprint || !Graph)
        throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

    auto BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");

    auto Var = BPClass->FindPropertyByName(*VarName);
    if ( !Var)
    {
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Variable %s not found in Blueprint class"), *VarName)));
    }

    FGraphNodeCreator<UK2Node_VariableGet> NodeCreator(*Graph);
    UK2Node_VariableGet* GetNode = NodeCreator.CreateNode();
    GetNode->VariableReference.SetSelfMember(*VarName);
    NodeCreator.Finalize();
    
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddSetVariableNodeToGraph(
    UBlueprint* Blueprint, UEdGraph* Graph, const FString& VarName)
{
    if (!Blueprint || !Graph)
        throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

    
    auto BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");

    auto Var = BPClass->FindPropertyByName(*VarName);
    if ( !Var)
    {
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Variable %s not found in Blueprint class"), *VarName)));
    }
    
    FGraphNodeCreator<UK2Node_VariableSet> NodeCreator(*Graph);
    UK2Node_VariableSet* SetNode = NodeCreator.CreateNode();
    SetNode->VariableReference.SetSelfMember(*VarName);
    NodeCreator.Finalize();

    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddBreakStructNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& StructTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	auto Struct = FindFirstObject<UScriptStruct>(*StructTypeName);
	if (!Struct)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Struct %s not found"), *StructTypeName)));

	FGraphNodeCreator<UK2Node_BreakStruct> NodeCreator(*Graph);
	UK2Node_BreakStruct* BreakStructNode = NodeCreator.CreateNode();
	BreakStructNode->StructType = Struct;
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddMakeStructNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& StructTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	auto Struct = FindFirstObject<UScriptStruct>(*StructTypeName);
	if (!Struct)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Struct %s not found"), *StructTypeName)));

	FGraphNodeCreator<UK2Node_MakeStruct> NodeCreator(*Graph);
	UK2Node_MakeStruct* MakeStructNode = NodeCreator.CreateNode();
	MakeStructNode->StructType = Struct;
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddCommentNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& CommentText)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	FGraphNodeCreator<UEdGraphNode_Comment> NodeCreator(*Graph);
	UEdGraphNode_Comment* CommentNode = NodeCreator.CreateNode();
	CommentNode->NodeComment = CommentText;
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

/*
void GraphUtils::AddSwitchEnumNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	UEnum* Enum = FindFirstObject<UEnum>(*PinTypeName);
	if (!Enum)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Enum %s not found"), *PinTypeName)));
	
	FGraphNodeCreator<UK2Node_SwitchEnum> NodeCreator(*Graph);
	UK2Node_SwitchEnum* SwitchEnumNode = NodeCreator.CreateNode();
	// some reason SetEnum doesn't work
	// unresolved external symbol "public: void __cdecl UK2Node_SwitchEnum::SetEnum(class UEnum *)"
	SwitchEnumNode->SetEnum(Enum);
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}*/

UClass* GraphUtils::FindK2NodeClassByName(const FString& NodeClassName)
{
	for (TObjectIterator<UClass> It; It; ++It)
	{
		UClass* Class = *It;
		if (Class->IsChildOf(UEdGraphNode::StaticClass()) &&
			(Class->GetName() == NodeClassName || Class->GetPathName() == NodeClassName))
		{
			return Class;
		}
	}
	return nullptr;
}


void GraphUtils::AddNodeByNameToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& NodeTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	UClass* NewNodeClass = FindK2NodeClassByName(NodeTypeName);
	if (!NewNodeClass)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Node type %s not found. get_supported_nodes lists the valid names."), *NodeTypeName)));

	auto NewNode = NewObject<UK2Node>(Graph, NewNodeClass);
	if (!NewNode)
		throw std::runtime_error("Failed to create node");

	NewNode->CreateNewGuid();
	NewNode->PostPlacedNewNode();
	NewNode->AllocateDefaultPins();
	Graph->AddNode(NewNode);
	
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddDynamicCastNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	auto TargetClass = ClassUtils::FindClassByName(PinTypeName);

	if (!TargetClass)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Class %s not found"), *PinTypeName)));

	FGraphNodeCreator<UK2Node_DynamicCast> NodeCreator(*Graph);
	UK2Node_DynamicCast* CastNode = NodeCreator.CreateNode();
	CastNode->TargetType = TargetClass;
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddClassCastNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
	auto TargetClass = ClassUtils::FindClassByName(PinTypeName);
	if (!TargetClass)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Class %s not found"), *PinTypeName)));

	FGraphNodeCreator<UK2Node_ClassDynamicCast> NodeCreator(*Graph);
	UK2Node_ClassDynamicCast* CastNode = NodeCreator.CreateNode();
	CastNode->TargetType = TargetClass;
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddByteToEnumNodeCastToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");

	auto Enum = FindFirstObject<UEnum>( *PinTypeName);
	if (!Enum)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Enum %s not found"), *PinTypeName)));

	FGraphNodeCreator<UK2Node_CastByteToEnum> NodeCreator(*Graph);
	UK2Node_CastByteToEnum* CastNode = NodeCreator.CreateNode();
	CastNode->Enum = Enum;
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddBranchNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
	FGraphNodeCreator<UK2Node_IfThenElse> NodeCreator(*Graph);
	NodeCreator.CreateNode();
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddExecutionSequenceNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, int32 OutputCount)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
	FGraphNodeCreator<UK2Node_ExecutionSequence> NodeCreator(*Graph);
	UK2Node_ExecutionSequence* Node = NodeCreator.CreateNode();
	NodeCreator.Finalize();
	for (int32 Index = 2; Index < FMath::Max(2, OutputCount); ++Index)
		Node->AddInputPin();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddSwitchEnumNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& EnumTypeName)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
	UEnum* Enum = FindFirstObject<UEnum>(*EnumTypeName);
	if (!Enum)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Enum %s not found"), *EnumTypeName)));
	FGraphNodeCreator<UK2Node_SwitchEnum> NodeCreator(*Graph);
	UK2Node_SwitchEnum* Node = NodeCreator.CreateNode();
	Node->SetEnum(Enum);
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddSwitchIntegerNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, int32 StartIndex)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
	FGraphNodeCreator<UK2Node_SwitchInteger> NodeCreator(*Graph);
	UK2Node_SwitchInteger* Node = NodeCreator.CreateNode();
	Node->StartIndex = StartIndex;
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddSwitchStringNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
	FGraphNodeCreator<UK2Node_SwitchString> NodeCreator(*Graph);
	NodeCreator.CreateNode();
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::AddSwitchNameNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph)
{
	if (!Blueprint || !Graph)
		throw std::runtime_error("Graph not found in this Blueprint. Use graph_name EventGraph or a function name; get_blueprint_graph lists its graphs.");
	FGraphNodeCreator<UK2Node_SwitchName> NodeCreator(*Graph);
	NodeCreator.CreateNode();
	NodeCreator.Finalize();
	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}


TArray<FString> GraphUtils::GetSupportedNode()
{
	TArray<FString> NodeTypes;
	for (TObjectIterator<UClass> It; It; ++It)
	{
		UClass* Class = *It;
		if (Class->IsChildOf(UK2Node::StaticClass()) && !Class->HasAnyClassFlags(CLASS_Abstract))
		{
			NodeTypes.Add(Class->GetName());
			// UE_LOG(LogTemp, Log, TEXT("Found K2Node class: %s"), *Class->GetName());
		}
	}
	return NodeTypes;
}

TArray<FString> GraphUtils::GetSupportedNodesForGraphType(const FString& GraphType)
{
	TArray<FString> NodeTypes;
	const FString Type = GraphType.ToLower();
	for (TObjectIterator<UClass> It; It; ++It)
	{
		UClass* Class = *It;
		if (!Class || Class->HasAnyClassFlags(CLASS_Abstract | CLASS_Deprecated))
			continue;

		bool bSupported = false;
		if (Type == TEXT("blueprint") || Type == TEXT("all"))
			bSupported |= Class->IsChildOf(UK2Node::StaticClass());
		if (Type == TEXT("animation") || Type == TEXT("animation_blueprint") || Type == TEXT("all"))
			bSupported |= Class->IsChildOf(UAnimGraphNode_Base::StaticClass());
		if (Type == TEXT("material") || Type == TEXT("all"))
			bSupported |= Class->IsChildOf(UMaterialExpression::StaticClass());

		if (bSupported)
			NodeTypes.AddUnique(Class->GetPathName());
	}
	NodeTypes.Sort();
	return NodeTypes;
}

UEdGraphNode* GraphUtils::GetNodeById(
	UEdGraph* Graph,
	const FGuid& NodeId)
{
	if (!Graph)
		throw std::runtime_error("Graph is null");

	for (UEdGraphNode* Node : Graph->Nodes)
	{
		if (!Node)
			continue;
		if (Node->NodeGuid == NodeId)
		{
			return Node;
		}
	}

	return nullptr;
}

static std::runtime_error PinNotFound(const UEdGraphNode* Node, const FString& PinName)
{
	TArray<FString> Pins;
	for (const UEdGraphPin* Pin : Node->Pins)
		Pins.Add(FString::Printf(TEXT("%s (%s %s)"), *Pin->PinName.ToString(), Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"), *Pin->PinType.PinCategory.ToString()));
	return std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Node '%s' has no pin '%s'. Its pins are: %s."),
		*Node->GetNodeTitle(ENodeTitleType::ListView).ToString(), *PinName, *FString::Join(Pins, TEXT(", ")))));
}

static std::runtime_error NodeNotFound(const FGuid& NodeId, const UEdGraph* Graph)
{
	return std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("No node with id %s in graph %s, which has %d nodes. get_graph lists the node ids."),
		*NodeId.ToString(), *Graph->GetName(), Graph->Nodes.Num())));
}

void GraphUtils::ConnectPins(
	UBlueprint* Blueprint,
	UEdGraph* Graph,
	const FGuid& OutputNodeId, const FString& OutputPinName,
	const FGuid& InputNodeId, const FString& InputPinName)
{
	if (!Blueprint)
		throw std::runtime_error("Blueprint is null");
    
	if (!Graph)
		throw std::runtime_error("Graph is null");

	UEdGraphNode* OutputNode = GetNodeById(Graph, OutputNodeId);
	UEdGraphNode* InputNode = GetNodeById(Graph, InputNodeId);

	if (!OutputNode) throw NodeNotFound(OutputNodeId, Graph);
	if (!InputNode) throw NodeNotFound(InputNodeId, Graph);

	// Find pins
	UEdGraphPin* OutPin = OutputNode->FindPin(OutputPinName);
	UEdGraphPin* InPin = InputNode->FindPin(InputPinName);

	if (!OutPin) throw PinNotFound(OutputNode, OutputPinName);
	if (!InPin) throw PinNotFound(InputNode, InputPinName);

	// The schema rejects bad links and notifies the nodes, which is how a cast or wildcard pin gets its type.
	const UEdGraphSchema* Schema = Graph->GetSchema();
	const FPinConnectionResponse Response = Schema->CanCreateConnection(OutPin, InPin);
	if (Response.Response == CONNECT_RESPONSE_DISALLOW)
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Cannot connect %s to %s: %s"), *OutputPinName, *InputPinName, *Response.Message.ToString())));
	if (!Schema->TryCreateConnection(OutPin, InPin))
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Graph schema rejected connecting %s to %s"), *OutputPinName, *InputPinName)));

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::BreakPinConnection(UBlueprint* Blueprint, UEdGraph* Graph, const FGuid& OutputNodeId,
	const FString& OutputPinName, const FGuid& InputNodeId, const FString& InputPinName)
{
	
	if (!Blueprint)
		throw std::runtime_error("Blueprint is null");
    
	if (!Graph)
		throw std::runtime_error("Graph is null");

	UEdGraphNode* OutputNode = GetNodeById(Graph, OutputNodeId);
	UEdGraphNode* InputNode = GetNodeById(Graph, InputNodeId);

	if (!OutputNode) throw NodeNotFound(OutputNodeId, Graph);
	if (!InputNode) throw NodeNotFound(InputNodeId, Graph);

	// Find pins
	UEdGraphPin* OutPin = OutputNode->FindPin(OutputPinName);
	UEdGraphPin* InPin = InputNode->FindPin(InputPinName);

	if (!OutPin) throw PinNotFound(OutputNode, OutputPinName);
	if (!InPin) throw PinNotFound(InputNode, InputPinName);

	OutPin->BreakLinkTo(InPin);

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

void GraphUtils::SetPinDefaultValue(
	UBlueprint* Blueprint,
	UEdGraph* Graph,
	const FGuid& NodeId,
	const FString& PinName,
	const FString& DefaultValue)
{
	if (!Blueprint)
		throw std::runtime_error("Blueprint is null");
    
	if (!Graph)
		throw std::runtime_error("Graph is null");

	UEdGraphNode* Node = GetNodeById(Graph, NodeId);

	if (!Node)
		throw NodeNotFound(NodeId, Graph);

	UEdGraphPin* Pin = Node->FindPin(PinName);
	if (!Pin)
		throw PinNotFound(Node, PinName);

	// The schema fills DefaultObject for class and object pins and DefaultTextValue for text pins, and tells the node.
	Graph->GetSchema()->TrySetDefaultValue(*Pin, DefaultValue);
	const FName Category = Pin->PinType.PinCategory;
	if (!DefaultValue.IsEmpty() && !Pin->DefaultObject
		&& (Category == UEdGraphSchema_K2::PC_Object || Category == UEdGraphSchema_K2::PC_Class))
		throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("%s is not a valid object or class for pin %s"), *DefaultValue, *PinName)));

	FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
}

