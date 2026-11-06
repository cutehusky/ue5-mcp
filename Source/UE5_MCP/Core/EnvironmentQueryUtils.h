#pragma once
#include "CoreMinimal.h"
struct FEnvironmentQueryReq;
class UEnvQuery;
namespace EnvironmentQueryUtils
{
 UEnvQuery* ValidateForRuntime(const FString& Path);
 FString Inspect(const FString& Path);
 FString Control(const FEnvironmentQueryReq& R,const FString& Operation);
}
