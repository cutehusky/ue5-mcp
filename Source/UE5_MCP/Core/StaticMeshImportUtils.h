#pragma once

#include "CoreMinimal.h"

class UStaticMesh;
struct FStaticMeshImportReq;

namespace StaticMeshImportUtils
{
	FString SourceJson(const UStaticMesh* Mesh);
	FString Import(const FStaticMeshImportReq& Request);
	FString Reimport(UStaticMesh* Mesh, const FStaticMeshImportReq& Request);
}
