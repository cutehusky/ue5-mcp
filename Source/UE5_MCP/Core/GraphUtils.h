#pragma once

// Utility functions for manipulating Blueprint graphs
class GraphUtils
{
	static UEdGraphNode* GetNodeById(UEdGraph* Graph, const FGuid& NodeId);

	static UClass* FindK2NodeClassByName(const FString& NodeTypeName);
public:
	
#pragma region AddNodes
	// Adds a function / custom event call node to the specified Blueprint's graph, calling the function from the Blueprint's own class
	// Careful: it doesn't check duplicated custom event names, may cause compile errors
	static void AddFunctionCallToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& FunctionName);

	// Adds a function call node to the specified Blueprint's graph, specifying the class to call the function from
	static void AddFunctionCallToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& ClassToCall, const FString& FunctionName);

	// Adds a math function call node to the specified Blueprint's graph, calling the function from UKismetMathLibrary
	static void AddMathFunctionCallToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& FunctionName);

	// Adds an existed event to the specified Blueprint's event graph
	// Careful: it doesn't check duplicated event names, may cause compile errors
	static void AddEventToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& EventName);
	
	// Adds a custom event to the specified Blueprint's graph
	static void AddCustomEventToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& EventName, const FString& EventSignature);

	// Adds a variable get node to the specified Blueprint's graph
	static void AddGetVariableNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& VarName);

	// Adds a variable set node to the specified Blueprint's graph
	static void AddSetVariableNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& VarName);

	// Adds a Break Struct node to the specified Blueprint's graph
	static void AddBreakStructNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& StructTypeName);

	// Adds a Make Struct node to the specified Blueprint's graph
	static void AddMakeStructNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& StructTypeName);

	// Adds a Comment node to the specified Blueprint's graph
	static void AddCommentNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& CommentText);

	// Adds a Switch Enum node to the specified Blueprint's graph
	// static void AddSwitchEnumNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName);

	// Adds a Dynamic Cast node to the specified Blueprint's graph
	static void AddDynamicCastNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName);

	// Adds a Class Cast node to the specified Blueprint's graph
	static void AddClassCastNodeToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName);

	// Adds a Byte to Enum Cast node to the specified Blueprint's graph
	static void AddByteToEnumNodeCastToGraph(UBlueprint* Blueprint, UEdGraph* Graph, const FString& PinTypeName);

	// TODO: Add support for Switch on Name, String, Int nodes
	
	// TODO: Add support for array, set, map operations nodes
	
	// TODO: Add support for UKismetXXXLibrary function nodes
	
	// TODO: Add special nodes handlers here

	// Adds a node by its type name to the specified Blueprint's graph
	// This is fallback method for adding nodes that do not have specific handling implemented
	// For nodes have implemented handling, please use the specific functions above instead
	static void AddNodeByNameToGraph(UBlueprint* Blueprint,
		UEdGraph* Graph,
		const FString& NodeTypeName);

#pragma endregion

	// Returns a list of supported node type names that can be added via AddNodeByNameToGraph
	static TArray<FString> GetSupportedNode();
	
#pragma region PinOperations

	// Connects two pins from two nodes in the specified Blueprint's graph
	static void ConnectPins(UBlueprint* Blueprint,
	                                UEdGraph* Graph,
	                                const FGuid& OutputNodeId,
	                                const FString& OutputPinName,
	                                const FGuid& InputNodeId,
	                                const FString& InputPinName);

	// Breaks the connection between two pins from two nodes in the specified Blueprint's graph
	static void BreakPinConnection(UBlueprint* Blueprint,
	                                   UEdGraph* Graph,
	                                   const FGuid& OutputNodeId,
									const FString& OutputPinName,
									const FGuid& InputNodeId,
									const FString& InputPinName);

	// Sets the default value of a pin from a node in the specified Blueprint's graph
	static void SetPinDefaultValue(UBlueprint* Blueprint, UEdGraph* Graph, const FGuid& NodeId, const FString& PinName,
	                               const FString& DefaultValue);
#pragma endregion
};
