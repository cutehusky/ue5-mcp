#pragma once
#include "CoreMinimal.h"
#include "IHttpRouter.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonWriter.h"
class UBlueprint;
struct FGameCoreReq;
// What an agent needs to fix its own work: compiler messages, Blueprint breakpoints, and C++ class creation and compile.
namespace DebugFeedbackUtils
{
 // While a breakpoint pauses the game thread, keeps HTTP served, limits it to debug routes, and resumes after a timeout.
 void Install(const TSharedPtr<IHttpRouter>& Router);
 // Compiles and writes status, error and warning counts, and messages. Returns false if the Blueprint has errors.
 bool CompileAndWrite(UBlueprint* Blueprint,const TSharedRef<TJsonWriter<>>& J);
 FString Compile(const FString& AssetPath);
 FString ListBreakpoints(const FString& AssetPath);
 FString EditBreakpoint(const FGameCoreReq& R);
 FString DebugState(const FString& Search,int32 Limit);
 FString DebugControl(const FGameCoreReq& R);
 FString CreateCppClass(const FGameCoreReq& R);
 FString LiveCodingStatus();
 FString LiveCodingCompile(const FGameCoreReq& R);
 // "unavailable", "disabled", "idle" or "compiling".
 FString CxxCompileStatus();
}
