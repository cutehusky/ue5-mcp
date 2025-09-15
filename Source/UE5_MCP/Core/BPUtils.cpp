#include "BPUtils.h"

#include "ClassUtils.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_Event.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_CallFunction.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_FunctionResult.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "ObjUtils.h"
#include "PinUtils.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraph.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraphPin.h"

// TODO: Add support for function metadata (e.g. BlueprintCallable, Category, etc.) ?

// TODO: use skeleton generated class or use generated class directly + compile after modification ? 

UEdGraph* BPUtils::CreateFunctionGraph(UBlueprint* Blueprint, const FString& FunctionName)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");
    
    UClass* BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");
    
    UFunction* NewFunc = NewObject<UFunction>(BPClass, *FunctionName, RF_Public | RF_Transient);
    NewFunc->SetFlags(RF_Public);

    UEdGraph* NewGraph = FBlueprintEditorUtils::CreateNewGraph(
        Blueprint,
        *FunctionName,
        UEdGraph::StaticClass(),
        UEdGraphSchema_K2::StaticClass()
    );

    FBlueprintEditorUtils::AddFunctionGraph<UFunction>(Blueprint, NewGraph, true, NewFunc);
    return NewGraph;
}

void BPUtils::AddFunctionGraph(UBlueprint* Blueprint,
                                     const FString& FunctionName,
                                     const FString& FunctionInputSignature,
                                     const FString& FunctionOutputSignature)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");
    
    if (FunctionName.IsEmpty())
        throw std::runtime_error("Function name cannot be empty");

    if (GetFunctionGraph(Blueprint, FunctionName))
    {
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Function %s already exists in the Blueprint"), *FunctionName)));
    }

    auto NewGraph = CreateFunctionGraph(Blueprint, FunctionName);
    UK2Node_FunctionEntry* EntryNode = nullptr;
    UK2Node_FunctionResult* ReturnNode = nullptr;
    GetOrAddEntryAndReturnNodesOfFunctionGraph(NewGraph, EntryNode, ReturnNode);
    if (!EntryNode || !ReturnNode)
    {
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Failed to get entry/return nodes of function graph %s"), *FunctionName)));
    }
    
    PinUtils::SetupFunctionPins(EntryNode, FunctionInputSignature, false);
    PinUtils::SetupFunctionPins(ReturnNode, FunctionOutputSignature, true);
    
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

void BPUtils::RemoveFunctionGraph(UBlueprint* Blueprint, const FString& FunctionName)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    // Find the function graph by name
    UEdGraph* FunctionGraph = GetFunctionGraph(Blueprint, FunctionName);
    if (!FunctionGraph)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Function %s does not exist in the Blueprint"), *FunctionName)));
    
    // Remove the graph from the Blueprint
    FBlueprintEditorUtils::RemoveGraph(Blueprint, FunctionGraph, EGraphRemoveFlags::Recompile);

    // Mark Blueprint as modified
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

void BPUtils::EditFunctionGraph(UBlueprint* Blueprint, const FString& FunctionName,
    const FString& FunctionInputSignature, const FString& FunctionOutputSignature)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    auto FunctionGraph = GetFunctionGraph(Blueprint, FunctionName);
    if (!FunctionGraph)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Function %s does not exist in the Blueprint"), *FunctionName)));

    if (Blueprint->ParentClass && Blueprint->ParentClass->FindFunctionByName(*FunctionName))
    {
        // It's an override function, do not allow changing signature
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Function %s is an override function, cannot change signature"), *FunctionName)));
    }
    
    UK2Node_FunctionEntry* EntryNode = nullptr;
    UK2Node_FunctionResult* ReturnNode = nullptr;
    GetOrAddEntryAndReturnNodesOfFunctionGraph(FunctionGraph, EntryNode, ReturnNode);
    if (!EntryNode || !ReturnNode)
    {
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Failed to get entry/return nodes of function graph %s"), *FunctionName)));
    }
    
    PinUtils::CleanFunctionPins(EntryNode, ReturnNode);
    PinUtils::SetupFunctionPins(EntryNode, FunctionInputSignature, false);
    PinUtils::SetupFunctionPins(ReturnNode, FunctionOutputSignature, true);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

UEdGraph* BPUtils::GetFunctionGraph(UBlueprint* Blueprint, const FString& FunctionName)
{
    if (!Blueprint)
        return nullptr;

    // Search in Blueprint function graphs
    for (UEdGraph* Graph : Blueprint->FunctionGraphs)
    {
        if (!Graph)
            continue;
        if (Graph->GetName() == FunctionName)
        {
            return Graph;
        }
    }
    return nullptr;
}

void BPUtils::GetOrAddEntryAndReturnNodesOfFunctionGraph(UEdGraph* Graph, UK2Node_FunctionEntry*& EntryNode,
    UK2Node_FunctionResult*& ReturnNode)
{
    EntryNode = nullptr;
    for (UEdGraphNode* Node : Graph->Nodes)
    {
        EntryNode = Cast<UK2Node_FunctionEntry>(Node);
        if (EntryNode)
            break;
    }

    if (!EntryNode)
    {
        FGraphNodeCreator<UK2Node_FunctionEntry> FunctionEntryCreator(*Graph);
        EntryNode = FunctionEntryCreator.CreateNode();
        EntryNode->FunctionReference.SetExternalMember(*Graph->GetName(), nullptr);
        FunctionEntryCreator.Finalize();
        UEdGraphSchema::SetNodeMetaData(EntryNode, FNodeMetadata::DefaultGraphNode);
    }


    ReturnNode = nullptr;
    for (UEdGraphNode* Node : Graph->Nodes)
    {
        ReturnNode = Cast<UK2Node_FunctionResult>(Node);
        if (ReturnNode)
            break;
    }
        
    if (!ReturnNode)
    {
        FGraphNodeCreator<UK2Node_FunctionResult> NodeCreator(*Graph);
        ReturnNode = NodeCreator.CreateNode();
        ReturnNode->FunctionReference = EntryNode->FunctionReference;
        ReturnNode->NodePosX = EntryNode->NodePosX + EntryNode->NodeWidth + 256;
        ReturnNode->NodePosY = EntryNode->NodePosY;
        NodeCreator.Finalize();
        UEdGraphSchema::SetNodeMetaData(ReturnNode, FNodeMetadata::DefaultGraphNode);
    }
}


UBlueprint* BPUtils::LoadBlueprint(const FString& Path)
{
    UObject* LoadedObj = StaticLoadObject(UBlueprint::StaticClass(), nullptr, *Path);
    return Cast<UBlueprint>(LoadedObj);
}

UEdGraph* BPUtils::GetEventGraph(UBlueprint* Blueprint)
{
    return GetEventGraph(Blueprint, "EventGraph");
}


UEdGraph* BPUtils::GetEventGraph(UBlueprint* Blueprint, const FString& GraphName)
{
    if (!Blueprint)
        return nullptr;

    for (UEdGraph* Graph : Blueprint->UbergraphPages)
    {
        if (Graph && Graph->GetFName() == FName(*GraphName))
        {
            return Graph;
        }
    }
    return nullptr;
}


void BPUtils::CompileBlueprint(UBlueprint* Blueprint)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");
   
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

TArray<FString> BPUtils::GetBlueprintVariables(UBlueprint* Blueprint, bool bIncludeAll)
{
    TArray<FString> Vars;
    TArray<FString> SeenVarNames;

    if (!Blueprint)
        return Vars;


    // Get variables defined in the Blueprint itself
    for (const FBPVariableDescription& VarDesc : Blueprint->NewVariables)
    {
        FString TypeName = VarDesc.VarType.PinCategory.ToString();
        if (!VarDesc.VarType.PinSubCategory.IsNone())
        {
            TypeName += FString::Printf(TEXT("<%s>"), *VarDesc.VarType.PinSubCategory.ToString());
        }
        FString VarName = VarDesc.VarName.ToString();
        Vars.Add(FString::Printf(TEXT("%s %s"), *TypeName, *VarName));
        SeenVarNames.Add(VarName);
    }
    
    if (!bIncludeAll)
        return Vars;

    if (UClass* BPClass = Blueprint->GeneratedClass)
    {
        for (TFieldIterator<FProperty> It(BPClass, EFieldIteratorFlags::IncludeSuper); It; ++It)
        {
            FProperty* Prop = *It;

            FString TypeName = Prop->GetCPPType();
            FString VarName = Prop->GetName();

            // Avoid duplicates (some Blueprint variables are mirrored as UPropertys)
            if (!SeenVarNames.Contains(VarName))
            {
                FString Entry = FString::Printf(TEXT("%s %s [ClassVar]"), *TypeName, *VarName);
                Vars.Add(Entry);
            }
        }
    } else
    {
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");
    }

    return Vars;
}

TArray<FString> BPUtils::GetBlueprintFunctions(UBlueprint* Blueprint)
{
    TArray<FString> Funcs;

    if (!Blueprint)
        return Funcs;

    UClass* BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");

    for (TFieldIterator<UFunction> It(BPClass, EFieldIteratorFlags::IncludeSuper); It; ++It)
    {
        UFunction* Func = *It;
        FString Pure = Func->HasAllFunctionFlags(FUNC_BlueprintPure) ? TEXT("[Pure] ") : TEXT("");
        FString Static = Func->HasAllFunctionFlags(FUNC_Static) ? TEXT("static ") : TEXT("");
        FString Sig = Pure + Static + Func->GetName() + TEXT("(");

        bool First = true;

        // Collect input parameters
        for (TFieldIterator<FProperty> ParamIt(Func); ParamIt; ++ParamIt)
        {
            if (!(ParamIt->PropertyFlags & CPF_Parm))
                continue;

            if (!First)
                Sig += TEXT(", ");
            First = false;

            FString Direction;
            if (ParamIt->PropertyFlags & CPF_OutParm
                || ParamIt->PropertyFlags & CPF_ReturnParm)
                Direction = TEXT("out ");
            else
                Direction = TEXT("in ");

            if (ParamIt->PropertyFlags & CPF_ConstParm)
                Direction += TEXT("const ");

            if (ParamIt->PropertyFlags & CPF_ReferenceParm)
                Direction += TEXT("& ");

            Sig += Direction + ParamIt->GetCPPType() + TEXT(" ") + ParamIt->GetName();
        }
        Sig += TEXT(")");
        Funcs.Add(Sig);
    }

    return Funcs;
}


void BPUtils::AddVariableToBlueprint(
    UBlueprint* Blueprint,
    const FString& VarSignature,
    const FString &DefaultValue = FString())
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");
    
    FString VarTypeName, VarName;
    if (!PinUtils::SplitTypeVar(VarSignature, /*out*/ VarTypeName, /*out*/ VarName))
        throw std::runtime_error("Variable signature must be in format: 'type name'");

    VarName = VarName.TrimStartAndEnd();
    if (VarName.IsEmpty())
        throw std::runtime_error("Variable name cannot be empty");
    
    // Build the pin type
    FEdGraphPinType PinType;
    if (!PinUtils::ResolvePinTypeByName(VarTypeName, PinType))
    {
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Unknown variable type: %s"), *VarTypeName)));
    }

    // Add the variable
    if (!FBlueprintEditorUtils::AddMemberVariable(Blueprint, *VarName, PinType, DefaultValue))
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Failed to add variable %s to Blueprint"), *VarName)));

    // Mark blueprint dirty
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

void BPUtils::RenameVariableInBlueprint(UBlueprint* Blueprint, const FString& OldVarName, const FString& NewVarName)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");
    
    if (OldVarName.IsEmpty() || NewVarName.IsEmpty())
        throw std::runtime_error("Variable names cannot be empty");
    
    FName OldName(*OldVarName);
    FName NewName(*NewVarName);

    FBlueprintEditorUtils::RenameMemberVariable(Blueprint, OldName, NewName);
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

void BPUtils::DeleteVariableFromBlueprint(UBlueprint* Blueprint, const FString& VarName)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    FName VarFName(*VarName);
    FBlueprintEditorUtils::RemoveMemberVariable(Blueprint, VarFName);    
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

void BPUtils::SetVariableDefaultValueInBlueprint(UBlueprint* Blueprint, const FString& VarName,
    const FString& DefaultValue)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    auto Var = Blueprint->NewVariables.FindByPredicate(
        [&](const FBPVariableDescription& V) { return V.VarName.ToString() == VarName; });
    if (!Var)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Variable %s not found in Blueprint"), *VarName)));

    Var->DefaultValue = DefaultValue;

    FBlueprintEditorUtils::ValidateBlueprintChildVariables(Blueprint, *VarName);
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

#include "Serialization/JsonWriter.h"

FString BPUtils::GetBlueprintGraphJson(UEdGraph* Graph)
{
    if (!Graph)
        throw std::runtime_error("Graph is null");
    
    FString Output;
    // Serialize graph to JSON
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Output);

    Writer->WriteArrayStart();

    for (UEdGraphNode* Node : Graph->Nodes)
    {
        if (!Node)
            continue;
        
        Writer->WriteObjectStart();

        Writer->WriteValue(FString(TEXT("Id")), Node->NodeGuid.ToString());
        Writer->WriteValue(FString(TEXT("Type")), *Node->GetClass()->GetName());
        
        Writer->WriteArrayStart(FString("Pins"));
        for (UEdGraphPin* Pin : Node->Pins)
        {
            Writer->WriteObjectStart();
            Writer->WriteValue(FString(TEXT("Name")), Pin->GetName());

            auto Dir =  Pin->Direction == EGPD_Input ? FString(TEXT("In")) : FString(TEXT("Out"));

            FString Info;
            FString Container;
            switch (Pin->PinType.ContainerType)
            {
                case EPinContainerType::Array:
                    Container = TEXT("TArray");
                    break;
                case EPinContainerType::Set:
                    Container = TEXT("TSet");
                    break;
                case EPinContainerType::Map:
                    Container = TEXT("TMap");
                    break;
                default:
                    Container = TEXT("");
                    break;
            }
            if (Container.IsEmpty())
                if (Pin->PinType.PinSubCategory.IsNone())
                    Info = FString::Printf(TEXT("%s-%s"), *Pin->PinType.PinCategory.ToString(), *Dir);
                else
                    Info = FString::Printf(TEXT("%s(%s)-%s"), *Pin->PinType.PinCategory.ToString(),
                        *Pin->PinType.PinSubCategory.ToString(),
                        *Dir);
            else
            {
                if (Pin->PinType.PinSubCategory.IsNone())
                    Info = FString::Printf(TEXT("%s<%s>-%s"),
                        *Container, *Pin->PinType.PinCategory.ToString(), *Dir);
                else
                    Info = FString::Printf(TEXT("%s<%s(%s)>-%s"),
                        *Container,
                        *Pin->PinType.PinCategory.ToString(),
                        *Pin->PinType.PinSubCategory.ToString(),
                        *Dir);
            }

            Writer->WriteValue(FString(TEXT("Inf")), Info);
            Writer->WriteValue(FString(TEXT("DefaultVal")), Pin->DefaultValue);

            Writer->WriteArrayStart(FString(TEXT("Link")));
            for (UEdGraphPin* Linked : Pin->LinkedTo)
            {
                Writer->WriteObjectStart();
                Writer->WriteValue(FString(TEXT("Id")), Linked->GetOwningNode()->NodeGuid.ToString());
                Writer->WriteValue(FString(TEXT("PinName")), Linked->GetName());
                Writer->WriteObjectEnd();
            }
            Writer->WriteArrayEnd();

            Writer->WriteObjectEnd();
        }
        Writer->WriteArrayEnd();
        
        Writer->WriteObjectStart(TEXT("Meta"));

        if (auto FuncNode = Cast<UK2Node_CallFunction>(Node))
        {
            Writer->WriteValue(TEXT("IsPure"), FuncNode->IsNodePure());
            Writer->WriteValue(TEXT("FuncName"), FuncNode->FunctionReference.GetMemberName().ToString());
            Writer->WriteValue(TEXT("FuncClass"), FuncNode->FunctionReference.GetMemberParentClass() ? FuncNode->FunctionReference.GetMemberParentClass()->GetName() : TEXT(""));
        }
        else if (auto EventNode = Cast<UK2Node_Event>(Node))
        {
            Writer->WriteValue(TEXT("EventName"), EventNode->EventReference.GetMemberName().ToString());
            Writer->WriteValue(TEXT("EventClass"), EventNode->EventReference.GetMemberParentClass() ? EventNode->EventReference.GetMemberParentClass()->GetName() : TEXT(""));
        }
        else if (auto CustomEventNode = Cast<UK2Node_CustomEvent>(Node))
        {
            Writer->WriteValue(TEXT("EventName"), CustomEventNode->CustomFunctionName.ToString());
        }
        else if (auto VarGetNode = Cast<UK2Node_VariableGet>(Node))
        {
            Writer->WriteValue(TEXT("VarName"), VarGetNode->VariableReference.GetMemberName().ToString());
            Writer->WriteValue(TEXT("VarClass"), VarGetNode->VariableReference.GetMemberParentClass() ? VarGetNode->VariableReference.GetMemberParentClass()->GetName() : TEXT(""));
            // TODO: add Variable type ?
        }
        else if (auto VarSetNode = Cast<UK2Node_VariableSet>(Node))
        {
            Writer->WriteValue(TEXT("VarName"), VarSetNode->VariableReference.GetMemberName().ToString());
            Writer->WriteValue(TEXT("VarClass"), VarSetNode->VariableReference.GetMemberParentClass() ? VarSetNode->VariableReference.GetMemberParentClass()->GetName() : TEXT(""));
            // TODO: add Variable type ?
        }
        
        Writer->WriteObjectEnd();

        Writer->WriteObjectEnd();
    }

    Writer->WriteArrayEnd();
    Writer->Close();

    return Output;
}


#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"

void BPUtils::AddComponentToBlueprintByName(UBlueprint* Blueprint, 
    const FString& ComponentClassName,
    const FString& ComponentVarName, const FString &AttachTo)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    auto BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");

    if (!BPClass->IsChildOf(AActor::StaticClass()))
    {
        throw std::runtime_error("Blueprint's GeneratedClass is not an Actor, cannot add component");
    }

    // Find the UClass from name
    UClass* ComponentClass = ClassUtils::FindClassByName(ComponentClassName);
    if (!ComponentClass || !ComponentClass->IsChildOf(UActorComponent::StaticClass()))
    {
        UE_LOG(LogTemp, Warning, TEXT("Component class %s not found or is not a subclass of UActorComponent"), *ComponentClassName);
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Component class %s not found or is not a subclass of UActorComponent"), *ComponentClassName)));
    }
    
    // Access Blueprint’s construction script
    USimpleConstructionScript* SCS = Blueprint->SimpleConstructionScript;
    if (!SCS)
        throw std::runtime_error("Blueprint's SimpleConstructionScript is null, please compile the Blueprint first");

    // Create node
    USCS_Node* NewNode = SCS->CreateNode(ComponentClass, FName(*ComponentVarName));

    if (!NewNode)
        throw std::runtime_error("Failed to create SCS node");

    // Attach as child to root node (or as root if none exists)
    bool bAttached = false;
    if (ComponentClass->IsChildOf(USceneComponent::StaticClass()))
    {
        if (!AttachTo.IsEmpty())
            for (USCS_Node* Node : SCS->GetAllNodes())
            {
                if (Node && Node->GetVariableName().ToString() == AttachTo)
                {
                    Node->AddChildNode(NewNode);
                    bAttached = true;
                    break;
                }
            }
        
        if (!bAttached)
        {
            if (SCS->GetRootNodes().Num() > 0)
            {
                // Attach to the first root node
                SCS->GetRootNodes()[0]->AddChildNode(NewNode);
                bAttached = true;
            }
        }
    }
    
    if (!bAttached) {
        // If not attaching, add as a root node
        SCS->AddNode(NewNode);
    }

    // Notify editor
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}


FString BPUtils::GetBlueprintComponentsJson(UBlueprint* Blueprint)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    UBlueprintGeneratedClass* BPClass = Cast<UBlueprintGeneratedClass>(Blueprint->GeneratedClass);
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");

    FString ResultString;
    
    TSharedRef<TJsonWriter<>> Writer =
        TJsonWriterFactory<>::Create(&ResultString);

    Writer->WriteObjectStart();

    Writer->WriteArrayStart("NativeComponents");
    // Iterate all native components from CDO
    if (AActor* CDO = Cast<AActor>(BPClass->GetDefaultObject()))
    {
        for (UActorComponent* Comp : CDO->GetComponents())
        {
            if (!Comp)
                continue;
            Writer->WriteObjectStart();
            Writer->WriteValue(TEXT("Name"), Comp->GetName());
            Writer->WriteValue(TEXT("Class"), Comp->GetClass() ? Comp->GetClass()->GetName() : TEXT("None"));
            Writer->WriteValue(TEXT("Attachable"), Comp->IsA<USceneComponent>());
            
            if (auto sceneComp = Cast<USceneComponent>(Comp))
            {
                for (auto socketName : sceneComp->GetAllSocketNames())
                {
                    Writer->WriteValue(TEXT("Socket"), socketName.ToString());
                }
                
                if (!sceneComp->GetAttachSocketName().IsNone())
                    Writer->WriteValue("AttachToSocket", sceneComp->GetAttachSocketName().ToString());
                
                if (sceneComp->GetAttachParent())
                    Writer->WriteValue("AttachToParent", sceneComp->GetAttachParent()->GetName());

                auto children = sceneComp->GetAttachChildren();
                if (children.Num() > 0)
                {
                    Writer->WriteArrayStart(TEXT("AttachChildren"));
                    for (auto child : children)
                    {
                        if (child)
                        {
                            Writer->WriteValue(child->GetName());
                        }
                    }
                    Writer->WriteArrayEnd();
                }
            }
            Writer->WriteObjectEnd();
        }
    }
    Writer->WriteArrayEnd();
    

    Writer->WriteArrayStart(TEXT("BpComponents"));
    // Iterate all SCS nodes
    if (Blueprint->SimpleConstructionScript)
    {
        for (USCS_Node* Node : Blueprint->SimpleConstructionScript->GetAllNodes())
        {
            if (!Node)
                continue;

            Writer->WriteObjectStart();
            Writer->WriteValue(TEXT("Name"), Node->GetVariableName().ToString());
            Writer->WriteValue(TEXT("Class"), Node->ComponentClass ? Node->ComponentClass->GetName() : TEXT("None"));
            Writer->WriteValue(TEXT("Attachable"), Node->ComponentTemplate && Node->ComponentTemplate->IsA<USceneComponent>());
            Writer->WriteValue(TEXT("IsRoot"), Blueprint->SimpleConstructionScript->GetRootNodes().Contains(Node));
            
            Writer->WriteArrayStart(TEXT("Children"));
            for (USCS_Node* Child : Node->GetChildNodes())
            {
                if (Child)
                {
                    Writer->WriteValue(Child->GetVariableName().ToString());
                }
            }
            Writer->WriteArrayEnd();
            
            if (auto sceneComp = Cast<USceneComponent>(Node->ComponentTemplate))
            {
                for (auto socketName : sceneComp->GetAllSocketNames())
                {
                    Writer->WriteValue(TEXT("Socket"), socketName.ToString());
                }
                
                if (!sceneComp->GetAttachSocketName().IsNone())
                    Writer->WriteValue("AttachToSocket", sceneComp->GetAttachSocketName().ToString());
                
                if (sceneComp->GetAttachParent())
                    Writer->WriteValue("AttachToParent", sceneComp->GetAttachParent()->GetName());

                auto children = sceneComp->GetAttachChildren();
                if ( children.Num() > 0)
                {
                    Writer->WriteArrayStart(TEXT("AttachChildren"));
                    for (auto child : children)
                    {
                        if (child)
                        {
                            Writer->WriteValue(child->GetName());
                        }
                    }
                    Writer->WriteArrayEnd();
                }
                
            }
            Writer->WriteObjectEnd();
        }
    }

    Writer->WriteArrayEnd();
    Writer->WriteObjectEnd();
    Writer->Close();

    return ResultString;
}

void BPUtils::RemoveComponentFromBlueprint(UBlueprint* Blueprint, const FString& ComponentVarName)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    USimpleConstructionScript* SCS = Blueprint->SimpleConstructionScript;

    for (USCS_Node* Node : SCS->GetAllNodes())
    {
        if (Node && Node->GetVariableName().ToString() == ComponentVarName)
        {
            SCS->RemoveNode(Node);
            FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
            FKismetEditorUtilities::CompileBlueprint(Blueprint);
            return;
        }
    }

    throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Component %s not found in Blueprint"), *ComponentVarName)));
}

void BPUtils::RenameComponentInBlueprint(UBlueprint* Blueprint, const FString& OldVarName, const FString& NewVarName)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");


    FString TrimmedNewName = NewVarName.TrimStartAndEnd();
    FString TrimmedOldName = OldVarName.TrimStartAndEnd();
    
    if (TrimmedNewName.IsEmpty() || TrimmedOldName.IsEmpty())
        throw std::runtime_error("Component variable names cannot be empty");
    
    for (USCS_Node* Node : Blueprint->SimpleConstructionScript->GetAllNodes())
    {
        if (Node && Node->GetVariableName().ToString() == TrimmedOldName)
        {
            Node->SetVariableName(FName(*TrimmedNewName));
            FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
            FKismetEditorUtilities::CompileBlueprint(Blueprint);
            return;
        }
    }

    throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Component %s not found in Blueprint"), *OldVarName)));
}

void BPUtils::ChangeAttachToOfComponentInBlueprint(UBlueprint* Blueprint,
    const FString& ComponentVarName,
    const FString& NewAttachTo)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    USimpleConstructionScript* SCS = Blueprint->SimpleConstructionScript;
    USCS_Node* TargetNode = nullptr;
    USCS_Node* NewParentNode = nullptr;
    USCS_Node* OldParentNode = nullptr;
    for (USCS_Node* Node : SCS->GetAllNodes())
    {
        if (Node && Node->GetChildNodes().Contains(TargetNode))
        {
            OldParentNode = Node;
        }
        
        if (Node && Node->GetVariableName().ToString() == ComponentVarName)
        {
            TargetNode = Node;
        }
        
        if (Node && Node->GetVariableName().ToString() == NewAttachTo)
        {
            NewParentNode = Node;
        }
        
        if (TargetNode && OldParentNode && (NewParentNode || NewAttachTo.IsEmpty()))
            break;
    }
    
    if (!TargetNode)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Component %s not found in Blueprint"), *ComponentVarName)));
    
    if (!NewAttachTo.IsEmpty() && !NewParentNode)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("AttachTo component %s not found in Blueprint"), *NewAttachTo)));

    if (NewParentNode) // Attach to new parent
    {
        
        if (NewParentNode == TargetNode ||
            NewParentNode->GetVariableName() == TargetNode->GetVariableName())
            throw std::runtime_error("Cannot attach component to itself");
        
        // Detach from old parent
        if (OldParentNode)
        {
            if (OldParentNode == NewParentNode
                || OldParentNode->GetVariableName() == NewParentNode->GetVariableName())
                return; // No change
            
            OldParentNode->RemoveChildNode(TargetNode);
        }
        else
        {
            SCS->RemoveNode(TargetNode);
        }
        
        if (!NewParentNode->GetChildNodes().Contains(TargetNode))
            NewParentNode->AddChildNode(TargetNode);
    }
    else // Detach to root
    {
        if (OldParentNode)
        {
            OldParentNode->RemoveChildNode(TargetNode);
        }
        
        if (!SCS->GetRootNodes().Contains(TargetNode))
            SCS->AddNode(TargetNode);
    }
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
}

FString BPUtils::GetComponentsPropertiesJson(UBlueprint* Blueprint, const FString& ComponentVarName)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");
   
    // Bp component
    if (Blueprint->SimpleConstructionScript)
    {
        for (USCS_Node* Node : Blueprint->SimpleConstructionScript->GetAllNodes())
        {
            if (Node && Node->GetVariableName().ToString() == ComponentVarName && Node->ComponentTemplate)
            {
                return ObjUtils::SerializeObjectToJson(Node->ComponentTemplate);
            }
        }
    }

    auto BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");
  
    // Native component
    auto Prop = BPClass->FindPropertyByName(*ComponentVarName);
    if (!Prop)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Component %s not found in Blueprint"), *ComponentVarName)));
    
    UObject* CDO = BPClass->GetDefaultObject();
    if (!CDO)
        throw std::runtime_error("Failed to get Blueprint's CDO");

    if (FObjectProperty* ObjProp = CastField<FObjectProperty>(Prop))
    {
        UObject* Obj = ObjProp->GetObjectPropertyValue_InContainer(CDO);
        if (UActorComponent* Component = Cast<UActorComponent>(Obj))
        {
            return ObjUtils::SerializeObjectToJson(Component);
        }
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s is not found in CD0"), *ComponentVarName)));
    }
    
    throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s is not a component"), *ComponentVarName)));
}

void BPUtils::SetComponentPropertyInBlueprint(
    UBlueprint* Blueprint, const FString& ComponentVarName,
    const TMap<FString, FString>& Properties)
{
    if (!Blueprint)
        throw std::runtime_error("Blueprint is null");

    if (Blueprint->SimpleConstructionScript) {
        for (USCS_Node* Node : Blueprint->SimpleConstructionScript->GetAllNodes())
        {
            if (Node && Node->GetVariableName().ToString() == ComponentVarName && Node->ComponentTemplate)
            {
                for (const auto& [PropertyPath, PropertyValue] : Properties)
                {
                    ObjUtils::SetPropertyValueFromString(Node->ComponentTemplate, PropertyPath, PropertyValue);
                }
                FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
                FKismetEditorUtilities::CompileBlueprint(Blueprint);
                return;
            }
        }
    }

    auto BPClass = Blueprint->GeneratedClass;
    if (!BPClass)
        throw std::runtime_error("Blueprint's GeneratedClass is null, please compile the Blueprint first");

    auto Prop = BPClass->FindPropertyByName(*ComponentVarName);
    if (!Prop)
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Component %s not found in Blueprint"), *ComponentVarName)));
    
    auto CDO = BPClass->GetDefaultObject();
    if (!CDO)
        throw std::runtime_error("Failed to get Blueprint's CDO");

    if (FObjectProperty* ObjProp = CastField<FObjectProperty>(Prop))
    {
        UObject* Obj = ObjProp->GetObjectPropertyValue_InContainer(CDO);
        if (UActorComponent* Component = Cast<UActorComponent>(Obj))
        {
            for (const auto& [PropertyPath, PropertyValue] : Properties)
            {
                ObjUtils::SetPropertyValueFromString(Component, PropertyPath, PropertyValue);
            }
            FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
            FKismetEditorUtilities::CompileBlueprint(Blueprint);
            return;
        }
        throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s is not found in CD0"), *ComponentVarName)));
    }
    
    throw std::runtime_error(TCHAR_TO_UTF8(*FString::Printf(TEXT("Property %s is not a component"), *ComponentVarName)));
}
