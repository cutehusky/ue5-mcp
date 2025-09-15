#pragma once

class UK2Node_FunctionTerminator;
class UK2Node_FunctionEntry;
class UK2Node_FunctionResult;

class BPUtils
{
	static UEdGraph* CreateFunctionGraph(UBlueprint* Blueprint,
	                                     const FString& FunctionName);
	

	static void GetOrAddEntryAndReturnNodesOfFunctionGraph(UEdGraph* Graph,
	                                 UK2Node_FunctionEntry*& OutEntryNode,
	                                 UK2Node_FunctionResult*& OutReturnNode);
	
public:
	static UBlueprint* LoadBlueprint(const FString& Path);

	static UEdGraph* GetEventGraph(UBlueprint* Blueprint);

	static UEdGraph* GetEventGraph(UBlueprint* Blueprint, const FString& GraphName);

	static UEdGraph* GetFunctionGraph(UBlueprint* Blueprint, const FString& FunctionName);
	
	static void AddFunctionGraph(UBlueprint* Blueprint,
	                           const FString& FunctionName,
	                           const FString& FunctionInputSignature,
	                           const FString& FunctionOutputSignature);
	
	// Careful: this not remove usages of the function in graphs, may cause compile errors
	static void RemoveFunctionGraph(UBlueprint* Blueprint,
								const FString& FunctionName);

	// Careful: this not update usages of the function in graphs, may cause compile errors
	static void EditFunctionGraph(UBlueprint* Blueprint,
	                              const FString& FunctionName,
	                              const FString& FunctionInputSignature,
	                              const FString& FunctionOutputSignature);

	static void CompileBlueprint(UBlueprint* Blueprint);

	// Get all variable names and type in format: 'type name' in the Blueprint
	// If bIncludeAll is true, include all variables including inherited from parent BP classes and C++ classes
	static TArray<FString> GetBlueprintVariables(UBlueprint* Blueprint, bool bIncludeAll = false);

	// Get all function signatures in the Blueprint
	static TArray<FString> GetBlueprintFunctions(UBlueprint* Blueprint);
	
	static void AddVariableToBlueprint(UBlueprint* Blueprint, const FString& VarSignature,
	                                   const FString& DefaultValue);

	static void RenameVariableInBlueprint(UBlueprint* Blueprint, const FString& OldVarName, const FString& NewVarName);

	static void DeleteVariableFromBlueprint(UBlueprint* Blueprint, const FString& VarName);

	static void SetVariableDefaultValueInBlueprint(UBlueprint* Blueprint, const FString& VarName, const FString& DefaultValue);
	
	static FString GetBlueprintGraphJson(UEdGraph* Graph);
	
	static void AddComponentToBlueprintByName(UBlueprint* Blueprint, const FString& ComponentClassName,
	                                          const FString& ComponentVarName, const FString& AttachTo);
	
	static FString GetBlueprintComponentsJson(UBlueprint* Blueprint);

	static void RemoveComponentFromBlueprint(UBlueprint* Blueprint, const FString& ComponentVarName);

	static void RenameComponentInBlueprint(UBlueprint* Blueprint, const FString& OldVarName, const FString& NewVarName);

	static void ChangeAttachToOfComponentInBlueprint(UBlueprint* Blueprint, const FString& ComponentVarName, const FString& NewAttachTo);

	static FString GetComponentsPropertiesJson(UBlueprint* Blueprint, const FString& ComponentVarName);

	static void SetComponentPropertyInBlueprint(UBlueprint* Blueprint, const FString& ComponentVarName,
		const TMap<FString, FString>& Properties);
};
