#include "PinUtils.h"

#include "ClassUtils.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_FunctionResult.h"
#include "K2Node_FunctionTerminator.h"


bool PinUtils::ResolvePinTypeByName(const FString& TypeStr, FEdGraphPinType& OutPinType)
{
    FString CleanType = TypeStr.TrimStartAndEnd();

    if (CleanType.IsEmpty())
        return false;

    // --- Match TArray<InnerType> ---
    {
        FRegexPattern Pattern(TEXT(R"(TArray<\s*(.+)\s*>)"));
        FRegexMatcher Matcher(Pattern, CleanType);
        if (Matcher.FindNext())
        {
            FString InnerType = Matcher.GetCaptureGroup(1);
            FEdGraphPinType InnerPinType;
            if (ResolvePinTypeByName(InnerType, InnerPinType))
            {
                OutPinType = InnerPinType;
                OutPinType.ContainerType = EPinContainerType::Array;
                return true;
            }
        }
    }

    // --- Match TSet<InnerType> ---
    {
        FRegexPattern Pattern(TEXT(R"(TSet<\s*(.+)\s*>)"));
        FRegexMatcher Matcher(Pattern, CleanType);
        if (Matcher.FindNext())
        {
            FString InnerType = Matcher.GetCaptureGroup(1);
            FEdGraphPinType InnerPinType;
            if (ResolvePinTypeByName(InnerType, InnerPinType))
            {
                OutPinType = InnerPinType;
                OutPinType.ContainerType = EPinContainerType::Set;
                return true;
            }
        }
    }

    // --- Match TMap<KeyType, ValueType> ---
    {
        FRegexPattern Pattern(TEXT(R"(TMap<\s*([^,]+)\s*,\s*(.+)\s*>)"));
        FRegexMatcher Matcher(Pattern, CleanType);
        if (Matcher.FindNext())
        {
            FString KeyType = Matcher.GetCaptureGroup(1).TrimStartAndEnd();
            FString ValueType = Matcher.GetCaptureGroup(2).TrimStartAndEnd();

            FEdGraphPinType KeyPinType, ValuePinType;
            if (ResolvePinTypeByName(KeyType, KeyPinType) &&
                ResolvePinTypeByName(ValueType, ValuePinType))
            {
                OutPinType = ValuePinType;
                OutPinType.ContainerType = EPinContainerType::Map;

                // Store key type in PinValueType
                OutPinType.PinValueType.TerminalCategory = KeyPinType.PinCategory;
                OutPinType.PinValueType.TerminalSubCategory = KeyPinType.PinSubCategory;
                OutPinType.PinValueType.TerminalSubCategoryObject = KeyPinType.PinSubCategoryObject;

                return true;
            }
        }
    }

    // --- UObject* ---
    if (CleanType.EndsWith(TEXT("*")))
    {
        FString ClassName = CleanType.LeftChop(1);
        if (UClass* FoundClass = ClassUtils::FindClassByName(ClassName))
        {
            OutPinType.PinCategory = UEdGraphSchema_K2::PC_Object;
            OutPinType.PinSubCategoryObject = FoundClass;
            return true;
        }
    }

    // --- Built-in types ---
    if (CleanType == "uint8" || CleanType == "byte")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Byte;
        return true;
    }

    if (CleanType == "int32" || CleanType == "int")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Int;
        return true;
    }
    
    if (CleanType == "int64" || CleanType == "long")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Int64;
        return true;
    }
    
    if (CleanType == "float")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Real;
        OutPinType.PinSubCategory = UEdGraphSchema_K2::PC_Float;
        return true;
    }
    if (CleanType == "double")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Real;
        OutPinType.PinSubCategory = UEdGraphSchema_K2::PC_Double;
        return true;
    }
    if (CleanType == "bool")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Boolean;
        return true;
    }
    if (CleanType == "FString")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_String;
        return true;
    }
    if (CleanType == "FName")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Name;
        return true;
    }
    if (CleanType == "FText")
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Text;
        return true;
    }

    // --- Structs ---
    if (UScriptStruct* Struct = FindObject<UScriptStruct>(ANY_PACKAGE, *CleanType))
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
        OutPinType.PinSubCategoryObject = Struct;
        return true;
    }

    // --- Enums ---
    if (UEnum* Enum = FindObject<UEnum>(ANY_PACKAGE, *CleanType))
    {
        OutPinType.PinCategory = UEdGraphSchema_K2::PC_Byte;
        OutPinType.PinSubCategoryObject = Enum;
        return true;
    }

    // --- Fallback ---
    OutPinType.PinCategory = UEdGraphSchema_K2::PC_Wildcard;
    return false;
}


void PinUtils::SetupFunctionPins(UK2Node_FunctionTerminator* Node,
                                const FString& Signature, bool bIsInput)
{
    if (Signature.IsEmpty())
        return;

    if (!Node)
        return;
    
    TArray<FString> Params;
    FEdGraphPinType PinType;
    Signature.ParseIntoArray(Params, TEXT(","), true);
    for (const FString& ParamStr : Params)
    {
        FString TypeName, VarName;
        if (!SplitTypeVar(ParamStr, TypeName, VarName))
        {
            UE_LOG(LogTemp, Warning, TEXT("Invalid parameter: %s"), *ParamStr);
            continue;
        }
        
        VarName = VarName.TrimStartAndEnd();
        
        if (VarName.IsEmpty())
        {
            UE_LOG(LogTemp, Warning, TEXT("Invalid parameter: %s"), *ParamStr);
            continue;
        }
        
        if (ResolvePinTypeByName(TypeName, PinType))
        {
            Node->CreateUserDefinedPin(*VarName, PinType, bIsInput ? EGPD_Input : EGPD_Output, false);
        } else
        {
            UE_LOG(LogTemp, Warning, TEXT("Unknown type: %s"), *TypeName);
        }
    }
}

void PinUtils::CleanFunctionPins(UK2Node_FunctionEntry* EntryNode, UK2Node_FunctionResult* ReturnNode)
{
    if (!EntryNode || !ReturnNode)
        return;

    // --- Clean old input pins from Entry ---
    for (int32 i = EntryNode->Pins.Num() - 1; i >= 0; --i)
    {
        UEdGraphPin* Pin = EntryNode->Pins[i];
        if (Pin && Pin->Direction == EGPD_Output && !Pin->bOrphanedPin
            &&  Pin->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
        {
            Pin->BreakAllPinLinks(true);    // disconnect
            EntryNode->RemoveUserDefinedPinByName(Pin->PinName);
        }
    }

    // --- Clean old output pins from Return ---
    for (int32 i = ReturnNode->Pins.Num() - 1; i >= 0; --i)
    {
        UEdGraphPin* Pin = ReturnNode->Pins[i];
        if (Pin && Pin->Direction == EGPD_Input && !Pin->bOrphanedPin
            &&  Pin->PinType.PinCategory != UEdGraphSchema_K2::PC_Exec)
        {
            Pin->BreakAllPinLinks(true);
            ReturnNode->RemoveUserDefinedPinByName(Pin->PinName);
        }
    }
}

bool PinUtils::SplitTypeVar(const FString& Signature, FString& OutType, FString& OutVar)
{
    auto Trimmed = Signature.TrimStartAndEnd();
    
    FRegexPattern Pattern(TEXT(R"(^(.+)\s+(\w+)$)"));
    FRegexMatcher Matcher(Pattern, Trimmed);

    if (Matcher.FindNext())
    {
        OutType = Matcher.GetCaptureGroup(1).TrimStartAndEnd();
        OutVar  = Matcher.GetCaptureGroup(2).TrimStartAndEnd();
        return true;
    }
    
    OutType.Empty();
    OutVar.Empty();
    return false;
}
