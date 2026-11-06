#include "Route.h"

#include "Route/BpRoute.h"
#include "Route/Function.h"
#include "Route/AssetRoute.h"
#include "Route/EditorRoute.h"
#include "Route/Graph.h"


void BuildRouter(TSharedPtr<HttpApp> App)
{
	BuildBlueprintRouter(App);
	BuildBlueprintFunctionRouter(App);
	BuildAssetRouter(App);
	BuildEditorRouter(App);
	BuildGraphRouter(App);
}
