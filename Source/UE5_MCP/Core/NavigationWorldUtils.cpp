#include "NavigationWorldUtils.h"
#include "Editor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include <stdexcept>
UWorld* NavigationWorldUtils::Resolve(const FString& Context,int32 PIEInstance)
{
	if(Context==TEXT("editor"))
	{
		if(PIEInstance!=-1) throw std::runtime_error("PIEInstance is only valid for world_context=pie");
		auto* W=GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if(!W || W->WorldType!=EWorldType::Editor) throw std::runtime_error("An active editor world is required"); return W;
	}
	if(Context!=TEXT("pie") || PIEInstance < -1 || !GEngine) throw std::runtime_error("WorldContext requires editor or pie, with PIEInstance >= -1");
	UWorld* Match=nullptr;
	for(const auto& C:GEngine->GetWorldContexts()) if(C.WorldType==EWorldType::PIE && C.World() && (PIEInstance==-1 || C.PIEInstance==PIEInstance))
	{
		if(Match) throw std::runtime_error("Multiple PIE worlds match; select an explicit PIEInstance"); Match=C.World();
	}
	if(!Match) throw std::runtime_error("No matching active PIE world"); return Match;
}
